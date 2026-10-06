# P04 — File ingestion, provider downloads and exchange data

- **Source:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`; current-only source inventory `docs/dev/evidence/p00-inventory.json`.
- **Dependencies:** P03.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.
- **UI completion:** Applicable features finish with backend + retained UI connected; preserve layouts. Production mocks cannot substitute for capability execution; keep a task unchecked while transport/contracts or required controls are unresolved.
- **Connected verification:** Use an isolated real host and temporary data. Existing mock-only/browser-API-blocking suites are UI regressions, not connected acceptance. Run `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build` after actual UI source changes.



- **Donor baseline:** SQX145 Dev 1 only; all source fingerprints and member seeds use `SQX_145_REFERENCE_ROOT`. Missing bodies remain prerequisites.
- **Scope:** 23 tasks; current archive allocations and resource/integration tasks only.

# 4.1 FEAT-DATA-SOURCE-HTTPASYNCCLIENT - httpasyncclient-4.1.4.jar

## 1. Objective

- **Goal:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/httpasyncclient-4.1.4.jar`; 86 raw class entries; SHA-256 `50e981a8e567a16ebdad104605b156540a863459fa127b8ba647f310dfc83ef8`.
- **Inspected reference:** [httpasyncclient-4.1.4.md](sqx/Libraries/httpasyncclient-4.1.4.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/httpasyncclient-4.1.4.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/httpasyncclient-4.1.4.jar" org.apache.http.impl.nio.client.AbstractClientExchangeHandler`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/integrations/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider HTTP transport and caching; bound timeouts/retries and validate usage; downstream P13,P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Create:** `app/host/integrations/http.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/integrations/retry.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/integrations/rate_limit.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/host/integrations/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_httpasyncclient.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_httpasyncclient.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx; verify timeout, status mapping, cache revalidation and connection release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-DATA-SOURCE-HTTPASYNCCLIENT-ABSTRACT-CLIENT-EXCHANGE-HANDLER-CONTRACT` → `org.apache.http.impl.nio.client.AbstractClientExchangeHandler`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-DATA-SOURCE-HTTPASYNCCLIENT-ABSTRACT-CLIENT-EXCHANGE-HANDLER-GET-ID` → `org.apache.http.impl.nio.client.AbstractClientExchangeHandler.getId()J`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-HTTPASYNCCLIENT-ABSTRACT-CLIENT-EXCHANGE-HANDLER-IS-COMPLETED` → `org.apache.http.impl.nio.client.AbstractClientExchangeHandler.isCompleted()Z`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_httpasyncclient.py --no-cov`; expect timeout, status mapping, cache revalidation and connection release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture timeout, status mapping, cache revalidation and connection release and visible failures.


# 4.2 FEAT-DATA-SOURCE-HTTPCLIENT-CACHE - httpclient-cache-4.5.13.jar

## 1. Objective

- **Goal:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/httpclient-cache-4.5.13.jar`; 83 raw class entries; SHA-256 `66cefdee7475985256af680bf3ae7cd5d7d42e8fdeb939a6277922e1bdeed43a`.
- **Inspected reference:** [httpclient-cache-4.5.13.md](sqx/Libraries/httpclient-cache-4.5.13.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/httpclient-cache-4.5.13.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/httpclient-cache-4.5.13.jar" org.apache.http.client.cache.CacheResponseStatus`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/integrations/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider HTTP transport and caching; bound timeouts/retries and validate usage; downstream P13,P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/integrations/http.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/retry.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/rate_limit.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/README.md` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_httpclient_cache.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_httpclient_cache.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx; verify timeout, status mapping, cache revalidation and connection release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-DATA-SOURCE-HTTPCLIENT-CACHE-CACHE-RESPONSE-STATUS-CONTRACT` → `org.apache.http.client.cache.CacheResponseStatus`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-DATA-SOURCE-HTTPCLIENT-CACHE-CACHE-RESPONSE-STATUS-VALUES` → `org.apache.http.client.cache.CacheResponseStatus.values()[Lorg/apache/http/client/cache/CacheResponseStatus;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-HTTPCLIENT-CACHE-CACHE-RESPONSE-STATUS-VALUE-OF` → `org.apache.http.client.cache.CacheResponseStatus.valueOf(Ljava/lang/String;)Lorg/apache/http/client/cache/CacheResponseStatus;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_httpclient_cache.py --no-cov`; expect timeout, status mapping, cache revalidation and connection release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture timeout, status mapping, cache revalidation and connection release and visible failures.


# 4.3 FEAT-DATA-SOURCE-HTTPCLIENT - httpclient-4.5.13.jar

## 1. Objective

- **Goal:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/httpclient-4.5.13.jar`; 470 raw class entries; SHA-256 `6fe9026a566c6a5001608cf3fc32196641f6c1e5e1986d1037ccdbd5f31ef743`.
- **Inspected reference:** [httpclient-4.5.13.md](sqx/Libraries/httpclient-4.5.13.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/httpclient-4.5.13.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/httpclient-4.5.13.jar" org.apache.http.auth.AUTH`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/integrations/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider HTTP transport and caching; bound timeouts/retries and validate usage; downstream P13,P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/integrations/http.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/retry.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/rate_limit.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/README.md` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_httpclient.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_httpclient.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx; verify timeout, status mapping, cache revalidation and connection release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-DATA-SOURCE-HTTPCLIENT-AUTH-CONTRACT` → `org.apache.http.auth.AUTH`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_httpclient.py --no-cov`; expect timeout, status mapping, cache revalidation and connection release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture timeout, status mapping, cache revalidation and connection release and visible failures.


# 4.4 FEAT-DATA-SOURCE-HTTPCORE-NIO - httpcore-nio-4.4.13.jar

## 1. Objective

- **Goal:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/httpcore-nio-4.4.13.jar`; 242 raw class entries; SHA-256 `71fcfbe869002c48563cc5979fc734571c8d0d167ccce42970c932f337981f19`.
- **Inspected reference:** [httpcore-nio-4.4.13.md](sqx/Libraries/httpcore-nio-4.4.13.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/httpcore-nio-4.4.13.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/httpcore-nio-4.4.13.jar" org.apache.http.impl.nio.DefaultClientIOEventDispatch`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/integrations/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider HTTP transport and caching; bound timeouts/retries and validate usage; downstream P13,P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/integrations/http.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/retry.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/rate_limit.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/README.md` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_httpcore_nio.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_httpcore_nio.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx; verify timeout, status mapping, cache revalidation and connection release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-DATA-SOURCE-HTTPCORE-NIO-DEFAULT-CLIENT-IOEVENT-DISPATCH-CONTRACT` → `org.apache.http.impl.nio.DefaultClientIOEventDispatch`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 8:** `FR-DATA-SOURCE-HTTPCORE-NIO-DEFAULT-CLIENT-IOEVENT-DISPATCH-CREATE-BYTE-BUFFER-ALLOCATOR` → `org.apache.http.impl.nio.DefaultClientIOEventDispatch.createByteBufferAllocator()Lorg/apache/http/nio/util/ByteBufferAllocator;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-HTTPCORE-NIO-DEFAULT-CLIENT-IOEVENT-DISPATCH-CREATE-HTTP-RESPONSE-FACTORY` → `org.apache.http.impl.nio.DefaultClientIOEventDispatch.createHttpResponseFactory()Lorg/apache/http/HttpResponseFactory;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_httpcore_nio.py --no-cov`; expect timeout, status mapping, cache revalidation and connection release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture timeout, status mapping, cache revalidation and connection release and visible failures.


# 4.5 FEAT-DATA-SOURCE-HTTPCORE - httpcore-4.4.13.jar

## 1. Objective

- **Goal:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/libs/httpcore-4.4.13.jar`; 253 raw class entries; SHA-256 `e06e89d40943245fcfa39ec537cdbfce3762aecde8f9c597780d2b00c2b43424`.
- **Inspected reference:** [httpcore-4.4.13.md](sqx/Libraries/httpcore-4.4.13.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/libs/httpcore-4.4.13.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/libs/httpcore-4.4.13.jar" org.apache.http.ConnectionClosedException`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/host/integrations/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider HTTP transport and caching; bound timeouts/retries and validate usage; downstream P13,P16,P17.
- **Dependency:** qualify stdlib/declared packages; approve additions; classify JVM-only internals.

- **UI disposition:** Infrastructure only; no standalone UI component found in this library allocation. Its owned backend consumer feeds Data Manager through the phase integration gate; do not invent a library screen or direct plugin route.

## 3. File Changes

- **Modify:** `app/host/integrations/http.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/retry.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/rate_limit.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Implement this feature's consumed typed contracts.
- **Modify:** `app/host/integrations/README.md` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_httpcore.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_httpcore.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Provide bounded HTTP sessions, streaming, retries and rate policies through httpx; verify timeout, status mapping, cache revalidation and connection release.
- [ ] **Step 4:** Wire qualified adapters to consumers; release resources on failure/shutdown.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Verify UI-facing consumer contract: Test this infrastructure through its declared backend/host consumer; expose failures through the owning domain envelope. The phase's connected UI gate verifies the observable workflow.


- [ ] **Step 7:** `FR-DATA-SOURCE-HTTPCORE-CONNECTION-CLOSED-EXCEPTION-CONTRACT` → `org.apache.http.ConnectionClosedException`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_httpcore.py --no-cov`; expect timeout, status mapping, cache revalidation and connection release; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture timeout, status mapping, cache revalidation and connection release and visible failures.


# 4.6 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE - CryptoExchangeBinance.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance/CryptoExchangeBinance.jar`; 1 raw class entries; SHA-256 `f61657cfd2d188cba920a733bdf0810138e8aa702fc8e38d47bf55b352646edb`.
- **Inspected reference:** [CryptoExchangeBinance.md](sqx/DataManager/CryptoExchangeBinance.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance/CryptoExchangeBinance.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance/CryptoExchangeBinance.jar" com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangeBinance/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinance`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinance/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinance/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinance/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_binance.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_binance.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-binance.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-CRYPTO-EXCHANGE-BINANCE-PLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-CRYPTO-EXCHANGE-BINANCE-PLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-CRYPTO-EXCHANGE-BINANCE-PLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.Binance.CryptoExchangeBinancePlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_binance.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-binance.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.7 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-COIN-M - CryptoExchangeBinanceCoinM.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM/CryptoExchangeBinanceCoinM.jar`; 1 raw class entries; SHA-256 `c4c52e21237bbfa6ebbfb00c51aaba93e54e7d91cc96bc844ca5b48e9e81daa5`.
- **Inspected reference:** [CryptoExchangeBinanceCoinM.md](sqx/DataManager/CryptoExchangeBinanceCoinM.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM/CryptoExchangeBinanceCoinM.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM/CryptoExchangeBinanceCoinM.jar" com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceCoinM/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceCoinM`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceCoinM/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceCoinM/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceCoinM/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_binance_coin_m.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_binance_coin_m.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-binance-coin-m.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-COIN-M-CRYPTO-EXCHANGE-BINANCE-COIN-MPLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-COIN-M-CRYPTO-EXCHANGE-BINANCE-COIN-MPLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-COIN-M-CRYPTO-EXCHANGE-BINANCE-COIN-MPLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceCoinM.CryptoExchangeBinanceCoinMPlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_binance_coin_m.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-binance-coin-m.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-COIN-M; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.8 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-USDT-M - CryptoExchangeBinanceUsdtM.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM/CryptoExchangeBinanceUsdtM.jar`; 1 raw class entries; SHA-256 `a0b5651358f2f617be7f10294346820f06a91f99b1aeac448c88bdb455d2a092`.
- **Inspected reference:** [CryptoExchangeBinanceUsdtM.md](sqx/DataManager/CryptoExchangeBinanceUsdtM.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM/CryptoExchangeBinanceUsdtM.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM/CryptoExchangeBinanceUsdtM.jar" com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceUsdtM/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBinanceUsdtM`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceUsdtM/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceUsdtM/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBinanceUsdtM/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_binance_usdt_m.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_binance_usdt_m.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-binance-usdt-m.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-USDT-M-CRYPTO-EXCHANGE-BINANCE-USDT-MPLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-USDT-M-CRYPTO-EXCHANGE-BINANCE-USDT-MPLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-USDT-M-CRYPTO-EXCHANGE-BINANCE-USDT-MPLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM.CryptoExchangeBinanceUsdtMPlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_binance_usdt_m.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-binance-usdt-m.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BINANCE-USDT-M; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.9 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BITFINEX - CryptoExchangeBitfinex.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex/CryptoExchangeBitfinex.jar`; 1 raw class entries; SHA-256 `6ff09545942c0fd51dd9e4d5d3ee2ffd95022c9cedee49d1faecaa01e00cfeee`.
- **Inspected reference:** [CryptoExchangeBitfinex.md](sqx/DataManager/CryptoExchangeBitfinex.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex/CryptoExchangeBitfinex.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex/CryptoExchangeBitfinex.jar" com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangeBitfinex/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeBitfinex`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBitfinex/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBitfinex/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeBitfinex/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_bitfinex.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_bitfinex.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-bitfinex.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BITFINEX-CRYPTO-EXCHANGE-BITFINEX-PLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BITFINEX-CRYPTO-EXCHANGE-BITFINEX-PLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-BITFINEX-CRYPTO-EXCHANGE-BITFINEX-PLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.Bitfinex.CryptoExchangeBitfinexPlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_bitfinex.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-bitfinex.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-BITFINEX; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.10 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-COINBASE-PRO - CryptoExchangeCoinbasePro.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro/CryptoExchangeCoinbasePro.jar`; 1 raw class entries; SHA-256 `fcec4232af5eccc490262dae6ea853be6edbf8e02d341ac784d1bf222add7a05`.
- **Inspected reference:** [CryptoExchangeCoinbasePro.md](sqx/DataManager/CryptoExchangeCoinbasePro.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro/CryptoExchangeCoinbasePro.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro/CryptoExchangeCoinbasePro.jar" com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangeCoinbasePro/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangeCoinbasePro`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeCoinbasePro/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeCoinbasePro/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangeCoinbasePro/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_coinbase_pro.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_coinbase_pro.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-coinbase-pro.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-COINBASE-PRO-CRYPTO-EXCHANGE-COINBASE-PRO-PLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-COINBASE-PRO-CRYPTO-EXCHANGE-COINBASE-PRO-PLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-COINBASE-PRO-CRYPTO-EXCHANGE-COINBASE-PRO-PLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro.CryptoExchangeCoinbaseProPlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_coinbase_pro.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-coinbase-pro.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-COINBASE-PRO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.11 FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-POLONIEX - CryptoExchangePoloniex.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex/CryptoExchangePoloniex.jar`; 1 raw class entries; SHA-256 `17330cbe60fbd5a601ef69ffd9d8c6d751143dbdbc6760f0619d4dfad0fad136`.
- **Inspected reference:** [CryptoExchangePoloniex.md](sqx/DataManager/CryptoExchangePoloniex.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex/CryptoExchangePoloniex.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex/CryptoExchangePoloniex.jar" com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/Crypto/CryptoExchangePoloniex/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Exchange data adapter; reassess current API/availability before execution; downstream P16.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/CryptoExchangePoloniex`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`.
- **Existing UI connection:** crypto provider; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/Crypto/CryptoExchangePoloniex/client.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangePoloniex/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/Crypto/CryptoExchangePoloniex/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_crypto_exchange_poloniex.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_crypto_exchange_poloniex.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-crypto-exchange-poloniex.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-POLONIEX-CRYPTO-EXCHANGE-POLONIEX-PLUGIN-CONTRACT` → `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-POLONIEX-CRYPTO-EXCHANGE-POLONIEX-PLUGIN-GET-NAME` → `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin.getName()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-CRYPTO-EXCHANGE-POLONIEX-CRYPTO-EXCHANGE-POLONIEX-PLUGIN-GET-SYMBOLS` → `com.strategyquant.plugin.CryptoExchange.impl.Poloniex.CryptoExchangePoloniexPlugin.getSymbols()Lorg/json/JSONArray;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_crypto_exchange_poloniex.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-crypto-exchange-poloniex.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-CRYPTO-EXCHANGE-POLONIEX; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.12 FEAT-DATA-SOURCE-DATA-SOURCE-CRYPTO - DataSourceCrypto.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCrypto.jar`; 3 raw class entries; SHA-256 `0fc7ef50935978a05bd392601a7a22eb1a1a67e541300eae56386acfb3790d79`.
- **Inspected reference:** [DataSourceCrypto.md](sqx/DataManager/DataSourceCrypto.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCrypto.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCrypto.jar" com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceCrypto/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/DataSourceCryptoService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/add/addPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceCrypto/import/importPopupCtrl.js`.
- **Existing UI connection:** crypto provider; exact retained source-map `ui/app/plugins/data_source/Crypto/source-map.json`. Target `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`; wire exchange/symbol catalog, provider capability selection and backend download jobs.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceCrypto/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceCrypto/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceCrypto/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceCrypto/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_crypto.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_crypto.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Crypto/DataSourceCryptoService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Crypto/cryptoStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Crypto/import/importPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Crypto/add/addPopup.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display exchange/symbol catalog, provider capability selection and backend download jobs from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-crypto.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind exchange/symbol catalog, provider capability selection and backend download jobs to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-CRYPTO-DATA-SOURCE-CRYPTO-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-CRYPTO-DATA-SOURCE-CRYPTO-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-CRYPTO-DATA-SOURCE-CRYPTO-SERVLET-ON-GET-EXCHANGES` → `com.strategyquant.plugin.DataSource.impl.Crypto.DataSourceCryptoServlet.onGetExchanges(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_crypto.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-crypto.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise crypto provider for FEAT-DATA-SOURCE-DATA-SOURCE-CRYPTO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.13 FEAT-DATA-SOURCE-DATA-SOURCE-DARWINEX - DataSourceDarwinex.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar`; 8 raw class entries; SHA-256 `572bfd20f193133a71cd02ffffccaaa69d9b46ca0463dfc4ce8b74fb911b8e3a`.
- **Inspected reference:** [DataSourceDarwinex.md](sqx/DataManager/DataSourceDarwinex.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DataSourceDarwinex.jar" com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceDarwinex/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/DarwinexService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/add/addPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDarwinex/download/downloadPopupCtrl.js`.
- **Existing UI connection:** Darwinex provider; exact retained source-map `ui/app/plugins/data_source/Darwinex/source-map.json`. Target `ui/app/plugins/data_source/Darwinex/DarwinexService.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceDarwinex/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDarwinex/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDarwinex/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDarwinex/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_darwinex.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_darwinex.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Darwinex/DarwinexService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Darwinex/darwinexStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Darwinex/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Darwinex/download/downloadPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Darwinex/add/addPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-darwinex.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-DARWINEX-DARWINEX-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-DARWINEX-DARWINEX-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-DARWINEX-DARWINEX-SERVLET-ON-ADD-CANCEL` → `com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexServlet.onAddCancel()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_darwinex.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-darwinex.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Darwinex provider for FEAT-DATA-SOURCE-DATA-SOURCE-DARWINEX; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.14 FEAT-DATA-SOURCE-DATA-SOURCE-DUKASCOPY - DataSourceDukascopy.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar`; 6 raw class entries; SHA-256 `40b61a3670af7fcf1265fa2d07889d6c75df100b96dd1d73b64c8de793e6913c`.
- **Inspected reference:** [DataSourceDukascopy.md](sqx/DataManager/DataSourceDukascopy.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DataSourceDukascopy.jar" com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceDukascopy/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/DukascopyService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/add/addPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceDukascopy/import/importPopupCtrl.js`.
- **Existing UI connection:** Dukascopy provider; exact retained source-map `ui/app/plugins/data_source/Dukascopy/source-map.json`. Target `ui/app/plugins/data_source/Dukascopy/DukascopyService.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceDukascopy/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDukascopy/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDukascopy/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceDukascopy/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_dukascopy.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_dukascopy.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Dukascopy/DukascopyService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Dukascopy/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Dukascopy/import/importPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Dukascopy/add/addPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-dukascopy.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-DUKASCOPY-DUKAS-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-DUKASCOPY-DUKAS-SERVLET-PRELOAD-AVAILABLE-DATA-RESPONSE` → `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet.preloadAvailableDataResponse()V`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-DUKASCOPY-DUKAS-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Dukascopy.DukasServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_dukascopy.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-dukascopy.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Dukascopy provider for FEAT-DATA-SOURCE-DATA-SOURCE-DUKASCOPY; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.15 FEAT-DATA-SOURCE-DATA-SOURCE-FILES - DataSourceFiles.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFiles.jar`; 10 raw class entries; SHA-256 `952be70cb76b5293fd6f110df9679eec6bbf1393139ae77f6f3cc5b0c3621783`.
- **Inspected reference:** [DataSourceFiles.md](sqx/DataManager/DataSourceFiles.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFiles.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFiles.jar" com.strategyquant.plugin.DataSource.impl.Files.DataSourceFilesServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceFiles/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/DataSourceFilesService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/add/DataSourceFilesAddCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceFiles/appImport/DataSourceFilesAppImportCtrl.js`.
- **Existing UI connection:** FileImport provider; exact retained source-map `ui/app/plugins/data_source/FileImport/source-map.json`. Target `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceFiles/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceFiles/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceFiles/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceFiles/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_files.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_files.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/FileImport/DataSourceFilesService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/FileImport/fileImportStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/FileImport/fileSymbolsStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/FileImport/add/DataSourceFilesAddCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/FileImport/add/addPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-files.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-FILES-DATA-SOURCE-FILES-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Files.DataSourceFilesServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-FILES-DATA-SOURCE-FILES-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Files.DataSourceFilesServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-FILES-DATA-SOURCE-FILES-SERVLET-ON-APP-IMPORT` → `com.strategyquant.plugin.DataSource.impl.Files.DataSourceFilesServlet.onAppImport(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_files.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-files.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise FileImport provider for FEAT-DATA-SOURCE-DATA-SOURCE-FILES; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.16 FEAT-DATA-SOURCE-DATA-SOURCE-MT5-API - DataSourceMt5Api.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/DataSourceMt5Api.jar`; 4 raw class entries; SHA-256 `0e9a2fcba6c8457afbf3412a09c50572f207d04290e96469cefa9858f33aaf64`.
- **Inspected reference:** [DataSourceMt5Api.md](sqx/DataManager/DataSourceMt5Api.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/DataSourceMt5Api.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/DataSourceMt5Api.jar" com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceMt5Api/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/import/DataSourceMt5ApiImportCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/import/importPopup.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceMt5Api/module.js`.
- **Existing UI connection:** MetaTrader provider; exact retained source-map `ui/app/plugins/data_source/MetaTrader/source-map.json`. Target `ui/app/plugins/data_source/MetaTrader/mt5ImportStore.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceMt5Api/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceMt5Api/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceMt5Api/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceMt5Api/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_mt5_api.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_mt5_api.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/MetaTrader/mt5ImportStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/MetaTrader/import/DataSourceMt5ApiImportCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/MetaTrader/import/importPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/plugins/data_source/MetaTrader/backendClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-mt5-api.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-MT5-API-DATA-SOURCE-MT5-API-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-MT5-API-DATA-SOURCE-MT5-API-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-MT5-API-DATA-SOURCE-MT5-API-SERVLET-UPDATE-SELECTED` → `com.strategyquant.plugin.DataSource.impl.Mt5Api.DataSourceMt5ApiServlet.updateSelected(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_mt5_api.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-mt5-api.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise MetaTrader provider for FEAT-DATA-SOURCE-DATA-SOURCE-MT5-API; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.17 FEAT-DATA-SOURCE-DATA-SOURCE-SQ-EQUITY-DATA - DataSourceSQEquityData.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/DataSourceSQEquityData.jar`; 5 raw class entries; SHA-256 `872584251e604ec4d6dc7a8837a5a674fc30daef5251891090d1fb0b85365e53`.
- **Inspected reference:** [DataSourceSQEquityData.md](sqx/DataManager/DataSourceSQEquityData.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/DataSourceSQEquityData.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/DataSourceSQEquityData.jar" com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceSQEquityData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/SQEquityDataService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/add/SQEquityDataAddCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQEquityData/update/SQEquityDataUpdateCtrl.js`.
- **Existing UI connection:** SQ Equity data; exact retained source-map `ui/app/plugins/data_source/SQData/Equity/source-map.json`. Target `ui/app/plugins/data_source/SQData/Equity/SQEquityDataService.ts`; wire equity catalog/availability, add/update requests, backend job status and persisted dataset resources.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceSQEquityData/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQEquityData/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQEquityData/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQEquityData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_sq_equity_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_sq_equity_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/SQData/Equity/SQEquityDataService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/SQData/Equity/add/SQEquityDataAddCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/SQData/Equity/update/SQEquityDataUpdateCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/SQData/Equity/add/addPopup.tsx`
  - Display equity catalog/availability, add/update requests, backend job status and persisted dataset resources from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display equity catalog/availability, add/update requests, backend job status and persisted dataset resources from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-sq-equity-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind equity catalog/availability, add/update requests, backend job status and persisted dataset resources to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-EQUITY-DATA-SQEQUITY-DATA-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-EQUITY-DATA-SQEQUITY-DATA-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-EQUITY-DATA-SQEQUITY-DATA-SERVLET-ON-GET-EXCHANGES` → `com.strategyquant.plugin.DataSource.impl.SQEquityData.SQEquityDataServlet.onGetExchanges()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_sq_equity_data.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-sq-equity-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise SQ Equity data for FEAT-DATA-SOURCE-DATA-SOURCE-SQ-EQUITY-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.18 FEAT-DATA-SOURCE-DATA-SOURCE-SQ-FUTURES-DATA - DataSourceSQFuturesData.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/DataSourceSQFuturesData.jar`; 5 raw class entries; SHA-256 `ae170dfb47e1a0b7bacebb47b8575ac7a33976d613784c84a96abf5507a38a3f`.
- **Inspected reference:** [DataSourceSQFuturesData.md](sqx/DataManager/DataSourceSQFuturesData.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/DataSourceSQFuturesData.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/DataSourceSQFuturesData.jar" com.strategyquant.plugin.DataSource.impl.SQFuturesData.SQFuturesDataServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceSQFuturesData/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/SQFuturesDataService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/add/SQFuturesDataAddCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceSQFuturesData/update/SQFuturesDataUpdateCtrl.js`.
- **Existing UI connection:** SQ Futures data; exact retained source-map `ui/app/plugins/data_source/SQData/Futures/source-map.json`. Target `ui/app/plugins/data_source/SQData/Futures/SQFuturesDataService.ts`; wire futures catalog/availability, add/update requests, backend job status and persisted dataset resources.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceSQFuturesData/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQFuturesData/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQFuturesData/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceSQFuturesData/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_sq_futures_data.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_sq_futures_data.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/SQData/Futures/SQFuturesDataService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/SQData/Futures/add/SQFuturesDataAddCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/SQData/Futures/update/SQFuturesDataUpdateCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/SQData/Futures/add/addPopup.tsx`
  - Display futures catalog/availability, add/update requests, backend job status and persisted dataset resources from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display futures catalog/availability, add/update requests, backend job status and persisted dataset resources from backend responses; preserve layout.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-sq-futures-data.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind futures catalog/availability, add/update requests, backend job status and persisted dataset resources to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-FUTURES-DATA-SQFUTURES-DATA-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.SQFuturesData.SQFuturesDataServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-FUTURES-DATA-SQFUTURES-DATA-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.SQFuturesData.SQFuturesDataServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-SQ-FUTURES-DATA-SQFUTURES-DATA-SERVLET-ON-GET-EXCHANGES` → `com.strategyquant.plugin.DataSource.impl.SQFuturesData.SQFuturesDataServlet.onGetExchanges()Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_sq_futures_data.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-sq-futures-data.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise SQ Futures data for FEAT-DATA-SOURCE-DATA-SOURCE-SQ-FUTURES-DATA; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.19 FEAT-DATA-SOURCE-DATA-SOURCE-TD - DataSourceTD.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTD.jar`; 5 raw class entries; SHA-256 `b3a965b9aed288cf77ff6c30c6a7a60719bae6593e65e415a8b8ac59691e9ea1`.
- **Inspected reference:** [DataSourceTD.md](sqx/DataManager/DataSourceTD.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTD.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTD.jar" com.strategyquant.plugin.DataSource.impl.TD.DataSourceTDServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceTD/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/DataSourceTDService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/import/DataSourceTDImportCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceTD/import/importPopup.html`.
- **Existing UI connection:** TickDownloader provider; exact retained source-map `ui/app/plugins/data_source/TickDownloader/source-map.json`. Target `ui/app/plugins/data_source/TickDownloader/DataSourceTDService.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceTD/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceTD/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceTD/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceTD/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_td.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_td.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/TickDownloader/DataSourceTDService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/TickDownloader/import/DataSourceTDImportCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/TickDownloader/import/importPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-td.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-TD-DATA-SOURCE-TDSERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.TD.DataSourceTDServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-TD-DATA-SOURCE-TDSERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.TD.DataSourceTDServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-TD-DATA-SOURCE-TDSERVLET-ON-LOAD-AVAILABLE-SYMBOLS` → `com.strategyquant.plugin.DataSource.impl.TD.DataSourceTDServlet.onLoadAvailableSymbols(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_td.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-td.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise TickDownloader provider for FEAT-DATA-SOURCE-DATA-SOURCE-TD; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.20 FEAT-DATA-SOURCE-DATA-SOURCE-YAHOO - DataSourceYahoo.jar

## 1. Objective

- **Goal:** Qualify and implement this provider's ingestion contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Import files and download normalized provider data through owned jobs.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/DataSourceYahoo.jar`; 5 raw class entries; SHA-256 `4a9d64a03e668d1563a14e179c041721779a83b440c7ada56097fb9d28f54a3d`.
- **Inspected reference:** [DataSourceYahoo.md](sqx/DataManager/DataSourceYahoo.md); full class/member metadata is linked there.
- **Research commands:** `jar tf "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/DataSourceYahoo.jar"`; `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/DataSourceYahoo.jar" com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet`. Inspect actual consumed bodies and callers before translation.
- **Gap:** current declarations seed proposed FRs; defaults, algorithm bodies, consumption and runtime outcomes require independent validation. No source fallback.
- **Owner:** `app/plugins/data_source/DataSourceYahoo/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Provider/file ingestion, catalog and download workflow; downstream .
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/YahooService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/add/addPopupCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataSourceYahoo/download/downloadPopupCtrl.js`.
- **Existing UI connection:** Yahoo provider; exact retained source-map `ui/app/plugins/data_source/Yahoo/source-map.json`. Target `ui/app/plugins/data_source/Yahoo/YahooService.ts`; wire provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/DataSourceYahoo/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceYahoo/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceYahoo/normalization.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/data_source/DataSourceYahoo/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_data_source_data_source_yahoo.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/data_source_data_source_yahoo.json`
  - Store versioned paraphrased donor input/output fixtures.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Yahoo/YahooService.ts`
  - Call owned typed commands; map responses/errors to current dialogs.
- **Modify:** `ui/app/plugins/data_source/Yahoo/yahooStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Modify:** `ui/app/plugins/data_source/Yahoo/add/addPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Yahoo/download/downloadPopupCtrl.ts`
  - Await backend validation/commands; bind actual result and job states to existing controls.
- **Modify:** `ui/app/plugins/data_source/Yahoo/add/addPopup.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Display provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts from backend responses; preserve layout.
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/feat-data-source-data-source-yahoo.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Qualify and implement this provider's ingestion contract; verify symbol mapping, pagination, timestamp units, rate limits and unavailable API.
- [ ] **Step 4:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 5:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

- [ ] **Step 6:** Connect retained UI: Ratify the feature-owned wire contract; bind provider catalog/symbol availability, add/import/download commands, backend job progress/cancellation and persisted dataset counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 7:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.


- [ ] **Step 8:** `FR-DATA-SOURCE-DATA-SOURCE-YAHOO-DATA-SOURCE-YAHOO-SERVLET-CONTRACT` → `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 9:** `FR-DATA-SOURCE-DATA-SOURCE-YAHOO-DATA-SOURCE-YAHOO-SERVLET-EXECUTE` → `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet.execute(Ljava/lang/String;Ljava/util/Map;Ljava/lang/String;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.
- [ ] **Step 10:** `FR-DATA-SOURCE-DATA-SOURCE-YAHOO-DATA-SOURCE-YAHOO-SERVLET-ON-ADD` → `com.strategyquant.plugin.DataSource.impl.Yahoo.DataSourceYahooServlet.onAdd(Ljava/util/Map;)Ljava/lang/String;`: confirm current consumed behavior, specify defaults/I/O/errors and independently test its accepted contract.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_data_source_data_source_yahoo.py --no-cov`; expect symbol mapping, pagination, timestamp units, rate limits and unavailable API; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture symbol mapping, pagination, timestamp units, rate limits and unavailable API and visible failures.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-data-source-data-source-yahoo.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Yahoo provider for FEAT-DATA-SOURCE-DATA-SOURCE-YAHOO; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.21 FEAT-UI-DATA-MANAGER-LOG - DataManagerLog resource contribution

## 1. Objective

- **Goal:** Qualify and connect DataManagerLog without assuming a missing backend JAR.
- **Context / Problem Solved:** DataManagerLog is one of 17 roadmap contributions with no immediate JAR.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog`; narrow source: `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog/module.js`.
- **FR:** `FR-UI-DATA-MANAGER-LOG-RESOURCE-WORKFLOW`; proposed owning README `app/plugins/data_source/README.md`.
- **Research:** inspect resource/module/config declarations and consuming registrations; fingerprint stable files and trace action routes.
- **Gap:** directory/resource presence does not prove an enabled workflow; empty contributions need explicit dispositions.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog`; `SQX_145_REFERENCE_ROOT/internal/web/QDM`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog/DMDataLogCtrl.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog/dataLog.html`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerLog/module.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Create:** `app/plugins/data_source/resource_contributions.py`
  - Mount only verified resource/action contributions through this owning capability.
- **Create:** `app/plugins/data_source/README.md`
  - Register the resource workflow and explicit empty/unavailable dispositions.
- **Create:** `tests/unit/sqx_features/test_ui_data_manager_log.py`
  - Verify contribution mount/unmount and action authority.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Bind the verified resource workflow to real capability state.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/app/workspace/DataManager/dataManagerClient.ts`
  - Typed domain client over host transport; ratify route/schema/version, errors and cancellation. Reuse this proposed owner if delivered earlier.
- **Create:** `ui/tests/unit/backend-connections/feat-ui-data-manager-log.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Add this feature's case using a real isolated application host; sandbox external dependencies only.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Inspect and specify resource/action declarations, defaults, route consumers and active registration; approve the resulting FR contract.
- [ ] **Step 2:** `FR-UI-DATA-MANAGER-LOG-RESOURCE-WORKFLOW`: implement the evidenced resource workflow or ratified empty contribution; preserve domain ownership.
- [ ] **Step 3:** Bind verified UI controls to host/domain capabilities; define disabled, denied and unavailable states.
- [ ] **Step 4:** Test mount/unmount, missing resources, action authority and FR logs; retain versioned donor observations.

- [ ] **Step 5:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 6:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_ui_data_manager_log.py --no-cov`; assert resource availability, owned lifecycle and denied/missing actions.
- **Manual / Browser Verification:** Import a small fixture; start a sandbox download; cancel it; inspect import logs and confirm unavailable providers have explicit states. Inspect the DataManagerLog contribution; an empty or unavailable contribution must remain explicit.
- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/feat-ui-data-manager-log.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for FEAT-UI-DATA-MANAGER-LOG; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.


# 4.22 FEAT-DATA-SOURCE-COT - COT download and update adapter

## 1. Objective

- **Goal:** Download and update approved COT custom data through typed host jobs.
- **Context / Problem Solved:** Build 145 adds/changes this donor contribution; existing mock presentation and a filename do not establish functional support.

## 2. Research and donors

- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DataManagerCustomData.jar`.
- **Donor:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataService.js`.
- **Ownership:** proposed `FEAT-DATA-SOURCE-COT` and `FR-DATA-SOURCE-COT-CONSUMED-CONTRACTS`; owner `app/plugins/data_source/COT/README.md`. No application registration or implementation is implied.
- **Dependencies:** P00 evidence/ownership, P01 logging and P02 typed sessions/jobs/resources; phase-specific data/engine/project prerequisites from the delivery graph.
- **Commands:** `jar tf "$SQX_145_REFERENCE_ROOT/<listed-archive>"`, `javap -c -p -classpath "$SQX_145_REFERENCE_ROOT/<listed-archive>" <consumed-class>` for JARs; inspect exact readable resource bodies and caller tests for resources. Substitute verified locators; never invent a class.
- **Known gaps/conflicts:** The servlet references an unavailable core; download protocol is not established by the UI route.
- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/cot/CustomDataCotCtrl.js`, `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerCustomData/DMCustomDataService.js`; connect COT updates to owned jobs.

## 3. File Changes

- **Create:** `app/plugins/data_source/COT/service.py` — Download and update approved COT custom data through typed host jobs.
- **Create:** `app/plugins/data_source/COT/contracts.py` — Download and update approved COT custom data through typed host jobs.
- **Create:** `app/plugins/data_source/COT/README.md` — ratify owning FEAT/FR contracts and status in the approved feature plan.
- **Create:** `tests/unit/reference_145/test_data_source_cot.py` — donor-derived normal, boundary, failure and FR-log checks.
- **UI connection files (retained views where present; missing controls are explicit gaps):**
  - **Modify:** `ui/app/workspace/DataManager/DataManager.tsx` — bind the feature-owned capability, status/errors and result/resource IDs; preserve retained layout.
  - **Create:** `ui/tests/e2e/sqx145-data_source_cot-backend.spec.ts` — isolated real-host acceptance; production mocks cannot qualify completion.
- **Delete / Deprecate:** none; version/dependency retirement requires explicit approved disposition.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Ratify cohort, owning FEAT/FRs, target decisions, dependencies and exact write paths in the canonical plan.
- [ ] **Step 2:** Trace onUpdateCot, CotManager.sync and the actual provider protocol; block unavailable body/entitlement evidence.
- [ ] **Step 3:** Specify timeout/retry/rate/redaction/progress contracts; no live provider request without its authorization.
- [ ] **Step 4:** Test sync failure, cancellation, duplicate releases, export errors and temporary-store update rollback.
- [ ] **Step 5:** Connect the UI last: bind actual commands/projections, loading/empty/denied/failure states and job cancellation/reconnect; keep absent controls visibly unavailable.
- [ ] **Step 6:** Verify backend + frontend together on an isolated real host; reconcile submitted inputs, output IDs and reload. No mock fallback counts.
- [ ] **Step 7:** Record timestamped observations and walkthrough; update the matching master checklist row only when all requirements pass.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/reference_145/test_data_source_cot.py --no-cov`; scoped Ruff format/check and strict Mypy; assert independent expected outputs and FR logs. After actual UI changes: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`; run the feature connected case with the P02 isolated-host harness.
- **Manual / Browser Verification:** Exercise the connected control, one denial/failure and job stop/reload where applicable; correlate host IDs and outputs.
- **Completion limit:** missing bodies/ownership/entitlement or independent expected outputs keep the task unchecked; static declarations do not establish SQX parity.


# 4.23 P04 integration — Import files and download normalized provider data through owned jobs

## 1. Objective

- **Goal:** Import files and download normalized provider data through owned jobs.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/V1/sqx-full-application-roadmap.md`, P04; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/DataManager/DataManager.tsx`; backend counterparts are proposed.
- **Declared dependencies:** httpx, psutil; optional Windows metatrader5 (P16).
- **Existing tests:** No audited phase backend suite; create the integration tests below.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

- **UI donors:** `SQX_145_REFERENCE_ROOT/internal/web/QDM`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppDataManager`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerData`. Inspect `SQX_145_REFERENCE_ROOT/internal/web/QDM/layout/QDMService.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/AppDataManager/module.js`; `SQX_145_REFERENCE_ROOT/internal/plugins/DataManagerData/DMDataService.js`.
- **Existing UI connection:** Data Manager; proposed shared consumer; verify the exact existing control and public contract before implementation. Target `ui/app/plugins/data_source/Common/dataManagerStore.ts`; wire dataset/catalog load and mutation, server resource IDs and authoritative row counts.
- **UI gap:** Ratify routes/schema and inspect mock resource/job authority. Missing retained controls or backend capabilities block completion; resolve them through a scoped plan.

## 3. File Changes

- **Modify:** `app/host/integrations/http.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/integrations/retry.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/host/integrations/rate_limit.py` (proposed earlier in FEAT-DATA-SOURCE-HTTPASYNCCLIENT)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/DataManager/DataManager.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/DataManager/dataManagerClient.ts` (proposed earlier in P03 integration)
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/plugins/data_source/README.md` (proposed earlier in FEAT-UI-DATA-MANAGER-LOG)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_data_ingestion_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-data-ingestion-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

- **UI connection files (existing presentation):**
- **Modify:** `ui/app/plugins/data_source/Common/dataManagerStore.ts`
  - Replace affected mock job/resource authority with server projections; preserve selection/view state.
- **Create:** `ui/tests/unit/backend-connections/task-4-23.test.ts`
  - Verify this feature's client/projection, real-response shapes and explicit failure/unavailable states.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Qualify each provider's current API, symbol mapping, credential requirements and availability.
- [ ] **Step 3:** Implement parsing/pagination, units/time normalization, bounded retry/rate limits and provenance.
- [ ] **Step 4:** Route download/import progress, cancellation and partial errors into DataManager.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

- [ ] **Step 8:** Connect retained UI: Ratify the feature-owned wire contract; bind dataset/catalog load and mutation, server resource IDs and authoritative row counts to actual backend commands/projections through host transport. Replace only affected production mocks; preserve view state and show loading/empty/unavailable/denied/errors. Use server job/resource IDs and cancellation/reconnect where applicable.
- [ ] **Step 9:** Verify backend + UI together: Run this feature's contract/UI tests against an isolated real host; reconcile submitted inputs, returned IDs/results and reload behavior. Cover a failure/unavailable path and cancellation for jobs. No application-API mock or fixture fallback counts; leave this task unchecked until both sides work.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_data_ingestion_workflow.py --no-cov`; `npm --prefix ui run test:ui -- tests/e2e/sqx-data-ingestion-backend.spec.ts`. Assert fixture-file import, pagination and normalized OHLCV/time metadata; reject rate limit, timeout, corrupt row, partial download and cancellation.
- **Manual / Browser Verification:** Import a small fixture; start a sandbox download; cancel it; inspect import logs and confirm unavailable providers have explicit states.

- **Connected UI tests:** `npm --prefix ui run test -- tests/unit/backend-connections/task-4-23.test.ts`; `npm --prefix ui run test:ui -- --config playwright.backend.config.ts tests/e2e/sqx-data-ingestion-backend.spec.ts --workers=1` with an isolated real host/store and approved base URL/proxy. Adapt a dedicated connected harness; retained mock-only tests still verify presentation.
- **Connected browser acceptance:** Exercise Data Manager for 4.24; request/output/resource IDs must match backend observations. Missing host/capability stays visibly unavailable; mock success and API interception fail acceptance.

## Phase completion gate

- [ ] Every applicable feature passed its own isolated real-host UI/backend case; no production mock fallback or unresolved required UI remains.

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

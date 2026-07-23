# Brokers Domain Static Completion Review

## 0. Review baseline and evidence limitations

| Item                         | Recorded baseline                                                                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Repository                   | `haruperi/HaruQuantAI`                                                                                                              |
| Branch                       | `main`                                                                                                                              |
| Commit                       | `88482e8237ac1488ce6b1bb2984852b1c8c95e37`                                                                                          |
| Commit message               | `chore: commit requested changes`                                                                                                   |
| Review timestamp             | `2026-07-23T16:48:48Z`                                                                                                              |
| Reviewed state               | Remote committed state only                                                                                                         |
| Local state visibility       | Uncommitted files, working-tree modifications, ignored files, local caches, local credentials, and local tool outputs are invisible |
| Commands executed            | None                                                                                                                                |
| Tests executed               | None                                                                                                                                |
| External provider calls      | None                                                                                                                                |
| Repository modifications     | None                                                                                                                                |
| GitHub status checks         | No combined status entries were visible for the reviewed commit                                                                     |
| Ruff, Mypy, pytest, coverage | `UNVERIFIED`                                                                                                                        |
| Python and uv versions       | `UNVERIFIED`; the repository declares Python 3.14 and uv-managed tooling                                                            |
| Provider behavior            | `UNVERIFIED` except for static code and test-design inspection                                                                      |

The authority order was applied as follows:

1. Owner instructions.
2. `AGENTS.md`.
3. `docs/PROJECT.md`.
4. `docs/ARCHITECTURE.md`.
5. Tooling and dependency configuration.
6. `app/services/brokers/README.md`.
7. Consuming and supplying domain boundaries.
8. `docs/CHANGELOG.md`.
9. Code and tests as evidence of current reality.

`AGENTS.md` requires one feature per module folder, one usage program per feature, explicit approval before edits, strict typing and docstrings, fail-closed behavior, and no production action by default.

---

## 1. Result

# `DRY-RUN FINDINGS`

There are multiple statically proven findings, including four `BLOCKING` findings.

The overall result is not `BLOCKED` because the mandatory repository resources were accessible and the review could proceed. The authoritative contradictions are bounded and explicitly identified, but they must be resolved before the domain can become `READY`.

---

## 2. Executive reason

The Brokers domain contains substantial implementation and test scaffolding, but it is not ready for completion certification.

The principal reasons are:

1. **A direct-construction path bypasses the registry write-release gate.** Concrete public adapter constructors accept caller-provided capability maps. Tests demonstrate enabling genuine MT5 mutation bodies through that path while the registry-created path correctly blocks writes.

2. **The package violates Focused Domain Architecture.** Fifteen registered features are implemented inside approximately eight feature-counted production directories, with several provider folders owning multiple unrelated features.

3. **Authoritative documents contradict one another.** These contradictions include Dukascopy bar semantics, Yahoo probe requirements, domain completion status, feature counts, and usage-program counts.

4. **Several declared runtime safety mechanisms are incomplete or disconnected.** MT5 constructs a circuit breaker but does not use it; cTrader lacks the specified rate/circuit enforcement; Binance lacks the declared provider-weight enforcement; configured reconnect limits are not used.

5. **Bounded queues silently evict already accepted events.** This contradicts the documented prohibition on silent drops.

6. **The fake adapter does not enforce operation-specific result types.** It can return a `BrokerOrder` from `place_order()`, whose declared return type is `BrokerOrderResult`.

7. **Behavioral completion claims are unsupported in this review.** The README claims 333 tests, clean Ruff/Mypy, coverage, dependency resolution, and real provider sessions, but all such evidence is `UNVERIFIED` because no commands were run and no current CI status was visible.

---

# 3. Blocking and high findings

## `REV-BRK-001` — Public adapter construction bypasses write-release policy

**Severity:** `BLOCKING`
**Affected IDs:** `FR-BRK-010`, `FR-BRK-011`, `FR-BRK-091`–`FR-BRK-097`, `FR-BRK-101`, `FR-BRK-104`, `FR-BRK-105`, `FR-BRK-135`, `NFR-BRK-004`, `WF-BRK-004`, `WF-BRK-009`, `SYS-WF-002`, `SYS-WF-008`
**Fix target:** Code, tests, documentation

### Evidence

The README states that `_WRITE` operations are excluded unconditionally from registry release.

However:

* `MT5BrokerAdapter.__init__()` publicly accepts an arbitrary capability mapping.
* `BrokerCapability` validates evidence when `access_mode == "WRITE"` but does not ensure that mutation capability IDs must be classified as `WRITE`.
* The mutation integration test constructs a capability map that marks mutation operations available and injects it directly into `MT5BrokerAdapter`.
* That directly constructed adapter executes the genuine `order_send` mutation path.
* The same test separately proves that a registry-created adapter blocks the mutation.

### Current behavior

A caller can bypass `create_broker_adapter()` and construct a public concrete adapter with a forged capability map.

### Required behavior

No caller-controlled value may release or reclassify mutation capabilities. Capability release must derive exclusively from the authoritative, immutable Brokers policy.

Only Trading may receive mutation capability, and unreleased mutations must remain unavailable regardless of construction path.

### Root cause

The capability catalogue is treated as caller-supplied instance configuration rather than immutable domain policy.

### Required correction

* Remove caller-provided capability maps from all production adapter constructors.
* Resolve the capability map internally from one authoritative registry policy.
* Validate a fixed capability-ID-to-access-mode mapping.
* Make a mutation ID declared as `READ` invalid.
* Keep provider mutation implementation testing behind private test harnesses or private implementation functions, not a production constructor override.
* Ensure direct construction, factory construction, subclassing, fixture injection, and monkeypatching cannot release a mutation through supported APIs.

### Regression risk

High. Adapter construction, provider tests, registry behavior, and public signatures will be affected.

---

## `REV-BRK-002` — Focused Domain Architecture and feature-count failure

**Severity:** `BLOCKING`
**Affected IDs:** `FEAT-BRK-00`–`FEAT-BRK-14`, package structure, Feature Registry, all provider feature ownership
**Fix target:** Code and documentation
**Selected remediation scenario:** **Fix both code and documentation**

### Evidence

`AGENTS.md` requires:

* one feature per module folder;
* one file per focused responsibility;
* one feature = one folder = one usage program.

The Brokers README itself admits that provider capabilities share folders and that the domain is therefore `Partial`.

Despite that admission, its final checklist claims:

* the tree matches Section 2;
* every module folder represents one coherent capability;
* every requirement and workflow is complete;
* fifteen usage programs align one-to-one with features.

### Reconciliation

| Item                               |                                                                                         Count or state |
| ---------------------------------- | -----------------------------------------------------------------------------------------------------: |
| Registered features                |                                                                        15: `FEAT-BRK-00`–`FEAT-BRK-14` |
| Feature-counted production folders | Approximately 8: `contracts`, `registry`, `mt5`, `ctrader`, `binance`, `dukascopy`, `yahoo`, `testing` |
| Support folder                     |                                                                                              `runtime` |
| Named usage programs               |                                                                                15: `00_*.py`–`14_*.py` |
| Equation                           |                                                                      `15 features ≠ 8 feature folders` |

Examples:

* `mt5/` owns lifecycle/account, mutation, history, and calculation behavior.
* `ctrader/` owns lifecycle, mutation, history, calculation, market-data, and streaming behavior.
* `binance/` owns lifecycle, market reads, and streaming.
* `dukascopy/` owns both BI5 tick behavior and web-chart candle behavior.

### Required correction

Split behavior into feature-owned folders while preserving package-root contracts and public signatures. A concrete target is specified in the correction plan.

### Regression risk

High. Import paths, provider class composition, tests, and documentation will all be affected.

---

## `REV-BRK-003` — Contradictory authoritative Dukascopy bar semantics

**Severity:** `BLOCKING`
**Affected IDs:** `FR-BRK-107`, `FR-BRK-126`–`FR-BRK-128`, `FEAT-BRK-05`, `FEAT-BRK-13`, provider-truth policy
**Fix target:** Specification and documentation

### Evidence

`docs/PROJECT.md`, which outranks the domain README, says Dukascopy “aggregates midpoint bars locally.”

The Brokers README says Dukascopy retrieves BID candles from the keyless web-chart feed and does not locally derive OHLC from ticks.

`docs/ARCHITECTURE.md` also says the web-chart interface supplies BID candles and that Brokers does not synthesize OHLC from BI5 ticks.

### Current behavior

The implementation is aligned with the detailed README/architecture position, not the stale `docs/PROJECT.md` sentence.

### Required behavior

There must be one canonical rule.

### Recommended owner resolution

Preserve direct provider BID candle mapping and correct the stale `docs/PROJECT.md` statement. Do not introduce local midpoint-bar aggregation.

Approval of this explicitly numbered plan would approve that documentation resolution. Without approval, the coding agent must not choose between the contradictory definitions.

### Regression risk

Low if corrected as documentation only; high if the owner instead chooses midpoint derivation.

---

## `REV-BRK-004` — Yahoo probe requirement contradicts itself

**Severity:** `BLOCKING`
**Affected IDs:** `DEC-BRK-001`, `FR-BRK-006`, `FR-BRK-108`, `WF-BRK-002`
**Fix target:** Specification, documentation, tests

### Evidence

The shared configuration manifest says:

* `probe_symbol` is optional;
* when unset, Yahoo verifies transport/session only;
* there is no hidden default.

The same README later says:

* Yahoo requires an explicit non-empty `probe_symbol`;
* missing probe configuration fails closed.

The implementation currently requires a probe symbol and fails configuration validation when absent.

### Recommended owner resolution

Make the explicit non-empty probe symbol mandatory for `YahooBrokerAdapter.connect()`.

Update every conflicting manifest, workflow, usage example, and test to that rule. Keep `probe_symbol=None` valid only for configurations that never call Yahoo `connect()`.

### Regression risk

Medium. Existing registry tests currently expect missing probe configuration to fail.

---

## `REV-BRK-005` — False or contradictory completion, inventory, and test claims

**Severity:** `BLOCKING`
**Affected IDs:** Domain status, Feature Registry, Definition of Done, usage manifest, release documentation
**Fix target:** Documentation

### Evidence

* `docs/PROJECT.md` calls Brokers a completed baseline.
* Its domain registry labels Brokers `Completed implementation baseline`.
* `docs/ARCHITECTURE.md` also labels it completed.
* The owning README labels it `Partial`.
* The test tree says usage files are `01_*.py` through `13_*.py`.
* The normative manifest later says `00_contracts.py` through `14_fake_adapter.py`.
* The Fake Adapter section incorrectly says `01_registry.py` demonstrates `FR-BRK-109`, while its own FR row assigns `14_fake_adapter.py`.
* The checklist claims 333 passing tests, clean tooling, resolved dependencies, and at least 80% coverage, none of which is current evidence available to this reviewer.

### Required correction

* Keep the domain status `Partial` until all approved corrections and validation pass.
* Remove unsupported test-count and “passing” language unless refreshed by current execution evidence.
* Reconcile feature IDs, folder counts, and usage programs.
* Correct system-level status entries after final validation only.
* Do not rewrite historical changelog entries; append a future released-version entry only when a release occurs.

---

## `REV-BRK-006` — Circuit, rate, and provider-weight controls are incomplete

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-111`, `FR-BRK-116`, `FR-BRK-119`, `FR-BRK-123`, `FR-BRK-130`, `NFR-BRK-004`, `NFR-BRK-009`, provider configuration manifest
**Fix target:** Code and tests

### Evidence

#### MT5

`_MT5Transport` constructs `_TransportCircuitBreaker`, but `_run()` never calls `before_call()`, `record_success()`, or `record_failure()`.

#### cTrader

`_CTraderTransport` has response-type serialization and timeout handling but no circuit breaker and no specified 50/5 requests-per-second throttling.

The provider manifest explicitly requires those cTrader limits.

#### Binance

The REST transport has a circuit, but no provider-weight accounting or enforcement. Its WebSocket stream path does not use the circuit.

#### Canonical error mapping

Yahoo and Binance raise `ConnectionError("BROKER_CIRCUIT_OPEN")` when blocked. That can be normalized as connection loss rather than the required `BROKER_CIRCUIT_OPEN`.

### Required correction

* Wire circuit admission and result accounting into every external call.
* Preserve `BROKER_CIRCUIT_OPEN` as a canonical result code.
* Implement cTrader request-rate windows.
* Implement Binance provider-returned weight/rate metadata tracking.
* Apply transport controls to stream establishment and reconnect probes.
* Never count business rejection, authorization failure, or rate-limit response as a circuit-qualifying transport failure unless the canonical requirement says so.

---

## `REV-BRK-007` — `connect_timeout_sec` and reconnect bounds are not reliably enforced

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-006`, `FR-BRK-048`–`FR-BRK-057`, `FR-BRK-104`–`FR-BRK-108`, `WF-BRK-002`
**Fix target:** Code and tests

### Evidence

`BrokerConnectionConfig` defines and validates both `connect_timeout_sec` and `transport_reconnect_max_attempts`.

MT5 initialization passes through `_run()`, which uses `request_timeout_sec`, not `connect_timeout_sec`.

No reviewed transport implemented a bounded reconnect loop controlled by `transport_reconnect_max_attempts`.

### Required correction

* Use `connect_timeout_sec` for initial connection and authentication.
* Use `request_timeout_sec` for post-connection operations.
* Implement a bounded connection-recovery loop.
* Count initial attempt separately from reconnect attempts.
* Never replay an interrupted read or mutation automatically.
* Make zero reconnect attempts mean one initial attempt and no automatic retry.

---

## `REV-BRK-008` — Subscription and lifecycle queues silently discard events

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-013`, `FR-BRK-057`, `FR-BRK-068`–`FR-BRK-072`, `FR-BRK-112`, `FR-BRK-114`, `WF-BRK-006`, `NFR-BRK-004`, `NFR-BRK-009`
**Fix target:** Code and tests

### Evidence

On subscription overflow:

* the subscription marks itself closed and requiring resynchronization;
* `_enqueue_terminal()` removes the oldest queue item when full before inserting the terminal error.

On explicit unsubscribe, a full queue also causes the oldest queued event to be removed before inserting the terminal marker.

The README explicitly says:

* silent drops are forbidden;
* explicit unsubscribe must complete after already enqueued events.

The existing overflow test expects the originally queued event to disappear and only the terminal error to remain.

### Required correction

* Never remove an accepted event from the queue.
* Separate terminal state from the bounded data queue.
* Drain already accepted events before yielding a terminal error or normal completion.
* Make overflow observable without forcing a producer to wait indefinitely.
* Apply equivalent explicit overflow semantics to connection-event delivery.

---

## `REV-BRK-009` — Fake adapter violates canonical operation result types

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-092`, `FR-BRK-109`, `FEAT-BRK-14`, test contract compatibility
**Fix target:** Code and tests

### Evidence

`FakeBrokerAdapter` accepts `Mapping[BrokerCapabilityId, object]` and places arbitrary fixture objects into `BrokerResult`.

The mutation test configures `PLACE_ORDER` with a `BrokerOrder`, although `place_order()` is declared to return `BrokerOrderResult`. It then asserts that the wrong object is returned unchanged.

The README requires the fake to preserve the same DTO and result invariants as real adapters.

### Required correction

* Define an operation-to-expected-payload-type registry.
* Validate fixtures when the fake is constructed and when fixtures are replaced.
* Reject a mismatched payload before invocation.
* Replace the mutation fixture with a valid `BrokerOrderResult`.
* Add coverage for generic pages, tuples, decimals, subscriptions, and `None` results.

---

## `REV-BRK-010` — Missing-dependency metadata is incomplete and mislabeled

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-101`, `WF-BRK-001`
**Fix target:** Code and tests

### Evidence

The README requires missing-dependency errors to include:

* package;
* required version;
* installed version;
* installation extra.

The current factory derives `required_version` from installed package metadata rather than from the project dependency manifest. When the package is absent, the value becomes `None`.

The test explicitly expects `required_version is None` for a missing package.

### Required correction

* Store the declared project constraint and installation extra in the immutable factory registration.
* Report the actual missing import name separately from the provider package.
* Report installed version only when metadata is available.
* Never inspect or modify the lockfile during runtime.
* Update tests to assert exact required constraints from `pyproject.toml`.

---

## `REV-BRK-011` — Per-adapter latency state is unsafe under concurrency

**Severity:** `HIGH`
**Affected IDs:** `NFR-BRK-005`, `NFR-BRK-008`, `NFR-BRK-010`
**Fix target:** Code and tests

### Current behavior

The shared adapter wrapper stores current call timing and provider latency as mutable instance fields.

Two concurrent calls on the same adapter can overwrite one another’s start time or provider-latency value before `_result()` consumes it.

The existing performance tests cover sequential calls but not concurrent calls.

### Required correction

Use task-local or invocation-local measurement state:

* `contextvars.ContextVar`;
* an immutable call-context object passed through the operation;
* or a wrapper that builds the result before leaving the invocation-local scope.

Add a deterministic barrier-based concurrency test proving that each result receives its own provider latency and total latency.

---

## `REV-BRK-012` — Verified session evidence is incomplete

**Severity:** `HIGH`
**Affected IDs:** `FR-BRK-012`–`FR-BRK-015`, `FR-BRK-048`–`FR-BRK-057`, `FR-BRK-104`, `FR-BRK-105`, `WF-BRK-002`
**Fix target:** Code, tests, documentation

### Evidence

MT5 connection verification checks:

* initialization;
* account presence;
* terminal presence;
* login;
* server.

It does not statically verify all documented evidence, including terminal connected state, trade permission, and explicit account/environment classification.

The provider manifest says the probe verifies terminal, account login, server, and trade permission.

### Required correction

* Populate provider-specific `BrokerConnectionStatus` fields.
* Preserve `trading_permitted=False` as provider truth.
* Do not infer mutation permission from connection success.
* Verify endpoint/account environment using provider evidence where available.
* Fail closed when account or environment cannot be established.
* Add negative tests for mismatched login, server, account ID, and environment.

---

## `REV-BRK-013` — Real non-production provider evidence is incomplete

**Severity:** `HIGH`
**Affected IDs:** Provider release evidence, `FR-BRK-104`–`FR-BRK-108`, `NFR-BRK-012`, `NFR-BRK-015`
**Fix target:** Tests and documentation

### Evidence

The credential-gated suite:

* genuinely connects MT5 when demo credentials are available;
* only constructs a cTrader adapter and does not make a network connection;
* contains no equivalent real test for Binance, Yahoo, or Dukascopy.

The settings file supports only MT5 and cTrader credentials.

### Required correction

Add explicit, read-only non-production validation for every released provider profile. A skipped test is not release evidence.

No provider mutation is authorized by this plan.

---

# 4. Medium and low findings

## `REV-BRK-014` — Package root uses wildcard contract import

**Severity:** `MEDIUM`
**Affected IDs:** `FR-BRK-135`, public API policy
**Fix target:** Code and tests

`app/services/brokers/__init__.py` uses a wildcard import from `contracts`, even though the required policy calls for explicit imports and an explicit `__all__`.

Replace the wildcard with explicit named imports and add a test asserting the complete root export set, not only selected exclusions.

---

## `REV-BRK-015` — Async context manager raises an undocumented domain-adjacent exception

**Severity:** `MEDIUM`
**Affected IDs:** Lifecycle public API, exception policy
**Fix target:** Documentation or code

The adapter async context manager raises `RuntimeError` when `connect()` returns a canonical failure, while the operation tables generally state that expected failures are result values and only cancellation escapes.

Either:

* explicitly document `RuntimeError` for `__aenter__`; or
* expose a separate result-aware context helper.

The recommended minimal resolution is to document the exception because Python context entry cannot return both the adapter and a `BrokerResult`.

---

## `REV-BRK-016` — Test and usage manifests and commands are inconsistent

**Severity:** `MEDIUM`
**Affected IDs:** `NFR-BRK-012`, Definition of Done
**Fix target:** Tests and documentation

Problems include:

* `01`–`13` versus `00`–`14`;
* fake usage mapped to the registry example;
* references to “thirteen” feature programs in one section and fifteen elsewhere;
* targeted pytest commands that inherit repository-wide coverage addopts and may not represent a clean targeted-test command;
* no current test for exact folder/feature/usage reconciliation.

Add a static documentation-parity test and provide commands that explicitly disable global addopts for targeted execution.

---

## `REV-BRK-017` — Broad suppressions and low-information docstrings

**Severity:** `LOW`
**Affected IDs:** Code-quality policy
**Fix target:** Code

Examples include:

* file-wide Ruff suppressions covering multiple rule families;
* docstrings such as “Value supplied to the operation”;
* generic “Handle open”/“Handle close” descriptions.

Narrow suppressions to specific lines and replace generic docstrings in files touched by this plan. Do not initiate an unrelated repository-wide formatting rewrite.

---

# 5. Expected-versus-actual package inventory

## Observed committed inventory

```text
app/services/brokers/
├── README.md
├── __init__.py
├── contracts/
│   ├── __init__.py
│   ├── enums.py
│   ├── models.py
│   ├── protocols.py
│   └── unsupported.py
├── runtime/
│   ├── __init__.py
│   ├── circuit_breaker.py
│   └── subscription.py
├── registry/
│   ├── __init__.py
│   ├── catalogue.py
│   └── factory.py
├── mt5/
│   ├── __init__.py
│   ├── adapter.py
│   ├── mapping.py
│   └── transport.py
├── ctrader/
│   ├── __init__.py
│   ├── adapter.py
│   ├── mapping.py
│   ├── network.py
│   └── transport.py
├── binance/
│   ├── __init__.py
│   ├── adapter.py
│   ├── mapping.py
│   ├── profiles.py
│   └── transport.py
├── dukascopy/
│   ├── __init__.py
│   ├── adapter.py
│   ├── instruments.py
│   ├── mapping.py
│   ├── transport.py
│   ├── candle_mapping.py
│   └── candle_transport.py
├── yahoo/
│   ├── __init__.py
│   ├── adapter.py
│   ├── mapping.py
│   └── transport.py
└── testing/
    ├── __init__.py
    └── fake.py
```

## Reconciliation result

| Check                           |                    Expected |                                                                     Actual | Result                                                     |
| ------------------------------- | --------------------------: | -------------------------------------------------------------------------: | ---------------------------------------------------------- |
| Registered feature IDs          |                          15 |                                                                         15 | Matches                                                    |
| Feature-owned folders           |                          15 |                                                            Approximately 8 | `NONCOMPLIANT`                                             |
| Usage programs                  |                          15 |                       15 named in normative manifest; execution unverified | Static count appears aligned                               |
| One feature per provider folder |                    Required |                                      Multiple features per provider folder | `NONCOMPLIANT`                                             |
| Root behavior files             | Only allowed infrastructure |                                     Root has only `__init__.py` and README | Compliant                                                  |
| Undocumented support behavior   |                  Prohibited | `runtime/` owns substantial behavioral FRs without a registered feature ID | `NONCOMPLIANT`                                             |
| Parallel legacy paths           |                None allowed |                                 No obvious legacy compatibility tree found | Static result `UNVERIFIED` pending filesystem/import audit |

---

# 6. Functional-requirement traceability matrix

This grouped matrix covers every `FR-BRK-*` ID. Behavioral status remains `UNVERIFIED` unless static noncompliance is proven.

| Requirement        | README owner                                       | Implementation                              | Unit/integration evidence                | Usage                              | Result         | Finding                                   |
| ------------------ | -------------------------------------------------- | ------------------------------------------- | ---------------------------------------- | ---------------------------------- | -------------- | ----------------------------------------- |
| `FR-BRK-001`–`005` | Contracts enums                                    | `contracts/enums.py`                        | `test_enums.py`                          | `00_contracts.py`                  | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-006`–`009` | Config/error/result/page                           | `contracts/models.py`                       | `test_models.py`                         | `00_contracts.py`                  | `UNVERIFIED`   | Runtime validation pending                |
| `FR-BRK-010`–`011` | Capability and flags                               | Models/catalogue/base adapter               | Models/catalogue tests                   | `00`, `01`                         | `NONCOMPLIANT` | `REV-BRK-001`                             |
| `FR-BRK-012`–`015` | Connection status/events/platform/permissions      | Models/base/provider adapters               | Model and lifecycle tests                | `00`, provider usage               | `NONCOMPLIANT` | `REV-BRK-008`, `012`                      |
| `FR-BRK-016`–`042` | Canonical DTOs and requests                        | `contracts/models.py`                       | `test_models.py`, provider mapping tests | `00_contracts.py`                  | `UNVERIFIED`   | Execute invariant and mapping suites      |
| `FR-BRK-043`–`047` | Core adapter protocol/lifecycle                    | `contracts/protocols.py`                    | `test_protocols.py`                      | `00_contracts.py`                  | `NONCOMPLIANT` | `REV-BRK-015`                             |
| `FR-BRK-048`–`057` | Session lifecycle/reconnect/events                 | Base and provider adapters                  | Lifecycle tests                          | Provider lifecycle usage           | `NONCOMPLIANT` | `REV-BRK-007`, `008`, `012`               |
| `FR-BRK-058`–`067` | Market reads                                       | Provider adapters/mappings                  | Data-boundary and provider tests         | Provider usage                     | `UNVERIFIED`   | Transport controls affect evidence        |
| `FR-BRK-068`–`072` | Subscriptions                                      | cTrader/Binance/runtime                     | Streaming tests                          | `11_price_streams.py`              | `NONCOMPLIANT` | `REV-BRK-008`                             |
| `FR-BRK-073`–`090` | Account/execution-state reads                      | MT5/cTrader                                 | Account-state tests                      | `02`, `03`, `09`                   | `UNVERIFIED`   | Execute provider mapping/workflow tests   |
| `FR-BRK-091`–`097` | Mutation operations                                | MT5/cTrader                                 | Mutation tests                           | `07`, `08`                         | `NONCOMPLIANT` | `REV-BRK-001`                             |
| `FR-BRK-098`–`100` | Provider calculations                              | MT5/cTrader                                 | Calculation tests                        | `10_calculations.py`               | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-101`       | Exact adapter factory                              | `registry/factory.py`                       | `test_factory.py`                        | `01_registry.py`                   | `NONCOMPLIANT` | `REV-BRK-001`, `010`                      |
| `FR-BRK-102`–`103` | Listing/catalogue                                  | Registry                                    | Factory/catalogue tests                  | `01_registry.py`                   | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-104`       | MT5 fulfillment                                    | `mt5/*`                                     | MT5 unit/integration                     | `02`, `07`, `09`, `10`             | `NONCOMPLIANT` | `REV-BRK-001`, `006`, `007`, `012`        |
| `FR-BRK-105`       | cTrader fulfillment                                | `ctrader/*`                                 | cTrader tests                            | `03`, `08`, `09`, `10`, `11`, `12` | `NONCOMPLIANT` | `REV-BRK-001`, `006`, `007`, `012`, `013` |
| `FR-BRK-106`       | Binance fulfillment                                | `binance/*`                                 | Binance tests                            | `04`, `11`                         | `NONCOMPLIANT` | `REV-BRK-006`, `007`, `013`               |
| `FR-BRK-107`       | Dukascopy fulfillment                              | `dukascopy/*`                               | Dukascopy tests                          | `05`, `13`                         | `NONCOMPLIANT` | `REV-BRK-003` specification conflict      |
| `FR-BRK-108`       | Yahoo fulfillment                                  | `yahoo/*`                                   | Yahoo tests                              | `06`                               | `NONCOMPLIANT` | `REV-BRK-004`, `006`, `013`               |
| `FR-BRK-109`       | Fake adapter                                       | `testing/fake.py`                           | `test_fake_adapter.py`                   | `14_fake_adapter.py`               | `NONCOMPLIANT` | `REV-BRK-009`                             |
| `FR-BRK-110`       | Unsupported results                                | `contracts/unsupported.py`                  | `test_unsupported.py`                    | `01_registry.py`                   | `UNVERIFIED`   | Execute no-call tests                     |
| `FR-BRK-111`       | Circuit breaker                                    | `runtime/circuit_breaker.py` and transports | Circuit unit/integration                 | `11_price_streams.py`              | `NONCOMPLIANT` | `REV-BRK-006`                             |
| `FR-BRK-112`       | Subscription protocol                              | Contracts/runtime                           | Protocol/stream tests                    | `11_price_streams.py`              | `NONCOMPLIANT` | `REV-BRK-008`                             |
| `FR-BRK-113`       | Contract exports                                   | `contracts/__init__.py`                     | Import-boundary tests                    | `00`, `01`                         | `UNVERIFIED`   | Execute exact-export tests                |
| `FR-BRK-114`       | Subscription implementation                        | `runtime/subscription.py`                   | Subscription tests                       | `11_price_streams.py`              | `NONCOMPLIANT` | `REV-BRK-008`                             |
| `FR-BRK-115`       | Private runtime initializer                        | `runtime/__init__.py`                       | Import-boundary test                     | `11_price_streams.py`              | `UNVERIFIED`   | Ownership changes under `REV-BRK-002`     |
| `FR-BRK-116`       | MT5 transport                                      | `mt5/transport.py`                          | MT5 transport tests                      | `02_mt5_account.py`                | `NONCOMPLIANT` | `REV-BRK-006`, `007`                      |
| `FR-BRK-117`–`118` | MT5 mapping/export                                 | `mt5/mapping.py`, `__init__.py`             | Mapping/import tests                     | `02`                               | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-119`       | cTrader transport/network                          | `ctrader/transport.py`, `network.py`        | Transport/correlation tests              | `03`                               | `NONCOMPLIANT` | `REV-BRK-006`, `007`                      |
| `FR-BRK-120`–`122` | cTrader mapping/export and Binance profiles        | Respective files                            | Unit/import/profile tests                | `03`, `04`                         | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-123`       | Binance transport                                  | `binance/transport.py`                      | Binance transport tests                  | `04`, `11`                         | `NONCOMPLIANT` | `REV-BRK-006`, `007`                      |
| `FR-BRK-124`–`129` | Binance/Dukascopy mapping/export                   | Provider files                              | Mapping/import tests                     | `04`, `05`, `13`                   | `UNVERIFIED`   | Subject to `REV-BRK-003`                  |
| `FR-BRK-130`       | Yahoo transport                                    | `yahoo/transport.py`                        | Yahoo transport tests                    | `06`                               | `NONCOMPLIANT` | Circuit canonical-code issue              |
| `FR-BRK-131`–`134` | Yahoo mapping/export, registry export, fake export | Respective files                            | Mapping/import tests                     | `01`, `06`, `14`                   | `UNVERIFIED`   | Execute tests                             |
| `FR-BRK-135`       | Package root public API                            | `brokers/__init__.py`                       | Import-boundary tests                    | `01_registry.py`                   | `NONCOMPLIANT` | `REV-BRK-001`, `014`                      |

---

# 7. Non-functional-requirement compliance matrix

| Requirement                            | Static result          | Reason                                                                             |
| -------------------------------------- | ---------------------- | ---------------------------------------------------------------------------------- |
| `NFR-BRK-001` Architecture boundary    | `UNVERIFIED`           | No obvious higher-domain production imports found; full import scan still required |
| `NFR-BRK-002` Provider truth           | `UNVERIFIED`           | Mapping code is structured conservatively; provider execution not run              |
| `NFR-BRK-003` API boundary             | `NONCOMPLIANT`         | Wildcard root import and direct concrete-construction safety issue                 |
| `NFR-BRK-004` Fail closed              | `NONCOMPLIANT`         | Direct adapter write-policy bypass                                                 |
| `NFR-BRK-005` Independence/concurrency | `NONCOMPLIANT`         | Shared mutable latency state                                                       |
| `NFR-BRK-006` Async safety             | `UNVERIFIED`           | Blocking calls generally use threads/async SDKs; cancellation suite must run       |
| `NFR-BRK-007` Security                 | `UNVERIFIED`           | Basic redaction tests exist; full log and exception scan not executed              |
| `NFR-BRK-008` Observability            | `UNVERIFIED`           | Logging code exists; fields and redaction require runtime capture                  |
| `NFR-BRK-009` Determinism              | `NONCOMPLIANT`         | Circuit error mapping and queue eviction violate documented deterministic outcomes |
| `NFR-BRK-010` Performance              | `NONCOMPLIANT`         | Concurrency timing race and missing provider-limit enforcement                     |
| `NFR-BRK-011` Domain independence      | `UNVERIFIED`           | Static imports appear appropriately downward; complete import audit required       |
| `NFR-BRK-012` Testing                  | `NONCOMPLIANT`         | Folder/usage mismatch, missing safety regressions, unsupported execution claims    |
| `NFR-BRK-013` Dependencies             | `UNVERIFIED`           | Manifest inspected; lock resolution and imports not executed                       |
| `NFR-BRK-014` Persistence              | `COMPLIANT` statically | No Brokers database, migration, credential store, or durable cache found           |
| `NFR-BRK-015` Research-provider scope  | `UNVERIFIED`           | Catalogue appears to gate production use; runtime/provider validation pending      |

---

# 8. Workflow and system-workflow verification

The README defines nine Brokers workflows.

| Workflow                                  | Static result                 | Behavioral result | Finding                                                                                       |
| ----------------------------------------- | ----------------------------- | ----------------- | --------------------------------------------------------------------------------------------- |
| `WF-BRK-001` Resolve explicit adapter     | `NONCOMPLIANT`                | `UNVERIFIED`      | Dependency metadata incomplete; direct factory gate is bypassable through public constructors |
| `WF-BRK-002` Connect/authenticate         | `NONCOMPLIANT`                | `UNVERIFIED`      | Timeout, reconnect, account/environment, and connection-event issues                          |
| `WF-BRK-003` Market-data acquisition      | Static implementation present | `UNVERIFIED`      | Test uses genuine Yahoo mapping over a stub, but forged capability map bypasses policy        |
| `WF-BRK-004` Submit mutation              | `NONCOMPLIANT`                | `UNVERIFIED`      | Direct concrete construction releases mutation bodies                                         |
| `WF-BRK-005` Read account/execution state | Static implementation present | `UNVERIFIED`      | Provider tests must run                                                                       |
| `WF-BRK-006` Stream events                | `NONCOMPLIANT`                | `UNVERIFIED`      | Silent eviction of accepted events                                                            |
| `WF-BRK-007` cTrader correlation          | Static implementation present | `UNVERIFIED`      | Correlation tests not executed; session-generation behavior requires confirmation             |
| `WF-BRK-008` Unsupported operation        | Static implementation present | `UNVERIFIED`      | Must additionally prove no constructor/capability bypass                                      |
| `WF-BRK-009` Inject canonical adapter     | `NONCOMPLIANT`                | `UNVERIFIED`      | Public concrete adapters accept mutable policy input                                          |

The workflow documentation requires explicit backpressure and forbids silent data loss.

## System workflows

| System workflow                  | Project status                            | Brokers assessment                                                            |
| -------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------- |
| `SYS-WF-001` Historical backtest | System remains incomplete outside Brokers | Brokers is upstream acquisition only; broker segment `UNVERIFIED`             |
| `SYS-WF-002` Governed order path | System workflow not complete              | Brokers mutation boundary `NONCOMPLIANT` because release policy is bypassable |
| `SYS-WF-008` Paper/live route    | Documented as completed at system level   | Brokers boundary is not statically safe until `REV-BRK-001` is fixed          |

---

# 9. Contract and persistence reconciliation

| Contract or policy                   | Owner                      | Consumer          | Static status          | Notes                                                                              |
| ------------------------------------ | -------------------------- | ----------------- | ---------------------- | ---------------------------------------------------------------------------------- |
| `BrokerAdapter v1`                   | Brokers                    | Data, Trading     | `NONCOMPLIANT`         | Protocol exists, but constructor/release policy can be bypassed                    |
| Capability traits                    | Brokers                    | Data, Trading     | `NONCOMPLIANT`         | Structural read/write split exists; capability-ID/access-mode invariant is missing |
| `BrokerConnectionConfig v1`          | Brokers                    | Composition root  | `NONCOMPLIANT`         | Fields exist; timeout/reconnect semantics are not fully implemented                |
| `BrokerResult v1` / `BrokerError v1` | Brokers                    | Data, Trading     | `UNVERIFIED`           | Static invariants present; canonical circuit/open mapping needs correction         |
| Canonical DTO family                 | Brokers                    | Data, Trading     | `UNVERIFIED`           | Strong static validation; mapping suites not executed                              |
| `BrokerFeatureFlags v1`              | Brokers                    | Data, Trading     | `NONCOMPLIANT`         | Trusts supplied capability map without authoritative-policy equality               |
| `BrokerSubscription`                 | Brokers                    | Data, Trading     | `NONCOMPLIANT`         | Queue semantics discard accepted data                                              |
| Request/correlation IDs              | Utils                      | Brokers           | `UNVERIFIED`           | Static calls use Utils ID utilities                                                |
| UTC policy                           | Utils                      | Brokers           | `UNVERIFIED`           | DTO validation exists; provider mapping must be executed                           |
| Secret redaction                     | Utils                      | Brokers           | `UNVERIFIED`           | Basic tests exist; full log capture and scan required                              |
| Persistence ownership                | Data/Trading as applicable | Brokers owns none | `COMPLIANT` statically | No database or migration behavior found in Brokers                                 |
| Raw provider objects                 | Must not cross             | All consumers     | `UNVERIFIED`           | Mapper designs are present; provider contract tests must run                       |

The architecture allows only Data and Trading to depend on Brokers, with only Trading permitted to mutate.

---

# 10. Public API and dependency-boundary review

## Static positives

* Contracts define explicit `__all__`.
* Provider SDKs are generally imported lazily.
* The root uses lazy provider-class resolution.
* The fake adapter is not registered as a production provider.
* No obvious business-domain or persistence imports were found in production Brokers files.
* Consumer trait tests distinguish read traits from mutation traits.

## Static defects

1. Root wildcard import violates the explicit-re-export policy.
2. Public concrete adapter constructors accept policy-bearing capability maps.
3. Tests frequently import provider implementation modules directly. This is acceptable only for provider integration tests, not consumer-boundary tests.
4. The existing root export test does not assert the entire exact root export set.
5. Capability metadata does not enforce a canonical access mode for each capability ID.
6. The dependency-error path does not return the required dependency constraint metadata.

---

# 11. Safety and security review

## Safety result

`NONCOMPLIANT`

The direct write-policy bypass is a blocking safety defect.

No evidence was found that the reviewed code automatically runs a live mutation at import time. However, the direct-construction path permits a caller to execute provider mutation bodies if supplied with valid production configuration and a forged capability map.

## Security observations

Static positives:

* Credentials use `SecretStr`.
* Config and error redaction tests exist.
* Provider logs generally bind selected metadata rather than complete credential payloads.
* SDK imports are lazy.

Unverified areas:

* Provider-native exception messages may contain account or endpoint information.
* Full log records were not captured.
* Account-reference fingerprinting was not executed.
* Secret scanning was not run.
* Real provider credentials and account classification were not available.

## Mandatory non-production provider checklist

Before any provider validation, the local agent must confirm:

* `ENVIRONMENT` is not `production`.
* `RUNTIME_PROFILE` is not `live`.
* `ALLOW_LIVE_MUTATIONS=false`.
* MT5 account is confirmed `DEMO`.
* cTrader account is confirmed `DEMO`.
* Binance profile is `TESTNET` for authenticated checks.
* Yahoo and Dukascopy use their research/sandbox profile.
* The generated capability catalogue reports every mutation operation `UNAVAILABLE`.
* Validation invokes only connection, metadata, market-read, account-read, subscription, and disconnect operations.
* No `place_order`, `modify_order`, `cancel_order`, `modify_position`, `close_position`, or equivalent native method is called.
* All provider sessions and subscriptions are explicitly closed.
* Logs and captured evidence contain no full credentials or account identifiers.

---

# 12. Commands and validation results

No command below has been executed.

| Phase                  | Command to be run by local agent                                                                                                                                                                                                                           | Purpose                                                | Expected exit | Current status                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------: | ---------------------------------- |
| Baseline               | `git rev-parse --abbrev-ref HEAD`                                                                                                                                                                                                                          | Record local branch                                    |           `0` | To be executed                     |
| Baseline               | `git rev-parse HEAD`                                                                                                                                                                                                                                       | Record local commit                                    |           `0` | To be executed                     |
| Baseline               | `git status --short`                                                                                                                                                                                                                                       | Record pre-existing owner changes                      |           `0` | To be executed                     |
| Environment            | `uv --version`                                                                                                                                                                                                                                             | Verify uv availability                                 |           `0` | To be executed                     |
| Environment            | `uv run --frozen python --version`                                                                                                                                                                                                                         | Verify existing frozen environment and Python          |           `0` | To be executed                     |
| Lock validation        | `uv lock --check`                                                                                                                                                                                                                                          | Verify lockfile is current without changing it         |           `0` | To be executed                     |
| Format                 | `uv run --frozen ruff format --check app/services/brokers tests/brokers`                                                                                                                                                                                   | Domain formatting                                      |           `0` | To be executed                     |
| Lint                   | `uv run --frozen ruff check --no-cache app/services/brokers tests/brokers`                                                                                                                                                                                 | Domain linting                                         |           `0` | To be executed                     |
| Types                  | `uv run --frozen mypy --no-incremental app/services/brokers tests/brokers`                                                                                                                                                                                 | Strict type validation                                 |           `0` | To be executed                     |
| Unit                   | `uv run --frozen pytest -o addopts="" tests/brokers/unit -q`                                                                                                                                                                                               | Domain unit tests without global coverage addopts      |           `0` | To be executed                     |
| Integration            | `uv run --frozen pytest -o addopts="" tests/brokers/integration -q`                                                                                                                                                                                        | Workflow and compatibility tests                       |           `0` | To be executed                     |
| Safety targets         | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_capability_policy.py tests/brokers/integration/test_trading_mutation_boundary.py -q`                                                                                                         | Prove write gate cannot be bypassed                    |           `0` | File to add/update                 |
| Transport targets      | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_transport_controls.py tests/brokers/integration/test_circuit_breaking.py -q`                                                                                                                 | Circuit/rate/reconnect behavior                        |           `0` | File to add/update                 |
| Queue targets          | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_subscription.py tests/brokers/integration/test_streaming.py -q`                                                                                                                              | FIFO, overflow, drain, resync                          |           `0` | To be executed after fixes         |
| Concurrency            | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_concurrent_result_timing.py -q`                                                                                                                                                              | Per-call latency isolation                             |           `0` | File to add                        |
| Fake contract          | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_fake_adapter.py tests/brokers/unit/test_fake_payload_contracts.py -q`                                                                                                                        | Operation-specific payload typing                      |           `0` | File to add/update                 |
| Import safety          | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_import_boundaries.py -q`                                                                                                                                                                     | Exact exports and lazy imports                         |           `0` | To be executed                     |
| Security               | `uv run --frozen pytest -o addopts="" tests/brokers/unit/test_security.py tests/brokers/unit/test_observability.py -q`                                                                                                                                     | Redaction and structured logs                          |           `0` | To be executed                     |
| Contract compatibility | `uv run --frozen pytest -o addopts="" tests/brokers/integration/test_provider_contracts.py tests/brokers/integration/test_consumer_boundaries.py tests/brokers/integration/test_data_boundary.py tests/brokers/integration/test_execution_injection.py -q` | Producer/consumer compatibility                        |           `0` | To be executed                     |
| Usage                  | `uv run --frozen python -c "from pathlib import Path; import subprocess,sys; [subprocess.run([sys.executable,str(p)],check=True) for p in sorted(Path('tests/brokers/usage').glob('[0-9][0-9]_*.py'))]"`                                                   | Run every standalone usage program separately          |           `0` | To be executed                     |
| Import smoke           | `uv run --frozen python -c "import sys; import app.services.brokers as b; assert not {'MetaTrader5','binance','yfinance','ctrader_open_api'} & set(sys.modules)"`                                                                                          | Ensure ordinary root import is SDK-free                |           `0` | To be executed                     |
| Coverage               | `uv run --frozen pytest -o addopts="" tests/brokers --cov=app/services/brokers --cov-report=term-missing --cov-report=xml:coverage-brokers.xml --cov-fail-under=80`                                                                                        | Domain coverage                                        |           `0` | To be executed                     |
| Secret scan            | `uv run --frozen detect-secrets scan --baseline .secrets.baseline`                                                                                                                                                                                         | Detect new secrets                                     |           `0` | To be executed                     |
| Full lint              | `uv run --frozen ruff format --check .`                                                                                                                                                                                                                    | Repository formatting regression                       |           `0` | To be executed after domain passes |
| Full lint              | `uv run --frozen ruff check --no-cache .`                                                                                                                                                                                                                  | Repository lint regression                             |           `0` | To be executed after domain passes |
| Full types             | `uv run --frozen mypy --no-incremental .`                                                                                                                                                                                                                  | Repository type regression                             |           `0` | To be executed after domain passes |
| Full tests             | `uv run --frozen pytest`                                                                                                                                                                                                                                   | Complete repository regression and configured coverage |           `0` | To be executed after domain passes |

No command in this plan authorizes dependency installation, `uv sync`, `uv add`, `uv remove`, lockfile modification, staging, commits, pushes, migrations, or destructive cleanup.

---

# 13. Coverage result

**Status:** `To be executed by local agent`

Required threshold:

```text
app/services/brokers package coverage >= 80%
```

Acceptance requires:

* command exits `0`;
* no excluded production file used to inflate coverage;
* every corrected safety branch has direct test coverage;
* usage scripts are executed independently and are not counted as pytest coverage;
* skipped provider tests are reported separately and never treated as passing release evidence.

---

# 14. README status and checklist accuracy

| Claim                           | Assessment                                                           |
| ------------------------------- | -------------------------------------------------------------------- |
| Domain status `Partial` at top  | Accurate                                                             |
| Contracts `Completed`           | Static implementation substantial; behavioral status `UNVERIFIED`    |
| Runtime `Completed`             | Incorrect due circuit integration and queue semantics                |
| Registry/public API `Completed` | Incorrect due bypass and dependency metadata                         |
| MT5 `Completed`                 | Incorrect due gate, circuit, timeout/reconnect, and session evidence |
| cTrader `Completed`             | Incorrect due gate, rate/circuit, provider validation                |
| Binance baseline completed      | Overstated until weight controls and provider validation pass        |
| Dukascopy baseline completed    | Specification conflict must be resolved                              |
| Yahoo baseline completed        | Probe contradiction and provider evidence remain                     |
| Fake utility completed          | Incorrect due wrong payload-type acceptance                          |
| Package validation completed    | Unsupported in this review                                           |
| 333 tests pass                  | `UNVERIFIED`                                                         |
| Ruff/Mypy clean                 | `UNVERIFIED`                                                         |
| Coverage >=80%                  | `UNVERIFIED`                                                         |
| Exact tree matches              | False under Focused Domain Architecture                              |
| Every checklist item verified   | False                                                                |

All completion checkboxes must remain unchecked or explicitly marked `UNVERIFIED` until current validation evidence is produced.

---

# 15. Feature Registry and changelog accuracy

## Feature Registry

The registry identifies useful capability groups, but the one-feature/one-folder mapping is not implemented.

Required changes:

* retain stable existing feature IDs where possible;
* add a feature ID for shared adapter runtime/circuit behavior rather than hiding behavioral FRs in a support folder;
* assign every production behavior to one feature owner;
* align each feature with one folder and one usage program;
* document thin provider facade composition separately from feature behavior;
* update statuses only after validation.

## Changelog

`docs/CHANGELOG.md` appears to follow a released-version history structure. It must not be rewritten as a current-state registry.

Do not alter historical statements in old release blocks merely to update current status. Future release-visible corrections should be recorded in a new release block only when actually released.

---

# 16. Final review checklist

* [x] Remote branch and commit recorded.
* [x] Remote committed-state limitation recorded.
* [x] Authority order applied.
* [x] Specification conflicts identified.
* [x] Purpose and ownership inspected.
* [x] Package structure reconciled.
* [x] Feature-count mismatch identified.
* [x] Public API inspected.
* [x] Cross-domain read/write boundaries inspected.
* [x] Workflows inspected.
* [x] Functional requirements traced.
* [x] NFRs assessed.
* [x] Contract and persistence ownership assessed.
* [x] Safety review performed.
* [x] Test inventory and test quality inspected.
* [x] Validation commands specified.
* [x] No commands executed.
* [x] No files modified.
* [x] No external provider contacted.
* [ ] Specification contradictions resolved by owner.
* [ ] Corrections implemented.
* [ ] Ruff passes.
* [ ] Mypy passes.
* [ ] Unit tests pass.
* [ ] Integration tests pass.
* [ ] Usage programs pass.
* [ ] Provider validation passes.
* [ ] Coverage is at least 80%.
* [ ] Documentation parity revalidated.
* [ ] Final result determined by local agent.

---

# 17. CORRECTION PLAN AND IMPLEMENTATION STEPS

# Correction Plan 1

This is the latest explicitly numbered plan.

Execution is authorized only after the local agent receives a standalone owner message whose entire trimmed content is exactly:

```text
APPROVED: EXECUTE
```

## Step 0 — Preserve baseline and scope

Before editing:

1. Run the baseline commands in Section 12.
2. Record all pre-existing local modifications.
3. Do not overwrite, revert, format, stage, or otherwise change owner work outside the approved file list.
4. If a required dependency is unavailable in the existing frozen environment, stop and report `BLOCKED`. Do not install or upgrade it.
5. Do not modify `uv.lock`.
6. Do not call a live or production provider.
7. Do not run any mutation method against any real provider.

---

## Step 1 — Resolve specification contradictions

### Findings

* `REV-BRK-003`
* `REV-BRK-004`
* documentation portion of `REV-BRK-005`

### Files

* `docs/PROJECT.md`
* `docs/ARCHITECTURE.md`
* `app/services/brokers/README.md`

### Exact changes

1. Change the stale `docs/PROJECT.md` Dukascopy statement from local midpoint aggregation to direct provider BID candle mapping.
2. Preserve the rule that Brokers does not derive OHLC locally from BI5 ticks.
3. Make Yahoo connect-time verification require an explicit non-empty `probe_symbol`.
4. Remove the conflicting text saying Yahoo can report a verified connection without a probe.
5. Set Brokers system/domain status to `Partial` while implementation corrections and validation remain outstanding.
6. Reconcile feature IDs as `FEAT-BRK-00`–`FEAT-BRK-14` before the structural addition below.
7. Correct all `13`, `01–13`, and misplaced fake-usage references.
8. Do not mark any test, coverage, provider, or tooling claim as current success.

### Validation

Add or update:

```text
tests/brokers/unit/test_documentation_parity.py
```

It must parse the active README and assert:

* one Feature Registry;
* no contradictory `probe_symbol` rule;
* no midpoint aggregation claim;
* exactly one usage path per registered feature;
* no checked completion claim while the overall status is `Partial`;
* every referenced path exists.

### Dependency

Must precede behavioral implementation where the contradiction affects code.

### Regression risk

Low under the recommended resolution.

---

## Step 2 — Close the write-release bypass

### Finding

`REV-BRK-001`

### Files

* `app/services/brokers/contracts/models.py`
* `app/services/brokers/contracts/protocols.py`
* `app/services/brokers/registry/catalogue.py`
* `app/services/brokers/registry/factory.py`
* all provider adapter constructors
* `app/services/brokers/__init__.py`
* provider tests that currently inject arbitrary capability maps

### Exact changes

1. Define one immutable canonical mapping from every `BrokerCapabilityId` to its allowed access mode.
2. Validate that:

   * mutation IDs cannot declare `READ`;
   * read IDs cannot be converted to `WRITE`;
   * an instance capability map equals the authoritative catalogue for its provider and environment.
3. Remove the `capabilities` argument from public production adapter constructors.
4. Make each production adapter derive its capability map from Brokers-owned policy.
5. Keep `create_broker_adapter()` as the supported instance creation route.
6. Keep concrete classes root-exported only if their direct constructor is equally safe and applies the same policy.
7. Extract unreleased mutation translation/provider-call bodies into private implementation methods or private feature mixins.
8. Test those private implementations with provider-shaped transports without replacing production release policy.
9. Ensure the public `place_order()` and related methods remain unavailable when the catalogue says so.
10. Ensure subclassing cannot override a plain instance field to release a write through the supported public wrapper.

### Tests

Create:

```text
tests/brokers/unit/test_capability_policy.py
```

Required cases:

* `PLACE_ORDER` declared `READ` raises at construction.
* `GET_QUOTE` declared `WRITE` raises.
* forged available write map is rejected.
* direct MT5 construction cannot release writes.
* direct cTrader construction cannot release writes.
* registry construction cannot release writes.
* fake fixture injection cannot release an unavailable capability.
* provider transport receives zero mutation calls for every blocked path.

Update:

```text
tests/brokers/integration/test_trading_mutation_boundary.py
tests/brokers/unit/test_models.py
tests/brokers/unit/test_catalogue.py
tests/brokers/unit/test_factory.py
```

### Acceptance

* Every public construction path blocks unreleased writes.
* Private mutation-implementation tests still verify translation and acknowledgement behavior.
* No real provider mutation is executed.
* Target commands exit `0`.

### Regression risk

High.

---

## Step 3 — Implement the approved Focused Domain Architecture

### Finding

`REV-BRK-002`

### Selected scenario

**Fix both code and documentation.**

### Target feature structure

Preserve existing IDs and add one new explicit runtime feature:

```text
FEAT-BRK-00  contracts/
FEAT-BRK-01  registry/
FEAT-BRK-02  mt5_account/
FEAT-BRK-03  ctrader_session/
FEAT-BRK-04  binance_session/
FEAT-BRK-05  dukascopy_ticks/
FEAT-BRK-06  yahoo_history/
FEAT-BRK-07  mt5_mutations/
FEAT-BRK-08  ctrader_mutations/
FEAT-BRK-09  execution_history/
FEAT-BRK-10  provider_calculations/
FEAT-BRK-11  price_streams/
FEAT-BRK-12  ctrader_market_data/
FEAT-BRK-13  dukascopy_bars/
FEAT-BRK-14  testing/
FEAT-BRK-15  adapter_runtime/
```

Usage files:

```text
00_contracts.py
01_registry.py
02_mt5_account.py
03_ctrader_lifecycle.py
04_binance_lifecycle.py
05_dukascopy_lifecycle.py
06_yahoo_lifecycle.py
07_mt5_mutations.py
08_ctrader_mutations.py
09_history_reads.py
10_calculations.py
11_price_streams.py
12_ctrader_market_data.py
13_dukascopy_bars.py
14_fake_adapter.py
15_adapter_runtime.py
```

### Exact implementation rules

1. Move `_UnsupportedAdapterBase`, invocation-local result wrapping, common lifecycle transitions, and the circuit breaker into `adapter_runtime/`.
2. Move `_BrokerSubscription` into `price_streams/`.
3. Extract MT5 mutation method bodies into `mt5_mutations/`.
4. Extract cTrader mutation method bodies into `ctrader_mutations/`.
5. Extract MT5/cTrader history reads into `execution_history/`.
6. Extract MT5/cTrader calculation methods into `provider_calculations/`.
7. Extract cTrader market-data reads into `ctrader_market_data/`.
8. Extract cTrader/Binance stream producers into `price_streams/`.
9. Keep provider connection/session transports in their lifecycle/session feature.
10. Provider facade classes may compose private feature mixins, but the facade file must contain no duplicated operation behavior.
11. Keep imports dependency ordered:

    * contracts;
    * adapter runtime;
    * provider session primitives;
    * feature operations;
    * thin facade;
    * registry;
    * package root.
12. Do not leave compatibility wrappers at old deep import paths.
13. Update tests to consume package-root public exports unless a test explicitly validates a private provider implementation.
14. Remove old production directories only after all behavior and imports have moved:

    * `runtime/`;
    * `mt5/`;
    * `ctrader/`;
    * `binance/`;
    * `dukascopy/`;
    * `yahoo/`.
15. The deletion of those exact superseded directories is authorized only as part of this structural move and only after import and usage tests pass against the new paths.
16. No other production directory may be deleted.

### Documentation

Update:

* Feature Registry.
* Section 2 tree.
* file tables;
* requirement ownership;
* usage mappings;
* dependency order;
* public API paths;
* count reconciliation.

Do not change statuses to `Completed` yet.

### Tests

Add exact reconciliation tests asserting:

```text
feature count == feature-folder count == numbered-usage count == 16
```

Each folder must have exactly one registered feature ID.

### Acceptance

* No feature behavior remains in an unregistered support directory.
* No old compatibility import path remains.
* Package-root public signatures remain compatible unless explicitly changed by `REV-BRK-001`.
* All import, unit, integration, and usage tests pass.

### Regression risk

High.

---

## Step 4 — Implement transport control requirements

### Findings

* `REV-BRK-006`
* `REV-BRK-007`

### Files after structural move

* `adapter_runtime/circuit_breaker.py`
* `mt5_account/transport.py`
* `ctrader_session/transport.py`
* `ctrader_session/network.py`
* `binance_session/transport.py`
* `yahoo_history/transport.py`
* `dukascopy_ticks/transport.py`
* `dukascopy_bars/transport.py`
* provider configuration models where necessary

### Exact changes

1. Add circuit admission before every provider transport call.
2. Record canonical success/failure exactly once after each admitted call.
3. Preserve `BROKER_CIRCUIT_OPEN` without converting it to connection loss.
4. Add a dedicated private transport exception or direct canonical result for an open circuit.
5. Use `connect_timeout_sec` for connect/authentication handshakes.
6. Use `request_timeout_sec` for provider operations.
7. Implement bounded reconnect attempts with no operation replay.
8. Add cTrader rate windows:

   * 50 non-history requests per second;
   * 5 history requests per second;
   * per connection/session.
9. Add Binance request-weight tracking from provider-returned metadata.
10. Fail with `BROKER_RATE_LIMITED` before exceeding a known provider bound.
11. Apply circuit/rate checks to stream creation and reconnect.
12. Ensure cancellations propagate.

### Tests

Create:

```text
tests/brokers/unit/test_transport_controls.py
```

Update provider transport suites and `test_circuit_breaking.py`.

Required cases:

* open circuit causes zero SDK calls;
* canonical result code is `BROKER_CIRCUIT_OPEN`;
* nonqualifying failures do not open circuit;
* timeout uses the correct config field;
* reconnect attempts are bounded;
* mutations are never replayed;
* cTrader limits are deterministic using an injected clock;
* Binance weight exhaustion blocks the next request;
* stream creation observes the same controls.

### Regression risk

High.

---

## Step 5 — Correct queue delivery semantics

### Finding

`REV-BRK-008`

### Files

* `price_streams/subscription.py`
* adapter-runtime lifecycle event delivery
* provider stream producers

### Exact changes

1. Do not evict accepted data to insert a terminal marker.
2. Keep terminal state outside the bounded data queue or reserve terminal capacity at construction.
3. On overflow:

   * mark inactive;
   * mark resynchronization required;
   * stop accepting new data;
   * drain accepted data;
   * yield exactly one `BROKER_BACKPRESSURE`;
   * terminate.
4. On explicit unsubscribe:

   * stop producer;
   * drain already accepted data;
   * terminate normally;
   * do not emit backpressure.
5. On disconnect/session-generation change:

   * drain accepted data if safe;
   * emit one resync-required terminal error;
   * terminate.
6. Make connection-event overflow explicit rather than dropping the current transition.

### Tests

Update:

```text
tests/brokers/unit/test_subscription.py
tests/brokers/integration/test_streaming.py
tests/brokers/integration/test_stream_cancellation.py
tests/brokers/integration/test_session_lifecycle.py
```

Add assertions for exact sequence ordering and no event disappearance.

### Regression risk

Medium to high.

---

## Step 6 — Enforce Fake Adapter result contracts

### Finding

`REV-BRK-009`

### Files

* `testing/fake.py`
* fake adapter tests
* mutation integration test
* usage `14_fake_adapter.py`

### Exact changes

1. Define the expected success payload category for every capability.
2. Validate fixtures before storing them.
3. Validate generated method results before returning.
4. Permit `None` only for operations returning `BrokerResult[None]`.
5. Validate `BrokerPage` item type for page-returning operations.
6. Replace the invalid `BrokerOrder` mutation fixture with `BrokerOrderResult`.
7. Ensure injected errors remain canonical and unavailable capabilities remain gated.

### Tests

Create:

```text
tests/brokers/unit/test_fake_payload_contracts.py
```

Use a complete parameterized matrix covering every capability.

### Regression risk

Medium.

---

## Step 7 — Correct dependency metadata

### Finding

`REV-BRK-010`

### Files

* `registry/factory.py`
* registry declaration data
* `tests/brokers/unit/test_factory.py`

### Exact changes

Extend each provider registration with:

```text
import package
distribution name
declared project constraint
installation extra
adapter module
adapter class
```

On missing dependency return:

```text
package
missing_import
required_version
installed_version
installation_extra
```

Do not parse or modify `uv.lock` at runtime.

### Regression risk

Low.

---

## Step 8 — Make timing state invocation-local

### Finding

`REV-BRK-011`

### Files

* adapter runtime base/wrapper
* all transport latency sinks
* performance tests

### Exact changes

1. Remove adapter-wide mutable current-call start and provider latency fields.
2. Introduce invocation-local timing context.
3. Ensure nested provider calls accumulate only within their owning invocation.
4. Ensure unsupported calls report zero latency and do not reuse prior measurements.
5. Ensure concurrent operations do not exchange latency values.

### Tests

Create:

```text
tests/brokers/unit/test_concurrent_result_timing.py
```

Use two calls held on independent barriers with distinct provider delays.

### Regression risk

Medium.

---

## Step 9 — Complete session verification

### Finding

`REV-BRK-012`

### Files

* MT5 session adapter
* cTrader session adapter/network
* Binance session adapter
* provider status mappings
* lifecycle tests

### Exact changes

1. Verify provider-connected state.
2. Verify configured account identity.
3. Verify provider environment/account classification.
4. Populate authentication and trading-permission fields from provider evidence.
5. Keep read-only connection success distinct from mutation availability.
6. Never make `trading_permitted=True` imply released writes.
7. Fail `READY` transition when mandatory identity evidence is absent.

### Tests

Add mismatched-account, mismatched-server, wrong-environment, permission-false, and missing-evidence cases.

### Regression risk

Medium.

---

## Step 10 — Add genuine non-production provider validation

### Finding

`REV-BRK-013`

### Files

* `tests/brokers/provider_settings.py`
* `tests/brokers/integration/test_provider_credentials.py`
* provider-specific integration files as needed

### Exact changes

Add gated settings for:

* Binance testnet;
* Yahoo sandbox/public probe;
* Dukascopy sandbox;
* explicit provider-test enable flags.

Update cTrader to perform a genuine demo handshake and one harmless read.

Each test must:

1. verify non-production environment before connecting;
2. assert all writes are unavailable;
3. perform only approved reads;
4. disconnect and release resources in `finally`;
5. fail rather than skip when the provider is designated mandatory for release validation but credentials/access are absent;
6. capture redacted evidence without secrets.

### Final-result rule

* Missing optional provider credentials: report the provider area `UNVERIFIED`.
* Missing credentials for a provider whose released capability requires current validation: final result `BLOCKED`.
* Any production or live account classification: abort immediately and report `BLOCKED`.

### Regression risk

Low to medium.

---

## Step 11 — Correct public exports, exception documentation, and code quality

### Findings

* `REV-BRK-014`
* `REV-BRK-015`
* `REV-BRK-016`
* `REV-BRK-017`

### Exact changes

1. Replace root wildcard imports with explicit imports.
2. Assert the complete root `__all__`.
3. Document `RuntimeError` from async context entry, or replace it with an explicitly documented result-aware helper.
4. Correct every usage-file reference.
5. Add the documentation-parity test.
6. Narrow broad Ruff suppressions.
7. Replace generic docstrings in all files touched by this plan.
8. Do not format unrelated domains.

### Regression risk

Low.

---

## Step 12 — Targeted validation

After each finding group:

1. Run Ruff format/check on only changed Brokers files.
2. Run Mypy on Brokers and Brokers tests.
3. Run the exact targeted tests named in that step.
4. Run the affected standalone usage file.
5. Stop on the first nonzero exit code.
6. Record command, exit code, failures, and corrective action.

No documentation status may be changed to `Completed` during targeted validation.

---

## Step 13 — Complete domain validation

Run, in this order:

1. Unit suite.
2. Integration suite.
3. Compatibility and boundary suite.
4. Security and observability suite.
5. Import-safety suite.
6. Every standalone usage program.
7. Domain coverage.
8. Ruff.
9. Mypy.
10. Secret scan.
11. Credential-gated non-production provider validation.
12. Full repository quality and test regression.

Every required command must exit `0`.

---

## Step 14 — Documentation status update

Only after all mandatory deterministic checks succeed:

1. Update the owning README statuses.
2. Record exact current test counts only if generated during this execution.
3. Record current coverage percentage.
4. Remove stale completion claims.
5. Re-run documentation-parity tests.
6. Update `docs/PROJECT.md` and `docs/ARCHITECTURE.md` consistently.
7. Do not rewrite old changelog entries.
8. Do not add a changelog release unless the owner separately authorizes and performs a release.

---

## Step 15 — Full post-correction re-review

The local agent must repeat the review against the final working tree:

* inventory;
* feature count;
* requirement traceability;
* NFR matrix;
* workflow matrix;
* contract ownership;
* imports;
* public API;
* provider safety;
* persistence;
* test quality;
* documentation parity.

The final report must classify every finding as:

* `RESOLVED`;
* open;
* newly discovered;
* `UNVERIFIED`.

Final result rules:

* `READY`: every finding resolved, all required validation exits `0`, coverage ≥80%, documentation accurate, mandatory provider evidence complete.
* `NOT READY`: any finding remains, any required deterministic command fails, or coverage is below threshold.
* `BLOCKED`: mandatory provider/environment/dependency validation cannot be completed without prohibited installation, missing access, unsafe target, or unresolved owner specification.

---

## Explicitly excluded from Correction Plan 1

* Dependency installation or upgrade.
* Lockfile changes.
* Staging, committing, or pushing.
* Branch creation.
* Pull-request creation.
* Database migration.
* Destructive commands.
* Changes outside Brokers and directly affected Brokers documentation/tests.
* Live or production mutation.
* Risk, Trading, Data, or UI/API redesign.
* Unrelated formatting.
* Compatibility wrappers for removed private paths.
* Release of any write capability.

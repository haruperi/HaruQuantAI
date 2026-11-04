# HaruQuantAI V3 — Stage 01 verification responsibility and closure map

Iteration 1; evidence review dated 2026-11-04. Scope: **S04–S14 only**.
Approved task: restore deleted evidence, classify donor-to-Python differences,
run verification where possible, and report unresolved obligations. Source HEAD
inspected through the GitHub connector:
`318aaff24b4911f59d7ac1fbe23263f456c4879f`. The working tree was not
available to inspect. **No production implementation was changed.**

This is not a declaration of complete donor parity. The previous map existed at
commit `2676c0589f6c1210ecf9145872d9542f93dd3e6c` and was deleted in
`318aaff24b4911f59d7ac1fbe23263f456c4879f`; this replacement preserves its
method-level findings while including all Stage 01 slices and explicit test
execution state. The previously recorded in-chat walkthrough and test results
cannot substitute for a fresh local regression run.

Legend: `D/` = `data/reference-donor/internal/libs/`. `Verified (reported)`
means a source/test review and prior implementation claim, **not** a passing
command witnessed in this closure task. `Subset` means donor-backed tests for
listed methods only. `Adapt/custom` means a distinct Python implementation
requiring owner disposition. `Gap` means donor-backed behavior not implemented.

## 1. Stage 01 responsibility inventory

| Slice | Donor owner / relevant methods | Canonical Python owner | Current classification | Existing verification evidence / limits |
| --- | --- | --- | --- | --- |
| S04 contracts | `D/datalib/ChartDef.java`, `DataInfo.java`; `D/tradinglib/{Order,StrategyBase}.java` | `app/core/data/contracts.py`; `app/core/trading/connection/contracts.py` | Verified (reported) for the scoped split | `tests/core/data/test_contract_imports.py`, `tests/core/trading/connection/test_contracts.py`; migration commit `1b10a216`; chart metadata subsequently moved to `app/core/data/charts.py` under S15. A current integration test run is still needed. |
| S05 random | `D/lib/random/{MTRandom,MersenneTwisterFast,MersenneTwisterRng}.java` | `app/core/lib/random.py::RandomGenerator` | Verified tested subset + retained custom methods | Java-output vectors and `tests/core/lib/test_random.py`, `test_random_generation.py`; exact limitations below. |
| S06 generic utilities | `D/pluginlib/program/Program.java`; `D/lib/exception/SQException.java`; `D/lib/{SQTime,TimePeriod,XMLUtil}.java` | `app/core/lib/{programs,errors,responses,time}.py`; strategy-local XML owners | Verified (reported) for scoped helpers | `tests/core/lib/test_{programs,errors,responses,time}.py`; commit `88c0a363`; not a full XML framework equivalence claim. |
| S07 engine bootstrap | `D/consolestarter/SQApp.java::main/initApp/initEngines/initPluginSystem` | `app/main.py`; `app/cli.py` | Verified (reported) Python adaptation | `tests/host/test_main.py`, `test_cli.py`; rollback/diagnostic commit `7afc490d`; check actual startup sequence. |
| S08 webserver | `D/consolestarter/SQWebServer.java`; `D/lib/app/webserver/MainAppWebServer.java` | `app/core/host/{transport,events}.py` | Verified (reported) Python HTTP/SSE/WS adaptation | `tests/core/host/test_transport.py`; port-probe commit `5ce6b8a9`. |
| S09 start/init | `D/consolestarter/{SQStarter,SQInitializer}.java` | `app/main.py`; `app/cli.py` | Verified (reported) Python launcher adaptation | `tests/host/test_main.py`; CLI override commit `37f698b7`. |
| S10 settings | `D/lib/app/AppSettings.java::{get,containsKey,set,load,save,putDefaultValues,putInternalValues,convertOldSettingsFormat}`; `D/lib/SettingsMap.java` | `app/core/host/settings.py::SettingsManager`; `HostPersistence` for SQLite writes | **Partial/adapt; open donor gaps** | `tests/core/host/test_settings.py`; method matrix below. Do not mark `verified`. |
| S11 memory/CPU | `D/lib/memory/{MemoryUsageChecker,CpuInfo}.java` | `app/core/host/resources.py` | Verified (reported) Python adaptation | `tests/core/host/test_resources.py`; commit `985c686c`; verify process/job integration. |
| S12 logging/diagnostics | `D/consolestarter/SQApp.java` | `app/core/host/logging.py` | Verified (reported) Python adaptation | `tests/core/host/test_logging.py`; commit `06d791a4`; verify redaction and startup diagnostics. |
| S13 sessions/secrets | `D/lib/app/webserver/MainAppWebServer.java::{loadHandlers,configureWebSocket}`; `D/tradinglib/connection/ConnectionsFileManager.java::{loadConnections,saveConnections}` | `app/core/host/session.py`; `app/core/host/transport.py` | **Custom host security; donor auth owner unmapped** | `tests/core/host/test_session.py`, `test_transport.py`; method matrix below. |
| S14 persistence | `AppSettings::{load,save,convertOldSettingsFormat}`; `ConnectionsFileManager::{loadConnections,saveConnections}` | `app/core/host/persistence.py::HostPersistence`; `app/core/host/strategy_storage.py::HostStrategyStorage` | **SQLite adaptation + custom JSON; donor counterpart unresolved** | `tests/core/host/test_{persistence,strategy_storage,editor_job_schema,watchlist_schema}.py`; method matrix below. |

The path `data/reference-donor/internal/libs/datalib/session/SessionManager.java`
is **not** an S13 authority reference. It concerns trading calendars and belongs
to Stage 02 / S20. In Stage 01, the Python `session.py` owns host authorization,
not market/trading sessions.

## 2. S05 — Java RNG source-backed subset

Public owner: `app/core/lib/random.py::RandomGenerator`. The
`MersenneTwisterRng` name aliases the existing owner; its runtime-checkable
`IRandomGenerator` protocol is a contract, not a second implementation.
The internal `_DonorStream` uses CPython's MT transition with donor-compatible
seed words, draw extraction and Java signed arithmetic. This is a Python
implementation adaptation, not proof that all inherited `random.Random` methods
match Java's API.

| Donor method(s) | Python method(s) | Evidence / precision |
| --- | --- | --- |
| `MersenneTwisterFast.setSeed(long)`; `MTRandom.setSeed(long/int[])` | `_DonorStream.seed` | Six Java seeds including signed long extremes and high-word-only seed; two independent streams. |
| `MersenneTwisterFast.nextDouble`; `MersenneTwisterRng.nextDouble()` | `_DonorStream.random`; `RandomGenerator.next_double` | Exact 26/27-bit extraction in Java vectors, 640 draws per operation. |
| `MersenneTwisterFast.nextInt(bound)` and wrapper ranges | `RandomGenerator.next_int` | Exact power-of-two sampling, rejection, signed range arithmetic. |
| `MersenneTwisterFast.nextLong` | `RandomGenerator.next_long` | Exact signed high/low 32-bit combination. |
| `MersenneTwisterFast.nextGaussian` | `_DonorStream.gauss`; `RandomGenerator.next_gaussian` | Polar transform and cache; `1e-14` absolute/relative tolerance. |
| `MersenneTwisterRng.nextBool/probability` | `RandomGenerator.next_bool/probability` | Includes negative/zero/one/greater-than-one/NaN probabilities and stream consumption. |
| `MersenneTwisterRng.nextDouble(min,max,step,decimals)`; `SQUtils.round` | `RandomGenerator.next_double` | Stepped vectors and rounding-tie tests; nonfinite arithmetic and Java saturation limits not fully qualified. |
| `MersenneTwisterRng.clone(long)/newInstance(long)` | `RandomGenerator.clone(seed)/new_instance(seed)` | New seeded streams. Python no-arg state-copy clone is custom. |
| `MersenneTwisterRng.getRandom` | `RandomGenerator.get_random` | Independent `MTRandom` stream; inherited Python convenience methods are not Java-equivalent claims. |

Retained Python differences: OS entropy instead of Java clock seeding, explicit
reseed of both streams, no-argument state-copy clone including Gaussian cache,
unstepped/nonpositive-step range semantics, and the Python `random.Random`
interface. Only the listed donor-backed subset is certified by the supplied
vectors. Strategy-generation parity is a later responsibility.

**Reproduction:**
`tests/core/lib/fixtures/stage01_random/{DonorRandomVectors.java,README.md,vectors.jsonl}`.
The fixture harness and README are restored. The checked-in vector file remains
unchanged. `tests/core/lib/test_random_generation.py` checks deterministic
integration through the real strategy generation caller, but cannot establish
full donor generation semantics.

## 3. S10 — settings: method-level disposition

`SettingsManager` owns Python scoped settings, detached cached reads, revision
checks and optimistic atomic SQLite saves; `HostPersistence` is the only SQL
owner. The current `settings.py` module explicitly states that **no defaults,
schema migrations or missing stored records are synthesized**.

| Donor responsibility | Python disposition | Qualification |
| --- | --- | --- |
| `AppSettings.get/containsKey` | `SettingsManager.get/contains_key` | Scoped stored-value lookup, tested; scoping differs from Java flat map. **Adapt**. |
| `AppSettings.set/load/save` | `save_settings/reload` plus `HostPersistence` | Python revision-checked SQLite, rejected corruption and atomic updates differ from donor XML/FST and error treatment. **Adapt; not exact parity**. |
| `AppSettings.putDefaultValues/putInternalValues` | No equivalent product-default/path owner established | **Gap**: donor initial defaults and internal paths not applied. Needs an explicit settings-by-settings donor/caller inventory before implementation. |
| `AppSettings.convertOldSettingsFormat` | No FST `settings.dat` migration | **Gap**: legacy plain-text SQLite rows are not donor FST conversion. Do not migrate active data here. |
| `SettingsMap.getDouble/getInt/getBool/getLong` | `get_float/get_int/get_bool`, generic getters | Typed coercion and defaults have Python semantics; no dedicated long-getter or full XML clone parity. **Subset/adapt**. |
| Roadmap environment override requirement | CLI `--host`/`--port` exists under S09; no generic settings override | **Unverified requirement**; donor `AppSettings`/`SettingsMap` source does not establish a universal environment override facility. |

Donor signatures also expose `AppSettings.toJSON`, `getBoolean`, and
`SettingsMap.setIfNotExists/getXML/clone` in
`data/reference-donor/internal/libs/signatures/SQLib_signatures.txt`.
Their semantics are not certified by this Stage 01 evidence review and should
be investigated if required by consumers. This task **does not** authorize
adding missing APIs or changing stored-setting contracts.

Integration evidence to rerun: `tests/core/host/test_settings.py`,
`tests/host/test_main.py`, `tests/host/test_cli.py`, and
`tests/core/host/test_transport.py`. The correct status is
**partial/adapt with two confirmed donor obligations still open**; an owner
must decide whether to implement them or explicitly justify a narrower
Python-host acceptance boundary in a new approved plan.

## 4. S13 — host sessions and credentials: method-level disposition

Single host owner: `app/core/host/session.py`. It implements
`SessionManager.hash_password/verify_password/verify_credentials/create_session/
validate_session/resolve_peer/revoke_session/has_scope/authorize`, plus
`WindowsCredentialVault.store/resolve/revoke` and credential staging.
The transport module owns HTTP/WebSocket authorization integration.

| Recovered donor reference | Supported statement | Unresolved / classification |
| --- | --- | --- |
| `MainAppWebServer.loadHandlers/configureWebSocket` | HTTP/WS route wiring and lifecycle exist in the donor. | No matching donor password, bearer token, expiry, scopes or session authority established. |
| `ConnectionsFileManager.loadConnections/saveConnections` | Donor serializes trading connection JSON. | No proof of donor Windows Credential Manager or OS vault parity. |
| No donor counterpart identified for Python session-security methods | Python hash, peer binding, sliding expiry, revocation, scope checks, fail-closed vault and redaction are covered by existing tests. | **Custom/adapted host security**, not donor-verified. Owner disposition required. |

Windows-specific test:
`tests/core/host/test_session.py::test_windows_credential_vault_store_resolve_revoke`
uses temporary generated test credentials and revokes them. It explicitly
**skips** if the Windows credential API is unavailable. A skipped test cannot
be counted as a Windows validation pass. Do not alter or access real user
credentials as part of this task.

## 5. S14 — generic persistence and strategy records

`HostPersistence` is the single generic SQLite gateway; schema setup, bound
queries, transaction scope, pagination and bounded writes are its responsibility.
`HostStrategyStorage` is an independent *strategy JSON record* store, not a
second generic SQLite gateway. Separate storage mechanisms are justified by
different data custody, but the JSON strategy format remains a custom divergence.

| Donor reference / Python responsibility | Evidence and qualification |
| --- | --- |
| `AppSettings.load/save/convertOldSettingsFormat` | Donor settings file custody does **not** prove an equivalent generic SQLite API. **Adapt**; FST migration gap remains S10. |
| `ConnectionsFileManager.loadConnections/saveConnections` | Donor connection-file logic does not prove full schema/retention/vault parity. **Unresolved**. |
| `HostPersistence._connect/transaction/create_records/read_records/update_record/delete_record` | Isolated tests cover WAL, foreign keys, binding, rollback, concurrency/busy failure, bounded changes, pagination, and absent database refusal. **Python-specific gateway tested; donor SQLite owner unmapped**. |
| `HostPersistence.ensure_*_schema` (code editor, jobs, custom data, datasets, broker costs, databanks, watchlists) | Temporary-store and incompatible-schema checks; no active migration authorized or observed. **Python adaptation**. |
| `HostStrategyStorage.load/save` | JSON record restart, revision conflicts, atomic failure and corruption tests. **Custom format**; native SQX/HSL disposition belongs to S63. |

`tests/core/host/test_persistence.py`, `test_editor_job_schema.py`,
`test_watchlist_schema.py`, and `test_strategy_storage.py` are evidence for
Python functionality; they do **not** certify donor schema equivalence or
native SQX project/strategy artifacts. No live database mutation is authorized.

## 6. Closure verification matrix

This section is an execution ledger, not an inferred green dashboard. The
GitHub connection exposes repository files and commit status, but writes through
Git commits, which are forbidden without separate owner commit approval.
The execution environment had no checkout mounted, and external GitHub clone
failed DNS resolution. The latest commit showed no available status checks or
PR workflow runs through the connector. Consequently **none** of the commands
below have a witnessed pass in this closure task.

| Check | Command / evidence target | Observed status |
| --- | --- | --- |
| Git baseline | `git rev-parse HEAD; git status --short` | **Not executable** without checkout; remote HEAD identified above. |
| Donor RNG regeneration | `tests/core/lib/fixtures/stage01_random/README.md` | **Not executed**; donor Java source not mounted. |
| Shared primitives and contracts | `uv run --no-sync pytest tests/core/lib tests/core/trading/connection --no-cov -q` | **Not run**. |
| Host | `uv run --no-sync pytest tests/core/host --no-cov -q` | **Not run**. |
| Data consumers | `uv run --no-sync pytest tests/core/data --no-cov -q` | **Not run**. |
| Bootstrap | `uv run --no-sync pytest tests/host/test_main.py tests/host/test_cli.py --no-cov -q` | **Not run**. |
| Ruff & format | `uv run --no-sync ruff check ...`; `ruff format --check ...` for changed scope | **Not run**. |
| Strict Mypy | `uv run --no-sync mypy --strict app/core/lib app/core/host app/core/data app/core/trading/connection` | **Not run**. |
| Architecture | `uv run --no-sync python scripts/check_architecture.py` | **Not run**. |
| Milestone | `uv run --no-sync python scripts/ci_check.py` | **Not run**. |
| Diff hygiene | `git diff --check` | **Not run** against checkout; patch separately syntax-checked. |

The current `scripts/ci_check.py` covers scripts Ruff/Mypy, architecture,
tests and frontend typecheck/test/build; it does not independently run full
strict Mypy and Ruff checks on all Stage 01 application source. Thus the
additional explicit commands above remain mandatory to establish the gate.
Run them once against the actual unchanged checkout after applying the
four-file documentation/fixture patch, and report pass/fail/skipped counts.

## 7. Outstanding owner decisions and Stage 02 entry

1. **S10 blocking donor obligations:** default/internal values and FST
   migration must be implemented or justified as an explicitly approved,
   narrower acceptance boundary. This evidence-only task cannot settle them.
2. **S13 donor source classification:** identify an actual donor auth owner, or
   ratify Python session/vault behavior as a host-specific adaptation.
3. **S14 donor source classification:** ratify SQLite gateway as a Python host
   adaptation; retain JSON strategy storage for the approved S63 disposition.
4. **Fresh verification:** run focused tests, architecture, strict typing,
   formatting and milestone qualification on an actual repository checkout.

**Verdict:** Stage 01 is **implemented substantially but not certified closed**.
Stage 02 should not inherit an unconditional full-donor-parity claim. It may be
planned while this evidence is resolved, but its acceptance gates must explicitly
track dependencies on open S10/S13/S14 decisions. No status was upgraded to
`verified` based solely on static code presence or historical green claims.

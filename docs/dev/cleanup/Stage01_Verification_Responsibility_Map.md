# Stage 01 verification corrections: S05, S10, S13 and S14

Approved plan: Stage 01 verification corrections, iteration 1, approved in chat
with `APPROVED: EXECUTE` on 2026-11-04. Baseline HEAD:
`0bbfd856feb2ecfbb118eaa879f4ad1aa701e820`, clean working tree.

This is a bounded evidence map for four reopened slices, not full Stage 01
certification. `D/` means `data/reference-donor/internal/libs/`. Source inspection
and passing Python tests do not establish full donor parity. Existing security,
settings, storage and Python RNG conveniences remain present; their identification
as divergences does not authorize removal or claim separate parity ratification.

## S05 — random streams

Single public owner: `app/core/lib/random.py::RandomGenerator` (the existing
`MersenneTwisterRng` name aliases that owner). Private `_DonorStream` reuses
CPython's MT transition through `setstate/getrandbits`, supplying donor seed words
and draw extraction. This is a necessary Python adaptation, not another RNG
implementation. `IRandomGenerator` remains its typed contract.

| Donor class/method | Python owner | Evidence / qualification |
| --- | --- | --- |
| `D/lib/random/MersenneTwisterFast.java::setSeed(long)` | `_DonorStream.seed`, primary mode | Low 32-bit seed initialization; six Java seed vectors include signed long limits and high-word-only seed. |
| `D/lib/random/MTRandom.java::setSeed(long/int[])` | `_DonorStream.seed`, secondary mode | Independent two-word long-seed initialization; Java `MTRandom.nextDouble()` vectors. |
| `MersenneTwisterFast.nextDouble` and `MersenneTwisterRng.nextDouble()` | `_DonorStream.random`, `RandomGenerator.next_double` | Exact 26/27-bit donor extraction; 640 draws per seed cross MT boundaries. |
| `MersenneTwisterFast.nextInt(int)` and wrapper overloads | `RandomGenerator.next_int` | Exact power-of-two selection and signed rejection; vectors include rejection-heavy bound. Nonpositive bounds reject; Java signed range arithmetic and truncating division retained. |
| `MersenneTwisterFast.nextLong` | `RandomGenerator.next_long` | Java signed high/low-word arithmetic, compared exactly to Java. |
| `MersenneTwisterFast.nextGaussian` | `_DonorStream.gauss`, `RandomGenerator.next_gaussian` | Polar transform/cache; Java vectors with `1e-14` absolute/relative tolerance. |
| `MersenneTwisterRng.nextBool/probability` | `RandomGenerator.next_bool/probability` | Exact boolean selection and probability stream consumption, including negative, zero, one, greater-than-one and NaN probabilities. |
| `MersenneTwisterRng.nextDouble(min,max,step,decimals)`; `D/lib/SQUtils.java::round(double,int)` | `RandomGenerator.next_double` | Stepped sequence vectors; source-derived positive/negative decimal tie tests. Positive precision uses donor epsilon and Java-style rounding; nonpositive precision leaves stepped values unrounded. Exceptional/nonfinite float arithmetic and Java saturation limits remain unqualified. |
| `MersenneTwisterRng.clone(long)/newInstance(long)` | `RandomGenerator.clone(seed)/new_instance(seed)` | Seeded calls create fresh streams; reseed/clone tests compare known Java seed-zero output. |
| `MersenneTwisterRng.getRandom` | `RandomGenerator.get_random` | Separate `MTRandom` stream; secondary doubles and independent advancement verified. Python `random.Random` interface retained; inherited Python convenience methods are not claimed equivalent to Java `Random` APIs. |

Preserved divergences: entropy initialization uses Python OS entropy rather than
Java clock seeding; explicit `seed()` resets both streams; no-argument `clone()`
copies both states including Gaussian caches; unstepped/nonpositive-step float
ranges retain Python uniform/round behavior and degenerate-bound handling.
These conveniences have no direct wrapper-method parity claim. Existing Python
`get_random()` return type is retained through a `random.Random` subclass.

Caller graph: `app/core/lib/__init__.py` reexports the existing owner;
`app/core/trading/generation/engine.py::GenerationEngine.__init__` instantiates it
and all generation draws use that instance. Repository search found no other
application callers of `get_random`, seeded cloning or reseeding. Integration
test `tests/core/lib/test_random_generation.py` exercises real strategy generation
with identical seeds, without claiming donor strategy-generation parity.

Evidence: `tests/core/lib/test_random.py` and
`tests/core/lib/fixtures/stage01_random/{DonorRandomVectors.java,vectors.jsonl,README.md}`.
Status: **verified tested donor subset + explicit Python divergences**. Seeded
strategy outputs intentionally change from the former CPython-seeded sequence.

## S10 — settings

Single owner: `app/core/host/settings.py::SettingsManager`; persistence is
delegated exclusively to `HostPersistence`. No runtime settings changes in this
correction. The following differences must not be hidden by `verified` wording.

| Donor class/method | Python owner | Evidence / disposition |
| --- | --- | --- |
| `D/lib/app/AppSettings.java::get/containsKey` | `SettingsManager.get/contains_key` | Scoped lookup and caller fallback tested in `test_settings.py`; scoping is a Python adaptation. |
| `AppSettings.set/save/load` | `SettingsManager.save_settings/reload` | Atomic SQLite record updates, detached cache and explicit reload tested; XML format, silent invalid-set behavior and swallowed load errors are not reproduced. Python rejects corruption and revision conflicts. |
| `AppSettings.putDefaultValues/putInternalValues` | No equivalent initialization owner established | **Gap**: donor product defaults/path injection are not applied. Existing stored-only settings contract is preserved. Mapping each product setting and its consumers requires a later bounded plan. |
| `AppSettings.convertOldSettingsFormat` | No Python FST importer | **Gap**: legacy Java `settings.dat` conversion is not implemented. Python legacy plain-text row reading is tested but is not that migration. No active migration is authorized here. |
| `D/lib/SettingsMap.java::getDouble/getInt/getBool/getLong` | `SettingsManager.get_float/get_int/get_bool` | Python typed/coercing getters tested. Donor casts and flattened `ValuesMap` storage are different; no dedicated long getter, XML clone or full SettingsMap parity claim. |
| Roadmap environment overrides | No generic settings override owner | **Unverified roadmap requirement**, not established by inspected `AppSettings`/`SettingsMap` donor source. CLI host/port overrides belong to S09; session-token environment input is not a settings override facility. |

Callers: `app/main.py` constructs/reloads settings and reads stored bind values;
host transport reads projections and applies revision-checked saves; host logging
and resources read settings. `tests/host/test_main.py`, `tests/host/test_cli.py`,
`tests/core/host/test_settings.py` and `test_transport.py` exercise these boundaries.
The existing stored-only contract is an identified divergence, not silently
ratified as donor parity. Status: **partial / adapt; defaults and migration gaps**.

## S13 — session authority and credentials

Single owner: `app/core/host/session.py` for session/password/scope authority,
Windows vault and credential staging; transport coordinates authenticated routes.

| Recovered donor reference | Python owner | Evidence / qualification |
| --- | --- | --- |
| `D/lib/app/webserver/MainAppWebServer.java::loadHandlers/configureWebSocket` | Host transport integrates `SessionManager.validate_session/authorize` | Donor source establishes HTTP/WS wiring, not equivalent bearer authentication, expiry or scope authority. Exact equivalent donor auth owner remains **unmapped**. |
| `D/tradinglib/connection/ConnectionsFileManager.java::saveConnections/loadConnections` | `session.py::WindowsCredentialVault.store/resolve/revoke`, `prepare_credentials` | Donor file serializes connection JSON; it does not establish OS vault parity. These Python security capabilities are **existing custom host behavior** retained unchanged. Trading connection serialization ownership is outside this correction. |
| No equivalent donor password/session methods established | `SessionManager.hash_password/verify_password/verify_credentials/create_session/validate_session/resolve_peer/revoke_session/has_scope/authorize` | Python lifecycle, legacy hashes, persistent revocation, sliding expiry, peer binding, failure-closed behavior, redacted logging and scope checks tested. No donor-equivalence claim. |

Evidence: `tests/core/host/test_session.py` and `test_transport.py`. The Windows
vault test uses a temporary generated credential and revokes it in `finally`;
this is a real OS vault operation, not merely a mock. Database fixtures use
temporary stores. Status: **custom host security tested; donor mapping unresolved**.
Do not map `datalib/session/SessionManager` here: it owns trading calendars (S20).

## S14 — persistence isolation

Single SQLite owner: `app/core/host/persistence.py::HostPersistence`. Atomic
strategy JSON owner: `app/core/host/strategy_storage.py::HostStrategyStorage`.
These are distinct persistence responsibilities, not duplicate implementations.

| Donor responsibility / methods | Python owner | Evidence / qualification |
| --- | --- | --- |
| `AppSettings.load/save/convertOldSettingsFormat` | Settings delegates to `HostPersistence.read_records/update_record/transaction` | Donor XML/FST files establish settings custody, not a generic SQLite database API. Storage format/transactions are a Python host adaptation. |
| `ConnectionsFileManager.loadConnections/saveConnections` | Connection consumers use host-owned persistence/vault | Domain-specific donor connection files do not certify all generic Python schemas or retention. No connection migration claim. |
| No equivalent generic donor SQLite class established | `HostPersistence._connect/transaction/create_records/read_records/update_record/delete_record` | Isolated tests cover binding, WAL, foreign keys, atomic rollback, concurrency/busy failure, bounded writes, cursor pagination and missing-database refusal. Generic donor DB parity remains unresolved. |
| Existing host schema custody | `HostPersistence.ensure_code_editor_schema/ensure_jobs_schema/ensure_custom_data_schema/ensure_datasets_schema/ensure_broker_cost_schema/ensure_databanks_schema/ensure_watchlists_schema` | Temporary-store schema/idempotency/incompatibility tests; no active DB migration performed. Method-specific donor schema parity is not established. |
| Donor native strategy artifacts vs existing custom JSON records | `HostStrategyStorage.load/save`, record verification | Temporary-directory restart, conflict, atomic failure and corruption tests. HSL JSON format remains **custom**, explicitly retained for S63 disposition; generic isolation tests do not certify native SQX artifacts. |

Evidence: `tests/core/host/test_persistence.py`, `test_editor_job_schema.py`,
`test_watchlist_schema.py`, `test_strategy_storage.py`; architecture persistence
isolation check. Callers include settings, resources, host transport, jobs,
databanks and workspace stores. No caller migration or SQL redistribution in this
correction. Status: **adaptation tested / custom strategy storage / donor gaps**.

## Closure boundary

The correction fixes the demonstrated RNG mismatch and makes evidence explicit.
It does **not** close all Stage 01 donor gaps. S10 defaults/FST migration and the
S13/S14 unresolved donor counterparts require subsequent source-backed plans.
No dependencies, active databases, authentication contracts or Git history are
changed. Verification commands/results are delivered in the in-chat walkthrough.

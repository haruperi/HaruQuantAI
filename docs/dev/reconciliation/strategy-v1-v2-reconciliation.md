# Strategy — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** strategy (`str`)
* **V1 audit report:** `strategy-v1-audit.md`
* **V2 requirements:** `04-strategy.md`
* **Comparison basis:** V1 audit evidence only; V2 requirement text only. No source code was inspected or modified during this reconciliation.
* **Comparison limitations:** V1 tests were not executed during the audit; dynamic external callers and stored custom strategies remain uncertain; the active roadmap phase, top-level package root, governance authority, performance benchmark, capacity assumptions, and final downstream execution owner were not supplied.

## 2. Executive Summary

V1 proves real value in vectorized signal generation, stateful advanced strategies, registry lookup, simulation integration, live rolling-bar decision support, and read-only basket calculations. Those behaviours should not be discarded. They should be moved behind one explicit typed strategy boundary that emits `TradeIntent`, diagnostics, and optional strategy-local state only.

The main V1 corrections are removal of import-path-dependent response contracts, elimination of arbitrary stored-Python execution, separation of mutable artifact storage from strategy execution, consolidation of duplicated signal schemas, migration of indicator calculations to the indicator domain, and replacement of the split `BaseStrategy`/trading-stateful lifecycle with two focused contracts: vectorized batch execution and event-hook execution.

The most important V2 additions are immutable registry references, schema-validated configuration, canonical TradeIntent identity/lineage, no-lookahead and readiness validation, immutable read-only state snapshots, deterministic replay/checkpoints, structured diagnostics, registered-only execution, and explicit strategy manifests. V2 proposals for a sandbox, full governance/compliance/operations enforcement, multiple concurrency models, advanced venue/ML/L2-L3 features, and unmeasured fixed SLOs are rejected, deferred, simplified, or left open.

All 18 V1 capabilities and all 443 V2 requirements receive explicit dispositions. V2 decisions: **Keep: 26**, **Modify: 148**, **Add: 143**, **Merge: 24**, **Defer: 61**, **Reject: 30**, **Open Decision: 11**.

**Recommended migration direction:** preserve strategy logic, replace contracts and activation mechanisms, remove unsafe dynamic loading, keep official execution outside strategy, and implement only the backtest/replay-focused capability slice approved by the unresolved system-level decisions.

## 3. Decision Principles

* Preserve proven decision logic and real workflows, not V1 file shapes.
* Keep strategy side-effect-free with respect to official trading state and external infrastructure.
* Use functions for stateless validation, conversion, identity, and diagnostics; use classes/protocol implementations only where a strategy owns lifecycle or local state.
* Consume normalized data and precomputed indicators through typed contracts.
* Emit one canonical TradeIntent; never emit official orders, fills, risk approvals, or portfolio mutations.
* Permit registered approved modules and typed configuration only in the initial rebuild.
* Keep one focused responsibility per file and one capability per module folder.
* Consolidate declarations into one applicability-aware manifest instead of adding one service per concern.
* Keep external governance, validation, execution, risk, portfolio, compliance, reporting, build, deployment, and operations enforcement outside strategy.
* Accept quantitative limits only after a reproducible benchmark and capacity model exist.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-STR-001 | Pure strategy decision boundary | V1-CAP-STRATEGY-001, 017; V1-WF-STRATEGY-001 to 003 | REQ-STRAT-017 to 028, 097, 304, 417 to 419, 437 to 439 | V1 allows storage side effects and exposes execution-shaped compatibility objects. | Modify | Strategy consumes prepared data, indicators, config, read-only snapshots, and context; returns decisions/intents, diagnostics, and optional local state only. | Refactor | Preserves proven signal logic while removing account, execution, filesystem, and governance ownership. |
| CAP-STR-002 | Versioned contracts and deterministic results | V1-CAP-STRATEGY-002, 003, 004, 016 | REQ-STRAT-001 to 010, 104 to 119, 195 to 198 | V1 has SignalDict/DataFrame columns and import-path-dependent response envelopes. | Modify | One versioned schema family for references, config, context, results, intents, diagnostics, manifests, and checkpoints. | Replace contract; reuse field semantics | Eliminates raw/enveloped ambiguity and makes cross-domain consumption testable. |
| CAP-STR-003 | Approved immutable registry and config validation | V1-CAP-STRATEGY-005, 006, 009, 012, 014; V1-WF-STRATEGY-004 | REQ-STRAT-062 to 076, 120 to 125, 190 to 194, 324 to 332 | V1 registry is mutable, process-local, hard-coded, and disconnected from file catalog. | Modify | Resolve exactly one approved immutable strategy version; validate config, lifecycle, environment, module, and hashes before execution. | Refactor registry; migrate metadata | Registry value is proven, but V1 discovery and storage are unsafe and inconsistent. |
| CAP-STR-004 | Vectorized strategy decision execution | V1-CAP-STRATEGY-001 to 004, 017; V1-WF-STRATEGY-001 and 003 | REQ-STRAT-029, 031, 049 to 061, 291, 293 to 294, 394, 397 to 398 | V1 produces mutable signal columns and downstream row decoding rather than typed intent batches. | Modify | Run a validated vectorized strategy as an atomic deterministic batch using normalized data and precomputed indicators, then emit ordered intents and diagnostics. | Refactor signal logic | Preserves vectorized value while removing indicator ownership and implicit timing. |
| CAP-STR-005 | Stateful event strategy execution | V1-CAP-STRATEGY-001, 004, 007, 008, 018; V1-WF-STRATEGY-002 | REQ-STRAT-030, 032 to 040, 295 to 302, 395 to 396 | V1 lifecycle is split between BaseStrategy and trading.stateful and directly receives mutable-looking runtime context. | Modify | Invoke typed applicable hooks in stable order with immutable snapshots; return intents, diagnostics, and atomic local-state updates. | Refactor advanced strategies and helpers | Advanced strategy workflows are proven, but the lifecycle boundary must be unified. |
| CAP-STR-006 | TradeIntent construction, identity, and lineage | V1-CAP-STRATEGY-002, 017; V1 SignalDict/TradeAction outputs | REQ-STRAT-041 to 048, 113, 119, 136 to 142 | No canonical cross-runtime intent, identity, idempotency, or lineage exists. | Add | Build schema-valid deterministic TradeIntent objects with sizing hints, timing, partial-fill preferences, rationale, identity, sequence, and lineage. | New; reuse V1 signal/reason fields | Provides the single safe handoff from strategy to simulation/trading runtimes. |
| CAP-STR-007 | Timing, readiness, and no-lookahead validation | V1 template shifting and helper behavior; V1-WF-STRATEGY-001 | REQ-STRAT-044, 049 to 061, 143 to 149, 336 to 343 | V1 timing behavior is strategy-specific and not enforced domain-wide. | Add | Validate required fields, indicator readiness, point-in-time timestamps, latency, and timing policy before any intent is emitted. | New validation around reused strategy logic | No-lookahead is a confirmed correctness and audit requirement. |
| CAP-STR-008 | Read-only external state and strategy-local decision state | V1-CAP-STRATEGY-007, 008, 018; V1-WF-STRATEGY-002 | REQ-STRAT-035 to 040, 089, 094 to 096, 181 to 182, 184 to 186, 350 | V1 helpers depend on trading-domain snapshots and state ownership is fragmented. | Modify | Use immutable typed snapshots; permit only serializable per-instance local decision state updated atomically. | Refactor helpers; remove indicator math | Preserves advanced strategy value without mutating official state. |
| CAP-STR-009 | Checkpoint and replay metadata | V1 has ad hoc state and version metadata but no replay contract | REQ-STRAT-090 to 094, 092 to 093, 103, 184 to 185, 198, 404 to 405, 426 | No deterministic replay manifest or validated checkpoint contract exists. | Add | Create and validate hash-linked replay manifests and optional bounded checkpoints; replay exact recorded interface/version/seed. | New | Required for reproducibility and safe stateful recovery. |
| CAP-STR-010 | Structured diagnostics and deterministic error mapping | V1-CAP-STRATEGY-006, 016; logs and broad exceptions across V1 | REQ-STRAT-003, 008, 010, 114 to 115, 118, 131, 150 to 154, 324 to 333, 335 to 346, 348 to 359, 361 to 376, 379, 381, 386 | V1 exposes logs, low-level exceptions, and inconsistent envelopes. | Add | Return bounded redacted diagnostics with stable codes, request/correlation IDs, timestamps, dependency status, and safe details. | Replace wrappers; reuse reason text | Makes failures safe and cross-domain consumable. |
| CAP-STR-011 | Registered-only security, resource, and determinism controls | V1-CAP-STRATEGY-010 and V1-WF-STRATEGY-005 expose dynamic code execution | REQ-STRAT-077 to 088, 163 to 173, 199 to 203, 276, 278 to 279, 303 to 323 | V1 executes stored Python, writes during import, and lacks budgets and deterministic input rules. | Add / Remove unsafe V1 | Allow approved modules and typed config only; prohibit arbitrary code, secrets, network/filesystem/process access, wall clock, and unseeded randomness; host enforces budgets. | New security gate; remove loader | Smallest safe initial execution model. |
| CAP-STR-012 | Strategy declaration manifest | V1 strategy class constants and parameters | REQ-STRAT-038 to 039, 058, 063, 117, 126 to 135, 145 to 147, 163 to 165, 190, 206 to 212, 214 to 223, 225, 234 to 238 | V1 metadata is sparse and scattered; V2 proposes many separate operational declarations. | Modify / Merge | Use one versioned manifest with required data/indicator/timing/environment/resource fields and optional applicable risk/execution/operations assumptions. | New schema using existing class metadata | Consolidates declarations without creating dozens of services or mandatory fields. |
| CAP-STR-013 | Approved artifact integrity metadata | V1-CAP-STRATEGY-009 to 014; V1-WF-STRATEGY-004 and 005 | REQ-STRAT-068, 123, 162, 174 to 175, 178 to 180, 440 to 441 | V1 mutable filesystem storage and dynamic loading conflict with immutable approved artifacts. | Split / Modify | Registry records immutable strategy version, module, source/artifact/dependency/config hashes, and provenance references; external catalog/build systems persist and approve artifacts. | Migrate metadata; remove mutable loading | Preserves version identity while moving persistence and supply-chain enforcement to correct owners. |
| CAP-STR-014 | Strategy examples, documentation, and traceability | V1-CAP-STRATEGY-015; stale and split V1 tests/usage examples | REQ-STRAT-011 to 016, 285 to 290, 303, 387 to 414, 416 to 435, 443 | V1 examples/tests target incompatible removed frameworks and lack complete traceability. | Modify | Provide executable examples for one vectorized and one event strategy, contract tests, accepted requirement/test mapping, migration guidance, and explicit deferrals/rejections. | Replace stale tests/examples; reuse proven scenarios | Documentation and test coherence are prerequisites for Builder handoff. |

## 5. V1 Disposition Register

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
| --- | --- | --- | --- | --- | --- | --- |
| V1-CAP-STRATEGY-001 | Abstract DataFrame strategy contract | `base.BaseStrategy` | Essential | Split | CAP-STR-004 and CAP-STR-005 | Confirm all built-in and stored strategy subclasses before removing the legacy base. |
| V1-CAP-STRATEGY-002 | Canonical row-level signal extraction | `BaseStrategy.get_signal()` | Essential | Modify | CAP-STR-004 and CAP-STR-006 | Retain until all signal-column consumers emit typed TradeIntent batches. |
| V1-CAP-STRATEGY-003 | Signal schema preparation | `ensure_signal_columns()` | Essential | Merge | CAP-STR-004 and CAP-STR-002 | Delete only after vectorized outputs use versioned result schemas rather than mutable column conventions. |
| V1-CAP-STRATEGY-004 | Explicit neutral/no-signal frames | `ensure_no_signal_columns()` | Essential | Modify | CAP-STR-004 / CAP-STR-005 no-action result | Verify advanced strategies no longer require neutral DataFrame columns. |
| V1-CAP-STRATEGY-005 | Built-in strategy registration and lookup | `registry.py` | Essential | Modify | CAP-STR-003 | Migrate all nine built-ins to immutable approved entries before removing mutable registration. |
| V1-CAP-STRATEGY-006 | Registry diagnostics | `list_strategy_names()`, `registered_strategies()` | Useful | Merge | CAP-STR-003 registry query output | Confirm no agent depends on package-wrapped legacy envelope shapes. |
| V1-CAP-STRATEGY-007 | Stateful market-price history helpers | Midpoint/history plus `rolling_rsi`, `rolling_sma` | Essential | Split | CAP-STR-008 plus indicator/data domains | Move indicator calculations to indicator contracts; retain only pure snapshot/view helpers where needed. |
| V1-CAP-STRATEGY-008 | Position basket calculations | Side filter, basket PnL, weighted price, oldest position | Essential/Useful | Modify | CAP-STR-008 | Verify calculations operate only on immutable read-only snapshots and never authoritative state. |
| V1-CAP-STRATEGY-009 | Strategy source and metadata version storage | `StrategyStorage.save/load*` | Essential in V1 | Split | CAP-STR-003 / CAP-STR-013 plus external artifact persistence | Confirm the owning artifact/catalog domain and migrate active metadata before removing mutable storage from strategy. |
| V1-CAP-STRATEGY-010 | Dynamic custom strategy loading | `StrategyStorage.load_strategy_class()` | Essential in V1 but unsafe | Remove | None in initial rebuild | Inventory deployed stored strategies and provide an approved-module migration path before deletion. |
| V1-CAP-STRATEGY-011 | Strategy archive export/import | `export_strategy()`, `import_strategy()` | Useful | Defer | Future approved artifact workflow | Verify no required user workflow depends on archive round-tripping during the initial rebuild. |
| V1-CAP-STRATEGY-012 | Strategy artifact deletion | `delete_strategy()` | Essential in V1 catalog | Modify | CAP-STR-003 lifecycle revoke/deprecate plus external retention | Confirm retention policy and catalog ownership before removing physical deletion. |
| V1-CAP-STRATEGY-013 | Per-version artifact deletion | `delete_strategy_version()` | Questionable | Remove | None | Confirm no external caller or regulatory retention workflow requires physical version deletion. |
| V1-CAP-STRATEGY-014 | Filesystem version discovery | `list_versions()` | Questionable | Remove | CAP-STR-003 immutable registry query | Confirm registry/catalog is authoritative and all active versions are migrated. |
| V1-CAP-STRATEGY-015 | Basic authoring template | `TemplateStrategy` | Useful | Modify | CAP-STR-014 examples/templates | Check stored strategies inheriting the template and provide migration examples before removing runtime dependency. |
| V1-CAP-STRATEGY-016 | Standardized AI-tool surface | Package wrappers and `__all__` | Useful | Modify | CAP-STR-002 explicit typed public APIs | Confirm agent callers and migrate them from import-path-dependent envelope behavior. |
| V1-CAP-STRATEGY-017 | Live rolling-bar signal processing support | `on_bar`/`get_signal` consumed by `SignalProcessor` | Essential | Modify | CAP-STR-004 / CAP-STR-005 cross-runtime decision APIs | Confirm live/paper consumers can consume canonical TradeIntent outputs before retiring SignalDict. |
| V1-CAP-STRATEGY-018 | Lifecycle event contracts | `StrategyEvent`, no-op hooks, `SignalIntent` | No demonstrated value as implemented | Modify | CAP-STR-005 typed event protocol and CAP-STR-006 TradeIntent | Remove unused hooks only after the minimal event lifecycle and external caller migration are approved. |

## 6. V2 Requirement Disposition Register

Every V2 requirement appears exactly once below. Requirements rejected as strategy-domain capabilities remain visible here with their correct external owner or rationale.

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| REQ-STRAT-001 | Each public capability shall document an exact Python signature before implementation begins. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has inconsistent raw-versus-wrapped contracts; the final public surface needs explicit versioned schemas and deterministic results. |
| REQ-STRAT-002 | Each public capability shall define versioned input and output schemas using Pydantic models, `TypedDict`, dataclasses, or an approved equivalent. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has inconsistent raw-versus-wrapped contracts; the final public surface needs explicit versioned schemas and deterministic results. |
| REQ-STRAT-003 | Each public capability shall include a decision table mapping every validation condition, dependency condition, lifecycle condition, timeout condition, and security condition to one deterministic error code. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Keep deterministic error mapping, but one exhaustive decision table per public function is excessive; maintain one domain error map plus focused function preconditions. |
| REQ-STRAT-004 | Each public capability shall define whether results are returned as a single batch, iterator, stream, or async stream; `run_vectorized_strategy_signals` shall be treated as batch output until a streaming contract is explicitly approved. | Keep | CAP-STR-002 — Versioned contracts and deterministic results | Batch output for vectorized execution is proportionate and matches the initial rebuild; streaming remains unapproved. |
| REQ-STRAT-005 | Each public capability shall define precise side effects, mutation permissions, idempotency behavior, concurrency assumptions, retry behavior, and redaction behavior. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has inconsistent raw-versus-wrapped contracts; the final public surface needs explicit versioned schemas and deterministic results. |
| REQ-STRAT-006 | Each public capability shall define its official callable name, stability level, intended consumers, input schema, output schema, deterministic error codes, side-effect policy, idempotency behavior, and compatibility guarantees before implementation begins. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | This duplicates REQ-STRAT-001 through REQ-STRAT-005 and should be satisfied by one public-contract specification. |
| REQ-STRAT-007 | Public capabilities shall be versioned and compatibility-tested before being consumed by orchestration, simulation, risk, portfolio, audit, reporting, or API workflows. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has inconsistent raw-versus-wrapped contracts; the final public surface needs explicit versioned schemas and deterministic results. |
| REQ-STRAT-008 | Public capabilities shall return structured results and shall not rely on free-form logs, unmapped exceptions, or implicit global state. | Modify | CAP-STR-002 — Versioned contracts and deterministic results | Keep structured results and mapped errors; remove implicit global state rather than merely documenting it. |
| REQ-STRAT-009 | Public schema changes shall require a schema-version change and compatibility review. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has inconsistent raw-versus-wrapped contracts; the final public surface needs explicit versioned schemas and deterministic results. |
| REQ-STRAT-010 | Error examples and diagnostics examples shall include `schema_version`, `request_id`, and `correlation_id`. | Keep | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Correlation fields are required for cross-domain traceability and are proportionate. |
| REQ-STRAT-011 | Before Builder handoff, each requirement shall include a stable requirement id, priority, phase, applicability tags, owning module, acceptance criteria, and at least one linked test case id where implementation is required. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep traceability for accepted implementation requirements, but do not force runtime tests for documentation-only or rejected items. |
| REQ-STRAT-012 | Applicability tags shall identify whether a requirement applies to `BACKTEST_CORE`, `REPLAY`, `PAPER`, `SHADOW`, `LIVE`, `ML_ONLY`, `L2_L3_ONLY`, `REGULATED_MARKET_ONLY`, or `FUTURE`. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep traceability for accepted implementation requirements, but do not force runtime tests for documentation-only or rejected items. |
| REQ-STRAT-013 | Requirements without implementation scope shall carry an explicit `Documentation Only`, `Future`, or `Not Implemented` rationale. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | Explicit non-implementation rationales are necessary to prevent deferred or external requirements from being treated as active code scope. |
| REQ-STRAT-014 | Each confirmed error code shall have at least one triggering scenario and a stable diagnostic shape before implementation acceptance. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep traceability for accepted implementation requirements, but do not force runtime tests for documentation-only or rejected items. |
| REQ-STRAT-015 | A traceability matrix shall be a required deliverable before implementation begins, not a future improvement. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | A reviewed traceability matrix is required before implementation handoff. |
| REQ-STRAT-016 | Stable requirement IDs, acceptance criteria, applicability tags, and linked test IDs are required for v1.0 Builder handoff. | Merge | CAP-STR-014 — Strategy examples, documentation, and traceability | This repeats REQ-STRAT-011 through REQ-STRAT-015 and should not create a separate capability. |
| REQ-STRAT-017 | Strategies shall emit `TradeIntent` objects and diagnostics, not broker orders, official fills, account mutations, portfolio mutations, risk approvals, or regulatory reports. | Add | CAP-STR-001 — Pure strategy decision boundary | The invariant is required to make the strategy layer read-only and reproducible; V1 does not enforce it consistently. |
| REQ-STRAT-018 | Risk, trading, simulation, live, portfolio, compliance, reporting, data, and indicator modules shall remain the authorities for their own enforcement responsibilities. | Add | CAP-STR-001 — Pure strategy decision boundary | The invariant is required to make the strategy layer read-only and reproducible; V1 does not enforce it consistently. |
| REQ-STRAT-019 | Strategy execution shall receive read-only snapshots or approved read-only handles for external state; strategy code shall not mutate official external state directly. | Add | CAP-STR-001 — Pure strategy decision boundary | The invariant is required to make the strategy layer read-only and reproducible; V1 does not enforce it consistently. |
| REQ-STRAT-020 | Every external-module interaction shall pass through a documented contract with deterministic error mapping, timeout behavior, and redaction behavior. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Document error mapping and redaction at boundaries, but strategy should receive prepared inputs rather than call data, indicator, or execution services directly. |
| REQ-STRAT-021 | Every strategy decision shall be reproducible from strategy id, strategy version, configuration hash, data checksum, indicator manifest, simulation config hash where applicable, interface version, timing policy, and seed material. | Add | CAP-STR-009 — Checkpoint and replay metadata | A minimal replay manifest is a confirmed audit need and is absent from V1. |
| REQ-STRAT-022 | Strategy implementation scope shall be narrowed to an approved phase slice before Builder handoff. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | The V2 document itself states implementation scope must be narrowed before Builder handoff. |
| REQ-STRAT-023 | The strategy module shall live under `tools/strategies/`. | Open Decision | Package location | Whether the final package is `tools/strategies/` or another canonical root is a system-level naming and dependency decision for cross-domain alignment step 05. |
| REQ-STRAT-024 | Strategies shall produce decisions, signals, trade intents, or strategy state updates. | Add | CAP-STR-001 — Pure strategy decision boundary | The boundary is required because V1 mixes strategy decisions with storage and execution-facing compatibility concerns. |
| REQ-STRAT-025 | Strategies shall not directly mutate official account, order, deal, position, pending-order, margin, equity, journal, or execution timestamp state. | Add | CAP-STR-001 — Pure strategy decision boundary | The boundary is required because V1 mixes strategy decisions with storage and execution-facing compatibility concerns. |
| REQ-STRAT-026 | Strategies shall not directly create official fills, deals, journal events, or reports. | Add | CAP-STR-001 — Pure strategy decision boundary | The boundary is required because V1 mixes strategy decisions with storage and execution-facing compatibility concerns. |
| REQ-STRAT-027 | Strategies shall not finalize official order volume, margin acceptance, execution price, fill status, or risk approval. | Add | CAP-STR-001 — Pure strategy decision boundary | The boundary is required because V1 mixes strategy decisions with storage and execution-facing compatibility concerns. |
| REQ-STRAT-028 | Official execution, matching, accounting, journal, reporting, and production-realism classification shall remain owned by `app/services/simulation/`. | Modify | CAP-STR-001 — Pure strategy decision boundary | Simulation owns execution only for simulated runs; strategy must hand intents to the runtime-specific downstream authority without owning execution. |
| REQ-STRAT-029 | The module shall support vectorized signal strategies. | Modify | CAP-STR-004 — Vectorized strategy decision execution | Reuse V1 vectorized signal value but replace DataFrame signal-column coupling with typed batch decisions and intents. |
| REQ-STRAT-030 | The module shall support stateful event strategies. | Modify | CAP-STR-005 — Stateful event strategy execution | Reuse V1 stateful strategy value but replace the split BaseStrategy/trading mixin contract with one typed event protocol. |
| REQ-STRAT-031 | Vectorized signal strategies shall compute indicators, generate signals, and convert signals to timestamped `TradeIntent` objects before simulation execution. | Modify | CAP-STR-004 — Vectorized strategy decision execution | Strategies should consume indicator outputs from the indicator domain rather than own indicator calculation internals. |
| REQ-STRAT-032 | Event strategies shall respond to initialization, bar-open, tick, and trade-transaction events through controlled interfaces. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-033 | `INTRABAR_EVENT` strategies may use current tick data only through approved event interfaces. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-034 | Martingale, grid, pyramiding, basket recovery, and trade-decomposition strategies shall execute through the canonical simulation tick engine. | Keep | CAP-STR-001 — Pure strategy decision boundary | V1 already routes advanced strategies through the canonical event-driven simulation tick loop; preserve that cross-domain boundary. |
| REQ-STRAT-035 | Advanced strategies shall query the simulation engine for actual fills, remaining volume, average price, and open exposure through approved read-only interfaces. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-036 | Advanced strategies that need fills or open positions shall use `ReadOnlyExecutionStateQuery` and `ReadOnlyExecutionStateSnapshot`; direct access to official simulation, execution, account, or position state is prohibited. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-037 | Martingale level progression shall be based on confirmed deals or official position state, not submitted requests. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-038 | A strategy registry entry may declare `min_expected_alpha`, `max_acceptable_transaction_cost`, both, or neither. | Defer | CAP-STR-012 — Strategy declaration manifest | Alpha and transaction-cost thresholds require agreed analytics/cost inputs and are not needed for the minimal initial runtime. |
| REQ-STRAT-039 | When `min_expected_alpha` or `max_acceptable_transaction_cost` is declared, the strategy shall evaluate the declared threshold before emitting a trade intent and shall emit a deterministic suppression diagnostic when the threshold blocks the decision. | Defer | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Suppression behavior depends on the deferred threshold declarations in REQ-STRAT-038. |
| REQ-STRAT-040 | Event strategies shall support `FILL_UPDATE` or `PARTIAL_FILL` events to react to incomplete executions through approved read-only execution-state interfaces. | Modify | CAP-STR-005 — Stateful event strategy execution | V1 proves both DataFrame and stateful strategy value, but the final contract must emit typed intents and use controlled read-only inputs. |
| REQ-STRAT-041 | Strategies shall emit `TradeIntent` objects instead of official orders. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 emits signal dictionaries or TradeAction objects rather than one canonical TradeIntent contract. |
| REQ-STRAT-042 | `TradeIntent` objects shall include strategy id, strategy version, symbol, side, intent type, requested sizing mode or quantity hint, optional stop loss, optional take profit, optional expiration, optional rationale, and signal timestamp. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 emits signal dictionaries or TradeAction objects rather than one canonical TradeIntent contract. |
| REQ-STRAT-043 | `TradeIntent` objects shall include an explicit `allow_partial_fills` boolean and `min_fill_size` parameter to guide the simulation or execution engine. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 emits signal dictionaries or TradeAction objects rather than one canonical TradeIntent contract. |
| REQ-STRAT-044 | Bar-based signals shall be aligned using the configured signal timing policy before becoming executable trade intents. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Intent creation must carry the approved signal timing policy and aligned timestamps. |
| REQ-STRAT-045 | The simulation engine shall transform `TradeIntent` into a sized `TradeRequest`. | Modify | CAP-STR-001 — Pure strategy decision boundary | For simulated runs, simulation converts intents to requests; other environments use their own downstream execution authority. |
| REQ-STRAT-046 | The simulation engine shall execute `TradeIntent` objects only when the canonical tick loop reaches an eligible tick. | Modify | CAP-STR-001 — Pure strategy decision boundary | The eligible-tick rule applies to simulation; the strategy domain only emits intents and timing metadata. |
| REQ-STRAT-047 | Strategies may request a sizing mode but shall not directly finalize official volume. | Keep | CAP-STR-006 — TradeIntent construction, identity, and lineage | Sizing must remain a hint because official volume belongs to downstream risk/execution. |
| REQ-STRAT-048 | Strategy-generated rationales shall be preserved for compliance or audit records when provided. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 reason fields provide reuse value but need structured rationale references. |
| REQ-STRAT-049 | The default strategy signal timing policy shall be `BAR_OPEN_PREVIOUS_CLOSE`. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-050 | At the first tick of bar `N`, strategies may use only bars up to and including fully closed bar `N-1`. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-051 | At the first tick of bar `N`, strategies shall not use current incomplete bar `N` high, low, close, volume, indicator-derived values, multi-timeframe values, or metadata derived from unavailable current-bar data. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-052 | Strategies shall enter at the first valid tick of bar `N` only when a valid trade intent is emitted from previous-closed-bar data. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-053 | Vectorized signal generation shall shift current-bar conditions so that bar-open entries are based on previous closed-bar values. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-054 | Strategy access to prohibited current-bar or future data shall fail with the canonical strategy-domain error code `STRATEGY_LOOKAHEAD_DETECTED`; lower-level simulation lookahead errors, if any, shall be mapped to this code before returning strategy diagnostics. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-055 | Strategy tests shall cover previous-close-only behavior, shifted signals, no current-bar leakage, and first tick of new bar activation. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-056 | Strategies shall enforce point-in-time correctness for all feature and indicator lookups. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Point-in-time correctness is required, but data and indicator domains produce point-in-time-safe inputs; strategy validates supplied timestamps/manifests. |
| REQ-STRAT-057 | A query for data at timestamp `T` shall return only the state of the data as it was known at `T`, excluding subsequent revisions, restatements, or late-arriving ticks. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Revision awareness belongs to data contracts; strategy must reject inputs whose as-known-at metadata exceeds the decision timestamp. |
| REQ-STRAT-058 | Strategies shall declare `max_data_latency_tolerance`. | Modify | CAP-STR-012 — Strategy declaration manifest | Latency tolerance should be declared only when the strategy is latency-sensitive; a module default may apply otherwise. |
| REQ-STRAT-059 | Data arriving outside the declared latency tolerance shall cause the strategy to skip the decision or emit `STRATEGY_STALE_DATA`. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 contains shifted template features but lacks a domain-wide timing and no-lookahead contract. |
| REQ-STRAT-060 | If a vectorized batch detects lookahead at any element, the entire batch shall fail atomically, emit `STRATEGY_LOOKAHEAD_DETECTED`, discard intents produced by that batch, and preserve a diagnostic identifying the first failing timestamp. | Keep | CAP-STR-004 — Vectorized strategy decision execution | Atomic batch failure prevents partial intent emission after a lookahead violation. |
| REQ-STRAT-061 | A vectorized batch decision clock shall be anchored to the supplied `StrategyExecutionContext.decision_timestamp`; wall-clock elapsed time during long-running batches shall not advance decision-time semantics. | Keep | CAP-STR-004 — Vectorized strategy decision execution | A fixed decision clock is required for deterministic vectorized replay. |
| REQ-STRAT-062 | The module shall provide an official strategy registry. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Reuse the V1 registry concept but replace mutable global registration and hard-coded imports with approved immutable entries. |
| REQ-STRAT-063 | Registered strategies shall declare strategy id, version, module path, owner, configuration schema, supported symbols or asset classes, supported timing policy, required indicators, required data, risk assumptions, and permitted execution modes. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-064 | Registered strategy identifiers shall resolve only to approved strategy modules. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-065 | Strategy configuration shall be schema-validated before execution. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-066 | Invalid strategy identifiers shall fail deterministically before simulation execution. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | V1 already rejects unknown names; retain the behavior under typed deterministic diagnostics before any strategy execution. |
| REQ-STRAT-067 | Invalid strategy configuration shall fail deterministically before simulation execution. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-068 | Strategy registry entries shall include version hashes for replay and audit. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-069 | Strategy files and module paths shall resolve through approved registries or allowlisted roots, not arbitrary user-supplied filesystem paths. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Approved module identifiers or allowlisted package roots are accepted; arbitrary runtime filesystem paths are removed. |
| REQ-STRAT-070 | Duplicate strategy id/version registry entries shall fail registry validation deterministically before execution. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-071 | Strategy version constraints shall resolve deterministically to exactly one approved immutable version or fail with `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE` before execution. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-072 | Deprecated strategies shall fail with `STRATEGY_DEPRECATED` unless explicitly run in approved historical replay mode. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | Deprecation gating is absent from V1 and is required for deterministic lifecycle behavior. |
| REQ-STRAT-073 | Strategy configuration schemas shall define default handling, unknown-field policy, required-field policy, type-coercion policy, enum validation, and version migration behavior. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 has only a mutable name-to-class map and filesystem loading; approved immutable references and schema validation are missing. |
| REQ-STRAT-074 | Strategy configuration validation shall reject configuration-injection patterns, including string fields that request evaluation, import, subprocess execution, filesystem access, network access, environment-variable access, template expansion, or dynamic attribute access unless a future approved sandbox contract explicitly permits them. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Reject executable configuration forms through typed schemas and bounded primitive values; avoid implementing a general-purpose content scanner. |
| REQ-STRAT-075 | Strategy configuration validation shall explicitly reject `eval()`, `exec()`, dynamic `__import__`, import strings, function-object strings, and magic-method access patterns in user-provided configuration. | Merge | CAP-STR-003 — Approved immutable registry and configuration validation | This is a concrete subset of REQ-STRAT-074 and belongs in the same configuration validation policy. |
| REQ-STRAT-076 | Strategy configuration validation shall enforce maximum payload size, maximum nesting depth, maximum string length, maximum collection length, and maximum schema-validation time before implementation acceptance. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Enforce payload, nesting, string, and collection limits; schema-validation time is enforced by the caller/runtime budget. |
| REQ-STRAT-077 | `run_backtest` shall not execute arbitrary user-provided Python code strings. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 dynamically executes stored Python and lacks registered-only execution and bounded failure behavior. |
| REQ-STRAT-078 | The strategy input path shall accept only registered strategy identifiers, validated strategy configuration schemas, or code explicitly vetted and sandboxed by the orchestration layer. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Phase 1 accepts only approved registry entries and typed config; sandboxed code paths are excluded rather than accepted by strategy orchestration. |
| REQ-STRAT-079 | Phase 1 strategy execution shall allow registered strategies and validated configuration only. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 dynamically executes stored Python and lacks registered-only execution and bounded failure behavior. |
| REQ-STRAT-080 | Code-based strategy execution shall remain disabled until sandbox policy, approval workflow, and prohibited-operation lists are approved. | Keep | CAP-STR-011 — Registered-only security, resource, and determinism controls | Code-based execution remains disabled in the initial rebuild. |
| REQ-STRAT-081 | Sandboxed code-based strategy execution, if enabled later, shall require `simulation.admin` approval, strategy owner approval, sandbox profile id, vetting artifact hash, allowed capability list, audit record, and approval expiry. | Defer | Future sandbox capability | No sandbox policy or approved workflow exists; this requirement activates only if arbitrary code support is later approved. |
| REQ-STRAT-082 | Sandbox policy shall define allowed imports, denied imports, filesystem access, network access, subprocess access, environment-variable access, timeouts, memory limits, and prohibited operations. | Defer | Future sandbox capability | Sandbox resource and permission policy is outside the initial registered-only execution slice. |
| REQ-STRAT-083 | Raw strategy-code injection attempts shall be rejected before execution. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 dynamically executes stored Python and lacks registered-only execution and bounded failure behavior. |
| REQ-STRAT-084 | Rejected raw strategy-code input shall return `SIM_ARBITRARY_CODE_REJECTED`. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Keep deterministic rejection but use a strategy-domain code such as `STRATEGY_ARBITRARY_CODE_REJECTED`; `SIM_*` incorrectly assigns the error to simulation. |
| REQ-STRAT-085 | Rejected strategy-injection attempts shall be journaled without logging unsafe code bodies in full. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy emits a redacted rejection diagnostic; journal persistence is owned by audit/orchestration. |
| REQ-STRAT-086 | Rejected strategy-input diagnostics shall include request id, strategy identifier when present, rejection reason, and deterministic error code. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 dynamically executes stored Python and lacks registered-only execution and bounded failure behavior. |
| REQ-STRAT-087 | Approved strategy code shall still be protected by resource controls for CPU time, recursion depth, loop iterations where measurable, memory growth, checkpoint size, diagnostic size, and dependency call timeouts. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Strategies declare budgets and avoid prohibited operations; CPU, memory, timeout, and process enforcement are owned by the execution host. |
| REQ-STRAT-088 | Resource exhaustion by sanctioned strategy code, sanctioned indicator calls, or sanctioned data access shall fail deterministically with `STRATEGY_RESOURCE_LIMIT_EXCEEDED` or a more specific approved error code. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 dynamically executes stored Python and lacks registered-only execution and bounded failure behavior. |
| REQ-STRAT-089 | Strategies may maintain decision state only. | Add | CAP-STR-008 — Read-only external state and strategy-local decision state | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-090 | Strategy decision state shall be serializable when checkpoint or replay workflows require it. | Add | CAP-STR-009 — Checkpoint and replay metadata | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-091 | Strategy state checkpoints shall not include secrets or unrestricted raw proprietary strategy source. | Keep | CAP-STR-009 — Checkpoint and replay metadata | Checkpoints must exclude secrets and raw source to preserve the side-effect-free security boundary. |
| REQ-STRAT-092 | Strategy replay shall use strategy id, strategy version, configuration hash, data checksum, indicator result manifest, and simulation config hash. | Add | CAP-STR-009 — Checkpoint and replay metadata | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-093 | The same strategy id, version, configuration, input data, indicator outputs, and simulation seed shall produce the same trade intents. | Add | CAP-STR-009 — Checkpoint and replay metadata | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-094 | Strategy-local state updates shall be atomic per decision event or shall fail with a deterministic rollback diagnostic. | Add | CAP-STR-008 — Read-only external state and strategy-local decision state | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-095 | Read-only external state supplied to a strategy shall be an immutable snapshot or shall carry a documented consistency model preventing races with concurrent simulation, risk, portfolio, or data updates. | Add | CAP-STR-008 — Read-only external state and strategy-local decision state | Immutable snapshots are necessary for V1-style advanced strategies without direct access to official state. |
| REQ-STRAT-096 | Concurrent strategy instances shall not share mutable strategy-local state unless an approved synchronization contract exists. | Add | CAP-STR-008 — Read-only external state and strategy-local decision state | V1 has ad hoc mutable state but no typed checkpoint, replay, isolation, or atomic-update contract. |
| REQ-STRAT-097 | Strategies may maintain decision state but shall not mutate official trading state. | Merge | CAP-STR-001 — Pure strategy decision boundary | This repeats core boundary, intent, security, rationale, and replay requirements already retained in focused capabilities. |
| REQ-STRAT-098 | Vectorized processing is allowed only for indicator and signal generation. | Merge | CAP-STR-001 — Pure strategy decision boundary | This repeats core boundary, intent, security, rationale, and replay requirements already retained in focused capabilities. |
| REQ-STRAT-099 | Bar-open trading must use previous closed-bar data by default. | Merge | CAP-STR-001 — Pure strategy decision boundary | This repeats core boundary, intent, security, rationale, and replay requirements already retained in focused capabilities. |
| REQ-STRAT-100 | Strategy execution shall occur only through registered strategies, validated schemas, or explicitly sandboxed and vetted orchestration paths. | Merge | CAP-STR-001 — Pure strategy decision boundary | This repeats core boundary, intent, security, rationale, and replay requirements already retained in focused capabilities. |
| REQ-STRAT-101 | Advanced stateful strategies and agent-generated strategies shall provide decision rationale when required by compliance configuration. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | A rationale may be required by configuration, but compliance owns the policy and strategy only emits the reference. |
| REQ-STRAT-102 | Strategy security rejections must be journaled with safe redaction. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy produces redacted security diagnostics; journaling is external. |
| REQ-STRAT-103 | Strategy identifiers, configuration hashes, and version hashes must be included in replay and audit metadata. | Merge | CAP-STR-001 — Pure strategy decision boundary | This repeats core boundary, intent, security, rationale, and replay requirements already retained in focused capabilities. |
| REQ-STRAT-104 | Registered strategy identifier. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-105 | Strategy version or version constraint. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-106 | Validated strategy configuration. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-107 | Indicator specifications or precomputed indicator outputs. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-108 | Normalized market data. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-109 | Symbol metadata. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-110 | Signal timing policy. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-111 | Optional read-only simulation state for event strategies. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-112 | Sandbox and vetting metadata only when code-based strategy execution is explicitly permitted. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-113 | Timestamped `TradeIntent` objects. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-114 | Strategy diagnostics. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-115 | Strategy rationale where provided. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-116 | Strategy state checkpoint where enabled. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-117 | Strategy manifest containing strategy id, version, configuration hash, required indicators, required data, and timing policy. | Modify | CAP-STR-012 — Strategy declaration manifest | Use one registry manifest containing identity, config hash, data/indicator requirements, timing, environment, and advisory declarations. |
| REQ-STRAT-118 | Structured error result with deterministic error code on failure. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | Treat these as fields of the accepted input/output schemas rather than separate runtime capabilities. |
| REQ-STRAT-119 | `TradeIntent` schema shall define required fields, optional fields, enum values, precision rules, nullability, serialization format, and schema version. | Merge | CAP-STR-002 — Versioned contracts and deterministic results | TradeIntent field rules belong in the versioned TradeIntent schema rather than a separate capability. |
| REQ-STRAT-120 | Registered strategies shall have one lifecycle status: `DRAFT`, `RESEARCH`, `BACKTEST_APPROVED`, `PAPER_APPROVED`, `LIVE_ELIGIBLE`, `DEPRECATED`, or `REVOKED`. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | The registry may store lifecycle metadata and enforce eligibility; promotion evidence and approvals remain external governance responsibilities. |
| REQ-STRAT-121 | A strategy shall not execute in an environment higher than its approved lifecycle status. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | The registry may store lifecycle metadata and enforce eligibility; promotion evidence and approvals remain external governance responsibilities. |
| REQ-STRAT-122 | Promotion between lifecycle states shall require recorded evidence, including test results, validation report, owner approval, and risk approval where applicable. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | The registry records evidence references and validates status; governance/risk systems approve promotions. |
| REQ-STRAT-123 | Material strategy changes shall require a new immutable strategy version. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | The registry may store lifecycle metadata and enforce eligibility; promotion evidence and approvals remain external governance responsibilities. |
| REQ-STRAT-124 | Deprecated or revoked strategies shall fail deterministically before execution unless explicitly run in historical replay mode. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | The registry may store lifecycle metadata and enforce eligibility; promotion evidence and approvals remain external governance responsibilities. |
| REQ-STRAT-125 | Strategy registry entries shall include owner, reviewer, approver, approval timestamp, approval expiry, and linked validation artifact ids. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Store owner and approval artifact references, but reviewer workflows and expiry enforcement remain governance-owned. |
| REQ-STRAT-126 | Registered strategies shall declare a strategy-level risk profile. | Modify | CAP-STR-012 — Strategy declaration manifest | Require a risk declaration only when the strategy uses local exposure, recovery, grid, or pyramiding behavior; keep simple strategies lightweight. |
| REQ-STRAT-127 | The risk profile shall include maximum gross exposure, maximum net exposure, maximum symbol exposure, maximum intent notional, maximum intent frequency, maximum concurrent positions, maximum pyramiding depth, maximum martingale level, and maximum grid depth where applicable. | Modify | CAP-STR-012 — Strategy declaration manifest | Keep applicable local limits such as intent frequency and recovery depth; official gross/net exposure and position limits remain external. |
| REQ-STRAT-128 | Strategy risk declarations shall be advisory inputs to the simulation or risk engine and shall not replace official risk approval. | Keep | CAP-STR-001 — Pure strategy decision boundary | Advisory strategy declarations must never replace official risk approval. |
| REQ-STRAT-129 | Strategies may self-suppress trade intents when strategy-local risk limits are breached. | Modify | CAP-STR-012 — Strategy declaration manifest | Keep applicable strategy-local risk assumptions as advisory declarations; official exposure and risk enforcement remain external. |
| REQ-STRAT-130 | The simulation or risk engine shall remain the final authority for official risk acceptance or rejection. | Keep | CAP-STR-001 — Pure strategy decision boundary | The risk or execution authority remains final for acceptance. |
| REQ-STRAT-131 | Risk-limit breaches shall produce deterministic diagnostics and audit metadata. | Modify | CAP-STR-012 — Strategy declaration manifest | Keep applicable strategy-local risk assumptions as advisory declarations; official exposure and risk enforcement remain external. |
| REQ-STRAT-132 | Strategy risk profiles shall include concentration risk limits where applicable. | Defer | CAP-STR-012 — Strategy declaration manifest | Concentration declarations are useful only for portfolio-aware strategies and are not required in the initial minimal schema. |
| REQ-STRAT-133 | Strategy risk profiles shall include time-based exposure limits where applicable. | Defer | CAP-STR-012 — Strategy declaration manifest | Time-based exposure declarations can be added when a confirmed strategy requires them. |
| REQ-STRAT-134 | Strategy risk profiles shall declare gap risk assumptions. | Defer | CAP-STR-012 — Strategy declaration manifest | Gap-risk assumptions are documentation metadata, not an initial runtime requirement. |
| REQ-STRAT-135 | Strategy risk profiles shall declare correlation assumptions during stress events. | Defer | CAP-STR-012 — Strategy declaration manifest | Stress-correlation assumptions belong to later portfolio/risk integration. |
| REQ-STRAT-136 | Every `TradeIntent` shall include a deterministic `intent_id`. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-137 | Every `TradeIntent` shall include a `decision_id` linking it to the strategy decision event that created it. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-138 | Every `TradeIntent` shall include an idempotency key. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-139 | Child intents shall include `parent_intent_id` when created from decomposition, scale-in, scale-out, recovery, or basket logic. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-140 | Trade intents shall include a monotonically increasing strategy-local sequence number. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | A deterministic strategy-local sequence makes ordering and replay unambiguous. |
| REQ-STRAT-141 | Duplicate `intent_id` or idempotency key collisions shall fail deterministically. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-142 | Superseded, cancelled, expired, or replaced intents shall preserve lineage to the original intent. | Add | CAP-STR-006 — TradeIntent construction, identity, and lineage | V1 has no deterministic intent identity, idempotency, sequence, or lineage model. |
| REQ-STRAT-143 | Strategies shall not emit executable trade intents until required indicators are warm and ready. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 helpers do not provide declared readiness, missing-data policy, stale-data policy, or point-in-time validation. |
| REQ-STRAT-144 | Indicator readiness shall include warmup period, minimum sample count, NaN policy, and dependency readiness. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 helpers do not provide declared readiness, missing-data policy, stale-data policy, or point-in-time validation. |
| REQ-STRAT-145 | Strategies shall declare their missing-data policy: reject, forward-fill, interpolate, skip signal, or use module default. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 helpers do not provide declared readiness, missing-data policy, stale-data policy, or point-in-time validation. |
| REQ-STRAT-146 | Strategies shall declare their stale-data policy. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 helpers do not provide declared readiness, missing-data policy, stale-data policy, or point-in-time validation. |
| REQ-STRAT-147 | Strategies shall declare whether they require bid, ask, mid, last, volume, spread, session metadata, corporate-action-adjusted prices, or raw prices. | Add | CAP-STR-007 — Timing, readiness, and no-lookahead validation | V1 helpers do not provide declared readiness, missing-data policy, stale-data policy, or point-in-time validation. |
| REQ-STRAT-148 | Multi-timeframe indicators shall be usable only when the higher-timeframe bar is fully closed as of the strategy decision timestamp. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Higher-timeframe closure is validated through indicator/data timestamps; strategy must not calculate or infer unclosed higher-timeframe values. |
| REQ-STRAT-149 | Strategy execution shall fail deterministically if required market data fields are missing, stale, out of order, duplicated, or timezone-inconsistent unless an explicit approved policy handles them. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Data module owns normalization; strategy fails only when supplied readiness metadata or required fields violate its declared contract. |
| REQ-STRAT-150 | Strategy execution shall emit structured diagnostics, not free-form logs. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 relies heavily on logs and unmapped exceptions; structured diagnostics are required at the domain boundary. |
| REQ-STRAT-151 | Diagnostics shall include run id, strategy id, strategy version, configuration hash, data checksum, decision timestamp, signal timestamp, intent id, decision id, and error code where applicable. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 relies heavily on logs and unmapped exceptions; structured diagnostics are required at the domain boundary. |
| REQ-STRAT-152 | Strategy metrics shall include intents emitted, intents suppressed, no-signal decisions, rejected decisions, invalid data events, lookahead detections, configuration validation failures, state checkpoint size, and per-event decision latency. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 relies heavily on logs and unmapped exceptions; structured diagnostics are required at the domain boundary. |
| REQ-STRAT-153 | Strategy diagnostics shall support debug mode without exposing secrets, proprietary source, unsafe code bodies, or excessive market-data payloads. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 relies heavily on logs and unmapped exceptions; structured diagnostics are required at the domain boundary. |
| REQ-STRAT-154 | Strategy execution shall support trace correlation across data, indicator, strategy, simulation, and reporting modules. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | V1 relies heavily on logs and unmapped exceptions; structured diagnostics are required at the domain boundary. |
| REQ-STRAT-155 | Parameter optimization shall produce a validation artifact. | Reject | Optimization domain | Producing optimization artifacts is an optimization responsibility; the strategy registry stores a reference when lifecycle policy requires one. |
| REQ-STRAT-156 | Validation artifacts shall include parameter search space, objective function, training period, validation period, test period, data checksum, transaction-cost assumptions, slippage assumptions, and random seed. | Reject | Optimization/analytics domains | Search space, objective, periods, costs, and seeds belong in the external validation artifact. |
| REQ-STRAT-157 | Strategy validation shall include in-sample and out-of-sample results. | Reject | Research/analytics domains | In-sample and out-of-sample evaluation is not strategy execution behavior. |
| REQ-STRAT-158 | Strategy validation shall include walk-forward or rolling-window analysis where applicable. | Reject | Optimization/research domains | Walk-forward analysis is external validation work. |
| REQ-STRAT-159 | Strategy validation shall include transaction-cost sensitivity and slippage sensitivity. | Reject | Analytics/simulation domains | Cost and slippage sensitivity are external analyses. |
| REQ-STRAT-160 | Strategy validation shall include market-regime analysis where applicable. | Reject | Research/analytics domains | Regime analysis is external validation work. |
| REQ-STRAT-161 | Strategy validation shall reject or flag configurations whose performance depends on future data, unclosed bars, unapproved survivorship-biased data, or unapproved parameter leakage. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Registry eligibility may require a validation artifact showing no leakage; strategy runtime does not perform research validation. |
| REQ-STRAT-162 | Optimized configurations shall be immutable and hash-addressed before simulation or production replay. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Store immutable hash-addressed approved configurations; optimization itself remains external. |
| REQ-STRAT-163 | Strategies shall declare expected computational complexity or supported maximum input size where applicable. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-164 | Strategies shall declare their concurrency model: `SYNC_BLOCKING`, `ASYNC_AWAIT`, or `MULTIPROCESS_ISOLATED`. | Modify | CAP-STR-012 — Strategy declaration manifest | Initial execution supports `SYNC_BLOCKING`; async and multiprocess profiles are deferred until orchestration contracts exist. |
| REQ-STRAT-165 | Strategy execution shall have configurable per-decision latency budgets. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-166 | Strategy execution shall have configurable memory limits. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Declare memory budgets in registry metadata; enforcement belongs to the execution host. |
| REQ-STRAT-167 | Strategy state checkpoint size shall be bounded and monitored. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-168 | Strategies shall not perform unbounded loops, unbounded recursion, unbounded memory growth, or unbounded history scans during event execution. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-169 | Strategies shall not instantiate unbounded caches, memoization dictionaries, or rolling window arrays without explicit maximum size limits and eviction behavior. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-170 | CPU-bound vectorized strategies shall run in isolated worker processes when their declared execution profile is `MULTIPROCESS_ISOLATED`, when configured by orchestration, or when measured event-loop latency exceeds the approved threshold for the target environment. | Defer | Future orchestration isolation | Multiprocess execution is an orchestration concern and has no confirmed initial workflow. |
| REQ-STRAT-171 | Event strategies shall be reentrant or explicitly marked single-threaded. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-172 | Strategy behavior under timeout shall be deterministic. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Keep bounded execution declarations and deterministic timeout behavior; runtime isolation and enforcement belong to orchestration. |
| REQ-STRAT-173 | Performance regression tests shall verify strategy latency and memory remain within approved budgets. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Add regression tests only after measured budgets and a reference benchmark are approved. |
| REQ-STRAT-174 | Registered strategy artifacts shall be immutable after approval. | Modify | CAP-STR-013 — Approved artifact integrity metadata | Keep immutable artifact hashes and provenance references; build pipeline, SBOM, and approval enforcement are external. |
| REQ-STRAT-175 | Strategy registry entries shall include source commit hash, artifact hash, package version, dependency lockfile hash, and build environment identifier. | Modify | CAP-STR-013 — Approved artifact integrity metadata | Keep immutable artifact hashes and provenance references; build pipeline, SBOM, and approval enforcement are external. |
| REQ-STRAT-176 | Strategy artifacts shall be produced by an approved build pipeline. | Reject | Build/CI domain | The strategy runtime does not produce artifacts through a build pipeline; it records approved provenance references. |
| REQ-STRAT-177 | Strategy artifacts shall pass type checking, linting, unit tests, contract tests, security scans, and dependency vulnerability checks before approval. | Reject | Build/CI domain | Type checks, linting, tests, scans, and vulnerability checks are pipeline gates, not runtime behavior. |
| REQ-STRAT-178 | Strategy artifacts shall include an SBOM where production packaging requires it. | Defer | Production packaging governance | SBOM requirements activate only for a production packaging workflow. |
| REQ-STRAT-179 | Strategy dependency versions shall be pinned for replayable execution. | Modify | CAP-STR-013 — Approved artifact integrity metadata | Keep immutable artifact hashes and provenance references; build pipeline, SBOM, and approval enforcement are external. |
| REQ-STRAT-180 | Strategy approval shall be invalidated if the source hash, artifact hash, dependency hash, or build provenance changes. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Registry validation fails closed when approved hashes change; approval invalidation decisions remain governance-owned. |
| REQ-STRAT-181 | A strategy failure shall not corrupt official simulation state. | Modify | CAP-STR-008 — Read-only external state and strategy-local decision state | Preserve failure isolation and checkpoint validation while leaving run-level failure policy and hard-stop enforcement to orchestration. |
| REQ-STRAT-182 | Strategy failures shall be isolated to the failing strategy instance unless configured fail-fast behavior requires run termination. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Strategy execution must be instance-isolated, but process/thread isolation is enforced by orchestration. |
| REQ-STRAT-183 | The orchestration layer shall support deterministic failure policies: `FAIL_RUN`, `DISABLE_STRATEGY`, `SKIP_DECISION`, or `QUARANTINE_INSTANCE`. | Reject | Orchestration domain | Run-level fail/disable/quarantine policy is not owned by strategy. |
| REQ-STRAT-184 | Strategy state checkpoint restore shall validate strategy id, version, configuration hash, state schema version, and checkpoint checksum. | Modify | CAP-STR-008 — Read-only external state and strategy-local decision state | Preserve failure isolation and checkpoint validation while leaving run-level failure policy and hard-stop enforcement to orchestration. |
| REQ-STRAT-185 | Corrupt, incompatible, or unauthorized checkpoints shall fail deterministically before execution. | Modify | CAP-STR-008 — Read-only external state and strategy-local decision state | Preserve failure isolation and checkpoint validation while leaving run-level failure policy and hard-stop enforcement to orchestration. |
| REQ-STRAT-186 | Repeated strategy errors shall trigger deterministic disablement or escalation according to configuration. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy returns deterministic repeated-failure diagnostics; disablement/escalation is orchestration-owned. |
| REQ-STRAT-187 | Strategies shall support an external asynchronous hard kill signal from the orchestration layer. | Modify | CAP-STR-005 — Stateful event strategy execution | Support a host cancellation signal between hook invocations; do not introduce an internal asynchronous control plane. |
| REQ-STRAT-188 | A hard kill signal shall immediately halt execution, cancel pending intents, and dump state according to the approved emergency policy. | Reject | Orchestration/execution domains | A strategy cannot cancel downstream or official intents; the host stops calls, discards unaccepted outputs, and owns emergency policy. |
| REQ-STRAT-189 | Upon receiving a hard kill signal, the strategy shall emit a final `STRATEGY_HARD_KILLED` diagnostic with the last known safe state checkpoint. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The host may emit `STRATEGY_HARD_KILLED` with the last checkpoint reference; strategy code need not manufacture it after forced termination. |
| REQ-STRAT-190 | Strategies shall declare permitted environments: `BACKTEST`, `REPLAY`, `PAPER`, `SHADOW`, or `LIVE`. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 does not enforce declared environment eligibility or environment-specific configuration hashes. |
| REQ-STRAT-191 | A strategy shall not execute in an environment not declared in its registry entry. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 does not enforce declared environment eligibility or environment-specific configuration hashes. |
| REQ-STRAT-192 | Paper or live execution eligibility shall require successful completion of configured validation gates. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Registry validates lifecycle evidence references; external governance decides whether gates are satisfied. |
| REQ-STRAT-193 | Live execution shall require explicit approval, expiry, rollback plan, monitoring plan, and emergency disable procedure. | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Store live eligibility and approval references, but rollback, monitoring, and emergency procedures are external operations artifacts. |
| REQ-STRAT-194 | Environment-specific configuration differences shall be explicit, hash-addressed, and audit-recorded. | Add | CAP-STR-003 — Approved immutable registry and configuration validation | V1 does not enforce declared environment eligibility or environment-specific configuration hashes. |
| REQ-STRAT-195 | Strategy interface versions shall follow explicit compatibility rules. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has no explicit interface compatibility or deprecation policy. |
| REQ-STRAT-196 | Breaking changes to `TradeIntent`, strategy configuration schemas, event interfaces, or registry schemas shall require a version bump. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has no explicit interface compatibility or deprecation policy. |
| REQ-STRAT-197 | Deprecated strategy APIs shall include removal version, migration guidance, and compatibility test coverage. | Add | CAP-STR-002 — Versioned contracts and deterministic results | V1 has no explicit interface compatibility or deprecation policy. |
| REQ-STRAT-198 | Strategy replay shall use the exact interface version active at the time of original execution unless an approved migration exists. | Modify | CAP-STR-009 — Checkpoint and replay metadata | Replay resolves the recorded interface version; migrations are registry-governed and explicit. |
| REQ-STRAT-199 | Strategies shall not use wall-clock time, system randomness, network state, filesystem state, or environment variables as decision inputs. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Deterministic calculation rules are necessary for replay and are not explicit in V1. |
| REQ-STRAT-200 | Randomized strategies shall use only simulation-provided seeded randomness. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Deterministic calculation rules are necessary for replay and are not explicit in V1. |
| REQ-STRAT-201 | Simultaneous events shall be processed using a stable deterministic ordering policy. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Deterministic calculation rules are necessary for replay and are not explicit in V1. |
| REQ-STRAT-202 | Price, volume, and quantity comparisons shall follow approved precision and rounding rules. | Modify | CAP-STR-002 — Versioned contracts and deterministic results | Define precision in contracts for prices, quantities, and identifiers; official execution rounding remains downstream. |
| REQ-STRAT-203 | Floating-point tolerance rules shall be explicit in tests. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Deterministic calculation rules are necessary for replay and are not explicit in V1. |
| REQ-STRAT-204 | Every production-eligible strategy shall include a runbook. | Defer | Production governance documentation | A runbook is required before production eligibility, not before the initial backtest/replay implementation. |
| REQ-STRAT-205 | The runbook shall document expected behavior, configuration parameters, known failure modes, monitoring metrics, disable procedure, replay procedure, and owner escalation path. | Defer | Production governance documentation | Runbooks are valuable for production promotion but do not belong in the initial backtest/replay strategy runtime slice. |
| REQ-STRAT-206 | Strategies shall declare their execution assumptions, including fill model, latency model, and market impact model. | Modify | CAP-STR-012 — Strategy declaration manifest | Keep generic declared fill/latency/impact assumptions without implementing downstream models in strategy. |
| REQ-STRAT-207 | Trade intents shall specify acceptable execution algorithms, such as `TWAP`, `VWAP`, or `ICEBERG`, where applicable. | Defer | CAP-STR-006 — TradeIntent construction, identity, and lineage | Execution-algorithm preferences are added only after simulation/trading expose a supported algorithm contract. |
| REQ-STRAT-208 | Strategies shall declare maximum permissible spread for execution. | Modify | CAP-STR-012 — Strategy declaration manifest | Allow optional maximum-spread suppression metadata; official spread acceptance remains downstream. |
| REQ-STRAT-209 | Strategies shall declare minimum volume requirements and maximum volume participation rates. | Modify | CAP-STR-006 — TradeIntent construction, identity, and lineage | Retain optional minimum fill and participation hints only when downstream contracts support them. |
| REQ-STRAT-210 | Dark pool, auction, and alternative venue eligibility shall be explicitly declared. | Defer | Future venue-aware execution | No confirmed dark-pool, auction, or alternative-venue strategy workflow exists. |
| REQ-STRAT-211 | Strategies shall declare one deterministic policy for each halt-like market state: `SUPPRESS_NEW_INTENTS`, `ALLOW_REDUCE_ONLY`, `CLOSE_INTENTS_ONLY`, or `NO_SPECIAL_HANDLING`. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain only strategy execution assumptions or intent preferences supported by downstream execution; matching models and venue behavior remain external. |
| REQ-STRAT-212 | The selected halt-like market-state policy shall be included in strategy diagnostics when such a market state affects a decision. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain only strategy execution assumptions or intent preferences supported by downstream execution; matching models and venue behavior remain external. |
| REQ-STRAT-213 | Fill probability models shall account for queue position and adverse selection where applicable. | Reject | Simulation/execution domains | Queue position, adverse selection, and fill probability models belong to matching and execution simulation. |
| REQ-STRAT-214 | Strategies shall declare interaction modes: `INDEPENDENT`, `COOPERATIVE`, or `PORTFOLIO_AWARE`. | Defer | CAP-STR-012 — Strategy declaration manifest | Interaction modes are not required until a confirmed multi-strategy coordination workflow exists. |
| REQ-STRAT-215 | Strategies shall declare portfolio-interaction assumptions and optional strategy-local exposure preferences. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain optional interaction and exposure assumptions as metadata; cross-strategy allocation and conflict resolution remain external. |
| REQ-STRAT-216 | Portfolio-level gross and net exposure enforcement shall remain owned by the portfolio or risk module. | Keep | CAP-STR-001 — Pure strategy decision boundary | Portfolio-level exposure enforcement must remain outside strategy. |
| REQ-STRAT-217 | Strategy-level capital allocation assumptions and position-sizing preferences shall be metadata for portfolio or risk consumers, not official allocation enforcement. | Keep | CAP-STR-012 — Strategy declaration manifest | Capital and sizing preferences may be emitted only as advisory metadata. |
| REQ-STRAT-218 | Strategies may declare conflict-priority hints, but cross-strategy conflict resolution shall remain owned by portfolio, risk, or orchestration modules. | Keep | CAP-STR-001 — Pure strategy decision boundary | Cross-strategy conflict resolution remains portfolio/risk/orchestration owned. |
| REQ-STRAT-219 | Correlation-aware position-limit assumptions shall be declared where applicable. | Defer | CAP-STR-012 — Strategy declaration manifest | Correlation assumptions require portfolio/risk integration and are not initial runtime behavior. |
| REQ-STRAT-220 | Strategy turn-off and onboarding runbook metadata shall describe existing-position assumptions; official position handling shall remain owned by trading, risk, portfolio, live, or simulation modules. | Defer | Production runbook metadata | Turn-off/onboarding behavior is an operations concern until production workflows are in scope. |
| REQ-STRAT-221 | Strategy health checks shall be defined for signal generation frequency, decision staleness, and data freshness. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy exposes signal frequency, staleness, and freshness metrics; health-check evaluation and alerting remain external. |
| REQ-STRAT-222 | Strategies shall declare circuit-breaker inputs, expected trigger diagnostics, and safe-disable behavior; circuit-breaker enforcement shall remain owned by orchestration, risk, live, or operations modules. | Modify | CAP-STR-012 — Strategy declaration manifest | Strategy declares suppression inputs and diagnostics; circuit-breaker enforcement remains external. |
| REQ-STRAT-223 | Strategies shall declare graduated-deployment eligibility metadata and rollback assumptions; deployment progression and rollback enforcement shall remain owned by deployment or operations modules. | Defer | Production observability and deployment metadata | No initial production operations workflow is confirmed; strategy may later expose metadata while external domains enforce monitoring and rollout. |
| REQ-STRAT-224 | Strategy performance metadata shall declare expected review bands for supplied analytics, but these bands shall not become approved risk thresholds or promotion rules until owner/governance approval records them. | Reject | Analytics/governance domains | Performance review bands and promotion thresholds are not strategy-runtime rules. |
| REQ-STRAT-225 | Strategies shall emit or expose drift-detection diagnostics where applicable; alert routing remains owned by observability or operations modules. | Defer | Production observability and deployment metadata | No initial production operations workflow is confirmed; strategy may later expose metadata while external domains enforce monitoring and rollout. |
| REQ-STRAT-226 | Canary-analysis metadata shall describe expected paper/live consistency checks; official comparison and promotion decisions remain owned by analytics, risk, live, or governance modules. | Defer | Production observability and deployment metadata | No initial production operations workflow is confirmed; strategy may later expose metadata while external domains enforce monitoring and rollout. |
| REQ-STRAT-227 | Strategies shall declare applicable regulatory regimes, such as `SEC`, `ESMA`, or `FCA`, where applicable. | Defer | Compliance metadata | Regulatory regime declarations are applicable only after a regulated-market workflow is approved. |
| REQ-STRAT-228 | Position-limit and reporting assumptions by jurisdiction shall be declared where applicable; official regulatory reporting and limit enforcement remain owned by compliance, risk, portfolio, or reporting modules. | Reject | Compliance/risk/reporting domains | Jurisdictional limits and reporting are external enforcement responsibilities. |
| REQ-STRAT-229 | Wash trade prevention rules shall be declared. | Defer | Compliance policy metadata | Wash-trade prevention requires a cross-strategy/execution compliance workflow, not a standalone strategy declaration. |
| REQ-STRAT-230 | Market manipulation safeguards shall prohibit spoofing, layering, marking the close, and equivalent manipulative behavior. | Reject | Compliance domain | Manipulation prevention is a system compliance policy and surveillance responsibility, not strategy-local enforcement. |
| REQ-STRAT-231 | Strategy audit metadata shall preserve intent creation and decision rationale references; official sizing, execution, fill, and regulatory audit records remain owned by trading, simulation, live, audit, or reporting modules. | Merge | CAP-STR-006 — TradeIntent construction, identity, and lineage | Intent identity, lineage, and rationale references already provide the strategy-owned audit contribution. |
| REQ-STRAT-232 | Best-execution and venue-analysis assumptions shall be declared where applicable; official venue analysis remains owned by execution, compliance, or reporting modules. | Reject | Execution/compliance/reporting domains | Best-execution and venue analysis are external. |
| REQ-STRAT-233 | Large-position reporting assumptions shall be documented where applicable; official reporting threshold enforcement remains external to the strategy module. | Reject | Compliance/reporting domains | Large-position reporting thresholds are external. |
| REQ-STRAT-234 | Strategies shall declare maximum permissible data gaps before entering safe mode. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain data requirements and deterministic response declarations; data validation and vendor failover remain data/orchestration responsibilities. |
| REQ-STRAT-235 | Dividend, split, and corporate action handling procedures shall be specified. | Modify | CAP-STR-012 — Strategy declaration manifest | Declare adjusted-versus-raw price requirements; corporate-action processing is owned by data. |
| REQ-STRAT-236 | Strategies shall declare startup data-readiness requirements for completeness, expected ranges, and consistency checks; validation enforcement remains owned by data, orchestration, or simulation modules. | Modify | CAP-STR-012 — Strategy declaration manifest | Declare startup requirements; data/orchestration/simulation validate source readiness. |
| REQ-STRAT-237 | Strategies shall declare behavior when the data layer reports cross-venue price deviation, degraded data quality, failover, or unavailable data. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain data requirements and deterministic response declarations; data validation and vendor failover remain data/orchestration responsibilities. |
| REQ-STRAT-238 | Strategies shall declare delisted-symbol assumptions and safe behavior; official position liquidation procedures remain owned by trading, risk, live, portfolio, or operations modules. | Modify | CAP-STR-012 — Strategy declaration manifest | Retain data requirements and deterministic response declarations; data validation and vendor failover remain data/orchestration responsibilities. |
| REQ-STRAT-239 | Data vendor failover orchestration shall remain owned by the data or operations module. | Reject | Data/operations domains | Vendor failover is not strategy behavior. |
| REQ-STRAT-240 | Strategy decision latency SLOs shall be defined by environment, including P50, P95, and P99 targets. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | P50/P95/P99 targets require a measured reference environment and phase-specific workload. |
| REQ-STRAT-241 | Signal generation throughput minimums shall be defined for expected market conditions. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | Throughput minimums require confirmed symbol and strategy concurrency assumptions. |
| REQ-STRAT-242 | Recovery time objectives shall be defined for strategy restarts and failovers. | Defer | Operations domain | Strategy restart RTO is a runtime/operations objective, not an initial domain contract. |
| REQ-STRAT-243 | Recovery point objectives shall be defined for strategy state. | Defer | Operations/replay domains | RPO requires checkpoint cadence and deployment topology decisions. |
| REQ-STRAT-244 | Resource utilization limits shall include CPU, memory, and network bandwidth budgets. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Declare CPU and memory budgets; network bandwidth is irrelevant because strategy execution has no network access. |
| REQ-STRAT-245 | Graceful degradation procedures shall be defined for overload conditions. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy produces deterministic timeout/suppression outcomes; overload degradation policy is orchestration-owned. |
| REQ-STRAT-246 | Strategies shall define calibration frequency and trigger conditions. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-247 | Parameter stability analysis shall cover different market regimes. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-248 | Sensitivity analysis shall include approved parameter perturbation bands, including plus or minus 10% and plus or minus 20% where applicable. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-249 | Minimum training data period requirements and regime representation shall be defined. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-250 | Overfitting detection criteria and automated strategy retirement procedures shall be defined. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-251 | Ensemble and model averaging policies shall be defined for production strategies where applicable. | Defer | External research and lifecycle governance | Calibration, sensitivity, overfitting, retirement, and ensembles belong to research/optimization/governance and are outside the initial runtime slice. |
| REQ-STRAT-252 | Strategies shall declare assumptions for backup execution venues where applicable; backup venue failover enforcement remains owned by execution, live, or operations modules. | Reject | Execution/live/operations domains | Backup venue assumptions are not needed by a side-effect-free strategy decision layer in the initial scope. |
| REQ-STRAT-253 | Strategy-local state checkpoint and restore assumptions shall be defined for primary and backup instances. | Modify | CAP-STR-009 — Checkpoint and replay metadata | Keep strategy-local checkpoint compatibility assumptions; primary/backup instance orchestration is external. |
| REQ-STRAT-254 | Maximum tolerable strategy-local state loss and decision staleness shall be declared. | Add | CAP-STR-012 — Strategy declaration manifest | Declare maximum tolerable checkpoint loss and decision staleness only for stateful strategies. |
| REQ-STRAT-255 | Communication metadata for strategy degradation shall identify owner escalation paths; incident communications remain owned by operations. | Defer | Operations runbook metadata | Owner escalation and incident communications are external production documentation. |
| REQ-STRAT-256 | Market closure and early close strategy behavior shall be declared. | Add | CAP-STR-012 — Strategy declaration manifest | Market closure and early-close decision behavior is strategy-local metadata and suppression logic. |
| REQ-STRAT-257 | Emergency position liquidation assumptions may be documented, but official liquidation procedures and responsible-party approval remain owned by trading, risk, live, portfolio, compliance, or operations modules. | Reject | Trading/risk/live/operations domains | Official emergency liquidation cannot be a strategy responsibility. |
| REQ-STRAT-258 | Strategy performance review cadence and responsible parties shall be defined. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-259 | Automated performance attribution shall distinguish alpha, market exposure, and style factor contributions where applicable. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-260 | Strategy improvements shall support an A/B testing framework where applicable. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-261 | Shadow testing requirements shall be satisfied before production promotion. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-262 | Kill criteria shall define objective rules for permanent strategy decommissioning. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-263 | Post-mortem documentation shall be required for strategy failures. | Defer | External analytics and governance | Performance review, attribution, A/B testing, promotion, decommissioning, and post-mortems are not strategy runtime capabilities. |
| REQ-STRAT-264 | Strategy intellectual property classification and protection measures shall be documented. | Reject | Governance/legal domain | IP classification is an artifact-governance record, not strategy execution behavior. |
| REQ-STRAT-265 | Third-party dependency licensing compliance shall be verified. | Reject | Build/legal domain | Dependency license verification belongs to build and legal compliance. |
| REQ-STRAT-266 | Data vendor agreement compliance checks shall be performed where applicable. | Reject | Data/legal domain | Vendor agreement compliance belongs to data governance/legal. |
| REQ-STRAT-267 | Strategy descriptions shall be available for regulatory filings where applicable. | Reject | Compliance/reporting domain | Regulatory filing descriptions are external documentation artifacts. |
| REQ-STRAT-268 | Material change notification procedures to stakeholders shall be documented. | Reject | Governance domain | Stakeholder notification is change governance, not strategy runtime. |
| REQ-STRAT-269 | Strategy documentation retention periods shall be defined for regulatory inquiries. | Reject | Records-management domain | Retention periods are not strategy runtime behavior. |
| REQ-STRAT-270 | ML-based strategies shall load models exclusively from an approved, versioned model registry or approved local artifact store, not arbitrary file paths. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-271 | Model artifacts shall be serialized in standardized, language-agnostic formats such as `ONNX` or `PMML` where possible. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-272 | Strategies shall declare any dependency on a feature store. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-273 | Feature lookups shall be validated against the strategy's declared point-in-time correctness policy. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-274 | ML-based strategies shall implement concept drift and data drift detection where applicable. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-275 | Strategies shall emit `STRATEGY_DRIFT_DETECTED` when input feature distributions or model prediction confidence deviate beyond approved statistical thresholds. | Defer | Future ML strategy support | No confirmed ML strategy workflow exists for the initial rebuild; model registry and drift controls should be added only with an approved ML phase. |
| REQ-STRAT-276 | Strategies shall be prohibited from containing hardcoded secrets, API keys, or credentials. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Registered strategy artifacts must be credential-free. |
| REQ-STRAT-277 | Strategies requiring external configuration secrets shall request them through an approved read-only secrets manager interface injected at runtime by the orchestration layer. | Reject | CAP-STR-001 — Pure strategy decision boundary | Initial strategies receive prepared data and indicators and therefore need no secret manager or external credentials. |
| REQ-STRAT-278 | Strategies shall not log, serialize, checkpoint, or expose secrets in diagnostics, rationale, manifests, or state snapshots. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | Secrets must never appear in diagnostics, checkpoints, manifests, or rationales. |
| REQ-STRAT-279 | Any attempt by a strategy to read environment variables not explicitly allowlisted in the sandbox profile shall emit `STRATEGY_ENVIRONMENT_NOT_PERMITTED`. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Phase 1 prohibits all environment-variable reads; reject the module/config before execution instead of adding runtime secret access logic. |
| REQ-STRAT-280 | Strategies using Level 2 or Level 3 data shall declare their maximum supported order book depth. | Defer | Future L2/L3 strategy support | No confirmed order-book strategy workflow or downstream contract justifies this complexity in the initial rebuild. |
| REQ-STRAT-281 | Strategies shall not assume infinite liquidity at the best bid or ask. | Defer | Future L2/L3 strategy support | No confirmed order-book strategy workflow or downstream contract justifies this complexity in the initial rebuild. |
| REQ-STRAT-282 | Strategies may annotate intents with declared maximum volume participation assumptions for visible order book data at the decision timestamp; official sizing validation remains owned by risk, trading, simulation, or live execution modules. | Defer | Future L2/L3 strategy support | No confirmed order-book strategy workflow or downstream contract justifies this complexity in the initial rebuild. |
| REQ-STRAT-283 | Strategies shall declare behavior during `AUCTION_PHASE`, `TRADING_HALT`, `CROSSING_SESSION`, and `BROKEN_MARKET` microstructure events. | Defer | Future L2/L3 strategy support | No confirmed order-book strategy workflow or downstream contract justifies this complexity in the initial rebuild. |
| REQ-STRAT-284 | Strategies shall define deterministic behavior when order book data is crossed, locked, stale, incomplete, or outside the declared supported depth. | Defer | Future L2/L3 strategy support | No confirmed order-book strategy workflow or downstream contract justifies this complexity in the initial rebuild. |
| REQ-STRAT-285 | Each requirement shall be traceable to a specific test case id where implementation is required. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Every accepted implementation requirement needs a test or rationale; rejected and documentation-only items need explicit non-implementation rationale. |
| REQ-STRAT-286 | Major design-choice requirements shall be traceable to an Architecture Decision Record. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | Major design choices should link to ADRs without turning every requirement into an ADR. |
| REQ-STRAT-287 | The strategy domain requirements document shall be versioned using Semantic Versioning. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep documentation versioning and traceability for accepted scope; production sign-off actors remain a governance decision. |
| REQ-STRAT-288 | Breaking changes to strategy interfaces shall require a major document version bump and a documented migration guide. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep documentation versioning and traceability for accepted scope; production sign-off actors remain a governance decision. |
| REQ-STRAT-289 | A strategy shall not be considered production-ready until it passes applicable testing, validation, and runbook requirements. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Keep documentation versioning and traceability for accepted scope; production sign-off actors remain a governance decision. |
| REQ-STRAT-290 | Production-ready strategy approval shall require sign-off from the Quant Research Lead and Engineering Lead, or their approved delegates. | Open Decision | External governance sign-off | Named approval roles must be confirmed by the top-level governance model before becoming normative. |
| REQ-STRAT-291 | Strategies shall follow a standard processing anatomy: data input, indicator calculation, signal generation, timing alignment, trade intent creation, and simulation execution. | Modify | CAP-STR-004 — Vectorized strategy decision execution | Final anatomy is normalized data plus precomputed indicators, signal decision, timing alignment, intent creation, then external execution. |
| REQ-STRAT-292 | Vectorized strategies shall calculate indicators in a vectorized manner where supported by the indicator module. | Reject | Indicator domain | Indicator calculation internals are explicitly owned by the indicator module; strategy consumes vectorized outputs. |
| REQ-STRAT-293 | Vectorized strategies shall generate signals in a vectorized manner before conversion to timestamped `TradeIntent` objects. | Add | CAP-STR-004 — Vectorized strategy decision execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-294 | Vectorized processing shall not bypass tick-accurate simulation execution, fill modeling, accounting, margin checks, risk checks, or journal generation. | Keep | CAP-STR-001 — Pure strategy decision boundary | Vectorized decision generation must not bypass tick-accurate downstream execution and accounting. |
| REQ-STRAT-295 | Event strategies shall implement a standard lifecycle interface where applicable. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-296 | The standard event strategy lifecycle interface shall include hooks such as `on_init`, `on_start`, `on_bar`, `on_tick`, `on_fill_update`, `on_partial_fill`, `on_order_update`, `on_timer`, `on_error`, `on_checkpoint`, `on_restore`, and `on_stop`. | Modify | CAP-STR-005 — Stateful event strategy execution | Define a minimal lifecycle with required `on_init` plus applicable event hooks; do not mandate every proposed hook for every strategy. |
| REQ-STRAT-297 | Hook inputs and outputs shall be typed and schema-documented. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-298 | Strategy hooks shall return only approved strategy outputs, including decisions, diagnostics, state updates, or `TradeIntent` objects. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-299 | Strategy hooks shall not mutate official simulation, execution, account, order, position, journal, or reporting state directly. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-300 | Hook execution order shall be deterministic and documented for vectorized runs, event-driven runs, replay, checkpoint restore, and shutdown. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-301 | Required and optional hooks shall be explicitly declared by strategy type. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-302 | Unsupported hooks for a strategy type shall fail deterministically or be ignored according to the approved interface contract. | Add | CAP-STR-005 — Stateful event strategy execution | V1 lifecycle and signal processing are fragmented; the final anatomy needs one typed deterministic contract per strategy type. |
| REQ-STRAT-303 | Strategy code shall pass the project's configured type checker, expose public interfaces with docstrings or generated API documentation, avoid nondeterministic decision inputs except simulation-provided seeded randomness, and include linked unit or contract tests for each public strategy behavior. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | Type checking, public documentation, determinism, and linked tests are necessary acceptance conditions. |
| REQ-STRAT-304 | Strategy APIs shall remain separate from simulation execution services. | Keep | CAP-STR-001 — Pure strategy decision boundary | Strategy APIs remain separate from simulation execution. |
| REQ-STRAT-305 | Strategies shall use indicator module contracts for indicator-derived inputs. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Consume indicator contracts or precomputed outputs; do not calculate indicators inside strategy. |
| REQ-STRAT-306 | Strategies shall use data module contracts for normalized market data. | Keep | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Normalized market data must come from the data domain. |
| REQ-STRAT-307 | Strategies shall return safe, deterministic errors for invalid configuration or unsupported inputs. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-308 | Strategies shall not perform production `print()` output. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-309 | Strategy imports shall be side-effect safe and shall not perform broker calls, network access, filesystem writes, subprocess execution, environment mutation, or decision-time clock/randomness reads. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | V1 violates this through global storage directory creation and dynamic filesystem imports; imports must become side-effect safe. |
| REQ-STRAT-310 | Strategy execution shall define measurable latency, memory, checkpoint-size, diagnostic-payload-size, event-queue, timeout, and retry-exhaustion limits per supported environment before implementation acceptance. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | Limits are required, but exact values and retry behavior need workload and host measurements. |
| REQ-STRAT-311 | Provisional v1.0 baseline: event-driven strategy decision latency shall target P99 <= 10 ms per event on the approved reference environment unless a stricter registry profile is approved. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | The proposed 10 ms P99 target has no measured reference environment in the supplied evidence. |
| REQ-STRAT-312 | Provisional v1.0 baseline: vectorized batch strategy execution shall target P99 <= 500 ms for the approved benchmark batch profile unless a stricter registry profile is approved. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | The proposed 500 ms batch P99 target lacks a defined benchmark batch profile. |
| REQ-STRAT-313 | Provisional v1.0 baseline: each strategy instance shall target memory usage <= 256 MB, checkpoint size <= 10 MB, diagnostic payload <= 64 KB per decision, configuration payload <= 64 KB, and dependency call timeout <= 2 seconds unless an approved registry profile overrides the value. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | The proposed memory, checkpoint, diagnostic, config, and timeout values are provisional and unvalidated. |
| REQ-STRAT-314 | Provisional v1.0 baseline: performance tests shall define reference hardware, operating system, Python version, dependency versions, dataset size, strategy type, and measurement method before targets are accepted in CI. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | Benchmark conditions must be explicit before any quantitative target is accepted. |
| REQ-STRAT-315 | Strategy execution shall define deterministic backpressure behavior when event volume exceeds configured capacity. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Execution host owns queues/backpressure; strategy receives bounded events and returns deterministic timeout or skipped-decision diagnostics. |
| REQ-STRAT-316 | Strategy diagnostics shall enforce redaction, maximum payload size, and structured schema validation. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-317 | Strategy APIs shall remain backward compatible within a major interface version. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-318 | Strategy modules shall be deterministic under repeated execution with the same seed, inputs, configuration, indicator outputs, and environment policy. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-319 | `ASYNC_AWAIT` strategies shall define an approved async compatibility contract and shall not block the event loop. | Defer | Future async strategy profile | Initial execution is synchronous; async compatibility adds unproven complexity. |
| REQ-STRAT-320 | `SYNC_BLOCKING` strategies shall define maximum call duration and isolation expectations before being used in shared event loops. | Modify | CAP-STR-011 — Registered-only security, resource, and determinism controls | Initial `SYNC_BLOCKING` execution must have a host-enforced duration budget and isolation policy. |
| REQ-STRAT-321 | `MULTIPROCESS_ISOLATED` strategies shall define serialization, timeout, cancellation, restart, and resource-limit behavior. | Defer | Future multiprocess strategy profile | Serialization, restart, and process limits belong to a later orchestration capability. |
| REQ-STRAT-322 | Randomized strategies shall use only the approved simulation-provided seeded randomness interface; direct use of process-global randomness is prohibited unless explicitly wrapped by that interface. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | These quality, determinism, and boundary constraints are largely absent from V1 and are required for a safe contract. |
| REQ-STRAT-323 | Strategy dependency calls to data, indicator, simulation, or read-only state providers shall define timeout, retry/no-retry, stale result, partial failure, and exception mapping behavior. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Strategy should not directly call data or indicator services; boundary callers map prepared-input and dependency failures into strategy diagnostics. |
| REQ-STRAT-324 | Unknown strategy id shall fail before execution. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-325 | Empty strategy identifier shall fail before execution with a deterministic validation error. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-326 | Unapproved strategy module shall fail before execution. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-327 | Invalid strategy configuration schema shall fail before execution. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-328 | Null or missing strategy configuration shall either apply schema defaults or fail according to the registry entry's configuration policy. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-329 | Unknown configuration fields shall be rejected or ignored according to an explicit schema policy. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-330 | Unsupported strategy version or unsatisfiable version constraint shall fail before execution. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-331 | Duplicate registry entry for the same strategy id/version shall fail registry validation. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-332 | Malformed registry configuration schema shall fail registry validation with `STRATEGY_INVALID_CONFIG`. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-333 | Raw arbitrary Python strategy code strings shall be rejected before execution. | Add | CAP-STR-011 — Registered-only security, resource, and determinism controls | This directly removes V1 dynamic raw-code execution from the initial rebuild. |
| REQ-STRAT-334 | Missing sandbox or vetting metadata for a code-based strategy path shall fail before execution. | Defer | Future sandbox capability | Sandbox metadata is irrelevant while code-based execution remains disabled. |
| REQ-STRAT-335 | Unsafe rejected code bodies shall not be logged in full. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-336 | Empty market-data input shall produce `STRATEGY_DATA_NOT_READY` or a more specific deterministic error. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-337 | Data-service timeout, unavailable dependency, broken connection, or network partition shall produce `STRATEGY_DATA_NOT_READY` after the approved retry/no-retry policy is exhausted. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The caller maps data dependency failures before or at the strategy boundary; strategy does not own network retry loops. |
| REQ-STRAT-338 | Indicator module timeout, unavailable dependency, broken connection, or unhandled indicator exception shall map to `INDICATOR_MODULE_ERROR` with original exception details redacted. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The caller maps indicator dependency failures; strategy consumes prepared indicator results and redacted dependency status. |
| REQ-STRAT-339 | Partial data degradation shall follow the strategy's declared missing-data policy: `reject` suppresses all intents, `skip signal` suppresses affected symbols, and any degraded subset execution shall emit `STRATEGY_DATA_QUALITY_GATE_FAILED` diagnostics naming omitted symbols without exposing private payloads. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-340 | Timezone-naive, DST-ambiguous, or timezone-inconsistent data shall fail unless an approved normalization policy exists. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Data module normalizes timestamps; strategy rejects inputs marked naive, ambiguous, or inconsistent with its declared contract. |
| REQ-STRAT-341 | Clock drift beyond the approved tolerance between strategy runtime, data feed, indicator outputs, or simulation clock shall fail closed with `STRATEGY_STALE_DATA`, checkpoint abort, or a more specific approved error code. | Modify | CAP-STR-007 — Timing, readiness, and no-lookahead validation | Strategy compares supplied timestamps to the fixed decision clock; system clock synchronization is external. |
| REQ-STRAT-342 | Clock drift detected during a long-running vectorized batch shall not change the batch decision timestamp; the batch shall either complete under the original timestamp or fail atomically according to the configured clock-drift policy. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-343 | Duplicate, out-of-order, stale, revised, or late-arriving ticks shall follow the declared data policy. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-344 | Strategy hook timeout shall return `STRATEGY_TIMEOUT` and follow the configured failure policy. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The execution host enforces timeout and returns the canonical strategy timeout diagnostic. |
| REQ-STRAT-345 | Checkpoint restore with unsupported schema version, checksum mismatch, or unauthorized source shall fail before execution. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-346 | Duplicate `intent_id`, duplicate idempotency key, or non-monotonic strategy-local sequence number shall fail deterministically. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-347 | Sandbox approval expiry shall cause code-based strategy execution to fail before execution. | Defer | Future sandbox capability | No sandbox execution is accepted in the initial rebuild. |
| REQ-STRAT-348 | Attempted secret exposure in diagnostics, checkpoints, manifests, or rationale shall fail redaction validation. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-349 | Simultaneous events for a single strategy instance shall be processed in a stable documented order, such as timestamp, event type priority, then deterministic sequence number. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The final domain needs deterministic validation and failure outcomes rather than V1 logging and low-level exceptions. |
| REQ-STRAT-350 | Concurrent read-only state snapshots across multiple strategies shall define isolation level, snapshot timestamp, and behavior when official state updates during decision traversal. | Modify | CAP-STR-008 — Read-only external state and strategy-local decision state | Snapshot isolation and timestamp are required contract fields; official update behavior remains owned by the snapshot provider. |
| REQ-STRAT-351 | `STRATEGY_INVALID_CONFIG` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-352 | `STRATEGY_NOT_FOUND` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-353 | `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-354 | `STRATEGY_DEPRECATED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-355 | `STRATEGY_UNAPPROVED_MODULE` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-356 | `STRATEGY_SCHEMA_VALIDATION_FAILED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-357 | `STRATEGY_UNSUPPORTED_TIMING_POLICY` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-358 | `STRATEGY_LOOKAHEAD_DETECTED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-359 | `SIM_ARBITRARY_CODE_REJECTED` | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Retain the rejection scenario but rename the code to the strategy domain; `SIM_ARBITRARY_CODE_REJECTED` is cross-domain leakage. |
| REQ-STRAT-360 | `STRATEGY_SANDBOX_REQUIRED` | Defer | Future sandbox capability | No sandbox path exists in the initial registered-only design. |
| REQ-STRAT-361 | `STRATEGY_INTERNAL_ERROR` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-362 | `STRATEGY_LIFECYCLE_NOT_APPROVED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-363 | `STRATEGY_ENVIRONMENT_NOT_PERMITTED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-364 | `STRATEGY_ARTIFACT_HASH_MISMATCH` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-365 | `STRATEGY_DEPENDENCY_HASH_MISMATCH` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-366 | `INDICATOR_MODULE_ERROR` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-367 | `STRATEGY_CHECKPOINT_INVALID` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-368 | `STRATEGY_CHECKPOINT_INCOMPATIBLE` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-369 | `STRATEGY_DATA_NOT_READY` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-370 | `STRATEGY_INDICATOR_NOT_READY` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-371 | `STRATEGY_MISSING_REQUIRED_DATA` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-372 | `STRATEGY_STALE_DATA` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-373 | `STRATEGY_DUPLICATE_INTENT` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-374 | `STRATEGY_RESOURCE_LIMIT_EXCEEDED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-375 | `STRATEGY_TIMEOUT` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-376 | `STRATEGY_VALIDATION_ARTIFACT_REQUIRED` | Modify | CAP-STR-003 — Approved immutable registry and configuration validation | Require this code only when the selected lifecycle policy mandates a validation artifact. |
| REQ-STRAT-377 | `STRATEGY_RISK_PROFILE_REQUIRED` | Modify | CAP-STR-012 — Strategy declaration manifest | Use only for strategies whose registry schema requires risk declarations; do not require a full risk profile for every simple strategy. |
| REQ-STRAT-378 | `STRATEGY_CIRCUIT_BREAKER_TRIGGERED` | Defer | External circuit-breaker enforcement | Circuit breakers are owned by orchestration/risk/live; strategy may later emit a local suppression diagnostic. |
| REQ-STRAT-379 | `STRATEGY_POSITION_LIMIT_EXCEEDED` | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Use for strategy-local declared limits only; official position-limit errors belong to risk or portfolio. |
| REQ-STRAT-380 | `STRATEGY_VOLUME_PARTICIPATION_EXCEEDED` | Defer | Future execution-participation support | No accepted participation-rate execution contract exists. |
| REQ-STRAT-381 | `STRATEGY_DATA_QUALITY_GATE_FAILED` | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The code is needed only if a retained capability can trigger it; the final error catalogue should be smaller than the proposal. |
| REQ-STRAT-382 | `STRATEGY_PERFORMANCE_DEGRADED` | Defer | External analytics/operations | Performance degradation detection requires analytics and monitoring inputs outside the initial runtime. |
| REQ-STRAT-383 | `STRATEGY_DRIFT_DETECTED` | Defer | Future ML strategy support | Drift diagnostics activate only with an approved ML capability. |
| REQ-STRAT-384 | `STRATEGY_REGULATORY_LIMIT_BREACHED` | Reject | Compliance/risk domain | Official regulatory-limit breaches are not strategy-owned errors. |
| REQ-STRAT-385 | `STRATEGY_MARKET_ACCESS_REVOKED` | Reject | Execution/compliance domain | Market-access revocation is external; strategy receives environment/lifecycle ineligibility. |
| REQ-STRAT-386 | `STRATEGY_HARD_KILLED` | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | The execution host emits this when it force-stops a strategy; it is not a self-generated strategy action. |
| REQ-STRAT-387 | Every requirement id shall have at least one linked test id or a documented non-implementation rationale. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Every accepted implementation requirement needs linked tests; rejected, deferred, and documentation-only requirements need an explicit rationale instead. |
| REQ-STRAT-388 | Every public capability shall have contract tests for valid input, invalid input, deterministic errors, idempotency, and side effects. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-389 | Every confirmed error code shall have at least one focused failure-path test that triggers the code and verifies the full response or diagnostic shape. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Focused tests are required for the reduced accepted error catalogue, not for rejected or deferred codes. |
| REQ-STRAT-390 | Every usage example shall be executable or schema-validatable as documentation test coverage. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-391 | The traceability matrix shall be tested or reviewed as an explicit pre-implementation deliverable. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-392 | Public capability tests shall verify exact Python signatures, input schema validation, output schema validation, error decision tables, side-effect rules, and batch/stream behavior. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-393 | Performance tests shall state the exact hardware/software environment, dataset size, strategy type, dependency versions, measurement method, and target thresholds used. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-394 | Strategy tests shall cover vectorized signal strategies. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-395 | Strategy tests shall cover stateful event strategies. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-396 | Strategy tests shall cover EMA trend intents, martingale recovery, decomposition child orders, and partial-fill handling. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Cover representative vectorized and advanced event strategies, including fill updates; do not hard-code a permanent list of named example strategies. |
| REQ-STRAT-397 | Strategy tests shall cover previous-closed-bar signal timing and no-lookahead behavior. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-398 | Strategy tests shall verify indicator-derived signals cannot access prohibited current-bar values. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-399 | Strategy registry tests shall verify registered strategy identifiers resolve to approved modules. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-400 | Strategy registry tests shall verify unregistered strategy identifiers are rejected. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-401 | Strategy registry tests shall verify unapproved modules are rejected. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-402 | Strategy configuration tests shall verify valid schemas pass and invalid schemas fail deterministically. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-403 | AI Tool strategy security tests shall verify `run_backtest` rejects raw arbitrary Python strategy code, returns `SIM_ARBITRARY_CODE_REJECTED`, does not execute rejected code, and does not log rejected code in full. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Test raw-code rejection at the strategy registry/orchestration boundary and assert the renamed strategy-domain error code. |
| REQ-STRAT-404 | Replay tests shall verify the same strategy id, version, configuration, input data, indicator outputs, and simulation seed produce the same trade intents. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-405 | Strategy tests shall include golden-file replay tests for emitted `TradeIntent` manifests. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-406 | Strategy tests shall include property-based tests for no-lookahead, deterministic replay, and risk-envelope invariants. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Use property-based tests for no-lookahead, determinism, and identity invariants where they add value; risk-engine invariants are external. |
| REQ-STRAT-407 | Property-based no-lookahead tests shall cover timezone offsets, DST gaps, DST overlaps, session boundaries, late-arriving data, revised bars, and multi-timeframe closure boundaries. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-408 | Strategy tests shall include fuzz tests for invalid configuration, malformed data, missing fields, duplicate ticks, out-of-order ticks, NaN indicators, and extreme prices. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-409 | Strategy tests shall include stress tests for large histories, many symbols, dense tick streams, and high-frequency event dispatch. | Open Decision | CAP-STR-014 — Strategy examples, documentation, and traceability | Stress profiles depend on unresolved capacity assumptions for symbols, history, ticks, and concurrent strategies. |
| REQ-STRAT-410 | Strategy tests shall include performance regression tests with approved latency and memory thresholds. | Defer | CAP-STR-014 — Strategy examples, documentation, and traceability | Performance regression thresholds cannot be enforced until the benchmark and targets are approved. |
| REQ-STRAT-411 | Strategy tests shall include contract tests against data, indicator, simulation, and registry interfaces. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-412 | Strategy tests shall include snapshot tests verifying stable intent ids, decision ids, configuration hashes, and replay manifests. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-413 | Strategy tests shall include scenario tests for session boundaries, holidays, weekend gaps, DST transitions, spread spikes, partial fills, rejected fills, and multi-timeframe bar closure. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Test strategy boundary behavior for these scenarios; matching, fill rejection, holidays, and spread execution details remain simulation/data responsibilities. |
| REQ-STRAT-414 | Strategy tests shall include mutation testing to verify that deliberate subtle corruptions to strategy logic or data inputs are caught by the test suite. | Defer | CAP-STR-014 — Strategy examples, documentation, and traceability | Mutation testing may be introduced after core contract and workflow tests are stable. |
| REQ-STRAT-415 | Strategy tests shall include chaos engineering scenarios, including simulated data-feed disconnections, sudden latency spikes, and out-of-order message injection during event processing. | Reject | Cross-domain integration/operations testing | Chaos injection into feeds and messaging is not a strategy unit-test responsibility. |
| REQ-STRAT-416 | Strategy tests shall verify memory leak detection over extended event-loop iterations and assert stable memory usage within approved thresholds. | Defer | CAP-STR-014 — Strategy examples, documentation, and traceability | Extended memory-leak testing depends on the final event host and measured resource budgets. |
| REQ-STRAT-417 | Boundary tests shall verify strategies cannot mutate official account, order, deal, position, margin, equity, journal, reporting, or execution timestamp state. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-418 | Boundary tests shall verify strategies cannot create fills, deals, official orders, reports, or journal events directly. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-419 | Boundary tests shall verify portfolio, compliance, disaster-recovery, deployment, and venue requirements are exposed only as declarations or metadata, not enforced inside the strategy module. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Boundary tests should prove declarations remain metadata; external domains own enforcement. |
| REQ-STRAT-420 | Security tests shall verify strategy imports perform no broker calls, network calls, filesystem writes, subprocess calls, environment mutation, or secret reads. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-421 | Security tests shall cover configuration-injection payloads, oversized configuration payloads, excessive nesting, excessive string lengths, and resource exhaustion through sanctioned strategy and indicator paths. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-422 | Error-code tests shall verify lower-level lookahead errors map to `STRATEGY_LOOKAHEAD_DETECTED` at strategy-module boundaries. | Add | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Lookahead errors must be normalized at the strategy boundary. |
| REQ-STRAT-423 | Dependency-failure tests shall verify data-layer failures map to `STRATEGY_DATA_NOT_READY` or approved data errors and indicator-layer failures map to `INDICATOR_MODULE_ERROR`. | Modify | CAP-STR-010 — Structured diagnostics and deterministic error mapping | Test caller-to-strategy error mapping using prepared dependency-status inputs, not direct strategy service calls. |
| REQ-STRAT-424 | Clock-drift tests shall verify behavior when strategy, data, indicator, or simulation timestamps exceed approved tolerance. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-425 | Concurrency tests shall verify read-only state snapshot isolation and stable event ordering for simultaneous events. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-426 | Replay tests shall verify historical interface versions are used unless an approved migration exists. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Retain tests for accepted contracts and workflows; reject or defer tests for capabilities outside the initial strategy scope. |
| REQ-STRAT-427 | Documentation shall include strategy registry behavior. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | Registry behavior is a required final README topic. |
| REQ-STRAT-428 | Documentation shall include strategy input modes approved for `run_backtest`. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Document registered identifier/config input only; code input is not approved. |
| REQ-STRAT-429 | Documentation shall state that raw arbitrary Python strategy code is not accepted by `run_backtest`. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | The final README and handoff require these domain-boundary, usage, replay, and contract explanations. |
| REQ-STRAT-430 | Documentation shall include configuration schema requirements for registered strategies. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | The final README and handoff require these domain-boundary, usage, replay, and contract explanations. |
| REQ-STRAT-431 | Documentation shall describe sandbox and vetting requirements if code-based strategy execution is ever enabled. | Defer | CAP-STR-014 — Strategy examples, documentation, and traceability | Document sandbox/vetting only when a future code-based workflow is approved. |
| REQ-STRAT-432 | Documentation shall describe no-lookahead strategy timing. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | The final README and handoff require these domain-boundary, usage, replay, and contract explanations. |
| REQ-STRAT-433 | Documentation shall include examples for vectorized signal strategies and event-driven strategies. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | The final README and handoff require these domain-boundary, usage, replay, and contract explanations. |
| REQ-STRAT-434 | Documentation shall describe strategy replay metadata. | Add | CAP-STR-014 — Strategy examples, documentation, and traceability | The final README and handoff require these domain-boundary, usage, replay, and contract explanations. |
| REQ-STRAT-435 | Documentation shall include public capability contracts, requirement IDs, applicability tags, acceptance criteria, and linked test IDs before Builder handoff. | Modify | CAP-STR-014 — Strategy examples, documentation, and traceability | Document accepted capability contracts, requirement IDs, acceptance criteria, applicability, and test links; excluded requirements retain disposition rationales here. |
| REQ-STRAT-436 | Strategy implementations target Python. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | This is a planning or platform assumption that should remain explicit until system alignment resolves it. |
| REQ-STRAT-437 | Official execution remains owned by the simulation module. | Modify | CAP-STR-001 — Pure strategy decision boundary | Simulation is the official executor for simulated workflows only; live or paper execution authority is resolved by the wider system, never by strategy. |
| REQ-STRAT-438 | Indicator calculations are owned by the indicator module. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | This is a planning or platform assumption that should remain explicit until system alignment resolves it. |
| REQ-STRAT-439 | Data normalization and source-readiness rules are owned by the data module. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | This is a planning or platform assumption that should remain explicit until system alignment resolves it. |
| REQ-STRAT-440 | Technology stack version constraints shall be explicit for production-eligible strategy execution. | Open Decision | CAP-STR-013 — Approved artifact integrity metadata | Production technology versions must be fixed by the project environment and build pipeline. |
| REQ-STRAT-441 | Third-party service dependencies shall be declared before production-eligible strategy execution. | Modify | CAP-STR-012 — Strategy declaration manifest | Declare third-party dependencies in approved artifact metadata; strategy runtime does not call arbitrary services. |
| REQ-STRAT-442 | Capacity assumptions shall include maximum supported symbols and maximum concurrent strategies. | Open Decision | CAP-STR-011 — Registered-only security, resource, and determinism controls | Maximum symbols and concurrent strategies require system-level capacity and benchmark decisions. |
| REQ-STRAT-443 | Assumption: This document remains a domain-level requirements source until the active roadmap approves Strategy implementation scope. | Keep | CAP-STR-014 — Strategy examples, documentation, and traceability | This is a planning or platform assumption that should remain explicit until system alignment resolves it. |

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
| --- | --- | --- | --- | --- | --- | --- |
| WF-STR-001 | Validate strategy reference and configuration | Internal | Missing; V1 registry lookup is partial | `validate_strategy_ref` and `validate_strategy_config` | Add | Input ref/config → strategy validates immutable registry, lifecycle, environment, module, schema, and hashes → validated reference/config or deterministic diagnostic. |
| WF-STR-002 | Generate vectorized strategy decisions | Cross-domain | V1-WF-STRATEGY-001 working but signal-column based | `run_vectorized_strategy_signals` | Replace | Normalized data + indicator outputs + validated ref/config/context → strategy performs atomic timing/readiness checks and signal logic → ordered TradeIntent batch, diagnostics, optional local state → simulation/research. |
| WF-STR-003 | Run stateful event strategy hook | Cross-domain | V1-WF-STRATEGY-002 working but fragmented | `run_event_strategy_hook` | Replace | Typed event + immutable read-only snapshot + context + local state → strategy applies one deterministic hook → intents, diagnostics, atomic state update/checkpoint request → simulation/orchestration. |
| WF-STR-004 | Build and hand off TradeIntent | Cross-domain | Missing canonical contract; V1 uses SignalDict/TradeAction | `build_trade_intent` | Add | Validated strategy decision metadata → strategy builds deterministic schema-valid intent and lineage → downstream runtime owns sizing, risk, matching, fills, and official state. |
| WF-STR-005 | Create replay manifest and checkpoint | Internal / Cross-domain | Missing; V1 only stores code/metadata | `create_strategy_replay_manifest` | Add | Validated ref/config hashes + input checksums + indicator manifest + seed/interface/timing → strategy emits replay manifest and optional bounded checkpoint → simulation/research/audit store references. |
| WF-STR-006 | Export structured diagnostics | Cross-domain | Partial through logs and wrapper envelopes | `export_strategy_diagnostics` | Add | Execution context + bounded details + redaction policy → strategy returns schema-valid diagnostics/metrics → orchestration, simulation, audit, and observability consume them. |
| WF-STR-007 | Consume strategy decisions in paper/live runtime | Cross-domain | V1-WF-STRATEGY-003 working through SignalProcessor | V2 says simulation owns official execution | Modify | Prepared live/paper data + validated strategy → strategy emits TradeIntent only → runtime-specific trading/risk/live authority handles official actions. Exact downstream owner is escalated. |
| WF-STR-008 | Register and approve immutable strategy version | Cross-domain | V1-WF-STRATEGY-004 mutable DB/filesystem/governance sequence | Registry, lifecycle, artifact hashes, approved modules | Replace | External build/catalog/governance produces approved artifact metadata → strategy registry validates and exposes immutable entry → execution resolves by id/version only. Mutable CRUD stays outside strategy. |
| WF-STR-009 | Reject arbitrary strategy code | Cross-domain | V1-WF-STRATEGY-005 dynamically executes stored Python | Registered-only phase and sandbox deferral | Replace | Raw code/path/archive input → registry/security validation rejects before import/execution and emits redacted strategy-domain diagnostic → audit/orchestration may persist the event. |

### `WF-STR-001` — Validate Strategy Reference and Configuration

**Scope:** `Internal`

**V1 behaviour:**

```text
Name lookup in a mutable process-local registry; configuration validation is strategy-specific or absent.
```

**V2 proposal:**

```text
Resolve an immutable id/version constraint, then validate a versioned configuration schema and lifecycle/environment eligibility.
```

**Final decision:**

```text
Add one validation workflow. It returns a validated immutable reference/config or a deterministic diagnostic and performs no execution.
```

**Reason:**

V1 registry lookup is useful but insufficient for immutable version, schema, lifecycle, environment, and hash validation.

### `WF-STR-002` — Generate Vectorized Strategy Decisions

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Simulation loads bars, resolves a class, calls `on_init()` and `on_bar()`, then downstream code interprets signal columns.
```

**V2 proposal:**

```text
Run a batch strategy with normalized data, precomputed indicators, fixed decision context, no-lookahead checks, and typed TradeIntent output.
```

**Final decision:**

```text
Replace the DataFrame signal-column boundary while reusing proven vectorized signal logic. Strategy does not calculate indicator internals or execute trades.
```

**Reason:**

The signal logic is proven; the DataFrame-column boundary is not a safe final cross-domain contract.

### `WF-STR-003` — Run Stateful Event Strategy Hook

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
The event-driven simulator builds `StrategyContext`, calls `on_event()`, and applies returned `TradeAction` objects; lifecycle types are split across domains.
```

**V2 proposal:**

```text
Invoke named typed hooks using immutable read-only state snapshots and return intents, diagnostics, and atomic local-state updates.
```

**Final decision:**

```text
Replace the split lifecycle with one minimal typed event protocol. Simulation remains the official state and fill authority for simulated runs.
```

**Reason:**

Advanced strategy value is proven, but direct runtime context and split lifecycle ownership must be removed.

### `WF-STR-004` — Build and Hand Off TradeIntent

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1 emits `SignalDict` or `TradeAction`; identity, idempotency, partial-fill preference, and lineage are inconsistent or absent.
```

**V2 proposal:**

```text
Build deterministic versioned TradeIntent objects from validated decisions.
```

**Final decision:**

```text
Add a pure builder. Input boundary → strategy decision metadata. Domain responsibility → validate and identify the intent. Output boundary → downstream runtime consumes but strategy never sizes or executes officially.
```

**Reason:**

A canonical intent is the smallest safe boundary between strategy decisions and downstream execution.

### `WF-STR-005` — Create Replay Manifest and Checkpoint

**Scope:** `Internal / Cross-domain`

**V1 behaviour:**

```text
V1 has mutable strategy dictionaries and file version metadata but no deterministic replay package.
```

**V2 proposal:**

```text
Hash strategy/config/data/indicator/simulation inputs and serialize bounded strategy-local state.
```

**Final decision:**

```text
Add replay metadata and optional checkpoint support. Persistence of manifests/checkpoints is external.
```

**Reason:**

Replay and state recovery require exact identity and input lineage that V1 storage does not provide.

### `WF-STR-006` — Export Structured Diagnostics

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
V1 mainly logs and sometimes returns generic standard envelopes.
```

**V2 proposal:**

```text
Return a redacted, bounded, versioned StrategyDiagnostics payload with stable codes and trace identifiers.
```

**Final decision:**

```text
Add one diagnostics contract and remove import-path-dependent wrapper semantics.
```

**Reason:**

Structured diagnostics replace V1 log dependence and package-wrapper ambiguity.

### `WF-STR-007` — Consume Decisions in Paper or Live Runtime

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
SignalProcessor calls `on_bar()`/`get_signal()` and returns SignalDict to live execution code.
```

**V2 proposal:**

```text
The strategy layer remains runtime-neutral and emits TradeIntent; execution ownership is environment-specific.
```

**Final decision:**

```text
Modify, not remove, the proven workflow. The final downstream owner and environment scope require system-level alignment.
```

**Reason:**

The existing live decision path provides value, while official execution must remain external and system-aligned.

### `WF-STR-008` — Register and Approve Immutable Strategy Version

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
API routes coordinate mutable database rows, files, archives, and governance updates without atomicity.
```

**V2 proposal:**

```text
Approved modules and artifacts are built and governed externally; strategy registry stores immutable references, hashes, lifecycle, schemas, and manifests.
```

**Final decision:**

```text
Replace mutable artifact CRUD inside strategy. Preserve identity/version metadata and registry lookup.
```

**Reason:**

Artifact persistence and approval are distinct from strategy execution and should not remain coupled in one storage class.

### `WF-STR-009` — Reject Arbitrary Strategy Code

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Stored Python is imported and executed dynamically through `importlib`.
```

**V2 proposal:**

```text
Phase 1 permits registered approved modules and typed configuration only; sandbox is deferred.
```

**Final decision:**

```text
Replace dynamic loading with pre-execution rejection. Inventory and migrate required stored strategies before removing V1 loaders.
```

**Reason:**

V1 dynamic imports contradict the proposed side-effect-free and registered-only security boundary.

## 8. Recommended Minimal Capability Structure

The package root is provisional pending the package-location open decision. The capability layout below assumes the V2 root for illustration only.

```text
tools/strategies/                 # Provisional domain package root
├── contracts/                    # Versioned schemas, results, and domain errors
├── registry/                     # Approved refs, manifests, config, lifecycle/environment validation
├── vectorized/                   # Atomic batch strategy decisions and timing/readiness checks
├── event/                        # Typed event hooks, immutable snapshots, local state updates
├── intents/                      # TradeIntent building, identity, idempotency, and lineage
├── replay/                       # Replay manifests and strategy-local checkpoints
└── diagnostics/                  # Structured diagnostics, redaction, metrics, error mapping
```

| Module | Capability | Source | Main decision |
| --- | --- | --- | --- |
| `contracts/` | Versioned public schemas and deterministic result/error contracts | Both | Modify |
| `registry/` | Immutable strategy resolution, configuration validation, manifests, lifecycle/environment gating | Both | Modify |
| `vectorized/` | Vectorized deterministic strategy decisions and no-lookahead batch validation | Both | Modify |
| `event/` | Stateful event lifecycle over immutable read-only snapshots | Both | Modify |
| `intents/` | Canonical TradeIntent construction, identity, idempotency, lineage | V2 with V1 field reuse | Add |
| `replay/` | Replay manifests and bounded strategy-local checkpoints | V2 | Add |
| `diagnostics/` | Structured redacted diagnostics, metrics, deterministic error mapping | Both | Add / Replace wrappers |

No initial `storage/`, `sandbox/`, `services/`, `managers/`, `handlers/`, `factories/`, `repositories/`, `ports/`, `adapters/`, or command layers are recommended inside the strategy package. Artifact persistence, sandboxing, orchestration, execution, and governance remain external or deferred.

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
| --- | --- | --- | --- | --- |
| 1 | `registry.py` and nine built-in registrations | Refactor | CAP-STR-003 | Registry resolution tests for every approved id/version; duplicate, lifecycle, environment, and config failures. |
| 2 | `BaseStrategy.on_bar()` and built-in vectorized signal logic | Refactor | CAP-STR-004 | Golden no-lookahead intent batches; equivalence tests for representative strategies. |
| 3 | `stateful_common.py` snapshot/basket helpers and advanced strategies | Refactor | CAP-STR-005 / CAP-STR-008 | Immutable snapshot tests, partial-fill progression, atomic local-state updates, deterministic ordering. |
| 4 | `SignalDict`, `TradeAction`, `get_signal()` fields | Replace contract; reuse semantics | CAP-STR-006 | TradeIntent schema, stable IDs, lineage, sizing-hint boundary, partial-fill fields. |
| 5 | Package wrappers and broad logging/error handling | Replace | CAP-STR-002 / CAP-STR-010 | Exact signatures, typed schemas, redaction, error-map, no raw/enveloped import difference. |
| 6 | `StrategyStorage` registry metadata and hashes | Split and migrate | CAP-STR-003 / CAP-STR-013 | Catalog ownership, migration completeness, immutable version lookup, hash verification. |
| 7 | `load_strategy_class()` and raw archive import | Remove / Defer | CAP-STR-011 | Inventory stored strategies; prove registered equivalents exist; assert raw code is never imported. |
| 8 | `TemplateStrategy` and usage examples | Refactor | CAP-STR-014 | Executable vectorized and event examples using final contracts; remove stale pybots imports. |
| 9 | Replay/checkpoint, diagnostics, identity, readiness | New | CAP-STR-006 to CAP-STR-010 | Contract, property, replay, security, and cross-domain boundary tests. |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
| --- | --- | --- |
| Flat `registry.py`, `protocols.py`, `errors.py`, `vectorized.py`, `event.py`, `sandbox.py` prescription | Mixes capability files at package root and introduces sandbox before approval | Use capability modules; integrate errors into contracts/diagnostics; omit sandbox from initial rebuild. |
| Arbitrary sandboxed user code path | No approved sandbox, vetting workflow, or demonstrated need; V1 proves the risk | Registered approved modules plus typed configuration only. Defer sandbox as a separate future capability. |
| Strategy-owned indicator calculation | Conflicts with stated indicator-domain ownership and duplicates indicator logic | Consume versioned precomputed indicator outputs and readiness metadata. |
| Mutable file storage, archive import/export, and dynamic class loading in strategy | Creates filesystem side effects, arbitrary execution, and catalog inconsistency | Registry stores immutable approved references/hashes; external artifact/catalog domain owns persistence. |
| Dozens of separate risk, execution, portfolio, operations, compliance, and data declarations | Would produce a bloated mandatory schema and duplicate external domains | One versioned manifest with core required fields and optional applicability-scoped metadata. |
| Complete governance, validation, regulatory, DR, legal, deployment, and monitoring enforcement | Belongs to other domains and has no initial strategy workflow | Keep references/declarations only where strategy decisions need them; reject or defer external enforcement. |
| SYNC, ASYNC, and MULTIPROCESS execution profiles in phase 1 | Three execution models multiply contracts, cancellation, serialization, and tests without evidence | Start with bounded synchronous execution; defer async and multiprocess profiles. |
| All 36 proposed error codes as mandatory | Many correspond to rejected/deferred external capabilities | Implement a smaller error set only for accepted strategy capabilities; map external failures at boundaries. |
| Fixed latency, memory, checkpoint, and timeout numbers | No reference benchmark or capacity evidence | Keep measurable budgets as an open decision; define benchmark before accepting targets. |
| Every proposed lifecycle hook mandatory | Most strategies need only a small subset and V1 shows several unused hooks | Define required hooks by strategy type and optional hooks by declared capability. |
| Package-level auto-wrapping plus raw module functions | Same names return incompatible types | One explicit typed public API; private pure helpers remain raw and unexported. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
| --- | --- | --- | --- | --- |
| Open | Canonical package root | V1 uses `app/services/strategy`; V2 prescribes `tools/strategies/`. | Adopt `tools/strategies/`; retain `app/services/strategy`; choose another canonical domain root. | CAP-STR-001 to CAP-STR-014 |
| Open | Universal downstream TradeIntent consumer and execution authority | V1 has simulation and live consumers; V2 assigns all official execution to simulation. | Simulation only for backtest/replay; environment-specific simulation/trading/live consumers; one unified execution domain. | CAP-STR-001, CAP-STR-006; WF-STR-002, 003, 007 |
| Open | Initial environment scope | V2 defines BACKTEST, REPLAY, PAPER, SHADOW, LIVE; no active roadmap slice is supplied. | Backtest only; backtest+replay; include paper/shadow; include live eligibility metadata only. | CAP-STR-003 to CAP-STR-011 |
| Open | Migration policy for existing stored Python strategies | V1 runtime depends on dynamic stored classes; V2 prohibits arbitrary code. | Migrate selected artifacts into approved modules; freeze legacy read-only runner; retire all custom artifacts. | CAP-STR-003, CAP-STR-011, CAP-STR-013; WF-STR-009 |
| Open | Owner of approved artifact and registry persistence | V1 combines DB/files/governance; V2 requires immutable approved artifacts but does not assign persistence clearly. | Strategy owns registry records; governance/catalog owns persistence; shared artifact registry. | CAP-STR-003, CAP-STR-013; WF-STR-008 |
| Open | Performance and capacity baselines | V2 proposes provisional limits; V1 audit contains no measurements. | Accept proposed baselines; benchmark and replace; leave non-quantitative for initial implementation. | CAP-STR-011, CAP-STR-012 |
| Open | Initial event hook set and fill-update support | V1 uses `on_event`; V2 proposes many hooks including partial fills and checkpoints. | Minimal init/bar/tick/fill/stop; full proposed set; phased hook additions. | CAP-STR-005, CAP-STR-008, CAP-STR-009 |
| Open | Lifecycle approval roles and promotion authority | V2 names lifecycle states and Quant Research/Engineering sign-off; top-level governance is not supplied. | Adopt as written; map to system governance roles; store only external status references. | CAP-STR-003, CAP-STR-013 |

The package root, downstream execution authority, initial environment scope, artifact ownership, capacity targets, and lifecycle authority affect more than one domain and must be escalated to the top-level system Open Decisions section and resolved there with ADRs. The stored-strategy migration and minimal hook set also require cross-domain confirmation from simulation/live/catalog owners.

Deferrals that change system shape and must appear in the top-level Deferred Capabilities section: arbitrary-code sandboxing; async/multiprocess strategy execution; production paper/live operations; ML strategies; L2/L3/order-book strategies; venue-aware execution algorithms; regulatory/compliance strategy metadata; and production DR/runbook workflows.

## 12. Inputs for the Final Domain README

### Approved capabilities

* Pure side-effect-free strategy decision boundary.
* Versioned typed strategy references, configuration, contexts, results, TradeIntent, diagnostics, manifests, and checkpoints.
* Approved immutable strategy registry with deterministic reference/config/lifecycle/environment validation.
* Atomic vectorized batch decision execution using normalized data and precomputed indicator outputs.
* Typed stateful event hooks using immutable read-only external state and atomic strategy-local state updates.
* Deterministic TradeIntent construction with identity, idempotency, sequence, lineage, sizing hints, timing, and rationale references.
* No-lookahead, readiness, stale-data, missing-data, and fixed decision-clock validation.
* Replay manifests and bounded optional strategy-local checkpoints.
* Structured redacted diagnostics and the reduced accepted strategy error catalogue.
* Registered-only execution, side-effect-safe imports, no secrets, no network/filesystem/process access, and seeded determinism.
* One applicability-aware strategy declaration manifest.
* Immutable artifact integrity metadata and external provenance references.

### Approved workflows

* `WF-STR-001` — Validate strategy reference and configuration
* `WF-STR-002` — Generate vectorized strategy decisions
* `WF-STR-003` — Run stateful event strategy hook
* `WF-STR-004` — Build and hand off TradeIntent
* `WF-STR-005` — Create replay manifest and checkpoint
* `WF-STR-006` — Export structured diagnostics
* `WF-STR-007` — Consume strategy decisions in paper/live runtime
* `WF-STR-008` — Register and approve immutable strategy version
* `WF-STR-009` — Reject arbitrary strategy code

### V1 behaviours to preserve

* Vectorized strategy signal logic from `BaseStrategy.on_bar()` implementations.
* Stateful advanced strategy decision logic and pure basket calculations over read-only state.
* Name/version strategy resolution as a concept.
* Simulation integration that routes advanced strategies through the canonical event-driven tick engine.
* Live/paper rolling decision consumption as a cross-runtime workflow, after conversion to TradeIntent.
* Reason/setup/group metadata that can populate rationale and lineage.

### V1 behaviours to modify

* Split the single DataFrame base contract into vectorized and event strategy contracts.
* Replace signal-column and SignalDict/TradeAction cross-domain outputs with typed TradeIntent results.
* Replace mutable global registry registration with immutable approved entries and schema validation.
* Move rolling RSI/SMA calculation out of strategy and consume indicator outputs.
* Limit stateful helpers to immutable snapshot calculations and atomic local state.
* Replace package auto-wrappers and free-form logs with explicit typed results and diagnostics.
* Split storage metadata from external artifact persistence and governance.
* Convert TemplateStrategy into executable documentation/examples rather than a production runtime dependency.

### V1 behaviours to remove

* Arbitrary dynamic Python loading through `StrategyStorage.load_strategy_class()` after active strategies are migrated.
* Raw archive-based strategy import in the initial rebuild.
* Physical per-version deletion and filesystem version discovery once the immutable registry/catalog is authoritative.
* Unused `SignalIntent` and no-op lifecycle hooks not selected for the final event protocol, after caller verification.
* Import-time global filesystem writes.
* Duplicate signal-schema creation and protection-field aliases after migration.

### V2 behaviours to add

* Immutable registry reference and configuration validation.
* TradeIntent schema and deterministic identity/lineage.
* No-lookahead and readiness validation.
* Typed event hooks and immutable execution-state snapshots.
* Atomic local-state updates, checkpoints, and replay manifests.
* Structured diagnostics, redaction, and deterministic error mapping.
* Registered-only security and bounded deterministic execution.
* Manifest-based declarations and artifact integrity metadata.

### V2 proposals to reject or defer

* Arbitrary-code sandboxing — defer until an approved security workflow exists.
* Strategy-owned indicator calculations — reject; consume indicator-domain outputs.
* Strategy-owned build, optimization, analytics, governance, compliance, reporting, deployment, DR, and execution enforcement — reject from this domain.
* Async and multiprocess profiles — defer; start with bounded synchronous execution.
* ML, feature-store, L2/L3, venue, dark-pool, queue-position, and advanced algorithm support — defer until confirmed workflows exist.
* Fixed provisional SLOs and capacity values — open until benchmarked.
* Mandatory exhaustive hook set and full error catalogue — simplify to applicable hooks and accepted capability errors.

### Required open decisions before README completion

* Canonical package root
* Universal downstream TradeIntent consumer and execution authority
* Initial environment scope
* Migration policy for existing stored Python strategies
* Owner of approved artifact and registry persistence
* Performance and capacity baselines
* Initial event hook set and fill-update support
* Lifecycle approval roles and promotion authority

## 13. Final Reconciliation Checklist

* [x] Every V1 capability received a disposition: **18/18**.
* [x] Every V2 requirement received a disposition: **443/443**.
* [x] Every V1 workflow was reconciled: **5/5**.
* [x] Every proposed core V2 workflow/public capability was reconciled.
* [x] Confirmed working V1 behavior was not discarded without a migration or removal condition.
* [x] Unused and disconnected V1 behavior was not preserved merely for compatibility.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The proposed direction follows Package → Module folder → File → Public symbol.
* [x] Behaviors belonging to simulation, execution, data, indicator, risk, portfolio, optimization, analytics, governance, compliance, reporting, build, deployment, and operations are explicitly bounded or flagged.
* [x] Unresolved conflicts are listed under Open Decisions.
* [x] Cross-domain open decisions and system-shape deferrals are identified for top-level escalation.
* [x] No code was inspected or changed during this step.
* [x] Neither source document was modified.
* [x] The reconciliation provides sufficient approved capability and workflow inputs for the next domain README step, subject to the listed open decisions.

---

## Source Integrity Note

This reconciliation was produced only from `strategy-v1-audit.md` and `04-strategy.md`. It does not re-audit source code and does not modify either input.

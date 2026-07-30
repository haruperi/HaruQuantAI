# Changelog

## [Unreleased]

### Audit Utils, Brokers, and Data runtime truth and public boundaries

The three audited domains now expose function-only package roots, focused tests exceed the per-file coverage floor, and usage evidence distinguishes genuine provider results from unavailable or test-only capabilities.

#### Added (1)

- Completed Strategy `FEAT-STR-11` external proposal evaluation plus `WF-STR-011` approved Optimization-result adoption and `WF-STR-012` research-only signal evaluation, without importing or changing the upstream Optimization, Simulator, Analytics, or Research domains.

#### Changed (7)

- Added the opaque `load_broker_provider_settings` function and Brokers-owned `resolve_provider_connection_config`/`create_connected_broker` operations so no settings class or connection DTO crosses a public package boundary.
- Rewrote the Data composition root `_LazyBrokerSession` to resolve MT5, cTrader, and credential-free providers through the Brokers resolver and removed its private `_ProviderRuntimeSettings`, so Data no longer resolves credentials or builds connection configurations.
- Migrated audited production, usage, workflow, and integration consumers to domain-root imports and added package-root function-only boundary checks.
- Marked `FEAT-DATA-11` and `FR-DATA-095`–`099`/`123`–`129` Pending because the repository has no licensed real economic-calendar transport; the usage now reports `SOURCE_UNAVAILABLE` instead of using `DemonstrationTransport`.
- Reworked every Indicators feature usage and the active workflow evidence to print bounded MT5-derived OHLCV and calculated DataFrames, and added direct subprocess coverage for `WF-INDI-006` through `WF-INDI-008`.
- Refactored Risk to a 63-function package-root boundary, migrated direct consumers away from public classes/constants and deep imports, and completed all fifteen registered Risk workflows with substantive bounded evidence.
- Refactored Trading to a function-only package-root boundary, migrated direct consumers, completed `WF-TRD-015` and `WF-TRD-016`, and raised every Trading production file above the 80% branch-aware coverage floor.

#### Fixed (9)

- Fixed the Data composition root silently ignoring `settings.mt5.*` in `app/configs/env.json` because `_ProviderRuntimeSettings` extended `BaseSettings` instead of `AppSettings` and therefore read only the process environment; real-MT5 retrieval through the Data path now honors the central settings file.
- Fixed Brokers package-root history/time-range forwarding and canonical timeframe normalization, restoring genuine MT5 history and Dukascopy bar reads.
- Fixed Data spread normalization so it rejects missing unit/scale evidence and record-shape mismatches instead of inventing `USD` or `scale=0`.
- Fixed historical backfill so it establishes governed storage and source identity before retrieval, allowing scheduled jobs to persist genuine provider records and checkpoints.
- Fixed Data source and real-time-feed usage evidence so it prints bounded provider-derived rows and ticks, while unavailable providers report explicit errors without injected fallbacks.
- Fixed external spread imports so decimal scale is derived from observed provider values rather than assigned a fabricated default.
- Fixed Indicators response handling, private Data structural typing, workflow configuration construction, and validation/error branch coverage so the focused suite passes with every Indicators production file above the 80% floor.
- Fixed Strategy response unwrapping, function-only contract/evaluator construction, deterministic checkpoint/configuration failures, and real MT5-backed usage evidence so all ten implemented workflows pass and every Strategy production file exceeds 80% branch coverage.
- Fixed Risk YAML profile coercion for tuple, enum, loss-basis, hash-compatibility, and crisis-window fields; focused validation now passes 187 tests at 85.4% branch-aware coverage with every Risk production file above 80%.

### Add observability, incidents, and operational control

The Agentic firm can now show what a run did, stop what has gone wrong the same way whoever noticed, and re-examine a run without letting it act again.

#### Added (1)

- `FEAT-AGT-21` Observability, Incidents, and Operational Control: a trace covers all ten required span kinds validated by set equality or does not exist, so a run whose emitters stayed silent produces a refusal naming the missing spans rather than a partial view that reads as complete, an unlabelled record is counted but covers nothing, and a span nobody agreed to does not widen the contract; redaction is inherited from the `FEAT-AGT-06` memory boundary and the package defines no redactor of its own, with the trace carrying the union of the paths that were removed so an operator can see redaction happened without the trace ever holding the material, and an unreadable cost is skipped with a warning rather than silently read as zero. Containment is a property of the incident kind through a fixed table rather than a judgement at the call site — injection, privilege, data-poisoning, and sandbox incidents quarantine and cancel, drift quarantines without cancelling, and cost, provider, runaway-loop, and schema incidents cancel — applied through the normal `FEAT-AGT-04` cancellation path, with an already-terminal run recorded against its real state rather than re-cancelled; a record whose action disagrees with its kind, a quarantine naming no role, a cancel naming one, or any containment without preserved evidence and a checkpoint are all unrepresentable, and one classified incident per kind per correlated run is enforced in the reference store and by a `UNIQUE (run_id, correlation_id, kind)` constraint in the durable table so a second report cannot replace the first and its evidence. Replay is isolated by the type: the environment is a literal `sandbox` so a production replay is unconstructable, every reference is a content digest re-verified against what the store actually holds, and an outcome reporting any attempted side effect is rejected. The package registers no role, has no prompt, and invokes no model — classifying an incident must be deterministic, and a model would be a place to argue that an incident was not one. Quarantine records a decision rather than mutating a role, replay is validated rather than executed, trace completeness is enforced on assembly rather than on emission, and no incident has occurred outside tests.

### Add trade proposal handoff

The Agentic firm can now hand a supported thesis to Strategy as an untrusted proposal, in a form that cannot become an order.

#### Added (1)

- `FEAT-AGT-20` Trade Proposal Handoff: neither a trade proposal nor its receipt defines a price, quantity, lot size, notional, stop, target, order type, venue, or account field, and three tests hold that line — field-set disjointness against the prohibition list, source-text absence in every module except the one that owns the list, and the receiver contract's own lack of anywhere to put one; execution vocabulary in prose is refused on top of `FEAT-AGT-07`'s single definition of authorization language. What is proposed — instrument, strategy identity, direction, horizon, evaluation scope — comes from the caller and evidence references come from the thesis, so a model output naming a different instrument changes nothing and a proposal cannot cite evidence that was never gathered; only a `supported` thesis may be proposed, with `contested` excluded so a conflict `FEAT-AGT-13` preserved is not buried by trading on it. The horizon and validity window are checked against the receiver's own thirty-one-day bound and its expiry-within-horizon rule before submission. The handoff targets Strategy's `FEAT-STR-11` external-proposal intake rather than the operations `WF-AGT-008` names, because `strategy.build_trade_intent` requires a `StrategyDecision` and a `StrategyExecutionContext` this domain does not have; `create_strategy_proposal_evaluation_request` derives the request identity and idempotency key from a content digest and refuses a caller that supplies either, which is what makes "no privileged route" structural rather than promised. A receipt carries Strategy's own status enumeration verbatim — `accepted_for_evaluation`, `rejected`, `expired`, `no_signal` — with no value meaning "filled", records a produced intent by identity alone and never by content, and refuses to report an intent against a status that produced none, an intent without its identity, or evaluated signals for a rejected or expired proposal. A result naming a different proposal or the same proposal at different content is refused. Exactly one receiver operation is imported and a test asserts the whole `app.services` import list is that single line; nothing names Risk, Trading, or Brokers. No signal has been evaluated, no intent constructed, and no receipt persisted.

### Add portfolio and risk advisory

The Agentic firm can now describe how exposure is distributed and what could go wrong with it, without any of that description being capable of instructing anything.

#### Added (1)

- `FEAT-AGT-19` Portfolio and Risk Advisory: non-binding is three structural facts rather than an adjective — an allocation proposal defines no lot size, notional, quantity, price, or order field, so nothing in it could reach an execution path even if the object were mishandled; approval language is refused through `FEAT-AGT-07`'s single definition rather than a third restatement of it, extended only by the level-and-price vocabulary specific to an advisor (`entry price`, `stop loss`, `take profit`, `buy at`, `deploy to live`); and expiry is mandatory and strict, so an already-expired proposal cannot be constructed and an expired one is never critiqued. All five receiver reads — Analytics allocation evidence, Portfolio common-mode exposure and cross-account correlation, the Data account snapshot, and the Risk firm mandate — traverse the governed authorization path and are audited, and each must carry its own observation instant: evidence without one is refused, evidence older than the declared bound is refused, and an unreadable or naive instant counts as stale, all before the provider is reached. Mandate identity, version, asset class, and base currency are copied from what Risk returned rather than from the model, so a proposal cannot quietly widen the scope it was bounded by. The risk critique covers mandate, barrier, tail, concentration, liquidity, correlation, operational, and model risk validated by set equality, rejects assessments too short or too reassuring to be assessments, and emits no approval by absence — the advisory carries no verdict, severity, or boolean a caller could read as consent. No module in the package imports Portfolio, Risk, Analytics, or Data; the receiver operations are reached through an injected port, and `FR-AGENTIC-057` is verified with Risk's own `AllocationReviewRequest` rejecting incomplete and incompatible projections assembled in the tests. No evidence port is bound to a real receiver and no advice has reached Portfolio or Risk.

### Add artefact promotion and lifecycle

The Agentic firm can now decide whether a staged artefact has earned promotion, and record what happened to it in a history that cannot be rewritten.

#### Added (1)

- `FEAT-AGT-18` Artefact Promotion and Lifecycle: every evidence field on a promotion packet is required, so a packet assembled without the artefact, the experiment verdict, the sweep verdict, the critique, the simulation manifest, or an approving human is unconstructable rather than merely thin, and the packet digest covers the whole assembly so evidence appended after approval yields a different packet; five deterministic gates run in the order `FR-AGENTIC-053` names them — in-sample-only evidence, holdout consumed by both the experiment and the sweep, cumulative search beyond its declared ceiling, incomplete artefact provenance, and absent or unauthorised approval — each read from evidence the packet already carries, with every failure reported rather than only the first; transitions are append-only because the ledger accepts a position once, backed durably by a composite primary key on `(artifact_hash, sequence)`; they are keyed on the artefact digest rather than its identifier, so a materially changed artefact begins with an empty history and cannot inherit an approval granted to a different one; the current state is read from the ledger rather than supplied by the caller, so holding a valid packet does not permit skipping a step; demotion from `registered` requires neither packet nor approval; and `research_only` is terminal, so re-assembling a passing packet does not reopen a terminated artefact. The package registers no role, has no prompt, and invokes no model — promotion is a decision procedure, and a model here would be a place to argue past a gate. It records and does not register: nothing in it imports Strategy or the simulator, and reaching `strategy.register_strategy_version` is `FEAT-AGT-22`'s. No artefact has been promoted and the durable ledger is not yet bound, so append-only holds within one process only.

### Add evaluation, critique, and economic acceptance

The Agentic firm can now decide whether one of its own roles has earned its place, on arithmetic no wording can move.

#### Added (1)

- `FEAT-AGT-17` Evaluation, Critique, and Economic Acceptance: an evaluation plan validates its six versioned set kinds and seven critique challenge kinds by set equality rather than by sufficiency, so an evaluation missing its poisoning set or a critique that never addresses leakage is unrepresentable rather than merely weaker, and each set requires its own calibrated grader; which sets exist at which version and whether a grader was calibrated are read through the governed tool path and audited, never asserted by the model, and coverage is checked before any model call; a candidate beats its simpler baseline only when its margin strictly exceeds the measurement uncertainty plus its extra cost, with an exact tie going to the baseline because complexity has to earn its place; the required continue, disable, or retire action is computed from the gate outcomes and that margin before the model is invoked, and the verdict recomputes it and refuses to be built when the recorded action disagrees, so a model cannot write `continue` over a failed adversarial, poisoning, or refusal gate; and challenges the candidate evidence already supports are derived from the `CodeArtifact`, `SweepVerdict`, and `ExperimentVerdict` and merged over the model's text rather than under it. The feature decides and does not mutate: applying a disable or a retire belongs to `FEAT-AGT-18` lifecycle or a governance manifest re-issue. No versioned set has been authored and no grader calibrated for any registered role, so the mechanism is verified and no role has yet been evaluated.

### Add bounded optimization coordination

The Agentic firm can now declare a bounded search before it runs and report what the whole search showed rather than what its best row showed.

#### Added (1)

- `FEAT-AGT-15` Optimization Coordination: sweep plans declare space, objective, method, trial budget, early-stop policy, seed, and holdout consumption before execution and carry a digest over the whole declaration, so a budget widened afterwards is a different plan; the trial ledger requires attempted to equal completed plus failed with a reason per failure and rejects a search that exceeded its budget, so survivorship bias is unrepresentable and an irreconcilable receiver report is refused before the verdict model is invoked; robustness, instability, and overfit evidence are assembled from deterministic Optimization operations rather than from the model or from rank, and a verdict consisting only of the winning parameters cannot be constructed; and a sweep consuming holdout reserves it from the same `FEAT-AGT-14` experiment ledger, so a thesis's single look cannot be spent once by an experiment and again by a sweep.

### Add governed code generation with staged artefacts

The Agentic firm can now turn an authenticated human specification into staged strategy or indicator source code that a person reviews before anything merges.

#### Added (1)

- `FEAT-AGT-16` Governed Code Generation and Sandbox: generation is gated on an authenticated human principal holding `agentic:author_code` and on a sandbox lease attesting separately to ephemerality, credential absence, blocked egress, and bounded resources, with any missing property refused before a model is called; artefacts carry files, per-file digests, dependency data, tests, model and prompt provenance, and complete search history, digested as one manifest; whether an indicator exists is read from the Indicators registry through the governed tool path, so a strategy requiring an unregistered primitive is either refused or staged as `blocked_on_indicator_merge` and structurally cannot claim readiness; and every staged path is validated on its raw text before parsing, then resolved and re-checked against the staging root, rejecting absolute paths, drive letters, traversal, symlink escapes, NTFS alternate data streams, and Windows reserved device names.

#### Changed (1)

- Added `tools.py` to the coder package beyond the canonical module specification, so the indicator-registry lookup traverses the same permission enforcement point as every other receiver call rather than importing Indicators directly.

### Add governed experiment design and Simulation coordination

The Agentic firm can now pre-register an experiment protocol, run it through the receiver that owns it, and bind a verdict to what that run actually returned.

#### Added (1)

- `FEAT-AGT-14` Experiment and Simulation Coordination: protocols are pre-registered and hashed before any run, so a falsification criterion rewritten afterwards produces a different digest; the receiver's request is submitted unchanged and its result verified to bind to it rather than reconciled, with the package importing neither Simulation contract; conclusions are keyed by the run identifier the receiver returned, never by one a model supplied; and holdout is claimed once per protocol, refused in-process before the receiver is reached and enforced durably by the experiment ledger's primary key.

### Begin Agentic Firm implementation

The Agentic package now delivers its complete control-plane foundation — contracts, governance, runtime, orchestration, permissions, governed memory, and bounded deliberation — while every agent role and consequential capability remains unimplemented.

#### Added (12)

- `FEAT-AGT-01` Canonical Agentic Contracts and Provenance.
- `FEAT-AGT-02` Firm Governance, Roster, and Authority.
- `FEAT-AGT-03` Provider-neutral model profiles, governed invocation with silent-substitution detection, and evaluated upgrade gating, behind an agent-graph port whose Google ADK binding is not yet implemented.
- `FEAT-AGT-04` Durable task and workflow orchestration with idempotent submission, checkpoint-before-execution, expected-version guards, and non-resumable terminal states.
- `FEAT-AGT-05` Deny-by-default tool authorization with an Agentic-owned single-use `ToolApprovalAttestation v1`, and a registry in which broker, order, kill-switch, override, and deployment capabilities are structurally unregistrable.
- `FEAT-AGT-06` Point-in-time context assembly with lookahead, trust, licensing, freshness, deduplication, and injection filters, plus four separated memory stores that redact before persistence and append corrections rather than overwriting.
- `FEAT-AGT-07` Bounded deliberation that collects independent briefs before any peer exposure, caps participants and rounds from the versioned limits profile rather than from any caller or model, preserves unresolved dissent, and makes a record structurally incapable of carrying an approval or a position size.
- `FEAT-AGT-08` The first registered leaf agent package, whose `prompt.md` is loaded as data and hash-verified against its role manifest before any model call, and whose output schema has no numeric field so a recomputed metric cannot be expressed.
- `FEAT-AGT-11` The first agent package with governed tool adapters, where every evidence call is authorized before invocation and every output binding is taken from a deterministic receiver rather than from the model.
- `FEAT-AGT-12` Quantitative research in which the analyst names a metric and the Analytics catalog supplies its formula and its minimum sample, so an unrecognized estimator is refused rather than authored; findings, estimators, and uncertainty are keyed alike so a point estimate with no interval is unrepresentable; and non-finite, under-sampled, hash-misaligned, or leakage-unsafe evidence is refused before the runtime is invoked.
- `FEAT-AGT-13` Falsifiable hypotheses that cannot be built without a rejection criterion, and non-executable strategy theses that reject code, orders, prices, sizes, and approvals outright.
- Package-wide Agentic settings and versioned limits profiles, disabled by default and fail-closed when incompletely configured.

#### Changed (5)

- Adopted `google-adk 2.5.0` as the Agentic runtime dependency behind the `AdkRuntime` port, resolved by a scoped `requests>=2.32.4` override that documents why `ctrader-open-api`'s exact pin does not apply to this project and when the override may be removed.
- Implemented the Google ADK 2.x binding as the sole construction site for an ADK object, with lazy imports so the Agentic public API loads no provider module, a resolved credential that never enters a contract, and an observed cost derived from reported tokens rather than reported as a false zero.
- Made `build_agent_result` generic so a role-bearing feature declares its own payload type without a cast at the call site.
- Made the Agentic package root a function-only public surface, matching the Brokers and Strategy boundaries, with `build_*` constructors that derive canonical content digests.
- Promoted the governed tool-call wrapper from the technical-analyst package into `FEAT-AGT-05` as `call_governed_tool`, with the audit sink injected as a callable so the permissions feature gains no dependency on governed memory.

#### Fixed (1)

- Fixed governed tool-call audit records colliding when a role called the same tool twice in the same instant: the record identity derives from redacted content, which was identical, so the second write was rejected. Audit entries now carry the call's ordinal within the task.

### Refactor Strategy Domain to Function-Only Public Surface

#### Changed (3)

- Reduced the Strategy package-root API to standalone functions, with contract factories and enum getters replacing external class and constant imports.
- Migrated Strategy consumers, workflows, usage evidence, and integration tests to import only from `app.services.strategy`.
- Added Data-owned transaction and MarketDataset accessors required by Strategy without exposing Data implementation classes across the domain boundary.

### Refactor Brokers domain to Function-Only Public Surface

The Brokers domain API was refactored to enforce Package-Root Export Gate, Domain-Root Imports Only, and Function-Only Public API Surface standards.

#### Changed (3)

- Refactored `app/services/brokers/__init__.py` to expose 58 standalone functions in `__all__`, encapsulating all internal classes, DTOs, enums, protocols, and raw dict constants within `app.services.brokers.contracts`.
- Updated all unit, integration, usage evidence, and workflow tests across `tests/brokers/` to import DTOs and contracts strictly from `app.services.brokers.contracts` and domain operations from `app.services.brokers`.
- Updated `app/services/brokers/README.md` to document the Package-Root Export Gate and Function-Only Public Surface architecture.



### Define the complete Agentic Firm end state

The fourteenth domain is specified as a full multi-agent research, engineering, advisory, and proposal firm while deterministic domains retain all consequential authority.

#### Added (3)

- Added the canonical twenty-two-feature Agentic Firm registry, specialized firm organization, dynamic deliberation, provider-neutral Google ADK runtime, durable workflows, governed memory, security, observability, and deterministic proposal-handoff contracts.
- Added supporting specifications for orchestration, firm organization, Google ADK/model providers, memory/evidence, security threats, operations, and data readiness.
- Added missing Data point-in-time research sources, Research fundamental/sentiment evidence, Strategy external-proposal evaluation, and UI/API Agentic operator seams required by the end-state workflows.

#### Changed (6)

- Expanded Agentic from a restricted offline eight-agent pipeline to the documented end-state firm covering fundamental, sentiment, technical, quantitative, trader, risk-advisory, portfolio, experimentation, optimization, and coding capabilities.
- Required every Agentic trade or allocation proposal to traverse the normal receiver-owned Strategy, Portfolio, Risk, Trading, and Brokers controls without direct Agentic execution authority.
- Reconciled Agentic requirements into one sequential canonical namespace and converted the supporting files from competing authorities into elaborations of the package Feature Registry.
- Corrected the retained research-report provenance and recorded Google ADK 2.x as the selected runtime behind HaruQuantAI-owned provider-neutral contracts.
- Reorganized the canonical Agentic README into the package README template, adding dependency-ordered module/file, workflow, configuration, persistence, testing, and change-process manifests without changing the approved twenty-two-feature end state.
- Replaced the uniform Agentic capability layout with a hybrid architecture that retains ten shared infrastructure modules and gives twelve role-bearing features registered department/agent packages with provider-neutral `agent.py`, integrity-checked `prompt.md`, focused schemas, and explicit optional files.

#### Fixed (2)

- Restored `app.services.research` importability by taking `DataError` and `MarketDataset` from `app.services.data.contracts` after the function-only refactor moved them off the package root.
- Corrected Agentic memory-record identity to derive from the content digest, so distinct records written in the same instant for one task no longer collide.

#### Removed (1)

- Removed the superseded Agentic v1, v2, and v3 document sets and completed historical consolidation plan after retaining the canonical research evidence and end-state specifications.


### Reorganize central settings and strengthen executable usage evidence

Central environment configuration is grouped into logical sections, while provider-backed usage evidence now demonstrates genuine non-production connections and complete domain workflows.

#### Added (1)

- Added the immutable generic `StandardResponse v1`, exact structured error and execution metadata contracts, approved-code catalogue validation, monotonic millisecond timing, and lossless raw-data/extension preservation foundation in Utils.

#### Changed (17)

- Migrated the immutable Brokers capability catalogue to `StandardResponse` and added JSON-only mapping-proxy serialization that preserves raw runtime identity while emitting a detached bounded mapping.
- Migrated the Brokers registered-profile listing to `StandardResponse[tuple[BrokerId, ...]]` while retaining the stable provider tuple directly in `data` and preserving SDK-free discovery.
- Migrated every bounded Brokers public operation to Utils-owned `StandardResponse[T]`, preserved the former envelope evidence in `metadata.extensions` and `error.details`, centralized all 31 Broker error definitions, and updated Data/Trading consumers without compatibility shims.
- Migrated root runtime-profile and execution-route validation from a public exception to `StandardResponse[None]` while preserving its established error code and value-free failure message.
- Restructured central `app/configs/env.json` into grouped lowercase `snake_case` sections and updated `_CentralJsonSettingsSource` to parse nested configuration objects without altering process environment precedence or setting model contracts.
- Replaced unused offline Brokers usage transports and placeholder credentials with enabled demo/testnet/sandbox session evidence, bounded released reads, exact capability-gate assertions, and deterministic disconnection without broker mutations.
- Replaced the singular Utils, Brokers, Data, Indicators, Strategy, Risk, Trading, and Analytics workflow scripts with eighty-three standalone separator-delimited programs, one per active workflow, plus domain runners and registry-parity tests; MT5-backed paths use genuine demo reads/connections from documented input to typed output boundaries, with broker mutations excluded.
- Added thirty-three standalone Simulator, Optimization, Portfolio, and Research workflow programs with registry-ordered runners, README evidence mappings, exact stage labels, parity tests, and bounded genuine MT5 demo market evidence.
- Migrated the Indicators Core and twenty-one official formula operations to Utils-owned `StandardResponse[T]` with the exact twenty-two-code catalogue, response metadata, nested-response unwrapping, and updated consumers and usage evidence.
- Migrated all twenty-three Strategy public operations and evaluator boundaries to Utils-owned `StandardResponse[T]` with raw payloads, trace metadata, explicit upstream-response unwrapping, and an immutable twenty-nine-code Strategy error catalogue.
- Migrated the ten official Optimization operations to Utils-owned `StandardResponse[T]` with direct raw advisory data, an immutable ten-code Optimization catalogue, safe upstream response unwrapping, and updated callers and usage evidence.
- Migrated the classified Research Edge Lab operation to `StandardResponse[ResearchReport]` with direct report data, Research-owned error definitions, safe advisory metadata, and updated API consumers.
- Migrated the Portfolio public facade and `PortfolioError.to_payload` to Utils-owned `StandardResponse[T]`, preserved raw allocation/rebalance state and execution truth, and removed the legacy `PortfolioOutcome` boundary.
- Migrated the 28 qualifying Analytics package-root operations to Utils-owned `StandardResponse[T]`, preserved raw analytical data in `data`, and updated callers, tests, usage evidence, and the Analytics API registry.
- Migrated the qualifying Simulation validation, timeline, accounting, execution, journal, reporting, run, ledger, and Trading-simulation seams to `StandardResponse[T]`, preserving raw results in `data` and updating callers and usage evidence.
- Migrated qualifying Trading public operations to Utils `StandardResponse[T]`, preserving raw DTOs, fail-closed unknown-outcome receipt evidence, and canonical symbolic error details.
- Migrated qualifying Risk public operations to Utils `StandardResponse[T]`, preserved decision states inside raw response data, and added the immutable Risk error catalogue and boundary usage evidence.

## 2.2.11

**Release date:** 2026-07-27

### Complete Research domain and govern economic-news restrictions

The Research domain now exposes twelve focused advisory feature modules, while normalized economic-calendar evidence flows deterministically from Data through Risk and Trading readiness.

#### Added (12)

- `FEAT-RES-01` Versioned Contracts and Configuration.
- `FEAT-RES-02` Deterministic Dataset Preparation.
- `FEAT-RES-03` Research-Specific Features.
- `FEAT-RES-04` Leakage Evidence, Splits, and Masking.
- `FEAT-RES-05` Core Metric Profile.
- `FEAT-RES-06` Seeded Statistical Validation.
- `FEAT-RES-07` Edge Discovery and Confirmation.
- `FEAT-RES-08` Sessions and Seasonality.
- `FEAT-RES-09` Market Structure Analysis.
- `FEAT-RES-10` Deterministic Unsupervised Insights.
- `FEAT-RES-11` Scorecards, Snapshots, and Edge Lab Profiles.
- `FEAT-RES-12` Safe Research Artifact Persistence.

#### Changed (1)

- Normalized provider-neutral economic events, symbol relevance, persistence, refresh policy, and fail-closed Data-to-Risk-to-Trading restriction evidence.

#### Fixed (1)

- Corrected economic-calendar typing, provider filtering, raw-value preservation, stable identifiers, UTC window handling, empty-calendar semantics, and original schedule retention.

## 2.2.10

**Release date:** 2026-07-26

### Complete Portfolio domain

The Portfolio domain now exposes eight focused feature modules with deterministic construction, governed activation, reduce-only rebalancing, cross-domain coordination, and standalone usage coverage.

#### Added (11)

- `FEAT-PORT-01` Portfolio Boundary Contracts.
- `FEAT-PORT-02` Evidence and Eligibility Validation.
- `FEAT-PORT-03` Deterministic Construction.
- `FEAT-PORT-04` Portfolio Persistence.
- `FEAT-PORT-05` Version and Activation Governance.
- `FEAT-PORT-06` Drift and Rebalance Planning.
- `FEAT-PORT-07` Cross-Domain Workflow Coordination.
- `FEAT-PORT-08` Public Portfolio API.

#### Changed (1)

- Relocated the requirement-bearing root `api.py` into a dedicated `api/` feature module folder and added four missing standalone usage programs so that feature count equals module folder count equals usage file count.

#### Fixed (1)

- Corrected portfolio test trace identifiers to canonical prefixed UUID4 format required by Risk and Trading contracts.

## 2.2.9

**Release date:** 2026-07-26

### Complete Optimization domain

The Optimization domain now exposes nine focused feature modules with bounded reproducible parameter search, deterministic scoring, leakage-aware validation, robustness analysis, versioned advisory evidence, and standalone usage coverage.

#### Added (11)

- `FEAT-OPT-01` Parameter Space and Provenance.
- `FEAT-OPT-02` Objectives, Ranking, and Overfit Evidence.
- `FEAT-OPT-03` Bounded Candidate Search.
- `FEAT-OPT-04` Simulation Execution Boundary.
- `FEAT-OPT-05` Monte Carlo and Stress Analysis.
- `FEAT-OPT-06` Optimization-Owned Durable State.
- `FEAT-OPT-07` Versioned Results and Handoffs.
- `FEAT-OPT-08` Time-Series Validation.
- `FEAT-OPT-09` Typed Optimization Boundary.

## 2.2.8

**Release date:** 2026-07-24

### Complete Simulator domain

The Simulation domain now exposes nine focused feature modules with deterministic execution, replay journals, fixed-precision account math, canonical artifacts, and standalone usage coverage.

#### Added (11)

- `FEAT-SIM-01` Boundary and Quality Validation.
- `FEAT-SIM-02` Simulation-Owned State.
- `FEAT-SIM-03` Canonical Tick Timeline.
- `FEAT-SIM-04` Fixed-Precision Account Math.
- `FEAT-SIM-05` Matching and Simulated State.
- `FEAT-SIM-06` Immutable Journal and Replay.
- `FEAT-SIM-07` Official and Research Orchestration.
- `FEAT-SIM-08` Domain Error Taxonomy.
- `FEAT-SIM-09` Results and Canonical Artifacts.

## 2.2.7

**Release date:** 2026-07-24

### Complete Analytics domain

The Analytics domain now exposes five focused feature modules with deterministic evidence, performance reports, bounded projections, and standalone usage coverage.

#### Added (5)

- `FEAT-ANLT-01` Schemas, Catalogs, and Evidence Safety.
- `FEAT-ANLT-02` Approved Upstream Result Mapping.
- `FEAT-ANLT-03` Internal Pure Analytical Evidence.
- `FEAT-ANLT-04` Canonical Reporting.
- `FEAT-ANLT-05` Bounded Report Projection.

## 2.2.6

**Release date:** 2026-07-24

### Complete Trading domain

The Trading domain now exposes nine focused feature modules with deterministic authority, fail-closed execution, reconciliation, operational evidence, and standalone usage coverage.

#### Added (11)

- `FEAT-TRD-01` Canonical Contracts and Registries.
- `FEAT-TRD-02` State and Deterministic Projections.
- `FEAT-TRD-03` Validation, Readiness, and Plans.
- `FEAT-TRD-04` Authority Selection and Dispatch.
- `FEAT-TRD-05` Reconciliation and Retry Guard.
- `FEAT-TRD-06` Operational and Budget Evidence.
- `FEAT-TRD-07` Live and Paper Session Lifecycle.
- `FEAT-TRD-08` Route-Aware Public Actions.
- `FEAT-TRD-09` Immutable Execution Evidence.

## 2.2.5

**Release date:** 2026-07-24

### Complete Risk governance domain

The Risk domain now exposes fifteen focused feature modules with deterministic policy enforcement, fail-closed governance, durable evidence, and standalone usage coverage.

#### Added (15)

- `FEAT-RISK-01` Versioned Contracts and Deterministic Errors.
- `FEAT-RISK-02` Risk Profiles and Stable Configuration.
- `FEAT-RISK-03` Portfolio Risk Snapshot.
- `FEAT-RISK-04` Position Sizing Recommendations.
- `FEAT-RISK-05` Tamper-Evident Risk Audit.
- `FEAT-RISK-06` Portfolio and Market-Context Limits.
- `FEAT-RISK-07` Regime Assessment and Limit Tightening.
- `FEAT-RISK-08` Strategy Operational Eligibility.
- `FEAT-RISK-09` Allocation Review and Budget Activation.
- `FEAT-RISK-10` Durable Approval-Token Lifecycle.
- `FEAT-RISK-11` Decision Reuse Revalidation.
- `FEAT-RISK-12` Canonical Risk Governor.
- `FEAT-RISK-13` Kill-Switch Authority and Block State.
- `FEAT-RISK-14` Advisory Scenario Analysis.
- `FEAT-RISK-15` Risk Decision Summaries.

## 2.2.4

**Release date:** 2026-07-24

### Complete Strategy domain

The Strategy domain now exposes ten focused feature modules with deterministic contracts, governed workflows, immutable proposal boundaries, and standalone usage evidence.

#### Added (11)

- `FEAT-STR-01` Versioned Strategy Contracts.
- `FEAT-STR-02` Deterministic Safe Diagnostics.
- `FEAT-STR-03` Immutable Registry and Configuration.
- `FEAT-STR-04` Canonical TradeIntent Proposals.
- `FEAT-STR-05` Deterministic Replay Manifests.
- `FEAT-STR-06` Bounded Persisted Local State.
- `FEAT-STR-07` Atomic Vectorized Evaluation.
- `FEAT-STR-08` Stateful Event Evaluation.
- `FEAT-STR-09` Concrete Signal Execution Boundary.
- `FEAT-STR-10` Strategy Signal Library.

## 2.2.3

**Release date:** 2026-07-24

### Complete Indicators calculation domain

The Indicators domain now exposes six focused feature modules with deterministic contracts, workflows, calculations, and standalone usage evidence.

#### Added (6)

- `FEAT-INDI-01` Indicator Contracts, Registry Discovery and Request Validation.
- `FEAT-INDI-02` Candlestick Pattern Labelling.
- `FEAT-INDI-03` Trend and Moving-Average Calculation.
- `FEAT-INDI-04` Momentum Oscillator Calculation.
- `FEAT-INDI-05` Volatility and Range Calculation.
- `FEAT-INDI-06` Volume-Flow and Price-Volume Calculation.

## 2.2.2

**Release date:** 2026-07-24

### Focused Brokers and Data domain correction

The Brokers and Data domains now expose their corrected focused feature architectures, governed provider and data controls, and complete standalone evidence suites.

#### Added (31)

- `FEAT-BRK-00` Canonical Provider-Neutral Contracts.
- `FEAT-BRK-01` Adapter Registry and Capability Discovery.
- `FEAT-BRK-02` MetaTrader 5 Account Lifecycle.
- `FEAT-BRK-03` cTrader Account Lifecycle.
- `FEAT-BRK-04` Binance Lifecycle.
- `FEAT-BRK-05` Dukascopy Tick Reads.
- `FEAT-BRK-06` Yahoo History.
- `FEAT-BRK-07` MetaTrader 5 Mutations.
- `FEAT-BRK-08` cTrader Mutations.
- `FEAT-BRK-09` Execution History Reads.
- `FEAT-BRK-10` Provider Calculations.
- `FEAT-BRK-11` Price Streams.
- `FEAT-BRK-12` cTrader Market Data.
- `FEAT-BRK-13` Dukascopy BID Bars.
- `FEAT-BRK-14` Deterministic Fake Adapter.
- `FEAT-BRK-15` Adapter Runtime.
- `FEAT-DATA-01` Canonical Data Contracts.
- `FEAT-DATA-02` Market Data Retrieval.
- `FEAT-DATA-03` Local Dataset Loading.
- `FEAT-DATA-04` Synthetic Data Generation.
- `FEAT-DATA-05` Tick-Series Derivation.
- `FEAT-DATA-06` Data Persistence and Storage.
- `FEAT-DATA-07` Data Quality and Validation.
- `FEAT-DATA-08` Data Transformation and Resampling.
- `FEAT-DATA-09` Time and Session Handling.
- `FEAT-DATA-10` Data Source Governance.
- `FEAT-DATA-11` Economic Calendar.
- `FEAT-DATA-12` Real-Time Feed Lifecycle and Observability.
- `FEAT-DATA-13` Scheduler and Job Management.
- `FEAT-DATA-14` Cross-Domain Evidence.
- `FEAT-DATA-15` Audit Evidence.

## 2.2.0

July 23, 2026

### Feature registries, focused domains, and contract hardening

Consolidated current feature ownership into package READMEs while completing focused-domain, contract, and documentation corrections without changing runtime behavior.

#### Added (11)

- Registered root runtime-profile and execution-route compatibility as `FEAT-APP-01` in `app/README.md`.
- Recorded the 15 Brokers capability IDs and usage programs and exposed shared-provider-folder structural status.
- Recorded eight Portfolio feature owners and exposed missing dedicated usage programs and the requirement-bearing root `api.py`.
- Aligned nine Simulator feature IDs with nine usage programs and exposed root `errors.py` ownership.
- Aligned nine Optimization feature IDs with their numbered usage programs and Section 4 specifications.
- Localized 12 missing Research feature targets to the Research README while retaining its `Missing` status.
- Localized 12 missing backend/frontend API feature targets to the UI/API README without claiming implementation completion.
- Established `app/services/data/contracts/` as Data’s canonical immutable contract boundary and migrated consumers without compatibility re-exports.

#### Changed (11)

- Made owning package READMEs the canonical current feature registries, kept this changelog history-only, and changed no code, API, contract, requirement, or test.
- Split broad Risk policy and decision ownership into focused feature owners, registered contracts as a feature, corrected the public API to `RiskConfig`, and aligned 15 usage programs.
- Adopted trusted-data canonical serialization through `canonical_digest(value)` and `canonical_json(..., max_items=None)` under `XDOM-01` while preserving default bounds and existing hashes.
- Kept tick derivation in `FEAT-DATA-05`, approved private fixed-point Numba kernels and bounded columnar persistence for eligible inputs, and retained exact Decimal behavior for special cases.
- Adopted closed Data quality behavior where `reject` raises `DATA_QUALITY_FAILED` and `warn` returns unchanged data with bounded evidence and calendar-aware inspection.
- Preserved genuinely unavailable analytical spread as float64 `NaN` with `spread_unit=None` and continued to reject conflicting supplied units.
- Removed the application-wide 50,000-record OHLCV ceiling while retaining governed bounds for tick, spread, payload, diagnostics, and resumable backfill chunks.
- Rebaselined Data under `CAP-DATA-028` to 15 focused feature owners while preserving active requirements, APIs, contracts, schemas, errors, and persistence boundaries.
- Classified Strategy evaluator implementations as catalogue content, separated signal execution, registered contracts, tightened manifest validation, and adopted shared canonical digest behavior.
- Reconciled Brokers provider capabilities and failure semantics, pinned Twisted compatibility, added 15 offline usage programs, and kept unsupported behavior fail-closed.
- Superseded `CAP-DATA-026` with `CAP-DATA-028` while retaining its ownership, dependency, migration, state, temporal, invariant, facade, and shim-removal principles where compatible.

#### Removed (1)

- Removed retired Data horizontal paths and compatibility shims while completing the approved `CAP-DATA-028` 15-feature/15-usage-program structure and preserving the frozen 35-operation API and contracts.

#### Fixed (4)

- Mapped canonical Yahoo `H1` bars to yfinance `1h` while preserving the requested canonical timeframe in provenance.
- Aligned the Indicators public registry with implemented Core and calculation signatures, including `IndicatorResult` helpers and the Bollinger Bands `std_dev` parameter.
- Added Utils `AuthContext` compatibility evidence, separated `AuditEvent` construction from Data persistence, documented sensitive-key matching, and corrected `flush_logging()` queue behavior.
- Populated Brokers result latency at adapter boundaries and documented capability-aware `BrokerResult` and `FakeBrokerAdapter` behavior with bounded subscriptions and failure gates.

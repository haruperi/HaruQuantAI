# Changelog

## [Unreleased]

### Reconcile positions consistently across routes

Trading now applies one authority-event ordering and position-reconciliation algorithm to Simulation, paper, and live routes (Phase 18a).

#### Fixed (1)

- Fixed route divergence by atomically coupling deal-position projection, sequence/event watermark, restart deduplication, and fail-closed foreign/manual orphan handling.

### Expose simulation deal history

Brokers now exposes bounded Simulation deal, exact-deal, and account-transaction authority reads (Phase 17b).

#### Added (1)

- Added fail-closed deal and transaction reads that preserve canonical linkage, entry/reason, fee signs, timestamps, sequencing, and pagination without recomputation.

### Complete order and deal lifecycle

Simulation now emits deterministic provider-shaped order, deal, position, protection, transaction, and race evidence (Phase 17a).

#### Added (1)

- Added evidenced expiration/fill policies, partial remainders, linked `DEAL_ENTRY_*` records, internal OCO protection, causal transactions, race partial orders, and recovery-stable tickets.

### Mirror MT5 account and provider semantics

Simulation now enforces effective provider revisions, account modes, and target-evidenced stop-out policy (Phase 16).

#### Added (1)

- Added stops/freeze, trade/execution/filling, directional-volume, dated-session, netting/hedging, margin-call, and post-swap stop-out semantics.

### Run incremental point-in-time evaluation

Canonical Simulation v2 now evaluates each scheduler instant through bounded evidence and the shared Trading-cycle composition (Phase 15b).

#### Changed (1)

- Removed whole-run v2 decision precomputation, excluded future records structurally, and omitted latency when scheduler clock-edge evidence is incomplete.

### Inject evaluation deadlines

Trading evaluation now receives route-owned deadline authority while preserving one public cycle and route-neutral results (Phase 15a).

#### Changed (1)

- Replaced the evaluation runtime's ambient timeout with a required injected deadline port and monotonic paper/live adapter.

### Cut Simulation over to Trading execution

Canonical simulation v2 runs now await approved Trading requests/actions, share one hashed initial authority snapshot, and enforce explicit terminal and account-activity policy (Phase 14b).

#### Changed (1)

- Added run-scoped async mutation, authority-deal protection evidence, policy-bound liquidation, and fail-closed exclusive/replayed account-activity admission while retaining labelled v1 compatibility.

### Converge Trading mutation routing

Trading now builds provider-bound approved requests once and routes simulation and broker mutations through the same action, Brokers adapter, and response-classification path (Phase 14a).

#### Changed (1)

- Removed the private simulation dispatch callback, added socket-free Simulation session lifecycle support, and retained only declared route-specific safety gates.

### Add effective-dated simulation calculations

Simulation now performs exact effective-dated MT5-FX profit, margin, and account-currency calculations and validates model-bound offline conformance artifacts (Phase 13b).

#### Added (1)

- Added fail-closed Decimal calculations, provider rounding, Data-evidenced FX conversion, model identity, and request-v2 calculation artifact binding.

### Add calculation conformance evidence

Brokers now preserves complete MT5 projected-account check evidence and validates bounded checksummed offline calculation fixtures (Phase 13a).

#### Added (1)

- Added specification-bound Decimal projections and a separately guarded dev/demo fixture collector that remains unreachable from default conformance runs.

### Add the simulation mutation surface

The simulation Broker channel now delegates its approved order and position mutation intersection through request-bound authority envelopes and the verified MT5 mapping path (Phase 12).

#### Added (1)

- Added exact route, tamper, idempotency, retcode, ambiguity, projected-position, and v2-policy guards without adapter-owned matching or accounting.

### Add clock-safe simulation reads

The simulation Broker channel now exposes its approved authoritative read intersection with explicit time, sequence, staleness, gap, and session-revision evidence (Phase 11b).

#### Added (1)

- Added fail-closed socket-free symbol, specification, market, account, position, order, permission, and revision-bound session reads without recomputation.

### Make MT5 mapping clocks injectable

Brokers now captures all ten MT5 observation-owned mapping timestamps through a validated injected UTC clock while retaining the live UTC default (Phase 11a).

#### Changed (1)

- Added one-call-per-payload fixed-clock mapping support with explicit naive/non-UTC rejection and unchanged provider timestamp semantics.

### Route simulation through the Broker identity boundary

Trading now admits the sim route only with the exact Brokers `sim`/`simulation` connection descriptor and forbids that environment everywhere else (Phase 10b).

#### Changed (1)

- Added fail-closed route/environment selection before dispatch while retaining the simulation callback until its Phase-14a authority migration.

### Add a socket-free simulation broker channel

Brokers now exposes the exact `sim`/`simulation` in-process route through an injected structural authority and the canonical adapter lifecycle (Phase 10a).

#### Added (1)

- Added exact simulation factory selection, lifecycle/finalization delegation, capability intersection, canonical conformance, and strict socket/credential/import isolation.

### Bind source and tick lineage

Simulator now proves independent source/tick identities, market-evidence class, clock coverage, and decision-time eligibility before parity admission (Phase 9).

#### Fixed (1)

- Added fail-closed source/tick integrity and lookahead validation, derived-path exclusion, and request-v2 eligibility identity fields.

### Reconcile live execution positions from authority deals

Trading now derives execution-position state from verified Broker deals and position snapshots rather than durable receipt payloads (Phase 8).

#### Fixed (1)

- Added restart-safe receipt correlation, netting/closure/reversal refresh, and fail-closed `UNKNOWN` position guards for missing or disagreeing authority evidence.

### Add signed transaction ledger and rollover swap

Simulator now conserves evidence-backed signed account transactions and calculates broker-server rollover swap modes without guessed posting evidence (Phase 7).

#### Added (1)

- Added deterministic signed transaction posting/restore and timezone-aware swap accrual, evidenced balance posting, and REOPEN identity semantics.

### Map explicit MT5 order policies

Brokers now preserves independent fill and lifetime policy from canonical request v2 into verified MT5 command fields (Phase 6b).

#### Changed (1)

- Added provider-bound Broker order request v2 with independent `type_filling`/`type_time` mapping, conditional UTC expiration, unsupported-combination rejection, and no symbol-default substitution.

### Add explicit Trading order policies

Trading request and executable-intent v2 now preserve independent fill and lifetime policy against an exact provider-specification revision (Phase 6a).

#### Added (1)

- Added immutable policy-v2 factories, conditional UTC expiration, provider-capability rejection, v2 execution-plan preservation, and explicitly labelled parity-ineligible legacy conversion.

### Add deterministic simulation scheduling

Simulation now owns one serializable simulated clock and deterministic event pump (`FEAT-SIM-15`, Phase 5).

#### Added (1)

- Added canonical priority-queue ordering, bounded async result pumping, fail-closed cancellation and failure behavior, and pending-event state restoration without wall-clock waits.

### Add backtest request V2 execution identity

Simulation now binds complete parity execution identity into an asynchronous-native
backtest request while retaining the declared V1 compatibility window (`FEAT-SIM-07`, Phase 4c).

#### Added (1)

- Added checksummed request V2 identity for execution model, source/tick lineage, provider-revision coverage, initial authority state, certification target, terminal-close policy, and a fail-closed synchronous bridge.

### Add effective-dated provider specification history

Data now persists immutable provider-specification revisions and proves exact
point-in-time coverage for the parity programme (`FEAT-DATA-02`, Phase 4b).

#### Added (1)

- Added checksummed half-open provider-specification revisions with atomic supersession, provenance-gated historical bounds, and fail-closed as-of and bounded-interval coverage reads.

### Add typed current provider specification snapshots

Brokers now publishes the versioned current specification observation the
parity programme certifies against (`FEAT-BRK-18`, programme Phase 4a).

#### Added (3)

- Added the immutable `ProviderSpecificationSnapshot v1` binding execution/order/filling/expiration/GTC modes, stops/freeze levels, directional volume limits, calculation mode, margin and swap evidence, instrument scalars, and account permission evidence to one provider/server/account/environment observation with a canonical checksum and current-only validity.
- Added the fail-closed MT5 mapping with verified bit-flag vocabularies, explicit unverified-exclusion handling for fields the upstream contract lacks, and a separate typed dynamic cost-evidence reference.
- Added the released `GET_PROVIDER_SPECIFICATION` adapter capability for MT5 plus six package-root functions to build, parse, dump, verify, and read snapshots.

### Add the parity envelope and relationship-preserving comparator

Simulation now publishes the versioned Parity Envelope v1, the alpha-renaming
evidence normalizer, and the comparator that every later maturity gate
certifies through (`FEAT-SIM-18`, programme Phase 2).

#### Added (4)

- Added the versioned Parity Envelope v1 (MT5-FX demo scope) with typed exact-structural, bounded-numeric, and distributional invariants, an explicit ignored-field registry, validity interval, aggregate economic-error budget, and invalidation triggers.
- Added relationship-preserving evidence normalization that alpha-renames order/deal/position/receipt/event/posting identifiers in encounter order while preserving cardinality, foreign keys, causal edges, and evidenced partial orders.
- Added the parity comparator with per-invariant tolerances, signed ledger-conservation checks, route-specific safety-gate policy comparison, and certificate scope/expiry/identity invalidation.
- Added the published L1–L4 maturity ladder with distinct L5-Demo and L5-Live certificates.

### Register the bounded sim⇄live parity architecture

The documentation authorities now record the approved parity programme's
dependency direction, maturity ladder, certificate model, evidence ownership, and
failure taxonomy before any programme code changes.

#### Changed (5)

- Recorded the acyclic dependency direction `Simulation → Trading → Brokers` plus `Simulation → Brokers` (read/factory through the Brokers-owned simulation authority port) with Simulation as a read/factory consumer of Brokers and Trading remaining the only application-mutation caller.
- Registered the L1–L4 maturity ladder with distinct expiring L5-Demo and L5-Live certificates, the versioned MT5-FX-only Parity Envelope v1 concept, the market-observability and initial-authority-state identity rules, and the certificate invalidation policy.
- Recorded the three parity failure classes (mirrored domain failures, fail-closed Simulation-integrity failures, seeded/journalled infrastructure injections) and the Brokers-current versus Data-historical provider-specification evidence ownership.
- Registered the four Pending Simulation features `FEAT-SIM-15`–`18` plus the declared Brokers, Data, and Trading parity-programme boundaries, the request v2/async operation with preserved v1/sync deprecation windows, and superseded all pre-programme numerical performance results.
- Folded `sim-as-broker-adapter-decision.md`, `simulator-backtest-pipeline.md`, and `trading-execution-pipeline.md` into the owning authorities and deleted them; `sim-live-parity-register.md` and the implementation plan remain reference-only until the claimed certificate is complete.

### Route live MT5 presentation through the MQL5 TCP bridge

Live market presentation now receives atomic one-second multi-symbol snapshots
from one persistent MT5 socket instead of serial Python-package polling.

The listener connection settings now load from global System Settings and its
authentication token is stored through the encrypted write-only credential
boundary rather than requiring a terminal environment variable.

#### Added (4)

- Added the versioned bounded `HaruQuantSnapshotBridge.mq5` JSON-lines producer and local TCP receiver with explicit lifecycle, ordering, framing, and health evidence.
- Added a Data-owned 1–200-symbol snapshot stream and authenticated SSE gateway route with API/frontend contract parity.
- Added live TCP Bid-as-Last, spread, and freshness presentation to Markets and live quote presentation to Charting Tools.
- Added a playground-equivalent Market Ticks diagnostic widget that exposes configured-symbol SSE connectivity, sequence gaps, quote age, and freshness.

#### Changed (8)

- Replaced the MT5 Python-package tick poller with one-second TCP snapshot consumption while retaining the package for non-streaming control and historical reads.
- Retired live closed-bar polling; charts retain genuine historical bars and never fabricate complete OHLCV from sampled snapshots.
- Replaced the Markets Bid and Ask columns with owner-supplied Spread and encoded live, stale, or not-live quote status through accessible green, yellow, or red Trade text.
- Presented Markets spread as integer MT5 points and added per-symbol whole-second Age from genuine TCP quote time, leaving initial HTTP-only age unavailable.
- Replaced the fixed EA symbol feed with a bounded revisioned demand union that follows active snapshot consumers and successful watchlist edits, reconciles after reconnect, and releases unused symbols after a grace period.
- Sequenced Markets initialization so all MT5 history/calculation batches complete before a visible 10-second settling interval and the first TCP snapshot subscription.
- Paused EA quote reads and snapshot payloads immediately when the final visible browser consumer releases demand, retaining only an idle control heartbeat and resuming after acknowledged non-empty demand.
- Sequenced Chart initialization through authoritative bars and a 10-second settling interval, limited Bid ticks to the forming candle, and returned to authoritative bars and indicators at every timeframe rollover.

#### Fixed (5)

- Preserved the Data-owned MT5 source identity in every browser snapshot event instead of presenting it as unknown.
- Corrected Markets ADR and change-pip conversion to prefer explicit symbol overrides and otherwise use ten genuine MT5 symbol points per pip, preventing commodity points from being mislabeled and avoiding blank ADR when symbol info is available.
- Preserved non-pip Markets technical evidence when a symbol has no explicit pip-size convention, and prevented quote snapshots from replacing initialized technical fields.
- Ordered MT5 composite snapshots so history-driven symbol selection completes before the initial Level-1 quote, removing first-load Last Price and Spread races.
- Prevented Chart rollover from repeatedly reopening its one-symbol SSE connection while MT5 still exposes the prior bar bucket; bounded delayed bar reads now gate stream resumption on authoritative target-bar availability.

### Complete the Charting Tools widget

Chart annotations, appearance controls, missing-bar evidence, and maximum-scale rendering now satisfy the remaining registered chart requirements.

#### Added (1)

- Added validated versioned instrument-scoped browser persistence for non-authoritative chart drawings.

#### Changed (2)

- Kept chart appearance controls presentation-only without refetching or replacing Data-owned bars.
- Bounded all chart and indicator rendering work to the clipped viewport at the registered 1,000,000-bar maximum while retaining the latest bar.

#### Fixed (1)

- Presented invalid slots and timeframe discontinuities as explicit gap regions and broke continuous price and indicator paths across missing bars.

### Serve chart indicators through the Indicators boundary

EMA overlays and RSI panels now consume timestamp-aligned owner calculations
instead of deriving indicator values in the browser.

#### Added (1)

- Added an authenticated uncached EMA/RSI chart-series route with visible parameters, explicit warm-up unavailability, and catalogue-backed indicator discovery that disables formulas without a chart-series contract.

#### Fixed (2)

- Normalized Indicators catalogue, capability, and specification reads into the canonical API envelope so contract validation no longer hides registered indicators from the chart popup.
- Anchored RSI panel timestamps to the chart's shared horizontal pan and zoom viewport so panel values remain aligned with their source candles.

### Verify watchlist symbols against the connected source

The Watchlist widget now preloads the complete connected symbol directory and
submits only exact provider-native instruments selected from that evidence.

#### Changed (2)

- Added bounded keyboard-accessible watchlist autocomplete, preserved provider casing and suffixes, and made MT5 symbol discovery fail closed when `symbols_total()` disagrees with `symbols_get()`.
- Removed manual watchlist class controls, derived new-item classes from exact MT5 symbol metadata, and displayed the persisted class beside each symbol.

#### Fixed (4)

- Normalized the symbol-discovery result into the canonical API envelope so the typed UI client can load the complete connected-source directory.
- Removed false `NOT TRADABLE` labels by checking watchlist membership against the complete in-memory connected-source universe instead of a bounded Markets page subset.
- Reconciled ambiguous legacy watchlist classes such as `AUDCAD / Other` from exact runtime symbol metadata and persisted more-specific classifications.
- Backfilled empty `asset_class` values on pre-existing watchlist items from exact connected-source metadata without modifying the immutable `api-0008` migration.

### Keep cached MT5 reads on one persistent event loop

Concurrent workstation reads now share one serialized MT5 event-loop owner, and
API shutdown deterministically disconnects and releases the composed session.

#### Fixed (1)

- Prevented concurrent Markets and Watchlist reads from moving a cached MT5 adapter across disposable event loops and returning empty successful pages after canonical broker errors.

### Separate frontend ownership from the API gateway

The Next.js application now has an independent UI feature authority and verification policy, while the API specification is limited to backend transport, security, composition, and orchestration.

#### Changed (3)

- Split the former UI/API registry into independently reconciled API and UI authorities with a UI-specific component-evidence exception.
- Grouped focused Operational, Watchlists, and Markets API features under the non-feature Workstation namespace, standardized their route/schema/orchestration files, renumbered the API registry contiguously, classified legacy widgets, moved market calculations to Indicators, and made runtime-source resolution fail closed.
- Dissolved the horizontal API routes, streams, persistence, and migrations packages and the root configuration/limits modules into focused Workstation, Settings, Identity, and Watchlists owners while preserving all HTTP operations, configuration policy, and immutable migration ledger inputs.

#### Removed (1)

- Removed ten redundant standalone frontend usage demonstrations in favor of executable UI unit, component, integration, and contract-parity evidence.

### Prevent automated Indicators usage from replacing MT5 credentials

Indicators usage now resolves only the configured database-backed MT5 account,
while ordinary pytest remains connection-free and unit fakes stay unit-only.

#### Fixed (1)

- Removed Indicators usage fallback credentials and provider-enablement writes, gated genuine usage behind explicit development opt-in, and made missing persisted configuration fail closed.

### Populate Markets rows from governed quote and D1 evidence

The Markets widget now fills its requested price, change, volatility, ADR, range,
and OHLC columns progressively from Data and Indicators while preserving explicit
missing-value presentation.

#### Changed (1)

- Reconciled `FEAT-DATA-01` directory, classification, composite-snapshot, and exact-symbol quote operations with focused modules, registered requirements, and numbered usage evidence.

#### Fixed (5)

- Populated Markets-widget columns using the documented usage formulas, corrected OTC zero-last fallback to bid, and bounded active-watchlist loading to sequential four-symbol batches.
- Corrected the Markets technical-evidence cache contract so valid MT5 D1 history supplies volatility, ADR, and range while current-quote fields are recomputed on every read.
- Switched Markets technical history to MT5's bounded 40-bar position read so every sufficiently historied symbol receives overlay evidence without depending on a preloaded chart range.
- Retried MT5's transient one-bar history synchronization response once without cache and cached only datasets sufficient for indicator warmup.
- Selected exact symbols into terminal-local MT5 Market Watch before historical reads so non-preloaded instruments can expose their genuine chart history.

### Reorganize Strategy operational-planning features into focused modules

Strategy's operational-planning capabilities were promoted into focused feature modules
(`profiles/`, `playbooks/`, `setup_evaluation/`, `trade_plan/`, `management_plan/`,
`automation/`, `lifecycle/`) while preserving the package-root public API and all engine
features. An additive migration `0003_strategy_operational_planning` defines the new
operational-planning tables.

#### Added (7)

- Added `profiles/` for strategy profiles and exact approved-expectancy references under `FEAT-STR-13`.
- Added `playbooks/` for human-readable and machine-evaluable setup definitions under `FEAT-STR-14`.
- Added `setup_evaluation/` for deterministic match/stale/regime/evidence outcomes under `FEAT-STR-15`.
- Added `trade_plan/` for canonical trade plans, versions, amendments, and manual-plan support under `FEAT-STR-16`.
- Added `management_plan/` for exit and management plans and ownership handoff under `FEAT-STR-17`.
- Added `automation/` for `OFF/ADVISORY/SUPERVISED/AUTOMATED` mode policy under `FEAT-STR-18`.
- Added `lifecycle/` for strategy lifecycle governance under `FEAT-STR-19`.

#### Changed (6)

- Reorganized Strategy operational-planning features into the eight focused modules (`profiles/`, `playbooks/`, `setup_evaluation/`, `trade_plan/`, `operating_envelope/`, `management_plan/`, `automation/`, `lifecycle/`) while preserving the package-root public API byte-for-byte.
- Folded `exit_plans/` into `management_plan/` and `manual_plans/` into `trade_plan/`, removing the old horizontal feature folders.
- Moved profile, playbook, setup-evaluation, and expectancy transports out of `contracts/` into their owning feature modules.
- Moved `evaluate_automation_mode` and `govern_strategy_lifecycle` out of `proposal_intake/` and `registry/` into `automation/` and `lifecycle/`.
- Consolidated the Strategy usage evidence set to 19 standalone feature programs with redistributed `FR-STR-*` demonstrations.
- Added additive migration `0003_strategy_operational_planning` with `strategy_profiles`, `strategy_playbooks`, `strategy_setup_evaluations`, `strategy_plans`, `strategy_automation_policy`, and `strategy_lifecycle` and gave each operational-planning table production reachability through `persist_*`/`list_*` operations and the public `ensure_strategy_storage` boundary.
- Corrected the Strategy usage-script MT5 fallback paths to build the current Data contracts and fall back to deterministic offline evidence when the live source is unavailable, and optimized the structural unit tests below the 100 ms ceiling.

### Complete Analytics, Portfolio, and operational workstation capabilities

Analytics, Portfolio, UI/API, and Utils notifications brought the registry to full completion; subsequent feature-folder absorption leaves 192 registered application features.

#### Added (6)

- Added immutable player journals, evidence-only behavioral and emergency-response analytics, and versioned qualification evaluation under `FEAT-ANLT-07` through `FEAT-ANLT-10` with additive Analytics migration `003_player_evidence_schema`.
- Added Decimal valuation/P&L, margin and buying-power views, portfolio risk health, broker reconciliation, and balanced corporate-action/settlement postings under `FEAT-PORT-10` through `FEAT-PORT-12` with additive Portfolio migration `003_portfolio_operations_schema`.
- Added the versioned operational workstation read model and optimistic command boundary under `FEAT-API-10`, including two authenticated HTTP operations and matching typed frontend transport.
- Added accessible instrument, planning, workflow, emergency, alarm, training, replay, and qualification presentation capabilities under `FEAT-API-15` through `FEAT-API-20`.
- Added `FEAT-UTIL-14`, a disabled-by-default unified Desktop, SMTP, Telegram, and Twilio notification service with operational templates and rate-limited orchestration.
- Added an unnumbered supplemental Data usage catalogue that preserves all legacy monolithic example scenarios on the current fourteen-feature public boundaries.

#### Changed (15)

- Completed all 199 canonical `FEAT-*` registrations with no partial or missing features remaining.
- Consolidated Data from nineteen registered features into fourteen focused owners while preserving its package-root API, requirements, migrations, and runtime behavior.
- Renumbered existing API frontend usage programs to `09` through `12`, reserving `14` through `20` for their owning feature evidence.
- Replaced the retired programme terminology in package READMEs and evidence filenames with consolidated application feature terminology.
- Replaced the repository JSON settings source with UI/API-owned versioned database settings, encrypted write-only credential slots, an administrator frontend, and a fail-closed one-time migration utility.
- Added `WF-UTL-010` as current package-root evidence for surviving legacy main Utils operations, with removed and reassigned responsibilities explicitly excluded.
- Replaced the abbreviated Utils aggregate usage sequence with the canonical 18-stage full-domain wrapper pipeline across all fifteen registered Utils features.
- Reconciled Brokers into eleven focused feature folders, moved canonical contracts and public operations under their owners, and activated the authoritative symbol-map migration and CRUD boundary during API startup.
- Reassigned `FEAT-BRK-00` to focused `instrument_profiles/` ownership, classified shared Broker contracts as non-feature support, and consolidated profile identity reads and mapping administration within the eleven-feature registry.
- Reassigned `FEAT-BRK-01` to `capabilities/`, made adapter/route traits explicit and fail-closed, moved factory/connection behavior to `_shared/`, and removed the mixed `registry/` implementation folder.
- Consolidated Brokers into five direct provider channels plus reconciliation, environment isolation, event normalization, and conformance; added immutable migration `002_broker_channel_state_v1` for redacted operational checkpoints.
- Returned detached analytical DataFrames directly from the deterministic OHLCV and tick projection helpers, removing unnecessary standard-response unwrapping from consumers.
- Completed the calculable Indicators formula-ownership migration with 64 registered formulas across twelve focused features while leaving unavailable book/trade-dependent formulas fail-closed.
- Folded Indicators `candles/` into `patterns/` and `input_guards/` into `core/`, then renumbered the twelve surviving owners and usage programs contiguously as `FEAT-INDI-01` through `FEAT-INDI-12` while preserving all package-root operations.
- Standardized Indicators calculator usage programs on genuine MT5 `EURUSD` H1 data for the dynamic 100-day interval ending at execution time, with explicit failure output and no synthetic fallback.

#### Fixed (15)

- Made stream reconnection conditional on retryable transport errors so terminal and validation failures return immediately.
- Corrected standalone Broker composition to use database-backed provider enablement and encrypted system credential slots instead of default-disabled Utils settings.
- Rendered the Indicators capability count, resolving the strict frontend unused-state type-check failure.
- Reconciled Utils verification evidence, restored its per-file coverage floor, moved real ZIP rollover IO to integration scope, and documented the completed `AuthContext v2` tenancy/profile split.
- Preserved raw OpenAPI and documentation responses for Swagger rendering and classified unknown routes with the stable `NOT_FOUND` API envelope.
- Reconciled frontend request identifiers with the canonical `req-<UUID4>` contract and rejected incompatible identifiers before authentication or persistence.
- Reconciled current API specifications, tests, and usage evidence to the authoritative 82-operation backend/frontend route inventory, including the authenticated fourteen-feature Data capability surface.
- Restored isolated API lifecycle tests by stubbing post-migration database-backed runtime settings alongside mocked migration success.
- Activated the validated global `LOG_LEVEL` after API migrations while retaining a persistence-independent safe `INFO` logging bootstrap.
- Injected validated database-backed provider enablement into Data/Brokers for the API lifespan, restoring configured MT5 source composition without lower-domain persistence access.
- Made direct supplemental Data provider examples use verified persisted development/demo settings automatically while retaining an explicit offline validation mode.
- Routed canonical secret-safe API request telemetry to both the general application log and specialized access log.
- Restored the Brokers per-file coverage floor and corrected stale architecture claims that its route-discipline requirements and symbol-map application wiring were withdrawn.
- Replaced the inaccessible Dukascopy BI5 tick route with bounded, validated keyless web-chart ticks and enforced applicable Google docstring sections across Brokers.
- Reconciled Data's fourteen-feature registry, schema and usage evidence, applicable Google-style docstrings, per-file coverage, test-tier performance ceiling, and frontend capability presentation.

### Complete Simulator mission and recovery capabilities

Simulator now completes all fourteen registered features with deterministic mission training, scenario and realism providers, durable secured-session recovery, and simulated alert lifecycle evidence.

#### Added (5)

- Added `FEAT-SIM-10` actual-state-bound checklists, four simulation-only assistance modes, governed optional bypass, and Risk-owned safe-stand-down mission completion.
- Added `FEAT-SIM-11` immutable mission definitions, deterministic trigger evaluation, emergency and abnormal templates, total injected-event priority, and Research/Optimization scenario providers.
- Added `FEAT-SIM-12` causal latency, queue-position fills, Decimal slippage and market impact, venue race ordering, no-leakage player views, and Optimization fill calibration.
- Added `FEAT-SIM-13` canonical replay identity, hash-linked secured-session checkpoints, verified restore, practice branching, scored anti-rewind, integrity failure, and explicit rearm under migration `003_simulator_secured_sessions_v1`.
- Added `FEAT-SIM-14` immutable simulated alerts, latched lifecycle, root-cause grouping, perception timing, and emergency-control availability.

#### Changed (3)

- Completed all fourteen Simulator feature registrations and updated the consolidated registry totals to 190 Completed, 0 Partial, 14 Missing, and 204 total.
- Activated the existing Optimization fill/scenario calibration and holdout consumer ports through Simulator-owned providers while retaining fail-closed provider absence.
- Resolved Simulator replay-identity ownership in favor of Simulator and retained UI/API as the external operational-alert delivery owner.

### Complete Utils and Research evidence capabilities

The sixteen formerly partial features are now fully implemented and evidenced,
leaving the consolidated 204-feature registry with no partial entries.

#### Added (3)

- Added Research expectancy provider adapters for Strategy and Risk, plus an Optimization-compatible stress calibration adapter.
- Added immutable Research expectancy-transition, performance-drift, and stress-scenario persistence under additive migration `003_research_governed_evidence_v1`.
- Added standalone usage and targeted unit/integration evidence for `FEAT-RES-14` through `FEAT-RES-16` and complete public-operation usage coverage for all Utils features.

#### Changed (2)

- Completed all fourteen Utils feature registrations, including the function-only shared validation-error constructor used by audited consumers.
- Updated the canonical registry totals to 204 features: 185 Completed, 0 Partial, and 19 Missing.

#### Fixed (2)

- Normalized the complete Research error catalogue to the shared six-category taxonomy so `FEAT-RES-11` workflow failures return their approved structured responses.
- Repaired repository-wide pre-push validation by normalizing remaining domain error categories, restoring Data contract schema identity and deterministic calendar coverage, and correcting Risk usage reconciliation and Agentic migration typing.

### Consolidate canonical feature documentation

Domain documentation now uses the owning `FEAT-*` registry as the only capability
inventory and removes the retired planning namespace and duplicate reconciliation
matrices.

#### Changed (2)

- Reconciled the canonical registry baseline to 204 features; the later completion entry above records the current 185 Completed, 0 Partial, and 19 Missing state.
- Retired the obsolete development planning archive after folding current capability ownership, requirements, and evidence into owning package READMEs.

### Add Portfolio balanced double-entry ledger

Portfolio now owns the application's foundational financial authority: a deterministic balanced double-entry ledger with a chart of accounts, exactly-once economic-event ingestion, settled/unsettled cash with accrued income and costs, reproducible balance rebuild, append-only reversal corrections, and snapshot accelerators validated against canonical entry truth.

#### Added (4)

- Added `FEAT-PORT-09` Balanced Double-Entry Ledger and Accounts (`ledger/`) covering the sixteen posting-type catalogue, balanced postings, exactly-once `(source_event_id, source_sequence)` ingestion, settled/unsettled cash, and rebuild-validated snapshots.
- Added `LedgerEntry v1`, `PostingBatch v1`, and `LedgerAccount v1` JSON-safe `build_*`/`parse_*` contract transports exported from the package root.
- Added migration step `002_portfolio_ledger_schema` creating five append-only ledger tables (`portfolio_ledger_accounts`, `portfolio_ledger_posting_batches`, `portfolio_ledger_entries`, `portfolio_ledger_balances`, `portfolio_ledger_snapshots`) through Data's ledger-verified, write-locked, transactional runner.
- Added the `09_ledger.py` usage program (`FR-PORT-049`..`FR-PORT-055`), `tests/portfolio/unit/test_ledger.py` (34 tests), and `tests/portfolio/integration/test_ledger_persistence.py` (5 tests).

#### Changed (1)

- Migrated the Portfolio error catalogue categories to the Utils-approved uppercase set (`TRANSIENT`/`PERMANENT`/`INTEGRITY`/`POLICY`/`DATA_STALE`/`UNKNOWN_STATE`) so the package imports under the strict error-catalogue whitelist.

### Complete Optimization feature reconciliation

Optimization now covers all 10 approved application capabilities: a versioned OptimizationStudy contract, three now-unblocked EXTEND items consuming the resolved Strategy operating-envelope, Risk TradingPolicyProfile, and Analytics process-scoring providers, and five fail-closed deferred-integration consumer ports for the still-absent Simulator fill/scenario and Risk/Research stress-shock providers.

#### Added (4)

- Added `OptimizationStudy v1` (`parameters/study.py`) carrying dataset/replay identity and approved budget caps behind `build_optimization_study`/`parse_optimization_study`.
- Added the operating-envelope candidate gate (`validation/envelope_gate.py`) consuming Strategy's `evaluate_operating_envelope` to bound searches to approved strategy/instrument envelopes.
- Added multi-objective candidate evaluation (`scoring/multi_objective.py`) combining the core objective with Analytics process-score dimensions, with a critical-failure override so raw profit is never the sole driver.
- Added five deferred-integration consumer ports with fail-closed fallback: fill-model calibration, scenario-difficulty calibration, scenario-holdout anti-leakage, stress-profile calibration, and the promotion gate (`execution/calibration.py`, `validation/scenario_holdout.py`, `robustness/stress_calibration.py`, `evidence/promotion.py`).

#### Changed (2)

- Extended risk-sensitivity analysis to measure outcome sensitivity to Risk TradingPolicyProfile parameters without weakening hard limits (`robustness/risk_sensitivity.py`).
- Reconciled all nine Optimization features as Completed and documented fail-closed provider ports.

### Add Analytics process scoring and repair the error boundary

Analytics now publishes deterministic process-first scoring with a critical-failure override, reproducibility hashes, comparative leaderboard ranking, and no-trade scoring, and repairs the domain error catalog so boundary failures return structured responses instead of raising.

#### Added (4)

- Added `FEAT-ANLT-06` Process Scoring (`scoring/`) covering versioned profiles, deterministic session scores, critical-failure override (invalidate/cap regardless of P&L), reproducibility hashes, comparative leaderboard ranking with profit secondary, and no-trade scoring.
- Added `create_process_scoring_profile`, `create_critical_failure_record`, `build_session_score`, and `compute_leaderboard_ranking` package-root operations.
- Added `analytics.process_score.v1` and `analytics.scoring_profile.v1` JSON-safe `build_*`/`parse_*` contract transports with producer–consumer compatibility tests.
- Added the `06_scoring.py` usage program (`FR-ANLT-061`..`FR-ANLT-066`) and `tests/analytics/unit/test_scoring.py` (25 tests).

#### Changed (1)

- Corrected `ANALYTICS_ERROR_CATALOG` categories to the Utils-approved set so `error_response` no longer rejects the Analytics catalog, repairing a latent fail-closed boundary crash.

### Complete Risk feature reconciliation

Risk now covers all 17 approved application capabilities: config threshold groups, a drawdown state machine, an emergency governor, a continuous-monitoring recalculation classifier, a stop-loss validator, a no-trade outcome classifier, planned risk/reward and cap-of-caps sizing, a strictest-wins effective-rule resolver, a fixed-precedence trade readiness gate, a blocking stress-loss gate, granular kill-switch lock/cooldown, and explainable resize/restrict decision outcomes.

#### Added (5)

- Added `FEAT-RISK-16` deterministic stop-loss side/tick/distance/loss/widening validation.
- Added `FEAT-RISK-17` no-trade outcome classification distinguishing a safe stand-down from failed gameplay.
- Added drawdown state-machine, emergency-governor, and continuous-monitoring-recalculation classifiers to the existing limits, governor, and validity modules.
- Added a fixed-precedence submit-time trade readiness gate composing market, lock, stop, portfolio, and stress checks.
- Added a blocking stress-loss gate alongside Risk's unchanged advisory scenario model.

#### Changed (3)

- Extended position sizing with planned risk/reward and a strictest-of-every-cap normalization.
- Extended the kill switch with additive granular lock permissions and a cooldown/re-arming requirement.
- Extended `RiskDecisionPackage` reporting with resize/restrict outcome classification layered on the authoritative decision state.

### Add Trading protection and ownership contracts

Trading now exposes fail-closed protective-order and trade-ownership capabilities while keeping current execution positions process-local.

#### Added (2)

- Added `FEAT-TRD-10` protective-order plans with versioned transport, exact coverage proof, and exposure-safe residual resizing.
- Added `FEAT-TRD-11` trade-ownership evidence with exclusive assignment and fail-closed orphan detection.

#### Changed (1)

- Completed the Trading execution lifecycle with transactional transition/fill materialization, durable protection/ownership evidence, first-class `UNKNOWN` reconciliation, and migration `004_order_lifecycle_states`.

### Keep current Trading positions memory-only

Trading now enforces its nine-state execution-position lifecycle in injected process memory while retaining `trading_positions` exclusively as the append-only closed-trade ledger.

#### Changed (1)

- Moved active Trading position authority out of durable projections, with restart uncertainty kept `UNKNOWN` until reconciliation and exposure increases blocked while unknown.

### Complete Strategy application planning contracts

Strategy now provides versioned profiles, playbooks, setup evaluations, immutable trade plans, operating envelopes, exit plans, manual-plan parity, and fail-closed expectancy and automation ports while preserving `TradeIntent v1` as the Strategy-to-Risk proposal.

#### Added (3)

- Added `FEAT-STR-12` operating-envelope evaluation with missing evidence restricted by default.
- Added `FEAT-STR-13` immutable exit and management plans with non-executable automation handoffs.
- Added `FEAT-STR-14` manual-plan support through the canonical `TradePlan v1` validation path.

#### Changed (2)

- Extended Strategy profiles, playbooks, setup evaluation, lifecycle governance, automation policy, and expectancy references with strict JSON-safe contract transport.
- Classified Strategy errors under the canonical Utils taxonomy and preserved the authoritative post-migration unsuffixed Strategy table family.

### Add Brokers application contract transport and route discipline

Brokers now publishes the versioned cross-domain contract pairs and the health-aware primary/backup route discipline the capability audit requires, transported as validated JSON-safe mappings behind `build_*`/`parse_*` function pairs.

#### Added (8)

- Added the `FEAT-BRK-16` Health-Aware Primary/Backup Route Discipline feature (`reconciliation/`) with `RoutePlan v1` and `FailoverDecision v1` contracts that are fail-closed, never submit a duplicate order, and never silently reroute a write across brokers.
- Added the `InstrumentVenueProfile v1`, `BrokerHealth v1`, `BrokerAccountSnapshot v1`, and `BrokerReconciliationSnapshot v1` versioned contract build/parse pairs covering instrument/venue rules, normalized health, normalized account reads, and consolidated reconciliation.
- Added a first-class broker-side `UNKNOWN` result for timeouts and lost acknowledgements with a deterministic blind-resubmission prohibition.
- Added safe order command port extensions (`attach_protection`, `reduce_position`) with explicit adapter-boundary idempotency keys and fail-closed unsupported defaults.
- Added ordered, deduplicated broker `EventEnvelope` normalization consuming the Utils `EventEnvelope v1` functions.
- Added one reusable adapter conformance suite (`run_adapter_conformance`) applied uniformly to every enabled route.
- Added the `BrokerUncertainty` and `BrokerResubmissionPolicy` enumerations backing the first-class `UNKNOWN` lifecycle.
- Added the `ATTACH_PROTECTION` and `REDUCE_POSITION` capability identifiers, declared fail-closed `NOT_IMPLEMENTED`/`UNAVAILABLE` for every provider.

#### Changed (3)

- Extended `BrokerOrder`, `BrokerPosition`, and `BrokerCapability` with additive fail-closed fields so existing constructors and tests remain green.
- Extended the capability matrix normative test and adapter mutation sets to cover the two new safe-order write capabilities.
- Updated the Brokers package-root public API to 109 function-only exports carrying the new contract-transport and safe-order operations.

### Add deterministic Indicators operational measurements

Indicators now publishes fail-closed snapshot transports, closed-input guards,
and causal market-speed, trend, structure, liquidity, order-flow, volatility,
and chart-pattern measurements while retaining Risk as regime-policy authority.

#### Added (2)

- Added the versioned JSON-safe IndicatorSnapshot contract with strict producer-consumer validation and explicit completeness, confidence, health, and causal-range evidence.
- Added closed-input enforcement rejecting incomplete, future, stale, unknown, and incompatible timeframe evidence.

#### Changed (1)

- Extended existing mathematical feature owners with neutral operational measurements and remapped Indicators error categories to the current Utils catalogue contract without changing error codes.

### Add Utils application foundation primitives

Utils now provides versioned, fail-closed shared mappings and deterministic business-neutral primitives for later operational-domain integrations.

#### Added (5)

- Added exact unit arithmetic with explicit quantization direction and unit/currency mixing rejection.
- Added generic state-transition evaluation and append-only transition evidence construction.
- Added strict validation outcomes with fail-closed `UNKNOWN` precedence and structured remediation evidence.
- Added owner-bound idempotency keys with explicit TTL and distinct in-flight, completed, and expired verdicts.
- Added versioned hash-derived random streams with cross-process deterministic draws and replay identity.

#### Changed (1)

- Extended Utils with versioned references, time domains, event envelopes, health metadata, audit-sink routing, operational identifiers, and producer-side compatibility evidence while leaving consumer migrations to their owning domains.

### Extend Data real-time streaming with application event coverage

Data's unified market-event model now carries the trade, order-book, venue, and corporate-action event families the capability audit requires beyond quotes and bars.

#### Added (1)

- Added `trade`, `depth`, `venue_state`, `halt`, `auction`, and `corporate_action` event families to the real-time market-event model, each with its own validated payload contract.

### Localize database specifications to owning domains

Database current state, target models, indexes, and reconciliation now live with their owning domain authorities while shared storage architecture remains centralized.

#### Changed (1)

- Folded the centralized schema documentation into each owning package README, relocated its verification gates to `scripts/schema/`, and removed `docs/schema/` as a second domain authority.

### Remediate Portfolio audit controls

Portfolio now has complete requirement usage evidence, an authoritative migration
runner, reachable immutable definitions, and a deliberate UI/API definition surface.

#### Added (3)

- Added Portfolio definition registration and exact-version reads through the function-only package root, API routes, typed frontend client, and Portfolio workspace widget.
- Added the complete-manifest `run_portfolio_migrations` operation and required API startup execution through Data's ledger verification, checksum, write-lock, and transaction runner.
- Added production reachability and compatibility coverage for the Portfolio-owned definition table and contract.

#### Changed (2)

- Completed all Portfolio workflow and functional-requirement usage evidence with actual bounded output and explicit success messages.
- Reconciled Portfolio ownership, schema reachability, logging, tests, and target-versus-live documentation with the production implementation.

### Remediate Research audit controls

Research now has package-root-only consumption, deterministic resource admission,
reachable artifact metadata, and reconciled executable evidence.

#### Changed (1)

- Reconciled Research package-root consumption, deterministic memory admission, Data-backed artifact metadata persistence, intelligence logging, usage evidence, per-file coverage, and target-versus-live schema documentation.

### Remediate Optimization audit controls

Optimization now owns a conforming support layout, authoritative migration runtime,
reachable relational state, per-file verification, and an advisory frontend surface.

#### Added (4)

- Added a documented Optimization `contracts/` support package for shared controlled errors without prohibited package-root production behavior.
- Added the five-file Optimization relational persistence support package tracing results and checkpoints through Data's public transaction boundary.
- Added the complete-manifest `run_optimization_migrations` operation and required API startup execution through Data's ledger, checksum, lock, and transaction runner.
- Added an advisory Optimization workspace widget invoking the typed bounded parameter-sweep client without trading or automatic Strategy-adoption authority.

#### Changed (2)

- Changed Optimization's testing gate to require at least 80% coverage for every production file and sub-100 ms unit-test calls.
- Reconciled Optimization README and schema documentation with the current migration, persistence, usage-program, and UI paths.

### Remediate Analytics audit controls

Analytics now has a function-only public boundary, exact executable feature
evidence, an authoritative migration runner, and no unreachable durable store.

#### Added (3)

- Added package-root `run_analytics_migrations` with Data-owned ledger, checksum, write-lock, and transactional execution.
- Added guarded migration step `002_retire_unused_analytics_derived_store`, which refuses to drop the six historical tables if any contains rows.
- Added focused migration, startup-readiness, workflow, function-boundary, latency, and per-file coverage evidence.

#### Changed (3)

- Changed all five numbered Analytics feature programs to emit explicit requirement success and actual bounded produced data.
- Changed internal long-running behavioral tests into a component tier so the unit tier enforces the 100 ms ceiling.
- Reconciled the Analytics README, architecture, project ownership record, and target schema model with the read-only implementation.

#### Removed (3)

- Removed the duplicate aggregate feature program and enforced exact five-feature-to-five-program reconciliation.
- Removed seven class and type exports from the literal package-root `__all__` function surface.
- Removed the unreachable Analytics CRUD support package and its six empty derived tables from the current target model.

### Remediate Simulator audit controls

Simulator now has a complete migration/readiness boundary, exact executable feature evidence, isolated test tiers, and current target-versus-live schema documentation.

#### Added (3)

- Added package-root `run_simulator_migrations` and executable `FR-SIM-103` evidence for the immutable complete Simulator manifest.
- Added fail-closed API startup coverage for Simulator migration failure and focused branch tests for runtime dependencies, relational persistence, and session lifecycle paths.
- Added a component-test tier for internal filesystem, journal, engine-loop, and orchestration behavior that is intentionally outside the 100 ms unit ceiling.

#### Changed (3)

- Changed all nine numbered Simulator feature programs to emit explicit success and produced-data evidence for every mapped functional requirement.
- Changed Data's Broker symbol-metadata adapter to accept additive provider metadata without allowing unknown fields or provider overrides of Data-owned lineage fields.
- Changed Simulator schema documentation to distinguish the complete target manifest from the inspected non-production database where step 002 remains unapplied.

#### Fixed (4)

- Removed the duplicate aggregate Simulator feature executable and enforced exact nine-feature-to-nine-program reconciliation.
- Removed deep Simulator imports from integration consumers while retaining white-box coverage in component tests.
- Wired the complete Simulator migration manifest into API readiness with Data-owned ledger, checksum, lock, and transactional enforcement.
- Raised every Simulator production file and the aggregate package above the 80% branch-coverage floor while keeping every unit test below 100 ms.

### Remediate Trading audit controls

Trading now exposes an authoritative complete-manifest migration runner, executable requirement evidence, secret-safe virtual workflows, exact API route enforcement, and typed governed frontend mutations.

#### Added (3)

- Added `run_trading_migrations` for the immutable two-step Trading manifest and executable `FR-TRD-077` evidence.
- Added focused coverage for Trading monitoring, state-boundary, and persistence conflict paths.
- Added a 17-operation broker-agnostic Trading walkthrough with one explicit Simulation, MT5, or cTrader target selection and fail-closed provider safety.

#### Changed (5)

- Changed all Trading feature examples to emit requirement success and bounded data evidence.
- Changed live workflow teaching programs to virtual non-production adapters that expose no account snapshots or credentials.
- Changed API and UI mutations to use the exact paper/live route and closed Trading request contract.
- Changed the workspace Trading panel to collect explicit order and authority inputs for governed submit, cancel, and close actions, default to paper, and re-lock after every attempt.
- Expanded the primary Trading workflow into a documented and executable 22-stage virtual pipeline from canonical request through governed outcome.

#### Fixed (3)

- Removed the duplicate legacy Trading usage executable and enforced exact nine-feature-to-nine-program reconciliation.
- Routed current Risk producer contracts through Trading's actual readiness consumer in compatibility tests, including fail-closed non-authorizing states.
- Reconciled Trading persistence, API boundary, virtual workflow, test, and coverage statements across active documentation.

### Expand the primary Risk workflow walkthrough

#### Changed (1)

- Expanded `WF-RISK-PRI` into a labelled 24-stage approved-and-blocked teaching trace with virtual portfolio evidence and a non-executing Trading handoff.

### Add default Risk account profiles

Risk now provides validated personal-account and generic prop-firm paper policies with immutable database registration.

#### Added (2)

- Added the complete operational-limit contract and cross-field fail-closed validation to `RiskConfig`.
- Added idempotent builders and registration for `personal-account-default-v1` and `prop-firm-default-v1`.

### Reconcile Trading closed-position persistence

Trading now stores complete closed trades only and leaves live tick-valued positions to broker/runtime state.

#### Added (1)

- Added a validated insert-only closed-position ledger with exact decimals, MAE/MFE, and slippage points.

#### Changed (1)

- Changed `trading_positions` through immutable migration `002_closed_position_ledger` to the closed-trade schema.

#### Removed (1)

- Removed empty redundant `trading_fills` and `trading_order_transitions` projections after a fail-closed row guard.

### Remediate Risk Domain Audit Controls

The Risk audit remediation corrects all 7 audit findings (`USE`, `COV`, `SCHEMA`, `REACH`, `CONTRACT`, `LOG`, `DOCS`) across Workstreams A through G: adding `register_risk_policy` (`FR-RISK-076`) and `get_risk_policy` (`FR-RISK-077`), executing table rebuild migration `risk-0002-schema-constraints` with `STRICT` mode, `CHECK` constraints and partial indexes, implementing cross-domain producer-consumer compatibility test suites across Trading, Portfolio, API, and Risk, enforcing contract versioning and fail-closed rejection, adding secret-safe semantic logging at public persistence boundaries, updating all 69 requirement usage programs + FR-076/077 to print explicit SUCCESS lines, and raising every Risk production file above the 80% branch-coverage floor.

#### Added (3)

- Added `register_risk_policy` (`FR-RISK-076`) and `get_risk_policy` (`FR-RISK-077`) in `app.services.risk` for durable policy version persistence and canonical hash lookup.
- Added immutable migration `risk-0002-schema-constraints` rebuilding Risk SQLite tables with `STRICT` mode, JSON validity checks, profile/scope/state enums, and partial index `idx_risk_audit_decision`.
- Added producer-consumer contract compatibility integration test suites for Trading, Portfolio, and API domains asserting version, schema ID, required fields, and invalid version rejection.

#### Changed (2)

- Updated all 15 functional requirement usage programs (`01_contracts.py` through `15_reporting.py`) and integration tests to emit explicit `SUCCESS: FR-RISK-NNN` and `Data -> ...` output contracts.
- Added semantic structured logging with trace IDs at public persistence and policy boundaries in `app/services/risk/audit/runtime.py` and `app/services/risk/config/runtime.py`.


### Remediate Indicators Domain Audit Controls

The Indicators audit remediation brings the pure calculation domain into full audit conformance (`USE`, `IT`, `REACH`, `NFR`, `DOCS`, `UI` controls): retiring unused persistence support schema, standardizing requirement output evidence, enforcing a 100 ms unit test latency ceiling, exposing authenticated read-only API routes, and mounting a typed frontend workspace.

#### Added (3)

- Added database migration retiring legacy unused indicator support schema with fail-closed row guards.
- Added authenticated read-only indicator catalog and specification API routes under explicit read permissions.
- Added interactive indicator catalog and specification workspace UI component with search and filtering.

#### Changed (2)

- Standardized indicator requirement usage program execution outputs and evidence logging.
- Isolated live broker indicator test workflows behind an explicit opt-in environment variable.

#### Removed (1)

- Removed unused indicator persistence support package and obsolete storage tests.

### Activate Strategy seven-table database integration

Strategy persistence is upgraded to a production-reachable seven-table model (`strategy_definitions`, `strategy_versions`, `strategy_configs`, `strategy_state`, `strategy_checkpoints`, `strategy_signals`, `strategy_mutations`) backed by immutable migration `0002_strategy_seven_table_runtime`. Seven built-in evaluators are bootstrapped and populated in `data/database/haruquant-dev.db`.

#### Added (3)

- Added immutable migration `0002_strategy_seven_table_runtime` in `app/services/strategy/migrations/definitions.py` and built-in strategy catalogue in `app/services/strategy/registry/catalogue.py`.
- Added standalone public operations for definition, configuration, runtime state, checkpoint, and signal outbox management.
- Added non-production Strategy database population tooling and verification for migration integrity, seven-table production reachability, and internal persistence contracts.

#### Changed (1)

- Extended Strategy persistence package (`create.py`, `read.py`, `update.py`) to support all seven Strategy tables using parameterized statements executed through `app.services.data`.

### Reconcile Strategy mechanical and reviewed audit controls

The Strategy audit remediation isolates SQLite operations from unit tests, fixes contract and response types, enforces unit test execution within 100 ms, removes stale aggregate usage scripts, and updates active package documentation.

#### Added (1)

- Added real SQLite integration coverage for Strategy registry reads, migration checks, and checkpoint restore workflows.

#### Changed (2)

- Reconciled `app/services/strategy/README.md` to index all production feature modules, numbered usage programs, and package status evidence.
- Optimized fixture allocation in unit test suites to keep every individual unit test duration strictly under 100 ms.

#### Removed (1)

- Removed redundant aggregate Strategy feature program, maintaining exact parity across all numbered feature programs.

#### Fixed (2)

- Fixed Strategy internal test models to produce valid `StandardResponse` envelopes and valid immutable mutation/request identity schemas.
- Fixed unit test storage isolation by mocking persistence boundaries to eliminate SQLite setup overhead from unit testing.


### Reconcile Data mechanical and reviewed conformance evidence

The Data audit remediation aligns its focused structure, public-boundary consumers,
standalone workflows, coverage evidence, resource lifecycle, and active documentation.

#### Added (4)

- Added stage-labelled `WF-DATA-020` economic-calendar restriction evidence with honest provider status and deterministic normalized fallback evidence.
- Added stage-labelled `WF-DATA-021` migration, immutable-ledger rerun, backup, restore, and dry-run retention evidence against a disposable approved store.
- Added `FEAT-DATA-18` application-triggered artifact/reference catalog operations, reconstruction evidence, and lifecycle reachability guards for all 23 Data tables.
- Added normalized Forex Factory event definitions, permanent URLs, verified specification metadata, and exact historical occurrence reconciliation through immutable migration `009_economic_event_definitions`.

#### Changed (9)

- Moved Data's function-only construction, getter, and predicate adapters from the package root into documented reconciliation-excluded `_shared/` support while preserving all 253 public functions.
- Migrated external Strategy, Trading, Simulator, and Research tests from private Data modules to the package-root function boundary.
- Reconciled Data's registry, active workflow count, requirement mappings, usage-program count, and completed system-domain status.
- Classified repository-scale and real local-infrastructure checks as structural or component tests so the Data unit suite enforces its 100 ms ceiling without weakening coverage.
- Activated the seven shipped catalog tables behind explicit transactions and made persisted verified-research-source manifests readable instead of write-only.
- Made Economic Calendar reads database-first, added explicit interval coverage, preserved rescheduling evidence, and added bounded CSV, historical Forex Factory, and current-week CSV synchronization through immutable migration `007_economic_calendar_database_first`.
- Added explicit non-production weekly Economic Calendar job scheduling and dispatch through additive migration `008_data_jobs_environment` while preserving existing market-job behavior.
- Replaced credit-dependent historical Forex Factory backfill with bounded credential-free Jina Reader acquisition, coverage-ledger resume, timezone-aware parsing, and retryable interval execution.
- Versioned Data quality evidence to percentage scoring with descriptive grades, explicit operational decisions, and decision-based downstream gates.

#### Fixed (4)

- Fixed Data Feature Registry parsing so all seventeen padded Markdown rows reconcile with their production folders.
- Fixed Data per-file coverage gaps in runtime codecs, cache deletion, and dashboard evidence.
- Replaced a real-time cache-expiration sleep with the supported injected clock and added explicit resource-warning verification.
- Removed the stale feature usage aggregator from canonical execution parity and included all seventeen numbered programs.

### Reconcile Brokers mechanical-conformance audit evidence

The Brokers Tier-1 audit found broken workflow usage imports, a padding-brittle
registry parity check, undocumented symbol-map persistence support, vacuous
usage-program success on evidence failure, and a flaky coverage gate; all are
now reconciled with their executable evidence.

#### Removed (1)

- Removed the orphaned `tests/brokers/wf_support.py` helper; workflow usage programs share the re-export boundary at `tests/brokers/usage/_support.py`.

#### Fixed (5)

- Fixed the nine Brokers workflow usage programs' shared-support import so `run_all.py` executes 10/10, and extended the workflow parity check to resolve every top-level local import.
- Fixed the executable registry parity check to tolerate README table padding in the usage-evidence column.
- Documented the Brokers `migrations/` and `persistence/` support directories and added pytest evidence for the symbol-map CRUD statements and the broker dashboard snapshot.
- Fixed the twelve Brokers feature usage programs to exit non-zero on evidence failure instead of passing vacuously.
- Fixed the flaky Brokers coverage gate by pinning `COVERAGE_CORE=pytrace`, avoiding the coverage.py 7.14.2 `sysmon`/CPython 3.14 asyncio running-loop race.

### Resolve the recorded UI/API exclusions

Live execution, external import, documentation scope, and the Simulator
live-engine gap are all resolved. The UI/API boundary now carries no `Partial`,
`Missing`, or `Excluded` row.

#### Added (6)

- Added governed external dataset import plus a dialect read delegating to Data's own parser, validator, and storage.
- Added `advance_run_timeline`, a behaviour-preserving extraction of the Simulation tick loop that can advance in bounded increments.
- Added `prepare_run_context`, which separates assembling a run from executing it, so a run can be opened without being driven to completion.
- Added bounded live what-if sessions to the Simulator: open, step, read, branch, and close over a resumable engine, with branches replaying parent inputs on their own engine so the parent is never mutated.
- Added the five gateway live-session operations and a `liveSimulation` typed client, taking backend v1 to 71 operations with matching frontend parity.
- Added `WhatIfView`, kept deliberately separate from `PlaybackView`: a finalized run is evidence and must not be steerable.

#### Changed (5)

- Changed the live what-if exclusion test into a shape invariant: what-if is now reachable, but only as a session with recorded lineage, so no route may mutate a completed run in place.
- Changed the Simulation routes' rate-limit class from `read` to `compute`. The compute class keyed on the owner string `simulation`, but every Simulation route declares its owner as `simulator`, so backtest runs had silently been limited as if they were reads.
- Changed Trading's execution boundary from a hardcoded live ban to a configured-route match: paper and live share one path, and live additionally requires explicit enablement.
- Changed the rebalance boundary and Trading session read to accept the live route, matching the construction contract that already did. Rebalance now applies Trading's execution gate rather than its own hardcoded refusal, so the two governed capital paths cannot disagree about whether a live request is reachable.
- Changed the documentation capability to withdrawn scope: `NFR-API-015` and `CAP-UI-019` are retired to Appendix R rather than carried as standing exclusions.

### Close the UI/API boundary at 64 operations with full frontend parity

The gateway now exposes every capability its owner domains can produce, the
frontend declares the same inventory, and each remaining exclusion carries a
recorded reason and an absence test.

#### Added (9)

- Added the governed Portfolio allocation lifecycle: activation, rollback, drift assessment, rebalance submission, and measurement recomputation at five new operations.
- Added governed Strategy registration and parameter updates behind an explicitly composed Strategy validation policy.
- Added governed dataset preparation, delegating fetch and persist to Data and returning the owner-authored storage manifest.
- Added the governed Risk kill-switch command, requiring a human operator, an approval attestation, and an explicitly composed Risk authority bundle.
- Added one shared `run_idempotent_write` reserve-execute-finalize cycle so governed routes no longer re-implement durable HTTP idempotency.
- Added typed frontend clients and route contracts for Portfolio, Optimization, Agentic, and journal playback, reaching 64 declared operations.
- Added the completed-run journal playback view, closing the frontend half of `CAP-UI-012`.
- Added `run_idempotent_write_async` so the three asynchronous Trading mutations reserve durably before the awaited call and finalize after it.
- Added request-time runtime-policy enforcement: a Trading mutation whose declared profile or route contradicts the deployment is refused before delegation.

#### Changed (4)

- Changed `FR-API-056` and `WF-API-017` to completed: Portfolio evidence and review are reachable through the public workflow handle, so no owner-domain change was required.
- Changed `WF-API-018` and `FR-API-068`–`FR-API-072` from a stale excluded status to completed, matching the Agentic operator tier already present in the code.
- Changed `DATABASE_URL` and `DATA_DIR` from missing to declared settings that name the shared store without exposing a connection.
- Changed the excluded families to authoritative exclusions, each recording whether it is blocked upstream, by safety policy, or by owner scope.

#### Fixed (2)

- Fixed the UI/API specification to match the merged code: the package tree omitted eight route files and five composition modules, and understated the frontend surface.
- Fixed the in-process provider manifest ordering, which is derived from binding insertion order and is contractually required to be sorted.

### Align architecture documentation with the completed Utils boundary

Stale status and settings references in `docs/ARCHITECTURE.md` are corrected to
the completed, function-only Utils package boundary.

#### Fixed (1)

- Fixed `docs/ARCHITECTURE.md`: Utils is a completed (not partial) implementation baseline, and settings bootstrap references the public `app.utils` settings boundary instead of the internal `AppSettings` symbol path.

### Add completed-run journal playback sessions

Simulation journals can now be traversed frame by frame over a resumable,
quota-governed SSE boundary without retaining a live engine.

#### Added (3)

- Added durable one-hour `sim_sessions` rows with completed-run validation and monotonic sequence cursors.
- Added two-pass, constant-memory hash-chain validation and raw journal-event playback from finalized JSONL artifacts.
- Added idempotent session creation and resumable SSE frame delivery at two new `/api/v1/simulation/sessions` operations.

#### Changed (1)

- Changed `FR-API-027` and `WF-API-007` to completed for the journal-playback tier while retaining `WF-API-008` live mutation/what-if as excluded.

### Bridge Optimization public operations behind the API gateway

The UI/API gateway now composes the Optimization domain's typed public API and
exposes its ten run/read operations plus one durable result read as governed
HTTP routes, mirroring the existing Simulation and Portfolio bridges.

#### Added (4)

- Added eleven `/api/v1/optimization` HTTP routes (`FEAT-API-07` / `FR-API-030`) covering the four governed runs, six read-only analyses, and one result read behind an explicitly composed Simulation/Analytics adapter.
- Added `app/services/api/composition/optimization_dependencies.py` composing the Optimization receiver-owned dependency bundle and `optimization.source` to the in-process provider graph with fail-closed default composition.
- Added the `load_result` operation to the `OptimizationStateStore` protocol and the public `load_optimization_result` read function backing the durable result route.
- Added `tests/api/unit/test_optimization_routes.py` covering dispatcher conversion, fail-closed behaviour, the discriminated robustness variant, and the read permission and 404 paths.

#### Changed (1)

- Changed the canonical route catalog and OpenAPI snapshot to fifty-four operations and removed the Optimization route-absence contract assertions.

### Close Utils public-boundary deep imports

Shared settings-integration helpers join the Utils public boundary, and every
in-scope consumer imports strictly through package roots.

#### Added (1)

- Added `get_app_settings_model_config` and `get_app_settings_sources` to the `app.utils` public boundary for typed domain settings infrastructure.

#### Changed (1)

- Moved three process/IO-bound Utils boundary proofs from unit to integration scope to restore the 100 ms unit-test ceiling.

#### Fixed (2)

- Fixed eight deep `app.utils.*` import sites in API/Data settings infrastructure and Research/Broker test consumers to use the documented public boundary.
- Fixed the malformed `FR-UTL-029` requirement row and restored per-file coverage evidence for the settings feature boundary.

### Establish two-tier system audit matrix

Domain status becomes an evidence-backed conformance record spanning architecture,
safety, and quant-correctness dimensions, with an advisory sweep for the
mechanically decidable subset.

#### Added (2)

- Added `scripts/audit_check.py`, an advisory Tier 1 sweep reporting registry, boundary, import, structure, evidence, test, coverage, and hygiene conformance per domain.
- Added an eighteen-row two-tier audit matrix that covers the system, configuration, frontend, and schema-model surfaces alongside the fourteen domains.

#### Changed (1)

- Changed Section 9.1 domain status from six existence checkboxes to twenty conformance dimensions requiring recorded `path:line` evidence.

### Unify user and system settings persistence

UI/API now owns one scoped settings store while central typed configuration remains
the bootstrap authority required to open the database.

#### Added (2)

- Added immutable migration `api-0006`, which copies legacy user documents into scoped `api_settings`, verifies exact row preservation, and removes the superseded table.
- Added admin-authorized global system settings reads and updates through the existing canonical settings route and API public boundary.

#### Changed (2)

- Changed user and system settings to share one versioned, bounded, secret-safe document contract keyed by derived scope and subject.
- Changed `DataSettings` to consume the central `app/configs/env.json` and process-override source order already used by other typed domain settings.

### Complete schema and persistence programme

The final API normalization, ledger repair, and schema-tooling decisions close the
schema programme without deleting development identity state or inventing absent
business producers.

#### Added (2)

- Added normalized API roles, permissions, role-permission grants, and scoped account bindings through immutable migration `api-0005`.
- Added complete-manifest migration validation that rejects applied ledger IDs absent from the owning code manifest.

#### Changed (5)

- Changed API account and session authority reads to normalized RBAC tables while retaining immutable-baseline JSON columns as dormant compatibility fields.
- Retained decimal-string Parquet values as the canonical precision-safe policy until bounded native-decimal scale metadata exists.
- Recorded genuine Brokers usage programs as manual, credential-gated non-production evidence rather than ordinary CI execution.
- Made licensed calendar, live research-provider, and genuine MT5 workflow verification explicit opt-ins so ordinary CI opens no provider connection.
- Reconciled system workflow evidence with owner-domain mutation APIs while retaining the backend-v1 exclusion of Strategy and operator kill-switch mutation routes.

#### Fixed (5)

- Repaired the development-only orphan `api-0004` ledger row after an immutable backup while preserving the existing account and sessions.
- Made the twelve-check schema verifier typed, formatted, resource-safe, and Ruff-clean.
- Synchronized migration-manifest, public-export, Trading catalogue, AuthContext compatibility, and relational usage evidence with the completed schema programme.
- Preserved function-only public ports while distinguishing mandatory Data persistence delegation from business-domain dependency cycles.
- Included the registered runtime-record step in Data's complete ordered migration manifest so a fresh database cannot create a future ledger orphan.

### Complete Agentic relational persistence

Agentic workflow, memory-record, lifecycle, and operations state now uses eight
Agentic-owned relational tables instead of the generic Data runtime-record store.

#### Changed (3)

- Changed active Agentic durable stores to construct direct relational operations through Data's public statement-plan and transaction boundary.
- Made workflow idempotency and revision guards, incident uniqueness, lifecycle sequencing, and immutable packet, trace, and replay writes survive process reconstruction.
- Expanded the unapplied Agentic baseline columns so checkpoints, lifecycle concerns, promotion evidence, trace spans, incident evidence, and replay outcomes round-trip without invented or discarded fields.

### Complete Simulator relational persistence

Simulator lifecycle and completed-result state now uses `sim_runs` directly, while
its canonical journal remains an append-only JSONL artifact rather than database
state.

#### Changed (3)

- Changed Simulator run identity, lifecycle, idempotency, and completed-result persistence to construct direct `sim_runs` operations through Data's public statement-plan and transaction boundary.
- Replaced generic runtime-record journal staging with partial canonical JSONL, reconstruction-safe sequence validation, group-commit `fsync`, and atomic final publication.
- Made lifecycle transitions compare request hash, run identity, prior status, and prior result material so identical replay is idempotent and stale or terminal mutation fails closed.

### Complete Portfolio relational persistence

Portfolio durable state now uses its owned relational tables instead of the generic
Data runtime-record store while preserving Portfolio's opaque public state boundary.

#### Changed (3)

- Changed construction results, allocation versions, active scope pointers, idempotency bindings, rebalance plans, and audit-outbox persistence to construct direct relational operations through Data's public statement-plan and transaction boundary.
- Made construction-plus-outbox, plan-plus-outbox, and allocation-plus-idempotency-plus-active-scope-plus-outbox writes atomic and fail closed on identity conflicts, stale revisions, or mismatched predecessors.
- Left `portfolio_definitions` without a runtime producer because no registered Portfolio command currently creates definitions; no speculative business record is synthesized to populate the table.

### Complete Risk relational persistence

Risk durable state now uses its owned relational tables instead of the generic Data
runtime-record store while preserving Risk's existing public contracts and Data's
connection and transaction ownership.

#### Changed (4)

- Changed Risk approval, audit, eligibility, allocation, kill-switch, and canonical decision persistence to construct direct relational operations through Data's public statement-plan and transaction boundary.
- Made approval consumption, allocation activation, and kill-switch-plus-audit updates atomic and fail closed on stale revisions, predecessors, chain heads, or identity conflicts.
- Exposed `run_risk_migrations` through the Risk package root so application composition and integration evidence can apply the immutable Risk manifest without importing private migration definitions.
- Removed the obsolete generic-store sequence allocator from canonical decision persistence, allowing every decision identity accepted by `RiskDecisionPackage v1` to round-trip through `risk_decision_snapshots`.

### Complete Trading relational persistence and Phase 4D materialization

Trading durable state now uses its owned event, idempotency, projection, order, fill,
position, and transition tables instead of the generic Data runtime-record store.

#### Added (2)

- Added `trading_orders`, `trading_fills`, `trading_positions`, and `trading_order_transitions` to the unapplied Trading baseline with the model's indexes and fail-closed constraints.
- Added atomic event-to-table normalization and integration evidence covering a nullable TIF, authority-time fills, current positions, and order transitions.

#### Changed (2)

- Changed Trading persistence to construct direct relational operations while delegating connections, locking, bounded execution, and transactions to Data's public boundary.
- Made `trading_orders.time_in_force` nullable so persistence preserves an omitted governed instruction rather than inventing a broker default.

### Add protected workflow pages — frontend build complete (FEAT-API-12, Section 4.12)

The fourth and final frontend feature delivers the access gate (`/login`) and the protected workspace composition point. The frontend build is now complete: Sections 4.9–4.12 (typed transport, session/page/governed/stream context, workflow components, protected pages) are all implemented.

#### Added (3)

- Added `app/ui/src/app/authentication-page.tsx` (`AuthenticationPage`), a dedicated `/login` route segment (`app/ui/src/app/login/page.tsx`) for the access gate with login/register toggle and clean session-recovery handling.
- Added `app/ui/src/app/protected-layout.tsx` (`ProtectedLayout`) which gates the widget workspace on the authenticated session and redirects unauthenticated visitors to `/login`, plus `workflow-page.tsx` (`WorkflowPage`) composing the protected workspace from the public surface.
- Added three unit test files and the numbered usage program `tests/api/usage/17_frontend_pages.tsx`.

#### Changed (1)

- Rewired the root route `app/ui/src/app/page.tsx` to delegate to `WorkflowPage` (was `<App/>`); marked `FEAT-API-12` and Section 4.12 functional requirements `FR-API-053`–`FR-API-055` `Completed` in the API README.

### Add workflow presentation components and grow the frontend route catalog to 32 (FEAT-API-11)

The third frontend feature delivers the auth-aware shell and the freshness-aware dashboard, read-only strategies, backtest simulation, risk state, trading session, and Edge Lab research views — the first components to render real backend data through the typed clients and auth context. The frontend route catalog grows from 23 to 32 to match the backend bridge entry below, completing Section 4.11 with no Excluded requirements remaining.

#### Added (3)

- Added `app/ui/src/components/workflow/` with `AppShell` (first `useAuth` consumer, error boundary), `DashboardView` (six parallel snapshots, stale warnings), `StrategyWorkspace` (read-only catalogue), `SimulationView` (run + lookup), `RiskView` (kill-switch + decisions), `TradingView` (session + governed actions disabled until preflight), and `ResearchWorkspace` (advisory report).
- Added the `simulation`, `risk`, and `trading` typed clients and wired the nine new routes into the frontend catalog, the drift test, the Sidebar ADD-WIDGETS catalog, and the WorkspaceGrid render switch.
- Added seven Vitest component tests and the numbered usage program `tests/api/usage/16_frontend_components.tsx`.

#### Changed (1)

- Marked `FEAT-API-11` and Section 4.11 functional requirements `FR-API-046`–`FR-API-051` `Completed` in the API README; no Section 4.11 requirement remains Excluded or Pending.

### Add Simulation, Risk, and governed Trading backend bridges

Backend v1 now exposes the owner-domain prerequisites for the deferred Simulation and Risk/Trading frontend work while keeping UI/API limited to transport and composition.

#### Added (4)

- Added synchronous canonical and portfolio Simulation run routes plus durable result retrieval, backed by explicitly composed Simulator ports and atomic lifecycle/result persistence.
- Added exact-scope Risk kill-switch reads and bounded newest-first immutable Risk decision reads through Risk-owned persistence.
- Added exact-scope Trading session reads and governed submit, cancel, and close routes through Trading public operations.
- Added route, composition, persistence-boundary, OpenAPI, and production-exclusion tests for the new operations.

#### Changed (2)

- Increased the backend-v1 route registry from 23 to 32 operations while leaving the frontend's existing 23-operation transport catalog for its separate follow-up.
- Excluded production-capital execution at the API boundary; only explicitly configured paper dependencies may execute mutations, and missing owner references fail closed.

### Adopt /auth/me identity recovery and add the SSE stream consumer (FEAT-API-10 closeout)

The frontend context layer now uses the server-authoritative identity route and ships the previously-deferred stream consumer, completing FR-API-045 and closing the two informational blockers that depended on backend routes added in the streaming-bridges entry below.

#### Added (4)

- Added `app/ui/src/context/streams.ts` (`consumeStream`, `StreamGapError`) with monotonic-sequence validation, heartbeat filtering, terminal-error surfacing, bounded reconnection after transient gaps, and an `onGap` hook for authoritative refresh over `GET /api/v1/data/stream`.
- Added the low-level SSE transport `app/ui/src/clients/stream.ts` (`openStream`) that opens an authenticated `fetch` streaming connection, parses `text/event-stream` frames, and yields Zod-validated `StreamEvent` objects.
- Added `StreamEvent`/`StreamEventType` schemas to `clients/contracts.ts`, plus `auth.me()` and `data.stream()` typed client wrappers and the `StreamTransportOptions` surface.
- Added unit tests for the stream consumer and the `auth.me` recovery path, and a `testUsageConsumeStream` case in the numbered usage program 15.

#### Changed (2)

- Refactored `AuthProvider` to recover identity server-authoritatively via `GET /api/v1/auth/me` (replacing the readiness-probe workaround); `sessionStorage` now mirrors identity only as a display fallback, and the session token never leaves the HttpOnly cookie.
- Grew the frontend route catalog from 21 to 23 operations by adding `api.auth.me` (auth-required, no permission) and `api.data.stream` (SSE, `StreamEvent.v1`); the drift test now asserts the 23-operation inventory and the new `authRequired`/`stream` route flags.

### Add Data-owned MT5 streaming and backend recovery bridges

The backend now resolves both prerequisites previously deferred by the frontend while preserving the gateway as orchestration only: Data owns genuine MT5 tick/bar acquisition and UI/API owns authenticated transport.

#### Added (4)

- Added Data-owned `ticks` mode, which delivers every MT5 tick independently of the selected display timeframe through bounded overlapping reads with multiplicity-preserving deduplication and explicit saturated-batch gaps.
- Added Data-owned `bars` mode, which emits genuine closed MT5 bars at canonical timeframe boundaries such as M1, M5, and H1 without publishing partial or fabricated bars.
- Added shared bounded Data stream fan-out with monotonic cursors, heartbeats, retained resume, explicit slow-consumer termination, and last-subscriber provider cleanup.
- Added authenticated `GET /api/v1/auth/me` identity recovery and `GET /api/v1/data/stream` SSE transport, increasing the backend-v1 registry from 21 to 23 operations.

#### Changed (2)

- Assigned MT5 market-stream business behavior to `app.services.data.realtime_feeds`; UI/API performs permission/quota checks, event translation, SSE framing, and resource cleanup only.
- Reclassified the frontend stream-consumer blocker: its backend SSE prerequisite now exists, while implementing `FR-API-045` and adopting `/me` in `AuthProvider` remain separate frontend work.

### Add frontend session and page context (FEAT-API-10)

The second frontend feature delivers the React context layer that recovers the authenticated browser session, registers bounded redacted page context, and preflights governed writes — the bridge between the typed clients (FEAT-API-09) and the widget workspace.

#### Added (3)

- Added the frontend context package `app/ui/src/context/` with `AuthProvider` (readiness-probe session recovery + non-secret identity in sessionStorage), `PageContextProvider` (≤200 visible ids, dedup, sensitive-key rejection), and `buildGovernedOptions` (30s preflight, auto idempotency key, advisory client check).
- Added Vitest unit tests (jsdom + Testing Library) and the standalone numbered usage program `tests/api/usage/15_frontend_context.tsx`, plus the `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`, and `@vitejs/plugin-react` dev dependencies.
- Added the `tsconfig.usage.json` automatic-JSX-runtime config and mounted `<AuthProvider>` in the root App Router layout so session recovery covers every route.

#### Changed (1)

- Marked `FEAT-API-10` and Section 4.10 functional requirements `FR-API-042`–`FR-API-044` `Completed` and `FR-API-045` `Pending` (no backend stream route exists today) in the API README.

#### Deprecated (1)

- Deprecated the stream consumer `FR-API-045` from the Section 4.10 scope: it is deferred pending a backend stream route, so no `streams.ts` ships in this feature.

### Add typed frontend transport (FEAT-API-09)

The first frontend feature delivers the single typed client transport layer that maps the 21 frozen backend-v1 operations to typed TypeScript calls, so the CME-style widget workspace can reach real backend data through one contract-validated entry point instead of parallel ad-hoc fetch helpers.

#### Added (3)

- Added the typed frontend transport package `app/ui/src/clients/` with a Zod-validated `ApiResponse` envelope mirror, frozen `RouteContract` definitions for the 21 registered operations, the single `request`/`unwrapData`/`ApiClientError` primitive, and nine focused domain clients aggregated into one `apiClients` catalog.
- Added Vitest unit and drift tests plus the standalone numbered usage program `tests/api/usage/14_frontend_clients.ts`, and a `next.config.mjs` same-origin rewrite proxy so session and CSRF cookies stay first-party in development.
- Added the `zod`, `vitest`, `tsx`, and `@vitest/coverage-v8` frontend dependencies and the `vitest.config.ts` runner configuration.

#### Changed (1)

- Corrected the planned `ui/` package tree in the API README to the actual single-page widget-workspace architecture and marked `FEAT-API-09` and the Section 4.9 functional requirements `Completed`.

### Withdraw feature status from the four persistence packages

Schema and CRUD are internal support, not capabilities. Registering them as features implied a public API that no domain exported, and produced registry rows whose stated evidence could not satisfy the usage-program contract. The registrations are withdrawn; the evidence they were meant to carry is kept as unit tests instead.

#### Changed (2)

- Withdrew `FEAT-DATA-18`, `FEAT-INDI-07`, `FEAT-ANLT-06` and `FEAT-BRK-16` along with their `FR-DATA-154`–`160`, `FR-INDI-036`–`040`, `FR-ANLT-055`–`059` and `FR-BRK-136`–`138` rows, and deleted the four numbered usage programs. The tables, migrations and private CRUD modules are unchanged and still applied; only their status as registered features is.
- Recorded `migrations/` as a support directory in the Data import-graph test, on the same reasoning: it holds schema definitions applied by the runner in `persistence/` and carries no feature identity.

#### Added (2)

- Added `tests/data/unit/test_catalog_schema.py`, `tests/indicators/unit/test_persistence_schema.py`, `tests/analytics/unit/test_persistence_schema.py` and `tests/brokers/unit/test_symbol_map_schema.py` — twenty-two tests asserting the invariants the withdrawn requirements described, against the shipped schema statements: the overlap predicate that `BETWEEN` gets wrong, the fail-closed integrity gate, duplicate formula versions, null measurements without a declared insufficient sample, and duplicate active symbol mappings.
- Added `docs/schema/verify_persistence_sql.py`, which asserts that every table named in a persistence SQL literal has a creating statement. Nothing else connected those strings to the migrations.

#### Fixed (5)

- Fixed ten statements still reading `hq_runtime_records` after the table was renamed to `data_runtime_records`. The migration had been updated and the statements that read it had not, so every one would have failed on first apply for trading, risk, portfolio, simulation, and agentic persistence alike.
- Fixed an identifier collision in which `FR-DATA-154` through `FR-DATA-157` named both the MT5 streaming requirements and the artifact-catalog requirements. Withdrawing the catalog rows leaves the streaming allocation intact.
- Fixed the reconciliation record, which listed Trading materialisation as delivered. `trading_orders`, `trading_fills`, `trading_positions` and `trading_order_transitions` exist in the model and in no migration; the comparison script now lists the twenty-six model tables no module creates, rather than reporting no drift for tables it never compared.
- Fixed the model's `data_migration_ledger.applied_at_ns` column, transcribed as `INTEGER` when the shipped column is `TEXT` with a nineteen-digit `GLOB` check that rejects a truncated or second-resolution stamp at write time.
- Fixed index-name extraction in the schema harness, which consumed `IF NOT EXISTS` as the name and reported two partial unique indexes as `IF`.

### Add Indicators, Analytics, and Brokers persistence

Three domains that previously owned no tables gain schema and private CRUD, following the artifact-catalogue pattern.

#### Added (4)

- Added indicator definition, parameter-set, and materialisation-reference tables, with generated columns exposing the frequently filtered parameter keys, plus create, read, update, and delete operations.
- Added the analytics derived store: metric definitions and values, closed round-trip analysis, profit attribution, equity-curve summaries, and generated reports, with create, read, and update operations.
- Added bitemporal provider-to-canonical symbol mapping for brokers, with forward, reverse, and point-in-time resolution.
- Added thirteen requirements across the three domains covering migration location, causality declaration, staleness invalidation, sample-size honesty, excursion recording, and mapping uniqueness.

#### Changed (3)

- Recorded indicator and analytics persisted state as delivered in the system data-ownership register, and named symbol mapping as the sole broker persisted state.
- Extended the model-versus-code comparison to the four new migration modules.
- Recorded that analytics and brokers delete nothing while indicators may purge materialisations, since a materialisation is recomputable and a mapping or measurement is evidence.

#### Fixed (1)

- Fixed column parsing in schema tooling that split definitions by line, so a wrapped constraint or generated-column expression was read as two entries and produced fragments as column names; inline comments are now stripped before splitting.

### Add the artifact catalog

The storage model chosen earlier — broker as runtime source, files as the pinned store — had no index. Seven tables now catalogue what has been written, so a pinned read selects the artifacts it needs by recorded time range instead of walking the artifact tree.

#### Added (4)

- Added seven catalogue tables covering instrument, provider, and session reference data, a logical dataset registry, a per-artifact index, a fetch log, and a quality-event log, as one additive migration step.
- Added create and read operations for the catalogue to the data persistence layer, including artifact selection by overlapping time range, the integrity gate, and coverage reporting.
- Added seven requirements covering manifest-derived rebuildability, the overlap predicate, the fail-closed integrity gate, write ordering, fetch-source recording, timestamp semantics, and quality-event attribution.
- Added usage evidence exercising every catalogue operation, including a demonstration that the naive range predicate silently drops an artifact that begins before the requested window.

#### Changed (3)

- Rewrote the artifact-layout and read-path sections to describe what the artifact writer actually does: one content-addressed file plus a sidecar manifest, written atomically, with no directory partitioning.
- Withdrew directory partitioning from the storage model. An index that prunes by recorded time range is more precise than one that prunes by directory name and needs no filesystem access, so partitioning by path became redundant once a catalogue existed.
- Recorded storing prices as decimal strings rather than a decimal logical type as an open improvement: the current form is precision-safe but forgoes numeric predicate pushdown.

### Record every shipped table in the schema model

Thirteen tables that ship today were absent from the model, which asserted authority over the target schema while omitting parts of the current one. The model now records all of them.

#### Added (2)

- Added eight operational and reference tables from the data domain, four from the interface domain, and one strategy mutation-command table to the schema model, generated from their conformed definitions so model and code cannot drift.
- Added a reconciliation section recording that model completeness is closed, that nine applied tables track time through purpose-specific columns rather than a creation timestamp, and that four applied strategy tables predate the strict-typing convention.

#### Changed (2)

- Extended the audit-column exemption in schema verification from two tables to nine, each annotated with the timestamp column it uses instead, and added an exemption for one applied table that tracks progress without a modification timestamp.
- Relaxed the namespace-coverage check to accept a ratified but deliberately unused namespace, now that the utility framework owns no tables.

### Separate Data schema definitions from the migration runner

Data's schema definitions move to the domain migration package while the shared migration runner stays in the persistence layer, completing the canonical migration layout across every domain.

#### Changed (2)

- Moved Data's own table definitions into the domain migration package, leaving ledger initialisation, checksum comparison, write-lock acquisition, and step application in the persistence layer under the shared-infrastructure exemption. The two applied statement sets were moved unchanged, so their recorded checksums still match.
- Documented that the definitions package must not re-export the runtime-store runner, since doing so makes importing the runner initialise a package that imports the runner back.

#### Fixed (1)

- Fixed a circular import introduced when the research-source definitions were relocated: importing the migration runner initialised the definitions package, which imported the runtime-store module, which imported the half-initialised runner.

### Conform Agentic and Data schema definitions

The final two definition owners move to canonical per-domain migration packages, completing the relocation across every domain that owns schema. The model absorbs seventeen shipped tables it had not recorded.

#### Added (3)

- Added the thirteen shipped Agentic tables and four shipped Data research-source and runtime tables to the schema model, recorded from the conformed definitions so model and code cannot drift apart.
- Added strict typing, creation timestamps, and request and correlation identifiers across all seventeen tables.
- Added five requirements covering migration location, strict typing and traceability, sequence uniqueness, the runner-versus-definition split, and research-source traceability.

#### Changed (4)

- Relocated five Agentic migration definitions into one package with a submodule per feature area, and two Data definitions into a Data migration package, leaving the shared migration runner in place under its infrastructure exemption.
- Renumbered the Agentic experimentation migration from sequence two to sequence five; two migrations previously claimed the same sequence, leaving apply order ambiguous.
- Renamed the runtime-record table into the ratified data namespace and corrected its ledger domain, which previously matched no folder, prefix, or ownership entry.
- Corrected the simulator ledger domain to match its owning package and dropped its non-standard checksum prefix so every domain stores a bare digest.

#### Fixed (1)

- Fixed the audit-column check in schema verification to exempt append-only tables, where a modification timestamp would wrongly imply a row can be revised.

### Conform Portfolio, Optimization, Research, and Simulator schema definitions

Four further domains move to the canonical per-domain migration package. In each case the schema model adopts the shipped design rather than the reverse, because the shipped design already satisfied the conventions the model was reaching for.

#### Added (2)

- Added request, correlation, and audit-timestamp columns across all eleven tables in the four domains, plus publication tracking on the portfolio audit outbox and covering indexes for scope, reproducibility, and audit lookups.
- Added a model-versus-code comparison script that reports column divergence per table and exits non-zero on mismatch.

#### Changed (4)

- Adopted the shipped Portfolio design into the schema model: composite-key immutable definition and plan history, a separate current-version pointer under a compare-and-swap guard, and no foreign keys, since version rows must survive independently.
- Adopted the shipped Optimization and Research designs into the schema model: a search identified by its own key with ranked candidates as a payload, and an artifact table that is a file manifest rather than a general catalog.
- Renamed the simulator run-identity table into the ratified abbreviated namespace and recorded that the canonical journal remains append-only newline-delimited JSON with no backing table.
- Relocated four domains' migration definitions into per-domain migration packages and repointed their public re-exports, requirement records, and test fixtures.

#### Removed (1)

- Withdrew the proposed separate portfolio definition-version table and three other unbuilt tables from the active model, demoting them and eleven others to an explicitly labelled target-only section.

#### Fixed (1)

- Fixed a constraint matcher in schema tooling that matched clause keywords as line prefixes and therefore silently discarded any column whose name began with one of them, hiding eight columns from every model-versus-code comparison.

### Conform Trading and Risk schema definitions to the authoritative model

Trading and Risk migration definitions move to the canonical per-domain migration package and adopt the model's audit, traceability, and strictness conventions. Neither step had been applied to a database, so both definitions are edited in place rather than extended.

#### Added (3)

- Added monotonic sequence, unique event identity, aggregate-version uniqueness, correlation and causation identifiers, and audit timestamps to the trading event log, so two concurrent writers computing the same next version collide at insert instead of double-appending.
- Added the consumed event-log position to trading projections, giving rebuilds a resume point and readers a staleness check.
- Added eight requirements covering migration location, strict typing, audit and traceability columns, and additive-only evolution across the two domains.

#### Changed (3)

- Declared every Risk table strict and gave each one creation, request, and correlation columns, with modification timestamps on the mutable ones.
- Adopted the shipped Risk table names and the eligibility versus allocation split into the schema model, rather than renaming the domain to match an independent design; the two decisions are made by different authorities on different cadences.
- Relocated Trading and Risk migration definitions into per-domain migration packages and repointed the state re-exports, requirement records, and unit tests.

### Close every open schema decision

All seven remaining schema decisions are resolved and written into the authoritative specifications; the system open-decisions section is now empty.

#### Added (1)

- Added an append-only portfolio definition version table so configuration history is immutable while child foreign keys continue to resolve against a single-column parent key, satisfying the portfolio data-ownership requirement.

#### Changed (5)

- Ratified the four undocumented table namespaces as singular full words matching the existing convention, renaming the system and indicator namespaces throughout the schema model.
- Ratified the abbreviated simulator namespace as canonical and recorded that the longer form in code was never applied to a database.
- Recorded the runtime database engine version as confirmed by evidence from the applied development database rather than assumed.
- Established the sidecar artifact manifest as authoritative and the database catalog as a rebuildable index over it, with a documented rebuild procedure.
- Set the adoption scope to rewriting the seven never-applied divergent definitions before first apply, leaving the six applied ones documented as divergent.

#### Removed (1)

- Removed the database schema open-decisions block from the system specification; no schema decisions remain unresolved.

### Correct two schema-model claims and close a dissolved decision

Investigation of the migration runner and the runtime-store layer showed that two recorded hazards do not exist, and the requirement-identifier convention is already established rather than absent.

#### Changed (2)

- Corrected the migration-relocation guidance: a step checksum covers its ordered SQL statements only and the ledger keys on domain and migration identifier, so relocating a definition is an import-path refactor rather than a checksum risk; the preserved invariants are now stated precisely.
- Recorded the requirement and feature identifier allocation convention alongside the additive-migration tier, including the next free identifier per domain, so later phases allocate in sequence instead of inventing.

#### Removed (1)

- Removed the open decision questioning whether the uniform persistence layout was overridden by the shared runtime-store layer; domain create, read, update, and delete operations already live in each domain's private persistence package and reach shared infrastructure only through the Data public API.

### Adopt a hybrid normalisation convention in the schema model

The schema model absorbs forty columns from twelve live tables that carry integrity, traceability, or state the model could not express, while rejecting twenty-six that duplicate existing columns or hold payloads the model normalises.

#### Added (4)

- Added integrity hashes, policy references, and traceability identifiers to the Strategy configuration, version, and checkpoint tables.
- Added canonical hashes, scope keys, activation timestamps, and plan versioning to the Portfolio definition, allocation, and rebalance tables, and reproducibility fields to optimization checkpoints.
- Added retention class, sensitivity, injection status, redaction paths, evidence references, and authoring role to agentic memory records, and workflow name, version, node, and payload hashes to workflow checkpoints, correcting a resume ambiguity across workflow versions.
- Added primary-key presence, rename-collision, and stated-count verification to the schema verification script.

#### Changed (3)

- Established the hybrid normalisation convention: a field becomes a typed column only when filtered, constraint-enforceable, or part of a unique key, and otherwise stays in a validated payload with generated columns for hot keys.
- Established one migration package per domain as the canonical location for immutable schema definitions, and recorded that relocating existing sites must preserve their migration checksums.
- Extended workflow-checkpoint uniqueness to include workflow version so two versions of one workflow may each hold the same sequence number.

### Correct the schema model against shipped architecture

Six defects in the target schema model are corrected against live code and the system data-ownership record, reducing the model from 90 to 86 tables.

#### Added (2)

- Added the write-lock lease table to the schema model, transcribed from the live locking implementation, closing a gap against the mandatory write-lock policy.
- Added request and correlation identifiers to twenty-one tables whose rows record a decision, a side-effecting mutation, an external interaction, or an audit event; reference, configuration, and derived-output tables are deliberately excluded.

#### Changed (4)

- Corrected the migration-ledger definition in the schema model to match the live implementation exactly, replacing an invented key and timestamp scheme.
- Aligned the Parquet partition-file catalog with the live storage-manifest contract by adopting artifact format, normalization version, source revision, provenance, and request identifier, while rejecting three fields already represented.
- Recorded the Analytics derived metric store as an owned, recomputable state in the data-ownership record, resolving its conflict with the schema model.
- Reordered the schema-model adoption priorities to reflect that Brokers is deliberately stateless and Analytics owns derived state.

#### Removed (2)

- Withdrew the simulation timeline-event table from the schema model; the canonical journal remains append-only JSONL, and the model now defers to that documented exclusion.
- Withdrew the broker provider, connection, account, and connection-event tables from the schema model, retaining only symbol mapping; the withdrawal of the production-connection safety constraint is recorded explicitly.

### Promote the cross-domain database schema model to authoritative

The target database schema model moves from the non-authoritative working area to `docs/schema/` and becomes canonical for cross-domain schema structure, while current-state registries and executable migrations keep their existing owners.

#### Added (3)

- Added `docs/schema/` as the authoritative cross-domain schema model covering 90 target tables across all 14 domains, with storage tiers, prefix ownership, column conventions, and indexing policy.
- Added a reconciliation record comparing the target model against the 59 live tables, classifying every overlap into an adoption tier.
- Added `docs/schema/verify_schema.py`, which executes the model against SQLite and asserts foreign-key resolution, index targets, audit columns, `STRICT` mode, prefix uniqueness, and absence of `REAL` monetary columns.

#### Changed (3)

- Routed target schema, prefix ownership, column conventions, indexing policy, and target-versus-live reconciliation to `docs/schema/` in the documentation update rules.
- Recorded the schema model, target-versus-current divergence handling, and its boundary against feature-registry and migration authority in the architecture reference.
- Recorded eleven unresolved schema decisions in the system open-decisions section, including two conflicts between the model and the existing data-ownership record.

### Standardize domain persistence layout

Strategy, API, Portfolio, Risk, Trading, Simulator, Agentic, and Data persistence now use the uniform private CRUD package while
preserving domain ownership, immutable records, public APIs, and Data-owned transaction mechanics.

#### Changed (8)

- Moved Strategy registry, configuration, mutation, and checkpoint CRUD statements into the private `strategy/persistence` create/read/update/delete layout without changing schemas or public behavior.
- Moved API account, session, credential, approval, idempotency, authentication-failure, and settings CRUD statements into the private `api/persistence` create/read/update/delete layout without changing schemas or public behavior.
- Moved Portfolio runtime-record reads and atomic construction, plan, and allocation transitions into the private `portfolio/persistence` create/read/update/delete layout without splitting compare-and-swap transactions.
- Moved Risk approval-token, audit-chain, eligibility, allocation-budget, and kill-switch CRUD calls into the private `risk/persistence` create/read/update/delete layout while preserving revision guards and compound atomic transitions.
- Moved Trading idempotency, append-only event, projection, reconciliation-evidence, and unresolved-attempt CRUD calls into the private `trading/persistence` create/read/update/delete layout while preserving scope isolation and optimistic concurrency guards.
- Moved Simulator journal staging and run-idempotency lifecycle CRUD calls into the private `simulator/persistence` create/read/update/delete layout while preserving append ordering, monotonic lifecycle validation, CAS updates, and canonical JSONL publication.
- Moved Agentic memory, lifecycle, operations, and orchestration runtime-record CRUD calls into the private `agentic/persistence` create/read/update/delete layout while preserving incident and workflow atomic transitions, append ordering, and workflow compare-and-swap updates.
- Consolidated Data-owned audit, cache, calendar, feed, source-policy, job, research-source, and runtime-store CRUD in `data/persistence` create/read/update/delete modules while retaining transaction, locking, migration, backup, and recovery infrastructure and preserving compound atomic transitions.

### Upgrade app/ui to React 19 and Next.js

The `app/ui` frontend package has been upgraded from Vite to Next.js (App Router) and React 19, enabling server-side rendering, optimized page routing, metadata management, and Zustand 5 state integration.

#### Changed (2)

- Upgraded `app/ui` framework dependencies from Vite + React 18 to Next.js 15.5+ with React 19.2 and Zustand 5.0.
- Migrated `app/ui` architecture to Next.js App Router (`src/app/layout.jsx`, `src/app/page.jsx`, `src/app/globals.css`), converting interactive layouts and widgets into Client Components.

### Implement the API backend foundation

The API service now provides the canonical contract, identity, governance,
routing, streaming, and application-composition foundation while owner-domain
with a truthful reduced owner-backed HTTP surface ready for frontend client work.

#### Added (3)

- Completed `FEAT-API-01` through `FEAT-API-08`, added canonical non-stream envelopes and the validated three-source in-process provider graph with required readiness probes and reverse shutdown.
- Added Data-owned durable runtime records and owner adapters for Simulation, Risk, Trading, Portfolio, and Agentic state while retaining the unresolved canonical provider-configuration gate.
- Added an exact 21-operation backend-v1 route/OpenAPI inventory and explicit absence evidence for uncomposed Simulation, Risk, Trading, Optimization, Portfolio, and Agentic HTTP families.

#### Changed (3)

- Reconciled the API feature registry and Sections 4.1 through 4.8 with executable tests, numbered usage evidence, and the reduced frontend-v1 capability map.
- Added fail-closed API runtime-profile validation, route-class rate limits, request deadlines, bounded pagination, import-boundary enforcement, and a deterministic 21-operation OpenAPI contract digest.
- Added Utils `AuthContext v2` and API account migration `api-0003`, preserving deployment tenancy separately from the bounded runtime profile so Risk consumes execution authority while Agentic retains deployment-environment binding.

### Close repository-wide validation regressions

The combined domain migration now preserves function-only runtime validation,
deterministic Strategy indicator evidence, and exact Analytics warning failures.

#### Fixed (3)

- Replaced the accidental public Utils `AuthContext` class export with documented factory and runtime-type getter functions and migrated API and Research usage consumers.
- Restored Strategy evaluator support for focused indicator evidence while preserving package-root getters for genuine Indicators results.
- Corrected Analytics warning-bound evidence to assert the exact configured-bound failure raised by production.

### Complete licensed economic-calendar evidence

Data now acquires, normalizes, persists, and evaluates real economic-calendar
evidence through its function-only package boundary.

#### Added (1)

- Added a bounded licensed Firecrawl transport with host, media-type, response-size, concurrency, timeout, cache, and secret-handling safeguards for all four declared calendar portals.

#### Changed (1)

- Completed `FEAT-DATA-11` and `FR-DATA-095`–`099`/`123`–`129` with genuine multi-site usage evidence and opt-in live verification while keeping default CI network-free.

#### Fixed (2)

- Fixed provider-neutral calendar retrieval to accept the real scrape provider's normalized list instead of assuming an injected response envelope.
- Added function-only event/state projection and persistence operations so consumers no longer need methods or fields from internal calendar classes.

### Complete point-in-time Research intelligence evidence

Data and Research now provide the governed source-to-evidence path required for bounded fundamental and deterministic sentiment research.

#### Added (3)

- Added Data `FEAT-DATA-16` bounded HTTPS source ingestion, immutable revision persistence, decision-time eligibility queries, and detached evidence projection.
- Added governed SEC, official macro-agency, GDELT-headline, and USDA normalization with immutable point-in-time structured observations for Data-backed Research evidence.
- Added Research `FEAT-RES-13` fundamental/sentiment evidence plus completed `WF-RES-012` profile comparison with genuine usage evidence.

#### Changed (1)

- Refactored Research to a function-only package-root boundary and migrated its direct consumers, tests, workflows, and registry documentation.

#### Fixed (1)

- Fixed Research spread cleaning for empty prepared frames and made official-feed identity and publication time derive from retrieved RSS content rather than caller assertions.

### Reconcile and complete the Brokers focused-domain baseline

The Brokers package registry, structure, and evidence now match the implemented sixteen-feature one-folder-per-feature layout, and the domain completion gate passes green.

#### Changed (1)

- Reconciled the Brokers README with the implemented one-feature/one-folder structure, added the `WF-BRK-010` discovery integration test, rewrote usage parity to the file-level evidence convention, and marked the Brokers baseline `Completed` with 424 passing tests.

### Audit Utils, Brokers, and Data runtime truth and public boundaries

The three audited domains now expose function-only package roots, focused tests exceed the per-file coverage floor, and usage evidence distinguishes genuine provider results from unavailable or test-only capabilities.

#### Added (1)

- Completed Strategy `FEAT-STR-11` external proposal evaluation plus `WF-STR-011` approved Optimization-result adoption and `WF-STR-012` research-only signal evaluation, without importing or changing the upstream Optimization, Simulator, Analytics, or Research domains.

#### Changed (10)

- Added the opaque `load_broker_provider_settings` function and Brokers-owned `resolve_provider_connection_config`/`create_connected_broker` operations so no settings class or connection DTO crosses a public package boundary.
- Rewrote the Data composition root `_LazyBrokerSession` to resolve MT5, cTrader, and credential-free providers through the Brokers resolver and removed its private `_ProviderRuntimeSettings`, so Data no longer resolves credentials or builds connection configurations.
- Migrated audited production, usage, workflow, and integration consumers to domain-root imports and added package-root function-only boundary checks.
- Marked `FEAT-DATA-11` and `FR-DATA-095`–`099`/`123`–`129` Pending because the repository has no licensed real economic-calendar transport; the usage now reports `SOURCE_UNAVAILABLE` instead of using `DemonstrationTransport`.
- Reworked every Indicators feature usage and the active workflow evidence to print bounded MT5-derived OHLCV and calculated DataFrames, and added direct subprocess coverage for `WF-INDI-006` through `WF-INDI-008`.
- Refactored Risk to a 63-function package-root boundary, migrated direct consumers away from public classes/constants and deep imports, and completed all fifteen registered Risk workflows with substantive bounded evidence.
- Refactored Trading to a function-only package-root boundary, migrated direct consumers, completed `WF-TRD-015` and `WF-TRD-016`, and raised every Trading production file above the 80% branch-aware coverage floor.
- Refactored Simulator to a lazy, function-only package-root boundary with opaque value/handle operations, migrated its direct consumers, and completed standalone evidence for `WF-SIM-011` and `WF-SIM-012`.
- Refactored Optimization to a function-only package-root boundary with opaque contract construction and inspection, replaced fake usage adapters with genuine MT5-derived Simulator/Analytics execution, and completed `WF-OPT-007` and `WF-OPT-008`.
- Refactored Portfolio to a 21-function package-root boundary, migrated external consumers to opaque values/handles, and replaced canned workflow evidence with genuine MT5 and Simulator results plus transactional SQLite Portfolio state.

#### Fixed (10)

- Fixed the Data composition root silently ignoring `settings.mt5.*` in `app/configs/env.json` because `_ProviderRuntimeSettings` extended `BaseSettings` instead of `AppSettings` and therefore read only the process environment; real-MT5 retrieval through the Data path now honors the central settings file.
- Fixed Brokers package-root history/time-range forwarding and canonical timeframe normalization, restoring genuine MT5 history and Dukascopy bar reads.
- Fixed Data spread normalization so it rejects missing unit/scale evidence and record-shape mismatches instead of inventing `USD` or `scale=0`.
- Fixed historical backfill so it establishes governed storage and source identity before retrieval, allowing scheduled jobs to persist genuine provider records and checkpoints.
- Fixed Data source and real-time-feed usage evidence so it prints bounded provider-derived rows and ticks, while unavailable providers report explicit errors without injected fallbacks.
- Fixed external spread imports so decimal scale is derived from observed provider values rather than assigned a fabricated default.
- Fixed Indicators response handling, private Data structural typing, workflow configuration construction, and validation/error branch coverage so the focused suite passes with every Indicators production file above the 80% floor.
- Fixed Strategy response unwrapping, function-only contract/evaluator construction, deterministic checkpoint/configuration failures, and real MT5-backed usage evidence so all ten implemented workflows pass and every Strategy production file exceeds 80% branch coverage.
- Fixed Risk YAML profile coercion for tuple, enum, loss-basis, hash-compatibility, and crisis-window fields; focused validation now passes 187 tests at 85.4% branch-aware coverage with every Risk production file above 80%.
- Fixed Simulator timeline type validation, response trace fallback, typed idempotent replay, and terminal liquidation so real MT5-backed runs publish closed-trade evidence rather than empty or canned results.

### Complete the Agentic firm with fundamental and sentiment research

The last two registered Agentic roles land now that Data and Research provide the point-in-time source-to-evidence path they depend on.

#### Added (2)

- `FEAT-AGT-09` Fundamental Research: applicability is the receiver's answer, read before any model call, so a fundamental reading of an FX instrument under the issuer model is refused and never queried for data — Research's issuer model covers equity, corporate bonds, and funds, and FX has no issuer, which under an FX mandate makes that the ordinary path rather than an edge case; observation and availability instants, source kinds, coverage counts, document references, and the canonical digest are all copied from Research's projection, so a model output claiming a different availability instant or digest changes nothing; and claims, assumptions, horizons, and falsifiers are validated as parallel key sets, so a claim nobody can say how to falsify is a construction error rather than a review finding. Every projected reference passes `FEAT-AGT-06`'s injection classifier before the model is invoked, flagged references are excluded and recorded in the pack's uncertainty, and a projection consisting only of instructions is refused outright. The pack defines no numeric field at all.
- `FEAT-AGT-10` News and Sentiment Research: source coverage, measured polarity, event classification, uncertainty, and unsupported narrative are five distinct fields, so a narrative the measurements do not support cannot be presented as one — and `unsupported_narrative` is kept rather than forbidden precisely so an analyst can say what the lexicon cannot measure, in the field labelled as not evidence. Trust, manipulation, revision, coverage, and availability metadata come from `SentimentSourceEvidence` unchanged; disagreement and unmeasurable documents are reported rather than averaged away; and the deterministic measurement version is checked against Research's closed set before any receiver round-trip. Instruction stripping runs **before** the model call, not after: flagged references are excluded from what the model sees, counted in the trusted context, recorded on the pack, and appended to its uncertainty.

Neither package imports Research or Data. Both reach the receiver through an injected port, so the chain stays Agentic to Research to Data, and a test asserts it. All twenty-two Agentic features are now implemented; none of it has run for real — no live provider call, no bound sandbox runtime, no durable store, no evaluated role, no promoted artefact, no reviewed advisory, no evaluated proposal, and no source fetched.

### Add the public Agentic API and operator control

An operator now has one authenticated, typed, bounded way to drive the Agentic firm, and one way to stop it that does not hide what it did.

#### Added (1)

- `FEAT-AGT-22` Public Agentic API and Operator Control: eight authenticated operations — submit, inspect, cancel, approve-handoff, replay, quarantine, audit, and disablement — over `AgenticDependencies`, a frozen record in which every port is a required field, so a partially wired firm cannot be invoked at all rather than failing at the point where it matters least; every operation takes the dependency record and the principal first, carries the caller's request and correlation identifiers through to its answer, and refuses on a missing permission or a context issued for another environment. Every answer is an `OperatorOutcome` whose payload is a mapping of bounded strings, which is what makes "without exposing prompts, credentials, or provider internals" structural rather than promised: there is no nested value a `ModelProfile` or an `AgentProvenance` could travel inside, a forbidden-key rule closes the text route, and an integration test renders every operator response and asserts no provider name, `vault://` reference, prompt text, or redacted credential appears anywhere on the surface. Failures are mapped rather than raised, so no provider or receiver exception crosses the boundary, and ordinary conditions — an unknown run, an already-terminal run, a forbidden lifecycle transition — are refusals with enumerated reasons rather than internal errors. Disablement is checked before authentication for anything that creates or changes work, so a principal holding nothing still gets `AGENTIC_DISABLED`; it drains or cancels active runs by policy through the normal orchestration path, writes over nothing, and leaves reads available so an operator can still learn why the firm stopped. Its safety-equivalence clause holds for a structural reason checked domain-wide: a test over every file in `app/agentic` asserts the package names no kill-switch operation, no risk approval, no live gate, no order dispatch, and no broker SDK, so disabling a package that never held safety authority cannot weaken safety. The package root grows to eighty-eight exports and stays function-only, verified by test. `WF-AGT-005`'s planned `open_sandbox` and `stage_code_artifact` are deliberately **not** exported, and neither are fundamental or sentiment operations: no isolation runtime exists to open and `FEAT-AGT-09`/`-10` are unimplemented, so a function that could not do what its name promises would be worse than the gap. Twenty of twenty-two features are now implemented and none of it has run for real — no live provider call, no bound sandbox, no durable store, no evaluated role, no promoted artefact, no reviewed advisory, no evaluated proposal, no incident outside tests.

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

### Bridge Portfolio construction and reads through the API gateway

The API gateway composes the Portfolio receiver-owned dependency bundle behind a fail-closed source and exposes the three HTTP-reducible Portfolio operations as thin delegations through the function-only public boundary.

#### Added (4)

- Added `app/services/api/composition/portfolio_dependencies.py` composing the twelve-callback `PortfolioWorkflowDependencies`, `PortfolioWorkflowService`, and opaque `PortfolioService` handle through Portfolio package-root factories and exposing a fail-closed route dispatcher.
- Added `app/services/api/routes/portfolio.py` with governed `POST /api/v1/portfolio/construct` and read-only `GET /api/v1/portfolio/{portfolio_id}/status` and `GET /api/v1/portfolio/{portfolio_id}/history` endpoints.
- Added `PortfolioConstructRequest`, `PortfolioStrategyAllocationRef`, `PortfolioFixedWeightInput`, and `PortfolioEvidenceReferenceSet` API boundary projections and registered three route contracts in the canonical catalogue.
- Added `tests/api/unit/test_portfolio_routes.py` covering DTO-to-strict-contract conversion, list-to-tuple normalization, fail-closed behaviour, read delegation, idempotency enforcement, and permission rejection.

#### Changed (5)

- Changed the canonical in-process graph from an exact eight-provider to an exact nine-provider manifest by binding the new `portfolio.source` provider.
- Changed the backend-v1 public surface from 32 to 35 HTTP operations and regenerated the frozen OpenAPI digest and operation inventory.
- Flipped `FR-API-056` from `Excluded` to `Partial` and `WF-API-017` from `Excluded` to `Partial` with the pending subset and its infeasibility reason documented.
- Updated `tests/api/unit/test_route_catalog.py`, `tests/api/unit/test_application.py`, `tests/api/unit/test_in_process_composition.py`, and `tests/api/contracts/test_openapi_contract.py` to the new operation count and provider manifest and removed the Portfolio route-absence assertions.
- Updated `app/services/api/README.md` and `docs/PROJECT.md` operation counts, structure tree, route table, and Portfolio boundary narrative.

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

# V2 product features

F01 is defined in [host foundation](host-foundation.md). F02-F13 below preserve
product breadth while sharing its services. Feature IDs are planning labels.
Dependency lists name required capabilities, not a demand to complete every
method/provider in an earlier feature group. See [delivery order](delivery-plan.md).

For each group, build the backend operation and its existing UI client together.
Real job/resource IDs, restart/reconnect, denied/unavailable/failure states and
cancellation belong to acceptance. Fixtures remain useful tests, not production
substitutes. Settings, commands and result tabs are parts of the owning operation.

## F02 Market data

**Includes:** Data Manager home/actions/help/logs; dataset, instrument and broker
definitions; sessions/timezones; baskets; custom columns/data; data selection;
file import and provider downloads/updates. Preserve precision, units, timestamp
meaning, source lineage and immutable revisions. Validate bars, duplicates, gaps
and ordering with an explicit reject/repair policy. Handle DST folds/gaps and
session boundaries. Native session import includes the evidenced overwrite/skip
policy and conflict handling. COT includes its symbol catalog, five-field mapping, release
alignment, custom-data creation/update and synchronization/export failures.

**Keep simple:** one catalog service, one normalized dataset contract and a narrow
provider adapter. File/provider jobs write the same validated artifacts. Use
Polars/PyArrow for data; datetime/zoneinfo for clocks; one bounded httpx policy
for provider I/O. The provider owns pagination, symbols, timestamp units and
authentication. Do not write separate HTTP/cache libraries for each source.

**Full provider checklist:** files; Binance spot, Coin-M and USDT-M; Bitfinex;
Coinbase Pro; Poloniex; the generic crypto source; Darwinex; Dukascopy; MT5 API;
SQ Equity Data; SQ Futures Data; TD; Yahoo; and COT. These are the V1 donor labels,
not claims that their APIs remain available. Qualify each current endpoint and
entitlement at implementation. Record unavailable sources or explicitly approved
replacement/compatibility decisions; a generic crypto adapter does not complete
all exchange variants. No network calls are required to publish this plan.

**Dependencies:** F01 configuration, jobs, resource publication and persistence.
**Acceptance:** import a small independent file, check exact normalized rows/units,
save/reload its revision and select it in a consumer. Test DST, native session
import overwrite/skip/conflicts, corrupt rows,
pagination, timeouts/rates, partial downloads and cancellation. Start with files
and one selected provider; later adapters remain open until individually qualified.

## F03 Strategies and authoring

**Includes:** all accepted indicator/snippet/block families and constants; typed
parameters, constraints and generation eligibility; AlgoWizard and CodeEditor;
templates/custom resources; real indicator testing; saved strategy revisions;
SQ3/SQ4 import and SQ3 save compatibility; source-code projections and platform
export. Include COT signals/emergency exits, volume/market profile, TPO, Delta,
POC/value-area calculations and AnchoredVWAP. Inventory all consumed snippet
families, not only the first indicators shipped in a usable milestone.

**Keep simple:** one versioned semantic strategy document: typed rules, parameters
and references to qualified block versions. Editors create it, generators propose
it and the simulator evaluates it. Each indicator owns its formula, lookback,
missing-value policy, types/defaults, metadata and lowering/export hooks. Use
explicit evaluators and templates; there is no need for Javassist or a Python
bytecode framework. Custom code executes only under the approved trust/isolation
policy. A code editor saving text does not qualify an indicator test.

**Formats/platforms:** use focused boundary adapters for native archives, XML fields
and export templates. Preserve accepted unknown fields where round trips require
it; reject unsupported versions explicitly. Qualify every retained export target
in the actual catalog; do not infer all platforms from a single template. NinjaTrader8
requires native `.cs` generation, escaping, package/version metadata, indicator
dependencies and session compatibility. Preserve evidenced bar-close behavior and
explicit on-tick rejection. Generic VolumeProfile and selected signals/TPO have
different engine availability; retain per-block restrictions. AlgoCloud parsing
belongs here; remote access belongs to F12.

**Dependencies:** F01 documents/resources/discovery; F02 data and F04 for execution
tests. Basic schema/save/edit can precede the full engine. **Acceptance:** author,
save/reload and run one strategy; independent formula/warm-up/shift/boundary vectors;
archive round trips; unsupported-block/version errors. Later platform exports need
independent compiler/import/native execution checks in approved isolated targets,
including the native indicator package. A generated string alone is insufficient.

## F04 Simulation

**Includes:** deterministic strategy evaluation; orders/fills/trade lifecycle;
money management and advanced trade management; costs, slippage, spread and
rounding; execution options/precision; multiseries alignment and clocks; stock
selection; event trace, trades, equity and reconciled account ledgers. Platform
execution profiles are explicit capabilities. NinjaTrader engine qualification
remains in scope and distinct from its code export.

**Keep simple:** one reference execution engine with clear event order and state
transitions. Indicators may use numerical arrays; order/accounting logic retains
sequential semantics where necessary. Begin with one qualified execution profile
and expand documented precision/profile behavior. Avoid separate backtest engines
for Builder, Optimizer, Retester or projects. Profile before accelerating kernels.

**Dependencies:** qualified F02 data, F03 strategy/block semantics and F01 jobs/storage.
**Acceptance:** hand-auditable trades and balances; costs/sizing/rounding; same-bar
entry/stop/target precedence; insufficient data; missing values; cancelled/failed
runs; repeatability across workers. Stock selection needs universe/ranking/rebalance
timing and capital/exposure tests. Higher precision needs actual data/event semantics,
not a label. The audit lacks a complete standalone NinjaTrader engine body; export
templates cannot qualify that profile. Keep its parity/release gate open until
supporting behavior and independent platform traces exist.

## F05 Results and reporting

**Includes:** databanks and named views/actions; rename/bulk rename and stable
identities; filters including correlation; custom actions and result plugins;
overview/configuration/exploration; trade lists/views/analysis/trades on charts;
stock-picker/SP views; equity, daily, drawdown, volatility, volume and benchmark
series; project databanks/results; saved view preferences and reports. Exports
include HTML, PDF, spreadsheets, trades and image artifacts/transformations.

**Keep simple:** one result repository and owner-defined metrics/projections over
immutable F04/F07/F08 artifacts. Browser charts/tables render those projections;
they do not invent trade results. Common correlation/metric primitives serve
filtering, portfolio views and ranking without duplicate formulas. Export adapters
consume the same report data. Browser rendering replaces Java chart/SVG/Swing
machinery; nontrivial image/export transforms still need a qualified adapter.

**Dependencies:** F01 retained resources; F04 run outputs for the first journey.
**Acceptance:** every displayed/exported total reconciles to stored records; test
alignment, undefined correlation/zero variance, threshold equality, rename collision,
empty results and incompatible producers. Reload preserved databanks/view state.
Verify HTML escaping, image dimensions/encodings, spreadsheet types/formula policy,
PDF layout/fonts and trade export precision. Start with tables/equity/trades and
simple data/HTML export; add other formats through one adapter each, with dependency
approval where necessary. AI result-tab completion consumes F13, not a separate
reporting AI backend.

## F06 Strategy generation

**Includes:** Builder settings/progress/dashboard/engine panels; what-to-build and
parts-to-improve; random generation; genetic population/selection/crossover/mutation;
fitness objectives, ranking/filters and automatic-retest hooks; genetic options;
finite stop budgets and retained candidate lineage.

**Keep simple:** search proposes F03 documents, calls F04, scores qualified metrics
and publishes accepted candidates through F05. One small generation/search module
per method suffices; do not reproduce Commons Math or Watchmaker as frameworks.
Only catalog-qualified blocks enter candidates. Keep method-specific random
distributions, selection/tie rules and generation bounds explicit.

**Dependencies:** F03/F04/F05 and F01 jobs; F07 only when automatic retest is enabled.
**Acceptance:** seed/candidate lineage, fitness direction/ties, nonfinite/missing
scores, generated validity, filtering, stop/cancel and reproducibility. Independent
search/sampling vectors establish accepted behavior; identical seed numbers alone
do not prove Java/Python random-stream equivalence. Start with random search;
genetic generation/improvement remains part of the full feature.

## F07 Optimization and validation

**Includes:** Optimizer and Retester settings/progress/results; simple parameter
search, sequential optimization, profiles and system-parameter permutations;
walk-forward partitions, optimization, result aggregation and matrix views;
Monte Carlo manipulation and Monte Carlo retest; additional-market retest;
higher-precision retest; What-If; robustness reports; what-to-retest selection;
automatic-retest data/chains, thresholds and cross-check configuration.

**Keep simple:** a shared experiment runner turns each method's configuration into
ordered candidate/scenario run specifications. F04 executes runs; the method
evaluates its own criterion and publishes F05-compatible results. Optimizer-backed
robustness checks reuse those optimization methods. Manipulating retained trades
and resimulating modified inputs are distinct Monte Carlo operations; sharing
execution does not collapse their semantics.

**Dependencies:** F04/F05, F02 for extra-market/precision data and F01 jobs/storage.
F06 is not mandatory to optimize or retest a saved strategy. **Acceptance:** ranges
and endpoints/order; objective ties; bounded sequential passes; in/out-of-sample
separation without leakage; window boundaries; seeded perturbations/replacement;
pass/fail threshold equality; excluded-trade denominators and aggregate accounting.
Require each named robustness method to pass independent vectors. Start with
parameter search and retest, then add walk-forward and the full scenario catalog;
unsupported precision/data remains visibly unavailable.

## F08 Portfolios

**Includes:** Portfolio Composer/Master, manual and automatic construction/search,
existing-portfolio fitness, member selection/weights, correlation, aggregate
accounting, exposures, charts/logs and retained portfolio revisions.

**Keep simple:** a portfolio references immutable strategy/run results and has one
composition/evaluation capability. Use F05's correlation primitives; own portfolio
selection objectives and accounting rules here. Search calls this same evaluation
instead of a separate simulator or plugin per chart. Combined results must specify
whether capital is independent, weighted or shared; summing equity curves is not
automatically a capital-constrained portfolio backtest.

**Dependencies:** qualified F05 inputs and F01 jobs/resources; F04 if reexecution
is required. Manual composition does not require Builder or every robustness check.
**Acceptance:** independent aggregate/weight/exposure vectors, timestamp/calendar
alignment, currency/cost basis, duplicate membership, missing samples, zero-variance
correlation, search bounds and deterministic ties; save/reload membership versions.
Deliver manual composition first, then automatic search/selection.

## F09 Research projects

**Includes:** Custom Projects/Task Manager, project settings/resources/databanks/
results, cloned/start/stop task lifecycle and notes. Conditions include cycle count,
go-to activated/evaluated state, result count and elapsed runtime. Tasks include
build, optimize, retest/automatic retest, portfolio/automatic portfolio and neural
training through their owning features; mass configuration; custom analysis;
filtering; go-to/wait/stop-and-start; file load/save; databank statistics; updates;
notifications/mail; external scripts; clear databanks and delete files. Include
the reusable discovery/build/testing workflow used by Q.

**Keep simple:** a finite state machine interprets a versioned project document
with typed task nodes/conditions. Each node delegates to an existing capability.
A task's settings schema and execution adapter are one local contribution. Start
with sequential tasks, then support bounded branches/repetitions; SQX go-to behavior
must remain representable, so this is not limited to acyclic DAGs. Enforce maximum
steps/cycles/runtime and document evaluation points, equality and disabled conditions.

**Dependencies:** F01 jobs/storage plus only the capabilities selected by a project.
**Acceptance:** child ownership, condition/counter boundaries, loops, failures,
cancel/restart, cloned settings and output lineage. Mass changes validate all targets
and rollback as specified. File/clear/delete tasks resolve exact owned targets and
preserve unrelated resources. Mail/external scripts/destructive operations need
their scoped authority, timeout/output controls and failure outcomes; project
execution grants no blanket side-effect permission. A missing neural/grid/provider
capability blocks its node, not every custom project.

## F10 Compute

**Includes:** local capacity/placement and worker limits; Grid Control and Grid Test;
remote worker enrollment/compatibility; versioned job messages, admission/leases,
heartbeats, result publication, cancellation, worker loss/retry and cleanup.

**Keep simple:** F01 already owns local scheduling. F10 adds a remote worker adapter
to that coordinator, with bounded HTTP transfer/events as sufficient. Workers get
validated specs and artifact references, not arbitrary executable-object payloads.
No Artemis/JMS/JGroups/Netty replicas are needed. Matching the donor wire protocol
is a separate requirement if adopted; this plan targets HaruQuantAI workers and
does not claim interoperability with SQX Java nodes.

**Dependencies:** F01 jobs/resources/security and an executable domain operation.
**Acceptance:** compare local/remote deterministic results; reject incompatible
worker versions; expire leases, ignore late/duplicate attempt output and preserve
lineage; test lost workers, cancellation and resource release. Seed partitioning
and aggregation order cannot depend on timing. Start with local processes; grid
scale follows measured workloads. Local data/backtests/neural training do not wait
for distributed messaging. Trusted numerical workers and untrusted code have
different execution policies.

## F11 Neural models

**Includes:** training-data/feature/target selection, scaling and temporal splits;
model architecture/settings; seeded training/validation metrics/progress;
model storage/versioning and inference in qualified strategies/projects.

**Keep simple:** one training/inference adapter behind typed documents. Use F01
jobs and resources, F02 data and the existing NeuralNetwork UI. Select the smallest
appropriate training backend after algorithm and Python-version evidence; do not
prebuild a GPU/cloud training platform. Preserve preprocessing with model metadata.

**Dependencies:** F02 and local F01 execution/storage; F03/F04 for strategy consumption.
F10 remote compute is optional. **Acceptance:** independent feature/scale/split/target
vectors, no future-data leakage, seeded training bounds, held-out metrics, saved-model
reload and identical preprocessing/inference. Reject incompatible/missing models
and invalid inputs; cancelled training is not complete. Missing donor training
semantics constrain the affected parity claim, rather than authorizing invented
SQX model behavior.

## F12 Connections and ecosystem

**Includes:** Connections/Trading surfaces; test/live-test/MT4 terminal contributions
and the MT5 data integration boundary; handshake, symbols/account mapping,
read-only account/order/status projections, reconnect/timeouts and authorized
live operations. Also Business/MCP tool/node configuration and lifecycle; AlgoCloud
strategy/result access; Marketplace catalog/install/disable/remove/upgrade.

**Keep simple:** narrow adapters share H06/H08/H10 transport/resources/authority.
F02 owns downloaded market-data semantics; F03 owns parsed strategy documents;
F12 owns external lifecycle/protocols. MCP has one qualified protocol implementation,
not one per versioned Java wrapper. Business/build workflows reuse jobs and code
export. Node-specific behavior belongs to each node's adapter. Vendor activation,
accounts, credits/licensing and entitlements require available documented services;
there is no license-system emulator implied by the word clone.

Marketplace stages packages, verifies manifests/checksums/contained entries, then
uses H05 attachment. Removing an extension preserves data and affects only declared
dependents. Marketplace controls are currently absent and need explicit UI scope.
Do not auto-execute downloaded packages during catalog inspection.

**Dependencies:** F01 security/resources/discovery; selected F02/F03/F04/F09 consumers.
**Acceptance:** real isolated connector/sandbox, mapped symbols/accounts, timeout/
disconnect/denied states, compatible protocol/tool schemas and bounded side effects.
Verify AlgoCloud document/version failures and Marketplace checksum/traversal/
upgrade rollback/removal. Fixtures qualify unit behavior, not a live connection.
Start with read-only/test and explicitly configured integrations. Live trading
stays disabled by default and needs distinct qualification and owner authorization;
ordinary implementation approval grants no real orders.

## F13 AI research assistant

**Includes:** Q chat/config/state/session/history/project operations and attachments;
late-subscriber replay and stopped/failed turns; editable knowledge/AI Brain/research
verdicts and learned procedures; bounded scheduled continuations; isolated Python
analysis/artifacts; extension skills/commands/agents/knowledge and reload; result-tab
completion, model selection, cache/regenerate, limits, permissions and credit policy.
Preserve the evidenced memory-layer contract when recovered; names alone do not
establish the audit's four-layer layout or its write/approval/removal semantics.

**Keep simple:** a bounded tool-calling loop over the same typed data/strategy/run/
project capabilities used by humans. Chat memory uses host resources; schedules
use host jobs and persisted deadlines; procedures are versioned resources. Begin
with one provider adapter and read-only explanation/tool discovery; add authorized
research orchestration. Do not rebuild AgentScope, a general multi-agent framework
or shell syntax parser unless a specific retained operation needs it.

**All Q procedure contributions remain in scope:** `ac-strategy`, `algowizard-lab`,
`analysis-tabs`, `auto-research`, `breakout-project-factory`, `custom-page`,
`market-analyst`, `plugin-maker`, `quant-research`, `sqx-indicator-builder`,
`sqx-project`, `sqx-reports`, `sqx-snippets`, `sqx-strategy`, `strategy-analyst`,
`strategy-architect`, `trading-memory` and `ui-pilot`. Implement their evidenced operations through
existing tools; a manifest name is not proof of payload behavior. Code/plugin/page
generation produces reviewable artifacts and uses explicit mutation authority.

**Dependencies:** F01 sessions/jobs/resources and whichever tools a turn selects;
F09 for project orchestration. **Acceptance:** independent tool/schema/permission
tests, bounded turns/time/cost, cancellation races, reconnect/state replay,
unavailable model/tool/data/skill and failed/partial workflows. Retain user-approved
memory revisions and source/result lineage. Python analysis requires enforceable
isolation; a normal worker pool is insufficient. Completion needs concurrency and
cache/regenerate tests. Never manufacture numerical outcomes from chat text.
Missing AI bodies/provider observations and the recorded market-analyst source gap
keep affected compatibility claims open. Full acceptance includes goal -> discovery
-> build -> retest -> retained research record, using actual domain outputs.

## Shell, distribution and retained target surfaces

F01 also owns browser navigation, Home/About/help, light/dark skin, language/zoom,
preferences, readiness and clean install/start/stop. Use React/CSS/native browser
SVG/editor presentation for JavaFX/WebLaF/Swing equivalents. A web close action
and explicit host shutdown have different lifecycle meanings; document the target
behavior instead of carrying over a desktop window manager.

The retained Chart, MTAnalyzer and Trading surfaces need real owned data/result/
connection inputs. MTAnalyzer and Live Trading are normative target additions in
the UI inventory; they are not established SQX donor features. Deliver their
qualified behavior within F02/F05/F12 and identify added scope in their actual plans.
Do not count unavailable commercial/licensed controls as working distribution.

Whole-product qualification spans these groups and [release gates](delivery-plan.md).
No single group is complete while any promised method, provider, format, native
package, procedure or required connected UI remains unqualified.

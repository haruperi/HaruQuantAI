# Unified strategy blocks and indicator refactor plan

Status: proposed implementation plan; no production refactor performed by this document.
Prepared: 2026-10-28. Baseline commit: `78dae6ee`.

## 1. Objective and agreed decisions

Create one discoverable strategy-block library used by CodeEditor, AlgoWizard,
the manual strategy builder, and automatic candidate generation. Preserve fast
batch calculations and existing behavior during an incremental migration.

1. Canonical strategy components live under `app/include/blocks/<category>/`.
2. One independently maintained, editor-visible block implementation per file.
3. Each indicator has ONE public implementation class. Parameters are Pydantic
   fields on that class; there is no separate `SMAParams` class.
4. Metadata is declared with `ClassVar` and excluded from configurable parameters.
5. Historical indicator calculation is batch-first: `calculate(bars)` returns
   all named series. Parameter validation and initialization happen once.
6. Generic conditions consume indicator outputs. Do not duplicate every generic
   comparison for every indicator or create a second indicator wrapper class.
7. Shared numerical helpers, market contracts, persistence, and broker services
   remain infrastructure, rather than selectable strategy blocks.
8. Both authoring paths emit the same versioned strategy document and use the
   same validator/compiler. Display text is never the executable representation.
9. Stable IDs and versions identify blocks independently of filenames and labels.
10. Discovery and package exports are isolated; a broken extension must not
    prevent unrelated block discovery or package import. Clean migration across the
    board with no compatibility aliases, import shims, or legacy facades.

## 2. Current implementation and migration impact

| Current location/behavior | Required change |
| --- | --- |
| app/include/indicators/ contains 73 exported indicator families | Move canonical definitions; migrate to single-class validated parameters |
| Indicator calculate() signatures differ; tester inspects signatures | Adopt one canonical indicator interface; migrate all callers and consumers directly across the board |
| app/include/functions.py is 813 lines | Package by independently editable function blocks; extract shared helpers and migrate callers directly |
| `actions/annotations.py` and `actions/logging.py` group several blocks | Separate independently editable action implementations |
| `price.py`, `bar_time.py`, `comparisons.py`, `types.py` mix utilities and blocks | Inventory ownership; extract selectable blocks while preserving utility APIs |
| `app/workspace/code_editor/registry.py` owns registry and metric/sizing bases | Move shared contracts/registration out of the workspace layer |
| Registry keys primarily use paths and classes | Introduce explicit descriptors, stable IDs, versions, and staged publication |
| CodeEditor templates/resolver/tester know current paths and method shapes | Migrate roots, schemas, templates, permissions, configuration IDs and paths |
| Builder `BuildingBlocksTab.tsx` reads `settingsFixtures.ts` | Replace production fixture catalog with the shared catalog API |
| Builder `builderClient.ts` sends a provisional demonstration graph | Replace demonstration payloads with validated shared strategy documents |
| AlgoWizard `algoWizardModel.ts` stores blocks as `{id, text}` | Add executable block references, parameters, ports and structural rules |
| Builder and AlgoWizard READMEs identify UI/prototype execution limits | Implement and label integration honestly; do not treat fixtures as an engine |

Existing evidence: 87/87 include-library files compile; 73/73 exported indicators
resolve; 562 workspace tests, 13 CodeEditor unit tests and 12 browser tests passed
in the preceding work. These are a baseline, not evidence for the new contracts.

## 3. Target ownership and layout

```text
app/include/
  blocks/
    __init__.py                  # Lightweight public API
    base.py                      # Shared validated block contract
    metadata.py                  # BlockSpec, ports, output and generation metadata
    registry.py                  # IDs, versions, staged publication, snapshots
    discovery.py                 # Confined declaration discovery and lazy loading
    series.py                    # Input/output protocols and validity conventions
    indicators/
      base.py                    # BaseIndicator; shared initialization/lifecycle
      trend/ momentum/ volatility/ volume/ price_action/ regime/ custom/
    functions/                   # plus.py, division.py, abs_val.py, etc.
    prices/                      # OHLC, quotes, spread, MTF and session blocks
    bar_time/                    # Time/date/session expression blocks
    comparisons/                 # Typed comparison and boolean operations
    signals/                     # Generic/composite or specialized signal blocks
    actions/                     # One action per file
    orders/                      # Order intent blocks
    money_management/            # Position-sizing blocks and base contract
    constants/                   # Selectable constant/value blocks
    variables/                   # Selectable variable read/write blocks
  contracts.py enums.py          # Existing canonical market/trading contracts
  market_storage.py             # Existing storage infrastructure
  calculators/                  # Shared batch kernels and streaming calculators
  metrics/ trade_columns/       # Reporting extensions, outside strategy blocks
  monte_carlo/ what_if/ analysis/
  ai_tools/                     # AI/MCP extensions; not automatically strategy nodes
  indicators/ actions/ ...       # Removed once consumers are migrated directly to app/include/blocks/

app/domain/strategy/             # New shared strategy domain, currently absent
  document.py validation.py compiler.py execution.py generation.py

app/workspace/code_editor/       # Authoring UI/API integration and diagnostics
app/workspace/strategy/          # Thin shared catalog/document/execution HTTP services
```

These are responsibility boundaries, not permission to create oversized modules.
Split implementations further before any new/modified file exceeds 1,000 lines.
Normal mathematical utilities do not need artificial block classes. Preserve
`BarPrice` as the shared array container; price blocks consume it rather than
introducing another OHLCV storage implementation. Timestamp normalization,
session calendars and broker access keep one canonical infrastructure owner.

Dependency direction: infrastructure -> block library -> strategy domain ->
workspace services/UI. The block library must not import CodeEditor or UI code.
Domain execution uses injected service protocols; broker integration adapts the
existing trading services rather than duplicating broker/order contracts.

## 4. Common block descriptor and parameter contract

Every selectable block has an explicit BlockSpec with:

- Stable ID, semantic version, display name, description, category and tags.
- Typed input/output ports, including selected indicator outputs and units.
- Execution kind: pure expression, condition, state read/write, action or order.
- Required market inputs, history requirements, timeframe/session dependencies.
- Output chart pane, units and optional bounds; no name-based pane guessing.
- Manual availability and automatic-generation eligibility/parameter search space.
- Determinism, causality/repainting, supported events and incremental capability.
- Explicit dependencies on other block IDs/versions; no filename-as-identity rule.
- Implementation revision fingerprint for cache invalidation and reproducibility.

Class blocks derive parameter schemas from Pydantic model fields. Shared base
configuration forbids unknown parameters, validates defaults, and freezes public
configuration. Validate at construction, not once per bar. Parameters requiring
cross-field checks use validators inside the same block class.

Simple stateless function blocks may use explicitly annotated callable entries.
Their decorator attaches descriptors without mutating the global registry during
import. The loader stages and validates them like class blocks. Ordinary helpers
are not discovered implicitly. Configurable/stateful blocks use the class form;
indicators always use the agreed single-class form.

Move BaseMetric to its reporting-extension owner (app/include/metrics/) and BasePositionSizer to the
block-library owner (app/include/blocks/money_management/). Update all importers directly across the
board with no compatibility aliases or shims. Do not turn reporting or MCP extensions into strategy blocks
merely to reuse a registry.

## 5. Indicator contract and numerical behavior

Illustrative authoring shape after the base contract exists:

```python
class SMA(BaseIndicator):
    spec: ClassVar[BlockSpec] = ...
    period: int = Field(default=20, ge=1, title="Period")

    def required_history(self) -> int:
        return self.period

    def calculate(self, bars: BarData) -> dict[str, IndicatorSeries]:
        values = sma_kernel(bars.prices.close_series().values, self.period)
        return {"value": IndicatorSeries(values, name="SMA")}
```

`BarData` is a lightweight shared calculation context around the existing
`BarPrice`, chronological UTC timestamps (int64 epoch milliseconds), instrument,
timeframe, session/calendar references and dataset revision. It adds context
without copying OHLCV arrays. Convert chart timestamps to seconds at the UI edge.

- Lifecycle: validate parameters -> base initialization -> optional `on_init()`
  once -> one or more independent batch `calculate()` calls.
- The base owns the Pydantic lifecycle; authors do not override its constructor
  or validation lifecycle. Metadata uses ClassVar; caches use private attributes.
- `on_init()` prepares parameter-dependent constants/weights. It performs no
  data download, broker action, or historical per-bar callback loop.
- Batch calls are deterministic for the same parameters, inputs and revision;
  they do not reuse mutable streaming state from a previous calculation.
- Input arrays remain unchanged. Enforce snapshot ownership and read-only views
  at the engine boundary rather than deep-copying arrays on every call.
- All outputs are named, chronological and aligned one-to-one with input rows.
  Preserve the existing IndicatorSeries/DataframeSeries numerical contract.
- Numeric warmup gaps remain NaN with validity information. Boolean condition
  outputs retain a separate validity mask; missing history is not a valid false.
- `required_history` means the first potentially valid result; recommended
  warmup/convergence history is separate metadata for recursive indicators.
- Specify SMA window endpoints, EMA/Wilder seeds, ddof, ties, division by zero,
  NaN handling, rounding and timezone/session semantics explicitly.
- For causal outputs, prefix results cannot change when future data is appended.
  Repainting/delayed indicators declare confirmation and availability semantics.
- Stored arrays stay oldest-to-newest; legacy `.get(shift=0)` remains newest-bar
  access. Graph lags are explicit nonnegative values, separate from plot offsets.
- Use native NumPy/Polars operations where suitable. Recursive algorithms may
  use supported compiled kernels; do not change numerical definitions to appear
  vectorized. `numpy.vectorize()` is not an optimization strategy.
- Convert formats at boundaries; do not repeatedly wrap arrays in dataframes
  inside shared kernels. Never construct Pydantic models per bar.

Optional live mode is an explicit capability: create per-instrument/timeframe
streaming state through a shared factory, then update with completed bars.
An author need not write a second public indicator class. Unsupported indicators
use a documented bounded recalculation fallback, not a fabricated incremental API.
Verify incremental/batch parity with identical seeds, history and closed-bar policy.

## 6. Generic conditions and block boundaries

Provide generic rising, falling, changes-up/down, crosses-above/below, comparison,
and boolean-composition blocks. Connect any compatible named indicator output.
Builder labels such as "RSI is rising" compose metadata; they do not require
`rsi_rising.py` and equivalent files for every indicator.

Keep indicator-specific algorithms with their indicator. Create a separate signal
block only for distinct behavior, such as a specialized multi-output condition.
Indicator comparison helpers and conditions migrate to generic comparison blocks
consuming indicator outputs. Preserve strict/inclusive crossing and lag conventions.

Functions, actions, prices and time blocks each keep their configuration,
descriptor and specific helpers together. Extract genuinely shared helpers.
Split grouped implementations into individual single-class/callable blocks while
updating all consumers directly. Migrate away from monolithic Functions, Comparisons,
Types, and time/price facades directly across the board, removing old monolithic files
once all callers are updated.

## 7. Discovery, reload, identity and file operations

- Discover declarations/manifests without eagerly executing the entire catalog.
- Confine resolved source paths to their authorized roots; reject traversal,
  symlink escapes and protected/private package mutations.
- Load one selected implementation with correct package-relative import context.
- Validate class/callable contracts, schemas, dependencies and duplicate IDs.
- Publish an entire successful registration batch atomically. Failed compilation
  retains the last valid registration and reports precise source diagnostics.
- Package `__init__.py` files expose lightweight/lazy exports; ordinary imports
  must remain usable when an unrelated editable block has a syntax error.
- Compile All distinguishes executable entries, helpers and abstract contracts;
  validates each without misregistering infrastructure as a concrete block.
- Rename updates source mappings, tabs, sessions and manifests; identity stays
  stable. Clone generates a new block ID as well as a unique implementation name.
- Delete reports strategy/dependency references and prevents silent graph damage.
  Bulk imports preflight identity collisions as well as filesystem collisions.
- New compilations resolve current registry entries. Running execution plans pin
  immutable versions/revisions; editing a file does not mutate a running strategy.
- Static `from ... import ...` references are not promised automatic rebinding.
  Execution resolves through registry snapshots, rather than stale global imports.

## 8. Shared strategy document and execution model

Create one schema-versioned document containing node IDs, stable block/version
references, validated parameters, typed edges with named outputs, designated
outputs, variables, market bindings, event triggers and ordered rule statements.
Store JSON-compatible values; never serialize live Python instances or executable
UI display strings. Separate implementation revisions from display names/paths.

Use an acyclic dataflow graph for pure calculations and conditions. Represent
if/else and ordered action sequences structurally, not as arbitrary dataflow
cycles. Stateful variable updates and order operations have explicit event order.
Recognize scalar/series types, units, broadcasts, missing values and bar lags.
Reject incompatible ports, unknown versions, invalid bounds and unavailable data.

The compiler resolves a catalog snapshot, validates/types the document, performs
topological scheduling, shares equivalent pure computations and builds an
inspectable execution plan. Cache keys include normalized parameters, input/
upstream revisions, dataset/instrument/timeframe/session/window and source version.
Cache size/lifetime are bounded; array identity alone is not a valid cache key.

Precompute pure series in batches. The event runner handles ordered conditions,
variables, positions and order intents using the shared trading adapter. Define
bar-open versus bar-close visibility to prevent future OHLC leakage. State belongs
to one run, never a global singleton shared between strategies or workers.

## 9. Ordered implementation phases and exit gates

### Phase 0: inventory and behavioral/performance baseline

- Inventory every exported indicator, helper, block, facade and import consumer.
- Assign legacy-to-canonical paths, stable IDs, output aliases and parameter maps.
- Identify infrastructure versus catalog entries in price/time/comparison/types.
- Record numerical fixtures, exceptional-input behavior, chart/output metadata,
  saved strategy/editor/test documents and existing archive layouts.
- Benchmark representative single/multi-output and recursive indicators on fixed
  datasets (small windows, 100k and 1M bars), fixed threads/runtime and cold/warm runs.
- Record median/p95 latency, peak memory and agreed regression budgets before edits.

Exit: complete migration manifest, representative fixtures and measurable budgets;
no existing public symbol or persisted document type is unaccounted for.

### Phase 1: shared contracts and independent registry

- Implement BlockSpec, typed ports, class/callable descriptors and catalog snapshots.
- Add the single-class validated BaseIndicator, BarData and uniform named outputs.
- Define optional streaming capabilities and frozen configuration/private state.
- Move metric/sizing contracts out of CodeEditor; update consumers directly without compatibility aliases.
- Add stable identity/version checks and explicit generation eligibility metadata.

Exit: sample indicator, function and action register without importing a workspace;
schemas exclude metadata/private state and reject invalid configuration.

### Phase 2: canonical package migration and consumer updates

- Introduce app/include/blocks/; move a representative vertical slice first.
- Update all consumers, importers, registry integrations, and tests directly to
  canonical paths across the board (no compatibility aliases, import shims, or legacy facades).
- Exclude internal modules from public catalog registration; Compile All validates
  syntax and registers canonical block identities.
- Correct relative imports, discovery roots, module identities and registry snapshots.
- Implement source-path and registration ownership consistently on Windows/POSIX.
- Define ID/version collision policies and retained last-valid reload behavior.

Exit: the slice works through canonical registry resolution and direct imports across
all consumers; an unrelated broken source file cannot break package import or execution.

### Phase 3: indicator migration, family by family

Status: complete. All 76 canonical indicators are migrated; see
[the Phase 3 completion report](phase-3-indicator-migration.md) and its final
catalog manifest, parity fixtures, and verification notes.

- Migrate SMA/MovingAverage and RSI first; then BollingerBands/MACD multi-output.
- Convert remaining trend, momentum, volatility, volume, price_action and regime
  families, then custom indicators. Inventory, not a hardcoded count, defines scope.
- Move parameters onto the indicator class; replace ad-hoc argument/default logic.
- Update all consumers, testers, and execution paths directly to canonical single-class
  interfaces. Do not retain legacy facades, method constants, or compatibility adapters.
- Centralize reusable kernels, conditions and metadata; remove duplicated formulas.
  Old files are deleted once consumers are migrated.
- Canonical indicator classes strictly validate configuration parameters on instantiation.

Exit per family: numerical/output parity, prefix/causality checks, schema tests,
tester charts and performance budgets pass before the next family.

### Phase 4: remaining strategy blocks and facades

- Split functions, comparisons and selectable price/time/constants/variable blocks.
- Separate each action; migrate orders and sizing while retaining trading contracts. Update consumers directly.
- Introduce generic signal blocks and indicator-specific signals only where needed.
- Keep infrastructure helpers outside the selectable catalog and avoid import cycles.
  Old monolithic facades are deleted once all consumers are migrated.

Exit: all inventoried selectable components have one canonical owner, an explicit descriptor
and direct consumer imports. An ID manifest tracks all migrated blocks.

### Phase 5: CodeEditor and extension packaging

- Move template destinations to canonical roots; generate single-class indicators.
- Retain all 12 current template categories, placing reporting/robustness/AI
  templates outside strategy blocks where appropriate; add explicit missing block
  templates for functions, prices/time, comparisons, constants and variables.
- Drive parameter controls from schemas, including enum/boolean/optional/nullable
  values and cross-field errors. Remove signature guessing from canonical execution.
- Use metadata for output selection and chart panes; maintain real-history reads.
- Update navigator badges, generic conditions, clone/rename/delete and diagnostics.
- Preserve CodeMirror highlighting/completion, tab histories, saves and shortcuts.
- Migrate saved paths/test names to IDs using HostPersistence; report ambiguity.
- Version archive manifests and migrate known old paths/identities before writing.
  Preserve unknown originals and return actionable errors rather than guessing.
- Keep MCP/AI registration working through its extension contract and adapter.

Exit: create -> edit -> compile -> test -> package -> import works for every category;
old saved editor/test setups and known archive versions migrate without data loss.

### Phase 6: shared strategy document, validation and compiler

- Implement the document, typed validation, version migrations and execution plans.
- Add pure graph evaluation, reusable series caching and an ordered rule/event model.
- Exercise trading through existing simulator/service adapters, never fixture metrics.
- Provide shared catalog/schema/validation/compile/evaluation APIs with host envelopes.

Exit: serialized documents round-trip; identical manual and generated documents
compile to equivalent plans and produce deterministic results on the same inputs.

### Phase 7: AlgoWizard and manual authoring integration

- Replace text-only block identity with typed references and configuration.
- Load catalog entries and parameter/output controls from the shared API.
- Preserve display text as presentation; migrate recognized legacy draft shapes.
- Keep unrecognized text drafts editable and explicitly unresolved; do not execute
  guessed meanings or silently discard them during import/save.
- Surface port/version/history errors and connect real validation/compile previews.

Exit: author and persist a valid strategy, reload it, and evaluate its actual graph;
existing local draft history/import/export behavior remains recoverable.

### Phase 8: Builder and automatic candidate generation integration

- Replace fixture production catalogs and demonstration graph requests with the
  shared catalog, generation settings and strategy document.
- Implement a bounded, seeded candidate-generation path using eligible blocks,
  typed grammar, legal parameter domains, complexity/history limits and shared validation.
- Persist enabled block IDs, weights, parameter ranges, seed and catalog revision.
- Support structural parameter mutation/crossover through the same validation rules;
  do not manipulate display strings as strategy logic.
- Evaluate candidates through the same compiler/execution contract as manual drafts.
- Keep unsupported production search/ranking/backtest features explicitly unavailable.

Exit: a seeded integration run produces repeatable valid candidates, displays them
in the existing builder UI, and opens a candidate in AlgoWizard without losing meaning.

### Phase 9: qualification, documentation and cleanup verification

- Run full tests, numerical parity, benchmark, package-failure and UI regressions.
- Update library/CodeEditor/Builder/AlgoWizard docs, examples and architecture notes.
- Remove fixture catalogs from production authoring paths; keep labelled test fixtures.
- Verify complete elimination of old legacy paths, aliases, shims, and obsolete files
  across the repository.

Exit: all acceptance criteria below pass; unresolved items remain explicit and
prevent claiming completion of the affected capability.

## 10. Verification and acceptance criteria

- All inventoried blocks are discoverable and correctly typed; all migrated
  indicators use the single-class parameter contract, with no public Params twin.
- Every canonical indicator returns aligned named outputs; multi-output selection,
  warmup, timestamps, missing values and causal availability are preserved.
- Invalid configuration fails before calculation. Batch runs do no per-bar model
  validation and do not mutate inputs or leak state between runs/workers.
- All consumers, imports, functions, and persisted documents are updated directly to
  canonical contracts with explicit migration tests. Obsolete paths and legacy facades
  are cleanly eliminated. Unknown versions remain recoverable and are rejected clearly.
- Failed reload retains the last valid implementation; unrelated broken files stay
  isolated; path escapes and protected mutations are rejected before execution.
- Clone creates a fresh identity; rename preserves identity; delete and import
  cannot silently invalidate dependencies or overwrite another registered block.
- Cached results invalidate on data, configuration, dependency or source changes.
- Manual and generated strategies use identical schema/validation/execution paths.
- Warmup-invalid conditions cannot trigger trades; event visibility and action
  ordering are deterministic. Simulator tests verify actual order outcomes.
- Incremental-capable indicators pass batch/stream parity and restart/state tests.
- Recorded performance/memory budgets pass on the same hardware/runtime settings.
- New/modified modules stay within 1,000 lines with concise FR-linked public APIs.
- `uv run pytest tests/ -q`, repository-wide Ruff lint/format, relevant strict mypy,
  frontend unit tests, production build and CodeEditor/Builder/AlgoWizard browser
  regressions pass. Record baseline failures separately; never suppress failures
  globally or replace real calculations with fixtures to satisfy a gate.

## 11. Delivery and scope boundaries

Deliver phases as small reviewable commits with migration manifests, tests,
benchmark evidence and rollback notes. Keep the application usable between phases.
The first implementation slice is shared contracts, one indicator, one generic
condition and one function block exercised through CodeEditor and the shared catalog.

This plan includes the common candidate-generation and execution foundations needed
to prove that both authoring paths share real blocks. Completing an industrial
evolutionary optimizer, distributed/cloud search, all robustness tools, every
broker's fill model, or external platform code generation is separate product work.
Do not claim those capabilities from successful folder moves or a seeded demo.
Do not combine behavior-changing numerical corrections with mechanical migration
without an explicit changed specification and updated reference fixtures.

Start implementation with the Phase 0 inventory and baseline, then deliver the
representative vertical slice before migrating the full catalog.

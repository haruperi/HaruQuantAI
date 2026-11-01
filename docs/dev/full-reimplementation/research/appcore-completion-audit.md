# AppCore Completion Audit and Requirement Verification Matrix

Date: **2026-11-01**
Authoritative Baseline: commit `675dd3c64d5ba79bacf7363c033bb769ab658f15`
Repository: `HaruQuantAI`

## 1. Executive Summary and Format Decision

This audit establishes the concrete status and test evidence for every active work order in AppCore (Phase 01). It replaces historical blanket completion claims with reproducible, requirement-level evidence.

### Ratified Project Format Decision
- **Native Container Format:** `.haru` is the ratified native project container format. It is an atomic ZIP-based package containing structured JSON entities: `manifest.json`, `project.json`, and optional `tasks/{task_id}.json` descriptors, guarded by strict ZIP path validation (no backslashes, absolute paths, or directory traversal).
- **XML `.cfx` Supersession:** Historical work-order instructions in WO-C11.02 and WO-C11.03 specifying XML-based `config.xml` and task XML files are **formally superseded** by this native JSON `.haru` specification.
- **External `.cfx` Interoperability:** Deferred as non-blocking legacy import/export compatibility work. No claim of native `.cfx` support or runtime conversion is made.

---

## 2. Requirement Verification Matrix

Status definitions:
- **`verified`**: Fully implemented with typed signatures, contract enforcement, and passing automated test suites.
- **`partial`**: Core primitives operational; higher-level workspace integrations or edge-case workflows remain ongoing.
- **`superseded`**: Replaced by an approved architectural decision (e.g., native JSON `.haru` format).
- **`routed`**: Reassigned to an owning workspace domain with preserved boundary interfaces.
- **`deferred`**: Explicitly postponed compatibility or non-critical secondary feature.

| Work Order | Capability / Feature | Implementation Files | Test Evidence | Status | Remaining Obligations & Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **COR-M01** | Core foundation migration sketch | `docs/dev/full-reimplementation/01-AppCore.md:125` | N/A (Historical plan) | `superseded` | Historical migration sketch superseded by concrete work orders WO-C00 through WO-C20 per `01-AppCore.md:122`. |
| **WO-C00** | CoreTestBootstrap | `app/web/package.json`, `app/web/vite.config.ts`, `app/web/shell/bootstrap.tsx` | `app/web/tests/bootstrap.test.tsx` | `verified` | Core test infrastructure and frontend isolation bootstrap. |
| **WO-C01** | DomainError | `app/core/lib/errors.py` | `tests/core/lib/test_errors.py` | `verified` | Standardized domain exception hierarchy, error codes, detail dictionaries, and JSON detachment. |
| **WO-C02** | StandardResponse | `app/core/lib/responses.py` | `tests/core/lib/test_responses.py`, `tests/core/host/test_responses.py` | `verified` | Standardized generic response envelope, HTTP status mapping, and backward-compatible builders. |
| **WO-C03** | ProgramRegistry | `app/core/lib/programs.py` | `tests/core/lib/test_programs.py` | `verified` | First-wins program registration, case-sensitive lookup, and structured error logging. |
| **WO-C04** | SettingsManager | `app/core/host/settings.py` | `tests/core/host/test_settings.py` | `verified` | Scoped settings persistence in SQLite, optimistic concurrency revisions, and atomic patching. |
| **WO-C05.01** | BaseBlock & BlockSpec | `app/core/trading/blocks/base.py`, `app/core/trading/blocks/metadata.py` | `tests/core/lib/test_block_contract_imports.py` | `verified` | Generic building block specifications, parameter contracts, and computation interfaces. |
| **WO-C05.02** | BlockRegistry | `app/core/trading/blocks/registry.py` | `tests/core/trading/blocks/test_registry.py` | `verified` | Thread-safe block discovery, staging transactions, duplicate ID policy, and catalog snapshots. |
| **WO-C06.01** | DomainContracts | `app/core/data/contracts.py`, `app/core/enums.py` | `tests/core/data/test_contract_imports.py` | `verified` | Canonical MarketBar, MarketTick, SymbolInfo, Timeframe, OrderType, and session models. |
| **WO-C06.02** | MarketStorage | `app/core/data/market_storage.py` | `tests/core/data/test_storage_imports.py` | `verified` | Arrow/Parquet encoding, integer pricing, and catalog partition scanning. |
| **WO-C06.03** | DataCatalog | `app/core/data/catalog.py`, `app/core/data/io.py` | `tests/core/data/test_catalog.py`, `tests/core/data/test_io.py` | `verified` | Canonical DatasetRef, DataBatch, partition reading, and dynamic OHLCV bar resampling. |
| **WO-C07.01** | LocalCompute | `app/core/jobs/manager.py` | `tests/core/jobs/test_manager.py`, `tests/core/host/test_resources.py` | `verified` | Reuses canonical JobManager process/thread pools for local execution. |
| **WO-C07.02** | RemoteCompute | `app/core/grid/contracts.py`, `app/core/grid/executor.py` | `tests/core/grid/test_executor.py` | `verified` | Canonical RemoteJobSpec, RemoteJobResult, worker heartbeat tracking, and deduplication. |
| **WO-C08.01** | ConditionComparator | `app/core/trading/conditions.py` | `tests/core/trading/test_conditions.py` | `verified` | Typed evaluation of trading condition comparators and complete truth-table assertions. |
| **WO-C08.02** | StrategyRuntime | `app/core/trading/strategy/contracts.py`, `app/core/trading/strategy/runtime.py` | `tests/core/trading/strategy/test_runtime.py` | `verified` | Event-driven rule evaluation, bracket order modifications, and StrategyEffects generation. |
| **WO-C09.01** | SimulationReuseBoundary | `app/core/trading/connection/base.py`, `app/core/trading/simulation/client.py` | `tests/core/trading/simulation/test_exits.py`, `tests/core/trading/simulation/test_operations.py`, `tests/core/trading/simulation/test_strategy_control.py` | `verified` | Shared broker connection contracts, in-memory simulator client, and order lifecycle testing. |
| **WO-C09.02** | BacktestRunner | `app/core/trading/backtest/contracts.py`, `app/core/trading/backtest/runner.py` | `tests/core/trading/backtest/test_runner.py` | `verified` | Chronological bar iteration, order fills, and MAE/MFE excursion tracking. |
| **WO-C10.01** | BaseMetric | `app/core/trading/statistics/base.py`, `app/core/trading/statistics/contracts.py` | `tests/core/trading/statistics/test_metric_contract.py` | `verified` | Base metric contracts and calculation interfaces. |
| **WO-C10.02** | StatisticsService | `app/core/trading/statistics/service.py` | `tests/core/trading/statistics/test_service.py` | `verified` | Performance metric calculation (Net Profit, Drawdown, Sharpe, Sortino, SQN). |
| **WO-C10.03** | MetricDependencyOrder | `app/core/trading/statistics/dependencies.py` | `tests/core/trading/statistics/test_dependencies.py` | `verified` | Topological sorting of metric dependencies. |
| **WO-C11.01** | HostPersistence | `app/core/host/persistence.py` | `tests/core/host/test_persistance.py` | `verified` | Transactional SQLite storage with WAL mode, busy timeout, and connection isolation. |
| **WO-C11.02** | ProjectStore & ResultStore | `app/core/trading/project/store.py`, `app/core/trading/results/store.py`, `app/core/trading/results/adapters.py` | `tests/core/trading/project/test_store.py`, `tests/core/trading/results/test_store.py`, `tests/core/trading/results/test_backtest_integration.py` | `verified` | StoredRunResult persistence, conversion adapter from backtest result, MAE/MFE retention. |
| **WO-C11.03** | ProjectEnvelope | `app/core/trading/project/envelope.py` | `tests/core/trading/project/test_envelope.py` | `verified` | Implemented native `.haru` container; XML `.cfx` marked superseded. |
| **WO-C12.01** | RandomGenerator | `app/core/generators.py` | `tests/core/lib/test_generators.py` | `verified` | Deterministic pseudo-random generation seeds and PRNG algorithms. |
| **WO-C12.02** | ResearchEngines | `app/core/trading/optimization/engine.py`, `app/core/trading/optimization/__init__.py` | `tests/core/trading/test_research_engines.py`, `tests/core/trading/test_walk_forward_execution.py` | `verified` | Fixed mixed-radix grid index inversion; added complete walk-forward execution workflow. |
| **WO-C13.01** | JobManager | `app/core/jobs/manager.py` | `tests/core/jobs/test_manager.py` | `verified` | Background process job coordinator, process/thread pool management, and event bus. |
| **WO-C13.02** | DatabankJobs | `app/core/jobs/databank.py` | `tests/core/jobs/test_databank.py` | `verified` | Transactional add, move, delete operations across databanks. |
| **WO-C14** | HostTransport | `app/core/host/transport.py`, `app/core/host/events.py`, `app/core/host/session.py` | `tests/core/host/test_transport.py`, `tests/core/host/test_events.py`, `tests/core/host/test_session.py` | `verified` | FastAPI ASGI application, session validation, and WebSocket event transport. |
| **WO-C15** | WizardTransformBoundary | `app/core/wizard/transform.py` | `tests/core/wizard/test_transform.py` | `verified` | Multi-platform code generator with fail-closed validation, Python AST parsing, and instance operand resolution. |
| **WO-C16** | SQAppLibAttribution | `docs/dev/full-reimplementation/01-AppCore.md:100-117` | Decompilation SHA-256 and AES-256-GCM verification | `verified` | Verified container bundle of SQTradingLib and plugins. |
| **WO-C17.01** | ApplicationEntrypoints | `app/main.py`, `app/cli.py` | `tests/host/test_main.py`, `tests/host/test_cli.py` | `verified` | FastAPI service lifecycle and headless CLI runner. |
| **WO-C17.02** | WebBuildServing | `app/main.py` | `tests/host/test_web_build.py` | `verified` | Static web distribution asset serving and SPA routing fallback implemented in `app/main.py:193`. |
| **WO-C18** | CodeEditorOwnership | Routed to `app/workspace/code_editor/` | `tests/workspace/code_editor/` | `routed` | Concrete code editor tabs, snippet tools, and compilation routed to AppCodeEditor (Phase 04). |
| **WO-C19** | SnippetOwnership | Routed to workspace owners (`app/include/blocks/`, `app/extend/monte_carlo/`) | `tests/include/blocks/`, `tests/include/what_if/`, `tests/extend/monte_carlo/` | `routed` | Concrete indicator and simulation extensions managed in workspace domains. |
| **WO-C20** | RuntimeDependencies | `pyproject.toml`, `uv.lock` | Environment lock validation (`uv lock --check`) | `verified` | Pinned dependency tree under uv package manager. |

---

## 3. Detailed Audit Defect Resolutions

### 1. Result Persistence Adapter
- **Defect:** `BacktestRunner.run` produces `backtest.contracts.RunResult` which was incompatible with `ResultStore.save_result` (expected `results.contracts.RunResult`). MAE/MFE excursions were dropped during databank persistence.
- **Resolution:**
  - Added dedicated conversion adapter `from_backtest_result` in `app/core/trading/results/adapters.py`.
  - Added optional `mae_mfe: tuple[dict[str, JSONValue], ...] = ()` to `results.contracts.RunResult` with full backward-compatibility for legacy records.
  - Mapped execution `max_drawdown` into stored `drawdown` summary KPI without altering input metrics.
  - Enforced fail-closed validation rejecting NaN/Inf floating point values in payloads and metrics.
  - Proved end-to-end integration via `tests/core/trading/results/test_backtest_integration.py`.

### 2. Optimization Linear Index Permutation Inversion
- **Defect:** `OptimizationIndexes.get_params` varied the last parameter fastest, whereas `get_index` varied the first parameter fastest, breaking index round trips on multi-parameter asymmetric grids.
- **Resolution:**
  - Corrected `get_index` in `app/core/trading/optimization/engine.py` to match the exact mixed-radix stride order of `get_params`.
  - Verified round-trips and explicit Cartesian combinations across asymmetric ($2 \times 3$, $2 \times 3 \times 4$), single-dimension, and singleton parameter spaces.

### 3. Strategy Export Fail-Closed Validation
- **Defect:** `StrategyTransformer` emitted raw unvalidated comparators and undeclared identifiers into exported platform code, producing syntactically invalid Python without failing closed. Declared parameters and state variables were referenced as bare symbols instead of instance attributes (`self.<name>`), causing runtime `NameError` on evaluation. Composition blocks were accepted without code generation.
- **Resolution:**
  - Enforced strict allowlist for comparators (`==`, `!=`, `>`, `<`, `>=`, `<=`).
  - Enforced operand validation against declared strategy parameters, state variables, and recognized market fields (`open`, `high`, `low`, `close`, `volume`, `tick_volume`, `open_price`, `high_price`, `low_price`, `close_price`).
  - Distinguished parameter and state variable symbols from market fields and numeric literals, emitting `self.<norm_name>` for Python exports while preserving bare identifiers for external platforms (MQL5, MQL4, cTrader, EasyLanguage).
  - Rejected unsupported indicator composition blocks that lack concrete code emission templates.
  - Validated Python output with `ast.parse` before asserting success. Non-Python external targets undergo template rendering without AST syntax compilation.
  - Verified generated Python strategies compile, instantiate, and evaluate cleanly with parameter overrides and mutable state variables.

### 4. Walk-Forward Execution Engine
- **Defect:** `OptimizationEngine` defined window generation and WFE calculations, but lacked an end-to-end execution workflow.
- **Resolution:**
  - Implemented `run_walk_forward` with typed `WalkForwardWindowResult`.
  - Enforced half-open slice bounds $[start, end)$, strictly monotonic bar timestamps, and cooperative cancellation token checks.
  - Verified aggregate WFE calculation, stable tie-breaking, slice data isolation, and progress logging.
  - Verified mid-run cancellation, cancellation immediately before return, bubbling of evaluator exceptions, and rejection (`INVALID_WALK_FORWARD_SPEC`) when fewer windows than requested can be generated.

### 5. Coverage and Acceptance Evidence Status
- **Application-Wide Coverage Status:** RESOLVED / PASSED.
  - Executing `uv run python -m pytest tests --cov=app --cov-branch -q` exited **0** with **2,651 passed** (in 187.28s) and **84.02%** combined statement/branch coverage across all application source (`app`).
  - This outcome satisfies and exceeds the repository `fail_under = 80` requirement across the full application test suite.
  - Diagnostic warnings regarding temporary test-generated source files that had been removed during execution were noted and verified benign.
- **Changed Core Target Modules Coverage:**
  - `app/core/trading/results/contracts.py`: 70/72 statements (97.2%), 10/14 branches (71.4%), 93% combined coverage.
  - `app/core/trading/results/adapters.py`: 70/72 statements (97.2%), 29/34 branches (85.3%), 93% combined coverage.
  - `app/core/trading/results/store.py`: 60/65 statements (92.3%), 9/12 branches (75.0%), 90% combined coverage.
  - `app/core/trading/optimization/engine.py`: 199/218 statements (91.3%), 59/72 branches (81.9%), 89% combined coverage.
  - `app/core/wizard/transform.py`: 212/235 statements (90.2%), 48/54 branches (88.9%), 89% combined coverage.

---

## 4. Documentation Migration and Deprecation Guidelines

Both `00-README.md` and `01-AppCore.md` are retained in place. Before archiving or deleting `00-README.md` or `01-AppCore.md`, the following dependencies must be preserved elsewhere:
1. **Preserve Provenance:** Historical notes describing decrypted carrier analysis (`SQAppLib.jar.enc`, `SQLib.jar.enc`) and static dependency graphs serve as permanent reference provenance and must not be deleted.
2. **Preserve Shared Instructions and Evidence:** Baseline reimplementation guidance, architecture rationale, and migration instructions must be fully migrated before deprecating either file.
3. **Update Cross-References:** Any incoming links from workspace specifications to `WO-C11.02` and `WO-C11.03` must link to this audit document and reference `.haru` as the accepted format.

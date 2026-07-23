# Optimization Domain — Capability Feature Extraction (from `09-Optimization.md`)

Source: `docs/dev/phase-implementation-plan/09-Optimization.md`. Module paths follow the plan's target tree under `app.services.optimization`. Example programs and package `__init__` re-exports are omitted.

---

## FEAT-OPT-01: Public Registry and Official Tool Boundary (app.services.optimization / .api)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `list_optimization_tools() -> tuple[ToolDescriptor, ...]` | Immutable official-tool catalog from explicit exports (with `validate_public_registry` and lazy `__getattr__`). | Missing |
| `optimization_tool_context(kwargs: Mapping[str, object]) -> OptimizationToolContext` | Extract request ID, agent name, environment, approval, and dry-run context. | Missing |
| `optimization_business_payload(kwargs: Mapping[str, object]) -> Mapping[str, object]` | Retain business request fields separately from standard context. | Missing |
| `package_optimization_request(request: OptimizationRequest, context: OptimizationToolContext) -> OptimizationRequestPackage` | Deterministic request packaging with no candidate execution, persistence, networking, or background jobs. | Missing |
| `optimization_tool_result(tool_name: str, outcome: ToolOutcome, context: OptimizationToolContext) -> OptimizationEnvelope` | Standard JSON-safe result envelope; `dry_run=True` by default and `places_trade=False` always. | Missing |
| `sanitize_public_payload(value: object) -> JsonSafePayload` | NaN/Infinity → null with warning, UTC ISO datetimes, normalized Decimals; fails closed on unsupported values. | Missing |

## FEAT-OPT-02: Optimization Contracts, Ports, and Errors (app.services.optimization.contracts)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `OptimizationRequest.validate() -> ValidationResult` | Validate request shape with deterministic field errors. | Missing |
| `OptimizationResult.to_record() -> Mapping[str, JsonValue]` | JSON-safe candidate result record (with `OptimizationSummary.top_n` and tabular payload). | Missing |
| `BacktestExecutionAdapter.execute(request: CandidateExecutionRequest) -> EngineOptimizationResult` | Versioned simulator/backtest adapter port executing one approved candidate. | Implemented |
| `OptimizationRepository.save_run(run: OptimizationRunRecord) -> SaveReceipt` | Injected persistence port (with `load_checkpoint`). | Missing |
| `ExecutionOrchestrator.submit(work: OptimizationWorkUnit) -> TaskReference` | Scheduling port with deterministic ordered mapping and isolated work-unit failures. | Missing |
| `optimization_error(code: OptimizationErrorCode, message: str, details: Mapping[str, JsonValue] \| None = None) -> OptimizationError` | Typed redacted domain errors with deterministic `OPT_*` codes (with execution-failure mapping and dependency-unavailable errors). | Missing |

## FEAT-OPT-03: Execution Profiles and Resource Caps (app.services.optimization.config)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_execution_profile(profile: ExecutionProfile) -> ValidationResult` | Reject unbounded or invalid resource settings. | Missing |
| `assert_resource_caps(request: OptimizationRequest, profile: ExecutionProfile) -> None` | Fail closed when requested work exceeds approved caps (with monotonic deadlines and packaging-latency estimation). | Missing |

## FEAT-OPT-04: Preflight Validation (app.services.optimization.validation)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `validate_optimization_request(request: OptimizationRequest) -> ValidationResult` | Validate request, objective, input sizes, strategy compatibility, and market-data prerequisites. | Missing |
| `validate_parameter_space(space: ParameterSpace) -> ValidationResult` | Validate float/integer/categorical/boolean/fixed/conditional/constrained parameter definitions. | Implemented |
| `evaluate_constraint(constraint: ConstraintDefinition, values: Mapping[str, ScalarValue]) -> ConstraintOutcome` | Evaluate only approved parsed constraints; block unsafe expressions. | Missing |
| `validate_evidence_package_shape(package: EvidencePackage) -> ValidationResult` | Validate schema and required evidence fields before persistence or handoff. | Missing |

## FEAT-OPT-05: Canonicalization, Candidates, Scoring, and Anti-Overfit (app.services.optimization.core)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `canonicalize_parameter_space(space: ParameterSpace) -> CanonicalParameterSpace` | Canonical parameter definitions with SHA-256 `parameter_space_hash` and `candidate_hash` deduplication identity. | Missing |
| `build_executable_candidate(space: ParameterSpace, proposed_values: Mapping[str, ScalarValue], lineage: CandidateLineage) -> OptimizationCandidate` | Filter inactive values, apply constraints, create canonical identity. | Missing |
| `rank_parameter_sets(candidates: Sequence[OptimizationResult]) -> tuple[OptimizationResult, ...]` | Deterministic ranking: score desc, trade count desc, candidate hash asc. | Implemented |
| `calculate_parameter_stability(candidates: Sequence[OptimizationResult]) -> ParameterStabilityReport` | Per-parameter stability (with in-sample vs OOS overfit-parameter detection). | Implemented |
| `optimization_get_scoring_func(objective: ObjectiveDefinition) -> ScoringFunction` | Resolve objective to a typed scoring function (Sharpe, Sortino, Calmar, profit factor, total return, weighted custom). | Missing |
| `select_pareto_front(candidates: Sequence[OptimizationResult], policy: ParetoPolicy) -> ParetoSelection` | Deterministic Pareto and knee-point fallback selection. | Missing |
| `evaluate_anti_overfit_gates(evidence: CandidateEvidence, policy: OverfitPolicy) -> AntiOverfitAssessment` | Evaluate configured overfit gates producing warnings/rejections without decision authority. | Missing |
| `calculate_deflated_sharpe(inputs: DeflatedSharpeInputs) -> DeflatedSharpeResult` | Raw/deflated Sharpe evidence with trial-count disclosure and no-live-readiness caveats. | Implemented |

## FEAT-OPT-06: Search Algorithms — Grid, Random, Bayesian, Genetic (app.services.optimization.algorithms)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_search(request: SearchRequest, adapter: BacktestExecutionAdapter, orchestrator: ExecutionOrchestrator) -> OptimizationSummary` | Coordinate approved candidate work with deterministic result aggregation. | Missing |
| `grid_search(request: GridSearchRequest, adapter: BacktestExecutionAdapter, orchestrator: ExecutionOrchestrator) -> OptimizationSummary` | Strict-iterator grid evaluation (with `iter_grid_candidates`, parallel variant, and dry-run-aware public wrapper). | Missing |
| `random_search(request: RandomSearchRequest, adapter: BacktestExecutionAdapter, orchestrator: ExecutionOrchestrator) -> OptimizationSummary` | Seeded reproducible sampling (with `sample_candidates`, deterministic phase seeds, parallel variant, public wrapper). | Missing |
| `bayesian_optimization(request: BayesianOptimizationRequest, backend: OptimizerBackend, adapter: BacktestExecutionAdapter) -> OptimizationSummary` | Approved Bayesian search via adapter (with public wrapper). | Missing |
| `genetic_algorithm(request: GeneticOptimizationRequest, adapter: BacktestExecutionAdapter, orchestrator: ExecutionOrchestrator) -> OptimizationSummary` | Deterministic population initialization, selection/crossover/mutation/elitism evolution (with public wrapper). | Missing |

## FEAT-OPT-07: Time-Series Splits and Walk-Forward (app.services.optimization.time_series)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `splitter_from_rolling(config: RollingSplitConfig) -> TimeSeriesSplitter` | Deterministic rolling windows (with expanding and train/validation/test splits). | Missing |
| `apply_purge_and_embargo(windows: Sequence[WalkForwardWindow], policy: EmbargoPolicy) -> tuple[WalkForwardWindow, ...]` | Purge/embargo gap controls with recorded effective embargo bars. | Missing |
| `generate_cpcv_paths(config: CpcvConfig) -> tuple[CpcvPath, ...]` | Deterministic purged, embargoed combinatorial CV paths (with split-evidence disclosure). | Missing |
| `walk_forward(request: WalkForwardRequest, adapter: BacktestExecutionAdapter, splitter: TimeSeriesSplitter) -> WalkForwardResponse` | Optimize each training window and evaluate OOS windows (with parallel, packaged, background-task, and public-wrapper variants). | Missing |
| `analyze_walk_forward_results(response: WalkForwardResponse) -> WalkForwardEvidence` | Derive fold pass rate, drift, OOS retention, WFE, score, and status. | Missing |

## FEAT-OPT-08: Robustness, Monte Carlo, Scenarios, and Prop-Firm Gates (app.services.optimization.robustness)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_spread_stress_test(request: RobustnessRequest) -> RobustnessWorkPackage` | Stress/MC work packaging family: spread, slippage, commission, trade-order/resample/skip/parameter/history randomization, combined MC, cross-market/timeframe, second/third OOS, and report packaging. | Missing |
| `assess_strategy_robustness(request: RobustnessRequest, rng: DeterministicRandom) -> RobustnessAssessment` | Comprehensive Monte Carlo robustness evidence (with deterministic robustness score and simulation runs). | Implemented |
| `monte_carlo_analysis(result: BacktestResult, simulation_type: MonteCarloMethod, seed: int) -> MonteCarloResult` | Selected MC analysis over a completed backtest (shuffle, resample, block bootstrap, method comparison, confidence intervals, background tasks). | Missing |
| `parametric_simulation(win_rate: Decimal, reward_risk_ratio: Decimal, risk_per_trade: Decimal, trade_count: int, simulation_count: int, initial_balance: Decimal, seed: int) -> ParametricSimulationResult` | Scenario family: parametric accounts, random win-rate, position sizing, consecutive losses, profit targets, multi-entry. | Missing |
| `evaluate_prop_firm_compliance(evidence: CandidateEvidence, profile: PropFirmProfile) -> PropFirmComplianceEvidence` | Evaluate selected prop-firm profile gates at required frequency (with profile validation and intraday-evidence requirement). | Missing |
| `calculate_pbo(cpcv: CpcvEvidence, policy: PboPolicy) -> PboAssessment` | Probability-of-backtest-overfitting gate with flag/reject outcome (with `calculate_probability_of_ruin`). | Missing |

## FEAT-OPT-09: Candidate Execution, Orchestration, and Progress (app.services.optimization.execution)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `run_strategy_backtest(request: CandidateExecutionRequest, adapter: BacktestExecutionAdapter) -> EngineOptimizationResult` | Execute exactly one candidate through the versioned adapter (with result conversion and adapter-request validation). | Missing |
| `load_strategy_from_path(path: StrategyPathRef, class_name: str) -> type[Strategy]` | Controlled module loading for candidate backtests (with class/factory normalization and load-then-execute helper). | Missing |
| `validate_no_live_capability(context: ExecutionContext) -> ValidationResult` | Reject live broker credentials, gateways, trade permissions, and production strategy mutation. | Missing |
| `run_optimization_task(request: OptimizationRequest, orchestrator: ExecutionOrchestrator) -> TaskReference` | Background run coordination (with serializable work-unit submission, deterministic aggregation, tabular analysis, prune hooks). | Missing |
| `ProgressTracker.advance(delta: int, event: ProgressEvent) -> ProgressSnapshot` | Synchronized bounded progress state (with start/cancel, speedup comparison, worker-count recommendation, and completion estimates). | Missing |

## FEAT-OPT-10: Run Persistence, Checkpoints, and Candidate Cache (app.services.optimization.persistence)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `save_run(repository: OptimizationRepository, run: OptimizationRunRecord) -> SaveReceipt` | Dependency-injected run persistence (with idempotent progress lookup and cancellation, safe transient retries, and capability validation). | Missing |
| `checkpoint_due(state: OptimizationRunState, policy: CheckpointPolicy) -> bool` | Checkpoint eligibility (with save, validation, resume selection, atomic write semantics, and pruned-candidate evidence). | Missing |
| `candidate_cache_key(lineage: CandidateLineage, candidate_hash: str) -> CandidateCacheKey` | Full lineage-aware cache key with governed invalidation (`is_cache_valid`) and cached-candidate loading. | Missing |

## FEAT-OPT-11: Evidence Packages, Handoffs, and Reports (app.services.optimization.evidence)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `build_evidence_package(summary: OptimizationSummary, assessments: EvidenceAssessments) -> EvidencePackage` | Compose full optimization, walk-forward, robustness, MC, prop-firm, decision, warning, and visualization evidence. | Missing |
| `build_risk_handoff(package: EvidencePackage) -> RiskGovernorHandoffPackage` | Advisory-only handoff to the Risk Governor; never grants approval (with `assert_advisory_only` and promotion-evidence validation). | Missing |
| `build_portfolio_handoff(package: EvidencePackage) -> PortfolioHandoffPackage` | Capacity, exposure assumptions, cross-market/timeframe/regime evidence, AUM, and warnings for Portfolio. | Missing |
| `build_chart_ready_payload(package: EvidencePackage) -> VisualizationPayload` | Chart-ready curves, distributions, heatmaps, Pareto, folds, cones, and capacity data without rendering. | Missing |
| `render_evidence_report(package: EvidencePackage, format: ReportFormat) -> ReportPayload` | JSON/Markdown evidence reports with mandatory sample/OOS/robustness/overfit caveats (with top-candidate report formatting). | Missing |

## FEAT-OPT-12: Periodic Portfolio Optimization (app.services.optimization.portfolio)

---

| Function | Purpose | Status |
| :--- | :--- | :--- |
| `pfo_from_optimize_func(callback: PortfolioOptimizationCallback, schedule: PeriodicOptimizationSchedule) -> PortfolioOptimizerResult` | Scheduled invocation of a supplied deterministic portfolio-optimization callback. | Missing |
| `pfo_plot(result: PortfolioOptimizerResult) -> NonUiInspectionPayload` | Allocation-weight inspection payload without UI rendering. | Missing |

---

**Note:** the optimization service is advisory-only: public tools default to `dry_run=True`, always carry `places_trade=False`, never access live brokers, and never return `approved_for_live_trading`. All randomness is seeded and all rankings, hashes, and aggregations are deterministic for reproducibility.

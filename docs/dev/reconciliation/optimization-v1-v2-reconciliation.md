# Optimization — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** optimization
* **Domain ID:** `opt`
* **V1 audit report:** `optimization-v1-audit.md`
* **V2 requirements:** `09_optimization.md`
* **Comparison limitations:** This reconciliation uses the V1 audit as the sole evidence of V1 behavior and the V2 document as the sole proposal source. No code was re-audited or changed. V1 callers outside the audited repository remain unconfirmed because the audit lacked indexed repository-wide search and clean-checkout execution. The V2 source has no stable IDs, so this document assigns reconciliation reference IDs (`V2-OWN-*`, `V2-API-*`, `V2-FR-*`, `V2-NFR-*`, `V2-EDGE-*`, `V2-TEST-*`) without modifying the source.
* **Cross-domain alignment limitation:** Package location, shared envelopes, Simulation adapter ownership, repository infrastructure, Risk/Portfolio handoffs, and system-level deferrals are marked for escalation to pipeline step 05. The top-level system document was not an allowed input or output in this step.

## 2. Executive Summary

V1 contains credible value in parameter validation, safe constraint evaluation, deterministic hashing, lazy grid generation, seeded pseudo-random generation, core scoring, DSR, time-series splits, trade-sequence Monte Carlo, stress transformations, atomic checkpoint semantics, and a thread-safe in-memory fixture. Those behaviors should be reused or refactored rather than rewritten indiscriminately.

The main V1 weaknesses are structural and contractual: a 151-name accidental facade, inconsistent return/error shapes, fake dry-run ranking from empty trades, broken simulator and strategy-registry imports, duplicated walk-forward and ranking/reporting surfaces, disconnected persistence, misleading save/task functions, mislabeled Bayesian/Sobol/LHS behavior, and broad exception swallowing that converts integration failures into zero scores.

V2 correctly establishes the no-live-trading boundary, public request-packaging versus internal execution separation, intentional registry, standard envelope, deterministic provenance, versioned evidence, a versioned backtest adapter contract, bounded execution, and explicit production gates. These are approved in simplified form.

V2 also proposes excessive initial scope: one public function per robustness variation, dynamic source-file loading, multiple algorithm-specific public wrappers, true Bayesian/genetic/advanced sampler backends, CPCV/PBO/topology gates, specialized simulations, portfolio allocation optimization, prop-firm rule evaluation, background orchestration, multiple repository backends, pruning, distributed backends, and a large mandatory institutional evidence schema. These items are rejected, merged, or deferred unless a demonstrated workflow and owner approval exist.

The recommended direction is a **small public packaging/calculation surface** over a **focused internal research core**: parameters, grid/pseudo-random search, execution adapter contract, scoring, splits/WFA, Monte Carlo/robustness, and evidence. Repository-backed execution, parallel/background orchestration, advanced optimizers, CPCV/PBO, and specialized scenarios remain deferred. Optimization never owns broker access, risk approval, portfolio allocation, strategy promotion, UI rendering, concrete persistence, or prop-firm rule evaluation.

## 3. Decision Principles

* Preserve proven deterministic calculations and safety behavior.
* Treat V1 as evidence, not as the future package contract.
* Treat V2 as a proposal, not an automatic implementation backlog.
* Keep public tools limited to validated packaging and lightweight deterministic calculations.
* Separate public packaging from internal compute and cross-domain execution.
* Use explicit exports; do not preserve the accidental 151-name V1 facade.
* Prefer functions for stateless calculations and typed data contracts for boundaries.
* Use a class or protocol only when it owns state, lifecycle, or an injected cross-domain dependency.
* Do not own Simulation, Risk, Portfolio, Strategy, UI, broker, or persistence-infrastructure behavior.
* Reject misleading compatibility, fake task IDs, fake saves, fake algorithms, and silent fallbacks.
* Add advanced algorithms, orchestration, repositories, and institutional gates only after a named workflow, owner, policy, and tests exist.
* Keep one focused capability per module folder and colocate its contracts; avoid generic `helpers.py` and monolithic `models.py`.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-OPT-001 | Public contracts and registry | `V1-CAP-OPT-016`; 151-name facade; `V1-WF-OPT-001` | `V2-OWN-OPT-001..003`; `V2-API-OPT-001..002,019..023`; `V2-FR-OPT-004..014,022..024` | V1 exposes accidental internals and inconsistent envelopes. | Modify | Expose only approved packaging/calculation tools; one JSON-safe envelope; `places_trade=False`; explicit stability and behavior classification. | Refactor | Preserves the useful envelope while removing accidental API surface and fake execution semantics. |
| CAP-OPT-002 | Request packaging and lightweight public calculations | `V1-CAP-OPT-016`; unused packaging helpers; V1 stability/overfit/ranking functions | `V2-API-OPT-003..016`; `V2-FR-OPT-032..062` | V1 mixes calculations, execution, and misleading save/report wrappers. | Modify | Validated, side-effect-free packages for expensive work; deterministic calculation tools for stability, overfit, ranking, and robustness score. | Refactor | Matches the V2 current milestone and prevents public tools from performing hidden compute or persistence. |
| CAP-OPT-003 | Parameter definitions, constraints, provenance, and hashes | `V1-CAP-OPT-001..002`; `V1-WF-OPT-001` | `V2-FR-OPT-015,017..021,169,203..206`; `V2-NFR-OPT-027..028` | V1 is strong but omits some provenance and guardrails. | Modify | Validated typed parameter spaces; safe constraints; executable-parameter filtering; canonical parameter-space and candidate provenance hashes. | Reuse/Refactor | This is proven self-contained value and foundational to reproducible search. |
| CAP-OPT-004 | Bounded grid and pseudo-random search | `V1-CAP-OPT-003..004`; `V1-WF-OPT-001..002` | `V2-FR-OPT-064,066,072..078`; resource NFRs | Dry-run ranks empty trades; real execution is broken; advanced sampler labels are false. | Modify | Internal bounded search engines evaluate candidates through an injected evaluator; grid is lazy; pseudo-random is deterministic; no false sampler claims. | Refactor | Keeps working candidate generation while separating packaging, execution, and optional algorithms. |
| CAP-OPT-005 | Backtest execution adapter contract | `V1-CAP-OPT-007`; broken `V1-WF-OPT-002` | `V2-OWN-OPT-020`; `V2-FR-OPT-083,085..092` | V1 directly imports missing simulator orchestration and hard-codes version/identity. | Modify | Optimization defines a small versioned adapter protocol and result contract; Simulation supplies the implementation; fail closed on incompatibility. | Replace integration, reuse result-shaping concepts | This is the smallest cross-domain boundary that enables real optimization without owning the simulator. |
| CAP-OPT-006 | Scoring, ranking, and baseline overfit evidence | `V1-CAP-OPT-009`; `V1-WF-OPT-006` | `V2-FR-OPT-037..040,148..165` | Trial semantics, objective fallback, and correlated-search warnings are inconsistent. | Modify | Core scores, deterministic ranking, DSR/nominal-trial evidence, IS/OOS gap, WFA and MC caveats; advanced topology/PBO gates deferred. | Refactor | Preserves credible calculations without accepting the entire institutional scoring proposal. |
| CAP-OPT-007 | Time-series validation splits | `V1-CAP-OPT-010`; split portion of `V1-WF-OPT-004` | `V2-FR-OPT-096..107` | Mechanical splits work but validation and leakage evidence are incomplete. | Modify | Validated chronological, rolling, anchored/expanding splits with configurable purging/embargo and explicit boundary evidence. | Reuse/Refactor | Essential for honest out-of-sample workflows; CPCV and PBO remain deferred. |
| CAP-OPT-008 | Walk-forward validation | `V1-CAP-OPT-011`; `V1-WF-OPT-004` | `V2-API-OPT-004`; `V2-FR-OPT-034..035,093..107` | Two V1 implementations diverge; dry-run is noninformative; real execution is broken. | Merge | One internal WFA workflow uses CAP-OPT-004/005/007; public tools only package requests; evidence records folds and degradation. | Refactor | Eliminates duplication and separates the public request boundary from internal compute. |
| CAP-OPT-009 | Monte Carlo analysis | `V1-CAP-OPT-012,019`; `V1-WF-OPT-005` | `V2-FR-OPT-108..128` | Core simulations work, but validation/evidence and seed provenance are incomplete. | Modify | Validated shuffle, empirical resample, block bootstrap, probability/interval summaries, and parametric simulation over supplied results. | Reuse/Refactor | Strong in-memory research value with no broker authority. |
| CAP-OPT-010 | Robustness analysis | `V1-CAP-OPT-013`; `V1-WF-OPT-005` | `V2-API-OPT-011..015`; `V2-FR-OPT-043..057,114..121,177` | Public-versus-internal behavior is confused and cross-market execution hides failures. | Modify | Internal deterministic stress calculations plus public request packaging; failures remain structured and never become zero scores silently. | Refactor | Preserves useful stress transforms while removing misleading execution and wrapper duplication. |
| CAP-OPT-011 | Versioned evidence and downstream handoffs | V1 reports and partial response models; no complete evidence workflow | `V2-API-OPT-017`; `V2-FR-OPT-025..027,030,102,127,179..184` | V1 lacks a coherent evidence package and overstates save/report completion. | Add | Versioned evidence containing provenance, candidates, scores, WFA/MC/robustness summaries, warnings, audit references, and chart-ready raw series. | New with selective reuse | Required cross-domain output; capacity/prop-firm data may be carried only when supplied by owning domains. |
| CAP-OPT-012 | Run-state, checkpoint, and repository contracts | `V1-CAP-OPT-014..015`; `V1-WF-OPT-007..008` | `V2-API-OPT-018`; `V2-FR-OPT-029,193..206` | V1 utilities are disconnected and concrete in-memory persistence lives in the domain. | Defer | Define only schemas/protocols now; activate save/resume/cancel/checkpoint workflows after repository backend, artifact root, and idempotency policy approval. | Refactor later | Valuable behavior exists, but production ownership and limits are unresolved and cross-domain. |
| CAP-OPT-013 | Execution progress, cancellation, and background coordination | `V1-CAP-OPT-018`; `V1-WF-OPT-009` | `V2-FR-OPT-133..147,188..192` | V1 IDs are stubs; V2 proposes a large orchestration layer without approved execution profile. | Defer | No fake task APIs. Add a minimal injected execution/progress contract only after queue, quota, cancellation, retry, and repository decisions. | Replace later | Avoids preserving stubs or prematurely adding managers/orchestrators. |
| CAP-OPT-014 | Advanced samplers and optimizers | `V1-CAP-OPT-005..006` | `V2-FR-OPT-068..080` | Genetic is unintegrated; Bayesian and Sobol/LHS are mislabeled/placeholders. | Defer | Pseudo-random remains baseline. True Sobol/LHS, genetic, Optuna, or skopt implementations require explicit workflow, dependency, and evidence approval. | Archive/rebuild later | No demonstrated current workflow justifies optional dependencies or multiple algorithm surfaces. |
| CAP-OPT-015 | Specialized scenario simulations | `V1-CAP-OPT-019..020` | `V2-FR-OPT-117..120,122,125,171,174..176,178` | Mostly schemas without implementation or callers. | Defer | Do not ship position-sizing, streak, target, random-pair, or multi-entry APIs until a named research workflow and owner approve each one. | Selective new work later | Prevents speculative model growth while preserving parametric/MC core. |
| CAP-OPT-016 | Portfolio allocation optimization | Only unused `PortfolioOptimizerResult` schema in `V1-CAP-OPT-020` | `V2-FR-OPT-185..187` | No V1 workflow; allocation ownership conflicts with Portfolio Manager boundary. | Remove | Optimization may provide candidate evidence, but portfolio weight optimization belongs to the Portfolio domain. | Do not reuse | This is a cross-domain ownership violation and unsupported scope expansion. |
| CAP-OPT-017 | Dynamic source-file strategy loading | `V1-CAP-OPT-008`; broken `V1-WF-OPT-003` | `V2-FR-OPT-081,084` | Broken, unsafe arbitrary code execution and duplicate strategy registration responsibility. | Remove | Accept approved strategy identifiers or adapter-owned strategy handles only; no arbitrary file loading in optimization. | Remove after caller check | A versioned adapter boundary makes this unnecessary. |
| CAP-OPT-018 | Errors, serialization, and safety metadata | V1 error mapper/registry, `json_safe_serialize`, mixed emitted codes | `V2-FR-OPT-006..014,022..024`; `V2-NFR-OPT-017..024,035..037` | V1 contracts are inconsistent and error codes do not match emissions. | Modify | One deterministic `OPT_` taxonomy, redacted structured errors, JSON-safe outputs, explicit side effects, and no live-trading authority. | Refactor | Cross-cutting behavior is required, but helper and registry duplication should be consolidated. |

## 5. V1 Disposition Register

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V1-CAP-OPT-001 | Parameter range/space validation | `models.ParameterRange`, `ParameterSpace`, AST constraint validation | Essential | Modify | CAP-OPT-003 Parameter definitions and validation | N/A | Preserve validation, add cycle/step/size checks, and separate schema validation from execution. |
| V1-CAP-OPT-002 | Canonical parameter/candidate hashing | `parameter_space_hash`, `get_active_parameters`, `build_candidate_hash` | Essential | Modify | CAP-OPT-003 Provenance and deduplication | N/A | Retain deterministic SHA-256 behavior; include the parameter-space hash explicitly and use executable parameters only. |
| V1-CAP-OPT-003 | Exhaustive grid search | `grid_search`, `parallel_grid_search` | Essential | Modify | CAP-OPT-004 Bounded search execution | N/A | Keep lazy grid generation; remove fake dry-run scoring and require an injected execution/evaluation function for real ranking. |
| V1-CAP-OPT-004 | Pseudo-random search | `random_search`, `parallel_random_search` | Essential | Modify | CAP-OPT-004 Bounded search execution | N/A | Retain seeded pseudo-random sampling; correctly model distributions and do not label pseudo-random output as Sobol/LHS. |
| V1-CAP-OPT-005 | Genetic search | `genetic_algorithm`, `crossover`, `mutate` | Useful | Defer | CAP-OPT-014 Advanced optimizers | Confirm no production caller and archive deterministic fixtures before excluding it from the initial rebuild. | The loop is plausible but has no demonstrated workflow and depends on the broken execution path. |
| V1-CAP-OPT-006 | Bayesian-labelled search | `bayesian_optimization` | Questionable | Remove | None; true Bayesian optimization is deferred under CAP-OPT-014 | Confirm no external caller relies on the misleading wrapper name or random-search fallback behavior. | V1 never performs Bayesian optimization; retaining the label would misrepresent evidence. |
| V1-CAP-OPT-007 | Simulator candidate adapter | `run_strategy_backtest`, `EngineOptimizationResult` | Essential | Modify | CAP-OPT-005 Backtest execution contract | N/A | Replace direct missing imports and hard-coded adapter version with a small versioned `BacktestExecutionAdapter` contract. |
| V1-CAP-OPT-008 | Dynamic strategy loading | `load_strategy_from_path`, `run_strategy_backtest_from_path` | Questionable | Remove | None; strategy resolution belongs at the Strategy/Simulation boundary | Confirm no approved workflow requires arbitrary source-file execution and no external caller imports these functions. | Arbitrary file execution is unsafe, broken, and unnecessary when a strategy registry/reference contract exists. |
| V1-CAP-OPT-009 | Performance scoring and DSR/MTB | `scoring.py` | Essential | Modify | CAP-OPT-006 Scoring, ranking, and baseline overfit evidence | N/A | Retain core scores and DSR; correct trial-count semantics, invalid timestamp handling, objective validation, and warnings. |
| V1-CAP-OPT-010 | Chronological/rolling/expanding splits | `splitting.py` split functions | Essential | Modify | CAP-OPT-007 Time-series validation splits | N/A | Retain deterministic split construction; add date/fold validation and explicit purge/embargo evidence. |
| V1-CAP-OPT-011 | Walk-forward optimization | Duplicate implementations in `splitting.py` and `sweeps.py` | Questionable | Merge | CAP-OPT-008 Walk-forward validation | N/A | Create one internal WFA workflow and one public packaging contract; remove duplicate response/error paths. |
| V1-CAP-OPT-012 | Trade-sequence Monte Carlo | `monte_carlo_analysis`, `optimization_monte_carlo` | Essential | Modify | CAP-OPT-009 Monte Carlo analysis | N/A | Retain deterministic shuffle/resample behavior, add input validation, return distribution evidence, and explicit seed derivation. |
| V1-CAP-OPT-013 | Robustness stress assessment | Stress transforms and `assess_strategy_robustness` | Useful | Modify | CAP-OPT-010 Robustness analysis | N/A | Retain cost and skip-trade stress calculations; distinguish internal calculation from public request packaging. |
| V1-CAP-OPT-014 | Atomic JSON checkpoints | `save_checkpoint`, `load_checkpoint`, fallback | Useful | Modify | CAP-OPT-012 Run-state and checkpoint contracts (deferred execution) | N/A | Preserve schema validation and atomic-write semantics as evidence; production filesystem implementation belongs to approved infrastructure. |
| V1-CAP-OPT-015 | Run repository/progress tracking | Repository ABC, in-memory repository, `ProgressTracker`, retry wrappers | Useful | Split | CAP-OPT-012 run-state contracts and CAP-OPT-013 execution progress (both deferred) | Move the in-memory adapter to tests only after confirming no runtime import; do not ship it as a production repository. | The interface, test fixture, progress state, and retry policy are separate responsibilities. |
| V1-CAP-OPT-016 | Standard sweep response envelope | `run_parameter_sweep`, `optimization_tool_result` | Useful | Modify | CAP-OPT-001 Public contracts and registry | N/A | Unify every approved public tool on one envelope; public sweep becomes packaging, not fake execution. |
| V1-CAP-OPT-017 | Markdown optimization report | `print_optimization_report`, `build_optimization_report` | Useful | Merge | CAP-OPT-011 Evidence and reporting handoff | Remove direct formatter only after downstream reporting accepts the evidence/report package contract. | Optimization should provide evidence and chart-ready data; presentation formatting belongs to reporting/UI. |
| V1-CAP-OPT-018 | Background task IDs | Three `run_*_task` UUID/log stubs | No demonstrated value | Remove | None; future execution coordination is CAP-OPT-013 and deferred | Confirm no external caller treats returned IDs as real queued tasks. | The functions create no task, lifecycle, polling reference, cancellation, or progress. |
| V1-CAP-OPT-019 | Parametric equity simulation | `parametric_simulation` | Useful | Modify | CAP-OPT-009 Monte Carlo analysis | N/A | Retain as a validated internal scenario calculation with typed output and reproducibility metadata. |
| V1-CAP-OPT-020 | Declared scenario schemas | Unsupervised, sizing, streak, target, multi-entry, portfolio models without behavior | No demonstrated value | Remove | Reintroduce individually only if deferred CAP-OPT-015 or an owning domain approves them | Confirm no external serialized-contract dependency before deletion. | Schemas without workflows create false public capability and a large accidental contract surface. |

## 6. V2 Requirement Disposition Register

The V2 document does not contain stable requirement IDs. The IDs below are assigned only for reconciliation traceability and preserve source order.

**Disposition counts:** Add: 11, Defer: 60, Keep: 143, Merge: 20, Modify: 121, Open Decision: 7, Reject: 23

### 6.1 Ownership proposals

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-OWN-OPT-001` | The public optimization tool registry exposed by `app.services.optimization.__all__`. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-002` | Standard optimization tool result/request packaging for agent-facing optimization and robustness tools. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-003` | Optimization request context extraction, business-payload extraction, and deterministic request packaging. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-004` | Parameter sweep, walk-forward optimization, walk-forward matrix, optimization comparison, parameter stability, overfit detection, parameter ranking, optimization result persistence-package, and optimization report-packa… | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-005` | Robustness request packaging for spread, slippage, commission, Monte Carlo, cross-market, cross-timeframe, and out-of-sample checks. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-006` | Robustness score calculation and robustness report-package behavior. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-007` | Lower-level search concepts for grid search, random search, Bayesian optimization, and genetic optimization. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-008` | Lower-level execution helpers that run candidate strategies through backtest/trading-engine contexts. | **Modify** | Own only the adapter contract and optimization-facing result conversion; Simulation owns execution. | Direct engine helpers caused the broken V1 integration and violate the stated boundary. |
| `V2-OWN-OPT-009` | Lower-level walk-forward analysis helpers and train/test split helpers. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-010` | Monte Carlo and scenario simulation helpers for trade-order shuffling, return resampling, bootstrap, ruin probability, confidence intervals, parametric simulations, position sizing, consecutive-loss, profit-target, rand… | **Modify** | Own core MC/robustness calculations; defer specialized scenarios. | Most specialized V2 scenarios have no demonstrated V1 workflow. |
| `V2-OWN-OPT-011` | Optimization scoring functions and objective-name resolution. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-012` | Optimization result and summary data structures. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-013` | Optimization API/request/response models for parameter ranges, optimization runs, walk-forward runs, Monte Carlo runs, and scenario simulations. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-014` | Optimization evidence packages, final decision states, rejected-candidate summaries, production-gate results, audit references, and chart-ready handoff data. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-015` | Candidate hashing, parameter-space hashing, cache-reuse rules, checkpoint metadata, resume metadata, and optimization repository contracts. | **Modify** | Retain the behavior with narrowed public/internal scope and explicit deferrals. | V2 combines current packaging, internal compute, future platform work, and cross-domain evidence in one ownership statement. |
| `V2-OWN-OPT-016` | Optimization-specific robustness gates including Deflated Sharpe Ratio, Probability of Backtest Overfitting, Walk-Forward Efficiency, multiple-testing correction, parameter topology stability, Monte Carlo survival, and… | **Modify** | Own DSR/WFE/MC evidence; defer CPCV/PBO/topology gates; consume rather than evaluate prop-firm compliance evidence. | Prop-firm rule evaluation belongs to Risk and advanced gates lack approved thresholds/workflows. |
| `V2-OWN-OPT-017` | Repository interface contracts and payload schemas for optimization evidence, checkpoints, candidate records, and resume/cancel/progress workflows, when persistence implementation is assigned to an approved infrastructu… | **Defer** | Retain repository contract intent for the deferred run-state capability. | Repository policy and infrastructure ownership are unresolved. |
| `V2-OWN-OPT-018` | Repository contracts as Python `Protocol` or abstract base class interfaces only; concrete repository implementations shall be injected by Dependency Injection from the approved infrastructure layer. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-019` | Chart-ready data contracts for optimization reports and handoffs, without UI chart rendering. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-020` | Definition of the versioned `BacktestExecutionAdapter` interface contract; concrete execution-engine implementation belongs to the approved Simulation or execution-engine layer. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |
| `V2-OWN-OPT-021` | Request and response model schemas for optimization APIs and tools, without owning the API transport layer. | **Keep** | Retain this ownership boundary. | It directly supports the approved optimization workflows without adding implementation layers. |

### 6.2 Explicit non-ownership boundaries

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-NOWN-OPT-001` | Strategy design, strategy signal logic, or strategy lifecycle promotion. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-002` | Market-data ingestion, provider adapters, or raw broker/data normalization. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-003` | Risk approval, portfolio governance, kill-switch policy, or live-trading authorization. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-004` | Trading order-intent creation, broker submission, execution receipts, or reconciliation. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-005` | Durable persistence implementation, database migrations, or repository ownership. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-006` | Production database provisioning, migration execution, credential management, or database operations unless an architecture decision explicitly assigns that responsibility. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-007` | Concrete implementation of repository interfaces, including SQLAlchemy models, database sessions, Redis clients, object-store or S3 uploaders, provider clients, connection pools, and database drivers. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-008` | API authentication, UI rendering, websocket connection management, or frontend chart behavior. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-009` | Final owner decisions about optimization algorithms, run limits, objectives, thresholds, or release acceptance. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-010` | Production strategy mutation or automatic promotion of optimized parameters. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-011` | Financial advice or claims that optimized parameters are safe for live use. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-012` | Live broker credentials, live broker gateway network access, broker position closure, order placement, or any `approved_for_live_trading` authority. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-013` | Final Risk Governor, Portfolio Manager, or Human Live Activation Approver decisions. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-014` | UI chart rendering, even when optimization provides chart-ready data. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |
| `V2-NOWN-OPT-015` | Treating optimization success, robustness success, or prop-firm evidence success as live-trading approval. | **Keep** | Retain this explicit non-ownership boundary. | It prevents optimization from acquiring broker, risk, persistence, UI, strategy, or governance authority. |

### 6.3 Public API proposals

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-API-OPT-001` | Export the approved optimization service tools through `app.services.optimization.__all__`. | **Modify** | Expose only the approved V2 public surface; package path remains an open system decision. | The V1 151-name facade must not define backward compatibility for accidental exports. |
| `V2-API-OPT-002` | Return standard optimization tool envelopes with tool name, status, request ID, data, errors, warnings, and audit metadata. | **Modify** | Use one shared standard envelope, subject to cross-domain contract alignment. | The behavior is required, but the exact shared schema is verified later. |
| `V2-API-OPT-003` | Package parameter sweep requests for downstream grid or random search execution. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-004` | Package walk-forward optimization and walk-forward matrix requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-005` | Package optimization run comparison requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Modify** | Expose as a validated lightweight calculation over supplied payloads. | V1 behavior is useful but must use the standard envelope and stronger validation. |
| `V2-API-OPT-006` | Calculate parameter stability from selected candidate parameter values. Classification: `public_service_now`; stability: `experimental`; behavior: `lightweight_calculation`. | **Modify** | Expose as a validated lightweight calculation over supplied payloads. | V1 behavior is useful but must use the standard envelope and stronger validation. |
| `V2-API-OPT-007` | Detect overfit risk from in-sample and out-of-sample score gaps. Classification: `public_service_now`; stability: `experimental`; behavior: `lightweight_calculation`. | **Modify** | Expose as a validated lightweight calculation over supplied payloads. | V1 behavior is useful but must use the standard envelope and stronger validation. |
| `V2-API-OPT-008` | Rank parameter candidate sets by score. Classification: `public_service_now`; stability: `experimental`; behavior: `lightweight_calculation`. | **Modify** | Expose as a validated lightweight calculation over supplied payloads. | V1 behavior is useful but must use the standard envelope and stronger validation. |
| `V2-API-OPT-009` | Package optimization result persistence requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-010` | Package optimization report creation requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-011` | Package spread, slippage, and commission stress-test requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Merge** | Consolidate related request packagers by method/type instead of one public function per variation. | The proposed public surface is unnecessarily wide and duplicates one packaging pattern. |
| `V2-API-OPT-012` | Package trade-order randomization, trade resampling, skipped-trade, randomized-parameter, randomized-history, and combined Monte Carlo robustness requests. Classification: `public_service_now`; stability: `experimental`… | **Merge** | Consolidate related request packagers by method/type instead of one public function per variation. | The proposed public surface is unnecessarily wide and duplicates one packaging pattern. |
| `V2-API-OPT-013` | Package cross-market, cross-timeframe, second out-of-sample, and third out-of-sample robustness requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Merge** | Consolidate related request packagers by method/type instead of one public function per variation. | The proposed public surface is unnecessarily wide and duplicates one packaging pattern. |
| `V2-API-OPT-014` | Calculate robustness scores from pass/fail robustness checks. Classification: `public_service_now`; stability: `experimental`; behavior: `lightweight_calculation`. | **Modify** | Expose as a validated lightweight calculation over supplied payloads. | V1 behavior is useful but must use the standard envelope and stronger validation. |
| `V2-API-OPT-015` | Package robustness report creation requests. Classification: `public_service_now`; stability: `experimental`; behavior: `packaging`. | **Merge** | Consolidate related request packagers by method/type instead of one public function per variation. | The proposed public surface is unnecessarily wide and duplicates one packaging pattern. |
| `V2-API-OPT-016` | Validate optimization requests, strategy compatibility, market data quality, parameter spaces, objective definitions, constraints, and evidence packages before expensive work or persistence. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-017` | Generate versioned optimization evidence packages for downstream Risk Governor, Portfolio Manager, UI/reporting, and human review workflows. | **Add** | Add as an approved public packaging or evidence capability. | V1 either executes, stubs, or lacks the required public contract. |
| `V2-API-OPT-018` | Resume, cancel, and report progress for optimization runs through repository-backed and checkpoint-aware workflows. | **Defer** | Exclude resume/cancel/progress from the initial public surface. | Repository, task lifecycle, and idempotency policies are unresolved. |
| `V2-API-OPT-019` | Produce official tool metadata that always reports `places_trade=False` and never exposes live-trading capability. | **Keep** | Retain as a public contract rule. | This is necessary for safe, inspectable, non-trading public tools. |
| `V2-API-OPT-020` | Define public tool contracts before Builder handoff, including tool name, public/internal status, stability, required inputs, optional inputs, defaults, output envelope schema, status values, error codes, warning codes,… | **Keep** | Retain as a public contract rule. | This is necessary for safe, inspectable, non-trading public tools. |
| `V2-API-OPT-021` | Mark each public capability as `stable`, `experimental`, `internal`, or `future_deferred`. | **Keep** | Retain as a public contract rule. | This is necessary for safe, inspectable, non-trading public tools. |
| `V2-API-OPT-022` | State whether each public capability packages work, performs lightweight deterministic calculation, or triggers repository-backed execution. | **Keep** | Retain as a public contract rule. | This is necessary for safe, inspectable, non-trading public tools. |
| `V2-API-OPT-023` | Public tool signatures exported through `app.services.optimization.__all__` shall preserve backward compatibility within a major module version; breaking changes require a new tool name, such as a `_v2` suffix, or an ap… | **Modify** | Guarantee compatibility only for the approved V2 public surface; accidental V1 exports may be removed after caller verification. | Preserving 151 accidental V1 exports would perpetuate the main structural defect. |

### 6.4 Functional requirements

| V2 requirement ID | Scope | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- | --- |
| `V2-FR-OPT-001` | General | Each requirement shall include a stable requirement ID, priority, scope tier, owner, acceptance criteria, and one or more mapped tests before Builder handoff. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-002` | General | Requirement priorities shall distinguish `P0 safety`, `P0 contract`, `P1 current public tool`, `P2 internal rebuild`, and `P3 future`. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-003` | General | Confirmed requirements, assumptions, proposed decisions, pending decisions, and future improvements shall remain separated. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-004` | General | The optimization registry must expose only intentional public service tools through `app.services.optimization.__all__`. | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-005` | General | The optimization registry must keep exports unique, callable, documented, and synchronized with tests and catalog entries. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-006` | General | Public service tools shall return the documented standard optimization envelope containing `tool_name`, `status`, `request_id`, `data`, `errors`, `warnings`, `audit`, and `side_effects`; unit tests shall verify conforma… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-007` | General | Public service tools must include request/audit context including request ID, tool name, risk level, and approval requirement. | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-008` | General | Public service tools that package work must not execute live broker actions or mutate production strategy state. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-009` | General | Request-packaging tools shall not trigger candidate execution, persistence writes, external network calls, or background jobs unless explicitly documented and approved. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-010` | General | Public service tools must preserve business request payloads separately from standard context fields. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-011` | General | Dry-run behavior shall be defined per capability type: packaging tools return a validated request envelope without execution, background jobs, persistence writes, or external calls; lightweight calculation tools still p… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-012` | General | When a caller omits `dry_run`, public optimization tools shall default to `dry_run=True`. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-013` | General | `dry_run` requested on a calculation-only public tool shall follow that tool contract and shall not change the calculation result except for side-effect metadata and audit context. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-014` | General | Public service tools must surface validation and runtime errors in structured result fields rather than uncaught exceptions. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-015` | General | Optimization workflows shall record reproducibility context including `strategy_id`, parameter-space definition including constraints, objective, data window start/end, engine type, engine version, seed, cost model hash… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-016` | General | Optimization workflows must warn about overfitting, parameter instability, and robustness weaknesses instead of presenting candidate scores as live readiness. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-017` | General | The module shall validate optimization requests, strategy compatibility, market data quality, parameter spaces, objective definitions, and evidence-package shape before running expensive work or persisting artifacts. | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-018` | General | The module shall support float, integer, categorical, boolean, fixed, conditional, and constrained parameter spaces. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-019` | General | Inactive conditional parameters shall be excluded from executable candidate parameters, candidate hashes, backtest adapter payloads, scoring, and strategy invocation, while remaining available only in metadata or audit… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-020` | General | Parameter constraints shall be evaluated before candidate execution, and unsafe constraint expressions shall be blocked. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-021` | General | Constraint violations shall be persisted or represented in audit-ready evidence and shall not be sent to the backtest adapter for execution. | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-022` | General | Official optimization tools shall never place trades, close broker positions, access live broker gateways, or return `approved_for_live_trading`. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-023` | General | Official optimization tools shall include side-effect metadata with `places_trade=False`. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-024` | General | Final optimization output states shall use the canonical enum `ready_for_risk_review`, `validation_needed`, `research_only`, `rejected`, `failed`, or `cancelled`; all requirements, schemas, tests, examples, and reports… | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-025` | General | Risk Governor handoff packages shall include the full evidence package, final decision, best candidate, top candidates, rejected-candidate summary, production gates, walk-forward evidence, robustness evidence, Monte Car… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-026` | General | Portfolio Manager handoff packages shall include capacity estimates, exposure assumptions, cross-symbol validation, cross-timeframe validation, regime evidence, intended deployment AUM, estimated capacity in deployment… | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-027` | General | UI/reporting handoff packages shall provide chart-ready data without requiring recomputation and shall not render charts inside this module. | **Modify** | Retain with applicability rules, shared-contract alignment, and cross-domain ownership limits. | The behavior is valid, but V2 states it too broadly or assigns externally owned evidence/calculation to optimization. |
| `V2-FR-OPT-028` | General | Execution-capable workflows shall require an approved execution profile with resource caps, timeout policy, repository policy, and safety gates. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-029` | General | Repository-backed workflows shall be idempotent for repeated resume, cancel, and progress requests. | **Defer** | Apply idempotency when repository-backed workflows are approved. | No initial repository-backed workflow is approved. |
| `V2-FR-OPT-030` | General | Evidence package schemas shall be versioned and backward-compatible according to a documented compatibility policy. | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-031` | General | Production implementation shall be blocked until owner-approved limits exist for max candidates, max parameter-space expansion, max runtime, max worker count, max Monte Carlo simulations, objective whitelist, repository… | **Keep** | Retain as a final requirement or production gate. | It is necessary for traceability, safety, reproducibility, or a clear public contract. |
| `V2-FR-OPT-032` | Optimization Service Tools | `run_parameter_sweep` shall package a grid or random parameter search request for downstream optimization execution. | **Modify** | Implement as a standard-envelope packaging or lightweight calculation tool. | V1 contains related behavior but mixes execution, inconsistent returns, or weak validation. |
| `V2-FR-OPT-033` | Optimization Service Tools | `run_parameter_sweep` shall require `search_method` with approved values `grid`, `random`, `latin_hypercube`, or `sobol`; distribution-based methods shall include validated distribution definitions instead of grid-only… | **Modify** | Support grid and pseudo-random packaging initially; model distributions correctly; defer Sobol/LHS execution. | The allowed values combine current and unapproved optional samplers. |
| `V2-FR-OPT-034` | Optimization Service Tools | `run_walk_forward_optimization` shall package rolling train/test walk-forward optimization details. | **Modify** | Implement as a standard-envelope packaging or lightweight calculation tool. | V1 contains related behavior but mixes execution, inconsistent returns, or weak validation. |
| `V2-FR-OPT-035` | Optimization Service Tools | `run_walk_forward_matrix` shall package a matrix of walk-forward train/test combinations. | **Add** | Add one walk-forward matrix request package. | No coherent V1 public packaging contract exists. |
| `V2-FR-OPT-036` | Optimization Service Tools | `compare_optimization_runs` shall package candidate optimization run IDs or result payloads for comparison. | **Modify** | Implement as a standard-envelope packaging or lightweight calculation tool. | V1 contains related behavior but mixes execution, inconsistent returns, or weak validation. |
| `V2-FR-OPT-037` | Optimization Service Tools | `calculate_parameter_stability` shall calculate standard-deviation-style stability by parameter across selected candidates. | **Modify** | Implement as a standard-envelope packaging or lightweight calculation tool. | V1 contains related behavior but mixes execution, inconsistent returns, or weak validation. |
| `V2-FR-OPT-038` | Optimization Service Tools | `detect_overfit_parameters` shall detect overfit risk from the gap between in-sample and out-of-sample scores. | **Modify** | Implement as a standard-envelope packaging or lightweight calculation tool. | V1 contains related behavior but mixes execution, inconsistent returns, or weak validation. |
| `V2-FR-OPT-039` | Optimization Service Tools | `rank_parameter_sets` shall rank optimization parameter candidates deterministically from highest score to lowest score. | **Merge** | Merge `rank_parameter_sets` and `rank_candidates` into one deterministic ranking capability. | V1 duplicates ranking behavior. |
| `V2-FR-OPT-040` | Optimization Service Tools | `rank_parameter_sets` tie-breaking shall sort tied scores by `trade_count` descending when available, then by `candidate_hash` ascending; missing `trade_count` shall sort after present `trade_count` for the same score. | **Keep** | Retain deterministic tie-breaking exactly as stated. | This resolves V1 ranking divergence and provides stable output. |
| `V2-FR-OPT-041` | Optimization Service Tools | `save_optimization_result` shall package optimization result metadata for downstream storage. | **Modify** | Package a storage request and never claim that persistence occurred. | V1 misleadingly returns `saved=True` without storage. |
| `V2-FR-OPT-042` | Optimization Service Tools | `build_optimization_report` shall package optimization report creation inputs for downstream reporting. | **Merge** | Merge report-request packaging into the versioned evidence/report handoff capability. | A separate formatter/package wrapper adds little value. |
| `V2-FR-OPT-043` | Robustness Service Tools | `run_spread_stress_test` shall package wider-spread stress-test inputs. | **Modify** | Keep internal deterministic stress calculations and expose side-effect-free public request packaging. | V1 currently uses the same names for direct calculation, while V2 defines public packaging. |
| `V2-FR-OPT-044` | Robustness Service Tools | `run_slippage_stress_test` shall package slippage stress-test inputs. | **Modify** | Keep internal deterministic stress calculations and expose side-effect-free public request packaging. | V1 currently uses the same names for direct calculation, while V2 defines public packaging. |
| `V2-FR-OPT-045` | Robustness Service Tools | `run_commission_stress_test` shall package commission stress-test inputs. | **Modify** | Keep internal deterministic stress calculations and expose side-effect-free public request packaging. | V1 currently uses the same names for direct calculation, while V2 defines public packaging. |
| `V2-FR-OPT-046` | Robustness Service Tools | `run_randomize_trade_order_mc` shall package shuffled-trade-order Monte Carlo inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-047` | Robustness Service Tools | `run_resample_trades_mc` shall package resampled-trade Monte Carlo inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-048` | Robustness Service Tools | `run_skip_trades_mc` shall package skipped-trade Monte Carlo inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-049` | Robustness Service Tools | `run_randomize_parameters_mc` shall package randomized-parameter Monte Carlo inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-050` | Robustness Service Tools | `run_randomize_history_mc` shall package randomized-history Monte Carlo inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-051` | Robustness Service Tools | `run_combined_monte_carlo` shall package combined Monte Carlo stress inputs. | **Merge** | Use one Monte Carlo/robustness request packager with an explicit method enum. | Six public wrappers duplicate the same validation and envelope behavior. |
| `V2-FR-OPT-052` | Robustness Service Tools | `run_cross_market_test` shall package cross-market robustness-test inputs. | **Merge** | Use one cross-validation robustness request packager with a validation-kind field. | Separate second/third OOS and market/timeframe functions create unnecessary API width. |
| `V2-FR-OPT-053` | Robustness Service Tools | `run_cross_timeframe_test` shall package cross-timeframe robustness-test inputs. | **Merge** | Use one cross-validation robustness request packager with a validation-kind field. | Separate second/third OOS and market/timeframe functions create unnecessary API width. |
| `V2-FR-OPT-054` | Robustness Service Tools | `run_second_oos_test` shall package second out-of-sample validation inputs. | **Merge** | Use one cross-validation robustness request packager with a validation-kind field. | Separate second/third OOS and market/timeframe functions create unnecessary API width. |
| `V2-FR-OPT-055` | Robustness Service Tools | `run_third_oos_test` shall package third out-of-sample validation inputs. | **Merge** | Use one cross-validation robustness request packager with a validation-kind field. | Separate second/third OOS and market/timeframe functions create unnecessary API width. |
| `V2-FR-OPT-056` | Robustness Service Tools | `calculate_robustness_score` shall calculate a deterministic robustness percentage from pass/fail checks. | **Modify** | Retain the deterministic percentage calculation with typed check records and a standard envelope. | V1 accepts only a bool mapping and lacks public validation. |
| `V2-FR-OPT-057` | Robustness Service Tools | `build_robustness_report` shall package robustness report creation inputs. | **Merge** | Build robustness evidence through CAP-OPT-011 rather than a separate report wrapper. | Reports should derive from evidence without recomputation. |
| `V2-FR-OPT-058` | Shared Helpers | `service_strategy_class` shall normalize either a concrete strategy class or a callable strategy-class factory. | **Merge** | Fold strategy-handle normalization into BacktestExecutionAdapter request validation. | A separate public helper is unnecessary and strategy resolution is a boundary concern. |
| `V2-FR-OPT-059` | Shared Helpers | `optimization_tool_result` shall build the standard HaruQuant optimization result envelope. | **Modify** | Retain as private/public-boundary support aligned to the shared envelope and context contract. | V1 helpers are useful but incomplete and currently underused. |
| `V2-FR-OPT-060` | Shared Helpers | `optimization_tool_context` shall extract request ID, agent name, environment, and dry-run context from tool keyword arguments. | **Modify** | Retain as private/public-boundary support aligned to the shared envelope and context contract. | V1 helpers are useful but incomplete and currently underused. |
| `V2-FR-OPT-061` | Shared Helpers | `optimization_business_payload` shall remove standard context fields and retain only business request fields. | **Keep** | Retain business/context separation. | It is required for deterministic request packaging and audit safety. |
| `V2-FR-OPT-062` | Shared Helpers | `package_optimization_request` shall create deterministic request packages without running compute-heavy optimization jobs. | **Modify** | Use focused package functions per approved request schema; no compute or persistence. | A single generic package helper must not erase capability-specific validation. |
| `V2-FR-OPT-063` | Shared Helpers | Lazy attribute resolution shall resolve lower-level optimization service attributes without putting business logic in the package initializer. | **Reject** | Use explicit imports/exports; add compatibility aliases only when a confirmed caller requires them. | Lazy attribute magic is not needed and would hide the public surface. |
| `V2-FR-OPT-064` | Search Methods | `grid_search` shall evaluate an exhaustive parameter grid over a supplied strategy/backtest context. | **Modify** | Retain as bounded internal search engines using an injected evaluator. | V1 generation is useful but fake dry-run ranking and broken direct execution must be removed. |
| `V2-FR-OPT-065` | Search Methods | `optimization_grid_search` shall expose a user-facing wrapper for exhaustive parameter grid search. | **Reject** | Do not expose compute-heavy algorithm wrappers as official public tools. | Public tools package work; duplicated algorithm-specific wrappers expand the contract without a workflow need. |
| `V2-FR-OPT-066` | Search Methods | `random_search` shall sample parameter combinations from distributions and evaluate candidates. | **Modify** | Retain as bounded internal search engines using an injected evaluator. | V1 generation is useful but fake dry-run ranking and broken direct execution must be removed. |
| `V2-FR-OPT-067` | Search Methods | `optimization_random_search` shall expose a user-facing wrapper for randomized parameter search. | **Reject** | Do not expose compute-heavy algorithm wrappers as official public tools. | Public tools package work; duplicated algorithm-specific wrappers expand the contract without a workflow need. |
| `V2-FR-OPT-068` | Search Methods | `bayesian_optimization` shall run Gaussian-process-style Bayesian optimization over a parameter space. | **Defer** | Exclude from the initial rebuild pending workflow, dependency, and evidence approval. | Optional/advanced algorithms are unproven in V1 and not needed for the minimum viable domain. |
| `V2-FR-OPT-069` | Search Methods | `optimization_bayesian` shall expose a user-facing wrapper for Bayesian parameter optimization. | **Reject** | Do not expose compute-heavy algorithm wrappers as official public tools. | Public tools package work; duplicated algorithm-specific wrappers expand the contract without a workflow need. |
| `V2-FR-OPT-070` | Search Methods | `genetic_algorithm` shall evolve parameter candidates through population, selection, crossover, mutation, and elitism behavior. | **Defer** | Exclude from the initial rebuild pending workflow, dependency, and evidence approval. | Optional/advanced algorithms are unproven in V1 and not needed for the minimum viable domain. |
| `V2-FR-OPT-071` | Search Methods | `optimization_genetic` shall expose a user-facing wrapper for genetic algorithm parameter optimization. | **Reject** | Do not expose compute-heavy algorithm wrappers as official public tools. | Public tools package work; duplicated algorithm-specific wrappers expand the contract without a workflow need. |
| `V2-FR-OPT-072` | Search Methods | Search methods shall support objective/scoring functions, initial balance, symbol, engine type, max workers, verbosity, progress callbacks, and reproducibility controls where implemented. | **Modify** | Support only inputs required by enabled algorithms; resource/progress controls come from an approved execution profile. | The requirement bundles optional controls into every method. |
| `V2-FR-OPT-073` | Search Methods | Search methods shall return optimization summaries containing candidate results, best parameters, best score, objective, runtime, and total-run metadata. | **Keep** | Return a common internal optimization summary. | This is a stable and useful cross-algorithm result contract. |
| `V2-FR-OPT-074` | Search Methods | Grid expansion shall support `100,000+` combinations through strict iterator mode that yields one candidate at a time and never materializes the full Cartesian product in memory. | **Modify** | Keep lazy iteration and prove bounded memory; do not make `100,000+` a universal acceptance threshold until benchmarked. | V1 claims bounded memory but its parallel queue can still grow. |
| `V2-FR-OPT-075` | Search Methods | Strict iterator mode shall stay within an owner-approved memory budget regardless of grid size; the budget value remains pending owner/architect approval. | **Open Decision** | Set and test the memory budget before production execution. | The required numeric budget is explicitly pending owner approval. |
| `V2-FR-OPT-076` | Search Methods | Seeded random search shall support pseudo-random, Sobol sequence, and Latin Hypercube sampling contracts. | **Defer** | Exclude from the initial rebuild pending workflow, dependency, and evidence approval. | Optional/advanced algorithms are unproven in V1 and not needed for the minimum viable domain. |
| `V2-FR-OPT-077` | Search Methods | Pseudo-random sampling shall be the always-available deterministic fallback. | **Keep** | Retain seeded pseudo-random as the dependency-free baseline. | V1 already provides this proven behavior. |
| `V2-FR-OPT-078` | Search Methods | Sobol or Latin Hypercube unavailability shall be explicit and shall either return `OPT_SAMPLER_UNAVAILABLE` or use an approved configured fallback with sampler method, seed, scramble setting, fallback usage, and fallbac… | **Keep** | Require explicit sampler error or approved, fully evidenced fallback. | V1 silently labels pseudo-random candidates as advanced samples. |
| `V2-FR-OPT-079` | Search Methods | Optional Optuna and scikit-optimize backends shall sit behind a stable optimizer backend interface and shall require dependency approval, version pinning, repository policy approval, and contract tests before production… | **Defer** | Exclude from the initial rebuild pending workflow, dependency, and evidence approval. | Optional/advanced algorithms are unproven in V1 and not needed for the minimum viable domain. |
| `V2-FR-OPT-080` | Search Methods | Optional backend-specific objects shall not leak into official tool responses. | **Keep** | Keep backend-specific objects out of official responses. | This preserves a stable contract and optional dependency isolation. |
| `V2-FR-OPT-081` | Execution Helpers | `load_strategy_from_path` shall dynamically load a strategy class from a file path and class name. | **Reject** | Remove arbitrary file-path strategy execution from optimization. | It is broken in V1, unsafe, and duplicates Strategy/Simulation registration responsibility. |
| `V2-FR-OPT-082` | Execution Helpers | `normalize_engine_type` shall normalize legacy engine labels to supported execution engine names. | **Modify** | Normalize engine identifiers inside the adapter request contract, not as a broad compatibility layer. | Legacy aliases should not become permanent accidental API. |
| `V2-FR-OPT-083` | Execution Helpers | `run_strategy_backtest` shall run one optimization candidate through the trading/backtest engine with supplied strategy, data, symbol, parameters, balance, engine type, and position size. | **Modify** | Implement through a small versioned adapter protocol and optimization-facing result contract. | V1 has useful result-shaping concepts but direct imports and hard-coded assumptions are broken. |
| `V2-FR-OPT-084` | Execution Helpers | `run_strategy_backtest_from_path` shall load a strategy class from disk and run one optimization candidate through the backtest path. | **Reject** | Remove arbitrary file-path strategy execution from optimization. | It is broken in V1, unsafe, and duplicates Strategy/Simulation registration responsibility. |
| `V2-FR-OPT-085` | Execution Helpers | `EngineOptimizationResult` shall expose a small optimization-facing result contract built from engine outputs. | **Modify** | Implement through a small versioned adapter protocol and optimization-facing result contract. | V1 has useful result-shaping concepts but direct imports and hard-coded assumptions are broken. |
| `V2-FR-OPT-086` | Execution Helpers | Execution helpers shall convert engine trades, equity points, processed tick counts, and analytics into optimization-ready result objects. | **Modify** | Implement through a small versioned adapter protocol and optimization-facing result contract. | V1 has useful result-shaping concepts but direct imports and hard-coded assumptions are broken. |
| `V2-FR-OPT-087` | Execution Helpers | Execution helpers shall return or raise structured `OptimizationExecutionError` results with deterministic `OPT_EXECUTION_FAILED`, `OPT_STRATEGY_LOAD_FAILED`, `OPT_ENGINE_CREATION_FAILED`, `OPT_SYMBOL_SETUP_FAILED`, or… | **Keep** | Retain deterministic fail-closed execution errors and realism/version checks. | These are required safety and diagnosability constraints. |
| `V2-FR-OPT-088` | Execution Helpers | Candidate execution shall occur only through a versioned `BacktestExecutionAdapter`. | **Add** | Define `BacktestExecutionAdapter` as the sole candidate execution boundary. | V1 lacks an operational cross-domain contract. |
| `V2-FR-OPT-089` | Execution Helpers | The backtest adapter shall validate required data columns, strategy compatibility, cost model, engine type, deterministic seed behavior, and adapter version before execution. | **Modify** | Implement through a small versioned adapter protocol and optimization-facing result contract. | V1 has useful result-shaping concepts but direct imports and hard-coded assumptions are broken. |
| `V2-FR-OPT-090` | Execution Helpers | Backtest adapter version mismatch shall fail closed before execution. | **Keep** | Retain deterministic fail-closed execution errors and realism/version checks. | These are required safety and diagnosability constraints. |
| `V2-FR-OPT-091` | Execution Helpers | Unsupported simulator realism shocks shall return structured unsupported-feature errors and shall not be silently ignored. | **Keep** | Retain deterministic fail-closed execution errors and realism/version checks. | These are required safety and diagnosability constraints. |
| `V2-FR-OPT-092` | Execution Helpers | Deterministic-only noisy-objective mode shall fail closed with `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` when stochastic simulator realism is active, and failure details shall include conflict subtype `STOCHASTIC_REALISM_CONFLI… | **Keep** | Retain deterministic fail-closed execution errors and realism/version checks. | These are required safety and diagnosability constraints. |
| `V2-FR-OPT-093` | Walk Forward And Splitters | `walk_forward` shall optimize parameters on rolling training windows and test them on out-of-sample windows. | **Modify** | Keep one internal walk-forward workflow using the approved split, search, and adapter capabilities. | V1 has duplicate partial implementations. |
| `V2-FR-OPT-094` | Walk Forward And Splitters | `optimization_walk_forward` shall expose a user-facing wrapper around walk-forward parameter optimization. | **Merge** | Merge the wrapper into the single public walk-forward request packager and one internal workflow. | A second wrapper repeats contracts and error handling. |
| `V2-FR-OPT-095` | Walk Forward And Splitters | `print_optimization_report` shall print or format a top-candidate optimization report for inspection. | **Reject** | Provide report/evidence data only; formatting/rendering belongs to reporting/UI. | A print/format function is presentation responsibility and duplicates report packaging. |
| `V2-FR-OPT-096` | Walk Forward And Splitters | `splitter_from_rolling` shall create deterministic rolling time-series train/test windows. | **Modify** | Retain deterministic split behavior with stronger validation and explicit leakage controls. | V1 split construction is useful but incomplete around invalid windows and boundary evidence. |
| `V2-FR-OPT-097` | Walk Forward And Splitters | `splitter_from_expanding` shall create deterministic expanding time-series train/test windows. | **Modify** | Retain deterministic split behavior with stronger validation and explicit leakage controls. | V1 split construction is useful but incomplete around invalid windows and boundary evidence. |
| `V2-FR-OPT-098` | Walk Forward And Splitters | `splitter_rolling_split` shall split tabular data into rolling train/test or train/validation/test slices. | **Modify** | Retain deterministic split behavior with stronger validation and explicit leakage controls. | V1 split construction is useful but incomplete around invalid windows and boundary evidence. |
| `V2-FR-OPT-099` | Walk Forward And Splitters | `SplitterResult` shall hold split windows and support plotting/inspection behavior. | **Modify** | Keep a typed split result for inspection data; remove plotting behavior from the domain. | Plot rendering is explicitly outside optimization. |
| `V2-FR-OPT-100` | Walk Forward And Splitters | Walk-forward results shall preserve train window, test window, selected parameters, train score, test score, and degradation context. | **Modify** | Retain deterministic split behavior with stronger validation and explicit leakage controls. | V1 split construction is useful but incomplete around invalid windows and boundary evidence. |
| `V2-FR-OPT-101` | Walk Forward And Splitters | Walk-forward validation shall support rolling, anchored, expanding, and custom fold modes. | **Modify** | Support rolling and anchored/expanding modes initially; defer custom fold plug-ins. | Custom fold behavior lacks a defined contract and workflow. |
| `V2-FR-OPT-102` | Walk Forward And Splitters | Walk-forward evidence shall include fold results, best parameters per fold, OOS results per fold, fold pass rate, parameter drift score, OOS retention score, walk-forward score, Walk-Forward Efficiency, and walk-forward… | **Modify** | Include the listed baseline fold and WFE evidence when WFA executes. | The evidence is valuable, but status/threshold semantics require approved profiles. |
| `V2-FR-OPT-103` | Walk Forward And Splitters | Walk-forward and cross-validation splits shall enforce configurable purging and embargo periods between training and validation sets when required. | **Modify** | Retain deterministic split behavior with stronger validation and explicit leakage controls. | V1 split construction is useful but incomplete around invalid windows and boundary evidence. |
| `V2-FR-OPT-104` | Walk Forward And Splitters | If average trade duration is known, effective embargo shall be at least the average trade duration in bars unless a stricter value is configured. | **Modify** | Apply trade-duration-aware embargo only when duration provenance is supplied and valid. | Optimization does not own trade-duration derivation. |
| `V2-FR-OPT-105` | Walk Forward And Splitters | CPCV validation shall support deterministic path generation when enabled and shall enforce purging and embargo on every path. | **Defer** | Exclude CPCV/PBO execution from the initial rebuild. | They require advanced validation design and approved thresholds. |
| `V2-FR-OPT-106` | Walk Forward And Splitters | PBO shall be calculated when CPCV is enabled, and PBO above the configured threshold shall flag or reject overfit risk according to the workflow profile. | **Defer** | Exclude CPCV/PBO execution from the initial rebuild. | They require advanced validation design and approved thresholds. |
| `V2-FR-OPT-107` | Walk Forward And Splitters | Evidence shall include embargo configuration, effective embargo bars, and leakage-prevention status for walk-forward and CPCV runs. | **Modify** | Include embargo/leakage evidence for enabled WFA; CPCV fields are conditional and deferred. | Do not require evidence for disabled capabilities. |
| `V2-FR-OPT-108` | Monte Carlo And Scenario Simulation | `monte_carlo_analysis` shall run Monte Carlo analysis against a backtest result with selected simulation type and random seed. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-109` | Monte Carlo And Scenario Simulation | `shuffle_trades_simulation` shall randomize trade order while preserving individual trade outcomes. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-110` | Monte Carlo And Scenario Simulation | `resample_returns_simulation` shall sample returns with replacement from the empirical return distribution. | **Add** | Add focused empirical resampling and statistical summary helpers to the core Monte Carlo capability. | These fill clear gaps in a real research workflow without adding a platform layer. |
| `V2-FR-OPT-111` | Monte Carlo And Scenario Simulation | `bootstrap_simulation` shall use block bootstrap to preserve short-term temporal structure. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-112` | Monte Carlo And Scenario Simulation | `calculate_probability_of_ruin` shall estimate probability that drawdown exceeds the configured ruin threshold. | **Add** | Add focused empirical resampling and statistical summary helpers to the core Monte Carlo capability. | These fill clear gaps in a real research workflow without adding a platform layer. |
| `V2-FR-OPT-113` | Monte Carlo And Scenario Simulation | `calculate_confidence_intervals` shall calculate confidence intervals for selected metrics. | **Add** | Add focused empirical resampling and statistical summary helpers to the core Monte Carlo capability. | These fill clear gaps in a real research workflow without adding a platform layer. |
| `V2-FR-OPT-114` | Monte Carlo And Scenario Simulation | `compare_simulation_methods` shall run multiple Monte Carlo methods and compare their results. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-115` | Monte Carlo And Scenario Simulation | `assess_strategy_robustness` shall produce a comprehensive Monte Carlo robustness assessment. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-116` | Monte Carlo And Scenario Simulation | `parametric_simulation` shall simulate outcomes from win rate, reward/risk ratio, risk per trade, trade count, simulation count, and initial balance. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-117` | Monte Carlo And Scenario Simulation | `position_sizing_simulation` shall compare linear and compounding position-sizing equity curves. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-118` | Monte Carlo And Scenario Simulation | `consecutive_losing_simulation` shall simulate maximum consecutive losses for win-rate and reward/risk pairs. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-119` | Monte Carlo And Scenario Simulation | `profit_target_simulation` shall estimate probability of reaching a target balance. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-120` | Monte Carlo And Scenario Simulation | `random_win_rate_simulation` shall simulate trading with random win-rate/reward-risk pairs. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-121` | Monte Carlo And Scenario Simulation | `robustness_simulation` shall simulate robustness with skipped trades, deterioration, and selected Monte Carlo mode. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-122` | Monte Carlo And Scenario Simulation | `multi_entry_simulation` shall simulate multi-entry strategy scenarios. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-123` | Monte Carlo And Scenario Simulation | `optimization_monte_carlo` shall expose a user-facing wrapper around Monte Carlo robustness simulation over trade results. | **Merge** | Keep one internal Monte Carlo capability and one public method-based request packager. | A compute wrapper using the public tool name would violate the packaging boundary. |
| `V2-FR-OPT-124` | Monte Carlo And Scenario Simulation | `MonteCarloResult` shall hold Monte Carlo simulation outputs and provide summary/statistics behavior. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-125` | Monte Carlo And Scenario Simulation | `ParametricSimulationResult`, `PositionSizingResult`, `ConsecutiveLosingScenarioResult`, and `ProfitTargetScenarioResult` shall hold scenario-specific simulation results. | **Defer** | Exclude specialized scenario APIs/models until a named workflow and owner approve them. | V1 has mostly unused schemas and no demonstrated callers for these scenarios. |
| `V2-FR-OPT-126` | Monte Carlo And Scenario Simulation | Monte Carlo and scenario simulations shall support reproducibility controls and must not claim certainty from randomized outputs. | **Modify** | Retain and validate the proven Monte Carlo/robustness behavior with typed results and reproducibility metadata. | V1 provides useful in-memory calculations but lacks complete validation and evidence contracts. |
| `V2-FR-OPT-127` | Monte Carlo And Scenario Simulation | Monte Carlo evidence shall include ruin probability, daily-loss breach probability, total-loss breach probability, profit-target probability, equity percentiles, drawdown percentiles, losing-streak distribution, and ret… | **Modify** | Require available MC distribution, drawdown, ruin, streak, and target evidence; daily/total breach fields are profile-dependent. | Not every simulation has the time granularity needed for every proposed statistic. |
| `V2-FR-OPT-128` | Monte Carlo And Scenario Simulation | Monte Carlo random number generation shall derive deterministic seeds from run seed, candidate ID, and phase-specific offsets. | **Modify** | Use documented deterministic sub-seed derivation for candidate/phase when parallel or multi-phase execution is enabled. | V1 supports seeds but not provenance-safe derivation. |
| `V2-FR-OPT-129` | Monte Carlo And Scenario Simulation | Prop-firm compliance gates shall support max daily loss, max total loss, monthly target, best-day consistency, news restrictions, weekend restrictions, overnight restrictions, exposure limits, correlated exposure limits… | **Reject** | Prop-firm rule configuration and evaluation belong to Risk; optimization may carry supplied compliance evidence only. | These requirements assign governance/risk behavior to the wrong domain. |
| `V2-FR-OPT-130` | Monte Carlo And Scenario Simulation | Prop-firm profiles shall be versioned configuration profiles and shall define rule-evaluation frequency as one of `per_tick`, `per_bar_close`, `per_trade_event`, `session_close`, or `end_of_day`. | **Reject** | Prop-firm rule configuration and evaluation belong to Risk; optimization may carry supplied compliance evidence only. | These requirements assign governance/risk behavior to the wrong domain. |
| `V2-FR-OPT-131` | Monte Carlo And Scenario Simulation | Prop-firm compliance checks shall evaluate max daily loss, max exposure, and max correlated exposure at the configured intraday frequency when the selected profile requires intraday evidence. | **Reject** | Prop-firm rule configuration and evaluation belong to Risk; optimization may carry supplied compliance evidence only. | These requirements assign governance/risk behavior to the wrong domain. |
| `V2-FR-OPT-132` | Monte Carlo And Scenario Simulation | End-of-day-only prop-firm evaluation shall be allowed only when the specific versioned prop-firm profile explicitly permits it. | **Reject** | Prop-firm rule configuration and evaluation belong to Risk; optimization may carry supplied compliance evidence only. | These requirements assign governance/risk behavior to the wrong domain. |
| `V2-FR-OPT-133` | Parallel Processing | `ProgressTracker` shall track progress for parallel optimization work in a thread-safe manner. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-134` | Parallel Processing | `parallel_grid_search` shall run parameter-grid candidate evaluations across multiple workers. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-135` | Parallel Processing | `parallel_random_search` shall run sampled parameter candidate evaluations across multiple workers. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-136` | Parallel Processing | `parallel_walk_forward` shall run walk-forward optimization across windows and/or candidates in parallel. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-137` | Parallel Processing | `compare_parallel_speedup` shall compare optimization runtime across different worker counts. | **Reject** | Do not add standalone speedup, CPU recommendation, or ETA helpers to the domain. | These utilities have no confirmed business workflow and belong to execution/observability infrastructure. |
| `V2-FR-OPT-138` | Parallel Processing | `get_optimal_n_jobs` shall recommend a worker count based on available CPU capacity. | **Reject** | Do not add standalone speedup, CPU recommendation, or ETA helpers to the domain. | These utilities have no confirmed business workflow and belong to execution/observability infrastructure. |
| `V2-FR-OPT-139` | Parallel Processing | `estimate_completion_time` shall estimate total execution time from single-run time, run count, and worker count. | **Reject** | Do not add standalone speedup, CPU recommendation, or ETA helpers to the domain. | These utilities have no confirmed business workflow and belong to execution/observability infrastructure. |
| `V2-FR-OPT-140` | Parallel Processing | `analyze_parallel_results` shall convert parallel optimization results into tabular analysis output. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-141` | Parallel Processing | `analyze_walk_forward_results` shall summarize walk-forward optimization results. | **Modify** | Summarize WFA evidence within CAP-OPT-011, not as a separate public analysis helper. | It is a report/evidence transformation rather than a distinct capability. |
| `V2-FR-OPT-142` | Parallel Processing | Parallel processing must keep worker inputs serializable and preserve deterministic aggregation of results. | **Keep** | Require serializable inputs and deterministic aggregation whenever parallel execution is enabled. | This is a necessary future execution invariant. |
| `V2-FR-OPT-143` | Parallel Processing | The service layer shall depend on an `ExecutionOrchestrator` abstraction rather than direct multiprocessing. | **Modify** | Use a minimal injected executor protocol only when execution concurrency is enabled; do not introduce a broad manager/service layer now. | The behavioral decoupling is valid, but the prescribed abstraction is premature. |
| `V2-FR-OPT-144` | Parallel Processing | Local sequential and local multiprocessing orchestration shall preserve deterministic aggregation order and equivalent failure isolation. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-145` | Parallel Processing | Future Ray, Dask, or Celery adapters shall remain deferred until repository idempotency, retry behavior, and resource accounting are production-mature. | **Keep** | Keep distributed backends explicitly deferred. | Repository idempotency, resource accounting, and retry maturity are not established. |
| `V2-FR-OPT-146` | Parallel Processing | The `ExecutionOrchestrator` shall support backend-neutral early-stopping and pruning hooks. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-147` | Parallel Processing | Pruned candidates shall remain persisted with partial evidence, including prune reason, prune phase, intermediate metric snapshot, backend name, and retryable flag. | **Defer** | Exclude execution concurrency/progress/pruning from the initial rebuild pending approved orchestration and repository policies. | V1 parallel behavior is only test-level and contains a bounded-queue defect; V2 platform controls are not approved. |
| `V2-FR-OPT-148` | Scoring | `sharpe_score` shall score results using Sharpe ratio. | **Keep** | Retain the proven core scoring functions. | V1 implements and tests these deterministic metrics. |
| `V2-FR-OPT-149` | Scoring | `sortino_score` shall score results using Sortino ratio. | **Keep** | Retain the proven core scoring functions. | V1 implements and tests these deterministic metrics. |
| `V2-FR-OPT-150` | Scoring | `calmar_score` shall score results using Calmar ratio. | **Keep** | Retain the proven core scoring functions. | V1 implements and tests these deterministic metrics. |
| `V2-FR-OPT-151` | Scoring | `profit_factor_score` shall score results using profit factor. | **Keep** | Retain the proven core scoring functions. | V1 implements and tests these deterministic metrics. |
| `V2-FR-OPT-152` | Scoring | `total_return_score` shall score results using total return percentage. | **Keep** | Retain the proven core scoring functions. | V1 implements and tests these deterministic metrics. |
| `V2-FR-OPT-153` | Scoring | `custom_score` shall calculate a weighted composite from return, Sharpe, and drawdown components. | **Modify** | Allow a configured composite only; remove hard-coded weights from the canonical objective set. | Hard-coded weights are an unapproved policy choice. |
| `V2-FR-OPT-154` | Scoring | `optimization_get_scoring_func` shall resolve supported objective names to scoring functions. | **Modify** | Resolve only an owner-approved objective whitelist and reject unknown names. | V1 silently falls back to total return, which can hide caller errors. |
| `V2-FR-OPT-155` | Scoring | Scoring helpers shall handle missing metrics with deterministic fallback behavior. | **Modify** | Use explicit unavailable/insufficient-data results; do not silently fabricate a different metric. | Determinism must not come at the cost of misleading scores. |
| `V2-FR-OPT-156` | Scoring | Candidate scoring shall support return, net profit, Sharpe, Sortino, Calmar, profit factor, expectancy, win rate, drawdown, trade count, exposure, turnover, cost-adjusted return, OOS retention, fold consistency, robustn… | **Modify** | Keep core optimization metrics and accept externally computed Analytics/Risk metrics through typed evidence; defer the full list. | Many proposed metrics belong to Analytics, Portfolio, or Risk and are not proven V1 capabilities. |
| `V2-FR-OPT-157` | Scoring | Candidate scoring shall support single-objective, weighted multi-objective, constraint-based, and Pareto-ready scoring. | **Modify** | Support single-objective and deterministic Pareto-ready ranking first; defer configurable weighted/constraint engines. | The full scoring framework is disproportionate to current workflows. |
| `V2-FR-OPT-158` | Scoring | Pareto selection shall be deterministic and shall record fallback behavior for knee-point selection when used. | **Modify** | Keep deterministic Pareto selection; knee-point selection is optional and must be explicitly configured/evidenced. | V1 has a basic Pareto front but no justified knee method. |
| `V2-FR-OPT-159` | Scoring | Anti-overfitting gates shall evaluate in-sample versus out-of-sample degradation, walk-forward consistency, parameter neighborhood smoothness, top-candidate clustering, profit concentration, trade count adequacy, cost s… | **Modify** | Approve baseline IS/OOS, WFA, DSR, trade-count, cost, and MC checks; defer topology, clustering, regime, and capacity gates. | The proposed gate list combines proven behavior with speculative institutional features. |
| `V2-FR-OPT-160` | Scoring | Every scored candidate shall include raw Sharpe, deflated Sharpe, multiple-testing method, nominal or effective trial count metadata, Sharpe variance estimate, MTB pass status, and MTB rejection reason. | **Modify** | Emit DSR/trial metadata when sufficient data exists; add explicit insufficient-data fields and correct Sharpe variance calculation. | V1 includes part of this evidence but trial handling is inconsistent. |
| `V2-FR-OPT-161` | Scoring | `nominal_trial_count` shall be calculated from unique executable candidate hashes after canonical normalization, inactive conditional exclusion, constraint rejection, and cache deduplication. | **Modify** | Count unique executable candidate hashes after rejection/deduplication and record the method. | This is sound but must integrate with actual execution/cache evidence. |
| `V2-FR-OPT-162` | Scoring | If topology-adjusted or effective-trial estimation is enabled, evidence shall include `effective_trial_count`, `trial_count_method`, and any required method metadata. | **Defer** | Do not implement effective-trial/topology estimation in the initial rebuild. | No approved method or workflow exists. |
| `V2-FR-OPT-163` | Scoring | Evidence shall include `trial_count_independence_warning` when nominal counts may overstate independence in highly correlated, Bayesian, exploitative, or highly constrained parameter spaces. | **Keep** | Retain warning/labeling safeguards and block PBO thresholds pending risk-owner approval. | They prevent statistical overstatement and premature production gates. |
| `V2-FR-OPT-164` | Scoring | `nominal_trial_count` shall not be presented as a statistically independent trial count unless the configured method explicitly supports that interpretation. | **Keep** | Retain warning/labeling safeguards and block PBO thresholds pending risk-owner approval. | They prevent statistical overstatement and premature production gates. |
| `V2-FR-OPT-165` | Scoring | PBO threshold enforcement shall remain blocked until the designated risk owner approves production, strict-capital, research-only, and exploratory-validation thresholds. | **Keep** | Retain warning/labeling safeguards and block PBO thresholds pending risk-owner approval. | They prevent statistical overstatement and premature production gates. |
| `V2-FR-OPT-166` | Results And Models | `OptimizationResult` shall represent one candidate optimization result with parameters, score, metrics, and metadata. | **Keep** | Retain a typed candidate result contract. | This is proven and central to search/evidence workflows. |
| `V2-FR-OPT-167` | Results And Models | `OptimizationSummary` shall represent an optimization run summary and expose top-N and dataframe conversion behavior. | **Modify** | Retain summary and top-N behavior; provide serializable table data and make pandas conversion optional/outside the core contract. | The V1 heavy optional import should not define the base result model. |
| `V2-FR-OPT-168` | Results And Models | `UnsupervisedConfigRequest`, `UnsupervisedRunSummary`, and `UnsupervisedAnalysisRequest` shall model unsupervised-analysis configuration and output attached to optimization flows. | **Reject** | Remove unsupervised-analysis models from optimization. | No behavior or workflow exists and unsupervised research belongs to Analytics/Research. |
| `V2-FR-OPT-169` | Results And Models | `ParameterRange` shall model a named parameter range for optimization requests. | **Keep** | Retain a typed parameter definition. | It is proven foundational behavior. |
| `V2-FR-OPT-170` | Results And Models | `OptimizationRequest`, `OptimizationResponse`, `OptimizationRunDetails`, and `OptimizationResultItem` shall model optimization request, response, run detail, and result item payloads. | **Modify** | Consolidate overlapping request/response/run models around actual public and internal workflows. | V1 contains redundant models and V2 risks preserving them all. |
| `V2-FR-OPT-171` | Results And Models | `PositionSizingRequest` shall model position-sizing simulation requests. | **Defer** | Add position-sizing request models only if CAP-OPT-015 is approved. | A schema without behavior is not useful. |
| `V2-FR-OPT-172` | Results And Models | `WalkForwardRequest`, `WalkForwardWindow`, and `WalkForwardResponse` shall model walk-forward analysis inputs and outputs. | **Modify** | Retain WFA request/window/response contracts for the single approved WFA workflow. | V1 models are useful but must align with the merged workflow and canonical statuses. |
| `V2-FR-OPT-173` | Results And Models | `MonteCarloRequest`, `ParametricMonteCarloRequest`, and `MonteCarloResponse` shall model Monte Carlo inputs and outputs. | **Modify** | Retain only models required by core trade-sequence and parametric MC workflows. | Avoid exposing unused scenario schemas. |
| `V2-FR-OPT-174` | Results And Models | `ConsecutiveLosingRequest`, `ConsecutiveLosingScenario`, and `ConsecutiveLosingResponse` shall model consecutive-loss simulation inputs and outputs. | **Defer** | Do not ship these models until the corresponding specialized simulation is approved. | V1 demonstrates schema-only dead weight for these capabilities. |
| `V2-FR-OPT-175` | Results And Models | `ProfitTargetRequest`, `ProfitTargetResult`, and `ProfitTargetResponse` shall model profit-target simulation inputs and outputs. | **Defer** | Do not ship these models until the corresponding specialized simulation is approved. | V1 demonstrates schema-only dead weight for these capabilities. |
| `V2-FR-OPT-176` | Results And Models | `ManualPairInput`, `RandomWinRateRequest`, `RandomWinRatePair`, `DistributionStats`, `RandomWinRateResult`, and `RandomWinRateResponse` shall model random win-rate simulation inputs and outputs. | **Defer** | Do not ship these models until the corresponding specialized simulation is approved. | V1 demonstrates schema-only dead weight for these capabilities. |
| `V2-FR-OPT-177` | Results And Models | `RobustnessRequest`, `RobustnessStats`, and `RobustnessResponse` shall model robustness simulation inputs and outputs. | **Modify** | Retain a compact robustness request/result contract aligned with approved checks. | V1 provides useful behavior but the V2 evidence scope is too broad. |
| `V2-FR-OPT-178` | Results And Models | `MultiEntryRequest`, `MultiEntryScenarioResult`, and `MultiEntryResponse` shall model multi-entry simulation inputs and outputs. | **Defer** | Do not ship these models until the corresponding specialized simulation is approved. | V1 demonstrates schema-only dead weight for these capabilities. |
| `V2-FR-OPT-179` | Results And Models | Evidence packages shall include best candidate, top candidates, rejected candidate summary, optimization summary, walk-forward evidence, parameter stability evidence, robustness evidence, Monte Carlo evidence, prop-firm… | **Modify** | Create a versioned baseline evidence package; optional sections appear only when produced or supplied by owning domains. | Making every advanced/institutional field mandatory would block useful research and blur ownership. |
| `V2-FR-OPT-180` | Results And Models | Evidence packages shall include institutional fields for raw Sharpe, Deflated Sharpe Ratio, multiple-testing method, purging and embargo data, leakage prevention status, parameter plateau score, isolation penalty, estim… | **Modify** | Require proven provenance, DSR, leakage, realism, and quota fields when applicable; defer topology/isolation/capacity calculations. | The institutional field list mixes approved and speculative evidence. |
| `V2-FR-OPT-181` | Results And Models | Evidence packages shall include advanced research fields for PBO, CPCV, sensitivity, noisy-objective handling, repeated score statistics, and compute cost when applicable. | **Defer** | Add advanced research fields only with the corresponding approved capability. | PBO/CPCV/topology/repeated-noise workflows are deferred. |
| `V2-FR-OPT-182` | Results And Models | Capacity evidence shall include `deployment_base_currency`, `intended_deployment_aum`, and `estimated_capacity_in_base_currency`. | **Modify** | Allow optional externally supplied capacity fields in handoffs; optimization does not calculate capacity. | Capacity estimation belongs to Portfolio/Execution/Market Impact ownership. |
| `V2-FR-OPT-183` | Results And Models | Reports shall be generated from evidence without recomputation and shall include constraint violations, WFE summary, sampler policy, Pareto selection method, PBO when enabled, pruning/partial-evidence behavior, and prod… | **Modify** | Generate report packages from stored evidence without recomputation; include only enabled-method sections. | The principle is valid but the mandatory content list includes deferred features. |
| `V2-FR-OPT-184` | Results And Models | Chart-ready data shall support equity curves, drawdown curves, candidate scatter plots, parameter heatmaps, Pareto front, walk-forward fold results, Monte Carlo cone, final equity distribution, drawdown distribution, re… | **Modify** | Provide baseline chart-ready series/tables for enabled workflows; do not mandate every proposed visualization dataset. | The complete visualization list is disproportionate and includes deferred/cross-domain evidence. |
| `V2-FR-OPT-185` | Portfolio Optimization | `pfo_from_optimize_func` shall periodically optimize portfolio allocation weights from a deterministic callback. | **Reject** | Move portfolio allocation optimization and its result/plot contracts to the Portfolio domain. | No V1 workflow supports it and it conflicts with the stated non-ownership of portfolio governance. |
| `V2-FR-OPT-186` | Portfolio Optimization | `pfo_plot` shall package periodic allocation-weight data for inspection and may provide non-UI diagnostic serialization; UI chart rendering shall remain outside the Optimization module. | **Reject** | Move portfolio allocation optimization and its result/plot contracts to the Portfolio domain. | No V1 workflow supports it and it conflicts with the stated non-ownership of portfolio governance. |
| `V2-FR-OPT-187` | Portfolio Optimization | `PortfolioOptimizerResult` shall hold periodic portfolio weights and non-UI inspection metadata. | **Reject** | Move portfolio allocation optimization and its result/plot contracts to the Portfolio domain. | No V1 workflow supports it and it conflicts with the stated non-ownership of portfolio governance. |
| `V2-FR-OPT-188` | Background Tasks | `run_optimization_task` shall coordinate a background parameter optimization run and report progress. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-189` | Background Tasks | `run_walk_forward_task` shall coordinate a background walk-forward analysis run and report progress. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-190` | Background Tasks | `run_monte_carlo_task` shall coordinate a background Monte Carlo simulation run. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-191` | Background Tasks | Background tasks shall isolate database/progress-manager side effects from low-level deterministic optimization helpers. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-192` | Background Tasks | Background task entry points shall return a `task_id` and polling/progress reference, not block the calling thread until optimization completion. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-193` | Background Tasks | The module shall write optimization runs, candidates, candidate results, checkpoints, evidence packages, and audit records only through an approved repository interface. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-194` | Background Tasks | The module shall own repository contracts and payload schemas, but shall not own production database provisioning, migrations, credentials, or operations unless explicitly assigned by architecture decision. | **Keep** | Retain the ownership and dependency-injection boundary for any future repository-backed workflow. | This prevents optimization core from owning infrastructure implementations. |
| `V2-FR-OPT-195` | Background Tasks | Concrete repository adapters shall be owned by the approved persistence layer unless explicitly assigned to this module by architecture decision. | **Keep** | Retain the ownership and dependency-injection boundary for any future repository-backed workflow. | This prevents optimization core from owning infrastructure implementations. |
| `V2-FR-OPT-196` | Background Tasks | Repository implementations shall be passed into execution-capable workflows through Dependency Injection rather than imported or constructed by optimization core code. | **Keep** | Retain the ownership and dependency-injection boundary for any future repository-backed workflow. | This prevents optimization core from owning infrastructure implementations. |
| `V2-FR-OPT-197` | Background Tasks | Repository backend support for in-memory fixtures, JSONL fixtures, SQLite, DuckDB/Parquet, PostgreSQL, or managed PostgreSQL-compatible databases shall require deployment-tier approval before production use. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-198` | Background Tasks | The module shall support checkpointing after configured candidate intervals, state transitions, before long robustness or Monte Carlo phases, on cancellation, and on recoverable errors. | **Defer** | Exclude background execution and repository-backed lifecycle from the initial rebuild. | The V1 task functions are stubs and production repository/orchestration policy is unresolved. |
| `V2-FR-OPT-199` | Background Tasks | Resume logic shall reject corrupted, partial, or schema-invalid checkpoint artifacts rather than silently resuming. | **Keep** | Retain fail-closed checkpoint validation and audited fallback behavior for the deferred run-state capability. | V1 already demonstrates useful corruption handling. |
| `V2-FR-OPT-200` | Background Tasks | If the latest checkpoint is corrupted but an earlier valid checkpoint exists, the run may resume from the earlier checkpoint with an audit warning. | **Keep** | Retain fail-closed checkpoint validation and audited fallback behavior for the deferred run-state capability. | V1 already demonstrates useful corruption handling. |
| `V2-FR-OPT-201` | Background Tasks | File-backed checkpoint and candidate-result writes shall use atomic rename semantics by writing to a uniquely named temporary file, flushing and fsyncing where supported, then replacing the target artifact. | **Modify** | Require atomic durability semantics; use an approved infrastructure writer rather than owning production filesystem adapters in optimization. | The safety behavior is valid but implementation ownership is external. |
| `V2-FR-OPT-202` | Background Tasks | Atomic write failure shall produce a structured repository or checkpoint error with artifact type, temporary path reference, target path reference, run ID, and phase. | **Modify** | Return structured artifact-write errors with redacted path references and run/phase context. | Raw temporary and target paths may be sensitive. |
| `V2-FR-OPT-203` | Background Tasks | Candidate cache entries shall be invalidated automatically when strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, module version, or parameter-space hash changes. | **Keep** | Invalidate cache when any provenance component changes. | This is essential for correct reuse. |
| `V2-FR-OPT-204` | Background Tasks | `candidate_hash` shall be the source of truth for candidate deduplication and shall deterministically combine strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, modul… | **Modify** | Make `candidate_hash` include `parameter_space_hash` explicitly in addition to strategy/data/cost/realism/objective/engine/module/executable parameters. | The V2 invalidation rule includes parameter-space changes but the listed hash inputs omit the hash itself. |
| `V2-FR-OPT-205` | Background Tasks | `candidate_hash` shall exclude inactive conditional parameters and shall use canonical JSON with sorted keys and normalized decimals. | **Keep** | Retain canonical executable-parameter and parameter-space hashing rules. | V1 already provides strong evidence for these behaviors. |
| `V2-FR-OPT-206` | Background Tasks | `parameter_space_hash` shall be order-invariant, shall sort dictionary keys, shall canonicalize parameter definitions, and shall include constraints after canonical sorting and normalization. | **Keep** | Retain canonical executable-parameter and parameter-space hashing rules. | V1 already provides strong evidence for these behaviors. |

### 6.5 Non-functional requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-NFR-OPT-001` | Optimization behavior must be reproducible for the same inputs where deterministic algorithms are used. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-002` | Random, Monte Carlo, Bayesian, and genetic workflows must support seed or random-state controls where practical. | **Modify** | Require seed/random-state controls for enabled randomized workflows; deferred algorithms inherit the rule when activated. | Bayesian/genetic are not initial capabilities. |
| `V2-NFR-OPT-003` | Public service tools must not perform unbounded compute directly when their documented behavior is request packaging. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-004` | Parameter spaces, iteration counts, population sizes, bootstrap counts, simulation counts, and worker counts must be bounded before production use. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-005` | The module shall perform no broker, database, network, multiprocessing, or heavy dependency initialization at import time. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-006` | Each execution-capable workflow shall enforce configured timeout, retry, cancellation, and backpressure policies. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-007` | Timeout enforcement shall use a monotonic clock source such as `time.monotonic()` or `time.perf_counter()` so NTP adjustments or wall-clock changes cannot cause premature timeout or infinite hangs. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-008` | Public request-packaging API responses shall complete within an approved latency budget. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-009` | Proposed engineering baseline: public packaging responses should complete in `<= 200 ms` under owner-approved payload-size limits, subject to owner finalization and benchmark validation. | **Open Decision** | Approve a packaging latency target and payload-size test profile before making it an acceptance threshold. | The proposed 200 ms value lacks an approved benchmark environment and payload cap. |
| `V2-NFR-OPT-010` | Proposed engineering baseline: execution-capable workflows should use a configurable default timeout of `30 minutes`, with overrides allowed only through approved resource profiles. | **Open Decision** | Approve execution timeout defaults through the execution profile. | The proposed 30-minute value is explicitly pending and workload-dependent. |
| `V2-NFR-OPT-011` | Proposed engineering baseline: repository writes over network-backed repositories should retry safe transient failures with exponential backoff up to `3` attempts before surfacing a persistent structured error. | **Open Decision** | Set retry policy in the owning repository/infrastructure contract. | Optimization does not own network repository implementation and blanket retries can be unsafe. |
| `V2-NFR-OPT-012` | Large request payloads shall be rejected before expensive validation or execution with `OPT_PAYLOAD_TOO_LARGE` when they exceed configured size limits. | **Open Decision** | Add `OPT_PAYLOAD_TOO_LARGE` after the maximum public payload size is approved. | No numeric limit exists. |
| `V2-NFR-OPT-013` | Optimization outputs shall include objective, executable parameters, candidate score, data slice, algorithm name and version, seed, engine type and version, cost model hash, simulator realism profile hash, parameter-spa… | **Modify** | Require full provenance on execution/evidence outputs; packaging responses contain validated requested provenance and missing-field warnings. | A request package cannot truthfully provide candidate score or engine result fields before execution. |
| `V2-NFR-OPT-014` | Optimization must control compute load and warn about overfitting risks. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-015` | Optimization must not mutate production strategy state without governance. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-016` | Optimization must not place trades, call live brokers, or bypass risk/trading/live safety gates. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-017` | Public result payloads shall be JSON-safe before envelope return. `NaN`, `Infinity`, and `-Infinity` shall serialize as `null` with a warning; `datetime` values shall serialize as UTC ISO-8601 strings; `Decimal` values… | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-018` | Error responses must be structured, traceable, and safe for API/agent consumption. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-019` | Metrics and reports must not overstate live readiness or hide sample-size, out-of-sample, robustness, or overfit caveats. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-020` | Parallel workflows must avoid race conditions in progress tracking and result aggregation. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-021` | Optional lower-level dependencies shall either use a documented fallback or return a structured dependency error such as `OPT_SAMPLER_UNAVAILABLE`, `OPT_OPTIMIZER_BACKEND_UNAVAILABLE`, or `OPT_DEPENDENCY_UNAVAILABLE`; u… | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-022` | Persist/package tools must distinguish request packaging from actual durable storage. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-023` | Generated reports, saved results, and logs must not expose secrets, credentials, broker tokens, private trade payloads, or authorization headers. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-024` | Logs, traces, reports, and errors shall redact secrets, credentials, authorization headers, private trade payloads, sensitive file paths, and environment variables. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-025` | Metrics shall include request count, validation failures, runtime failures, resource-cap rejections, execution duration, queue time, candidate count, and cancellation count. | **Modify** | Emit structured observability events/fields; the shared observability domain owns collection and storage. | Optimization should not create a separate metrics subsystem. |
| `V2-NFR-OPT-026` | Registry changes must remain covered by tests and catalog updates. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-027` | Hashing shall use SHA-256 over canonical JSON with sorted keys and normalized decimals, with decimals quantized to eight decimal places by default unless field-specific precision is declared. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-028` | Repeated deterministic runs with the same inputs shall produce the same candidate ordering, same candidate hashes, same parameter-space hash, and same evidence when backtest execution is deterministic. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-029` | Resource caps shall fail closed by default unless an explicitly approved override is present. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-030` | Resource overrides shall include approver, reason, requested cap, approved cap, timestamp, request ID, and workflow trust context in audit metadata. | **Keep** | Record approved resource overrides in audit metadata. | This is necessary if any fail-closed cap override is allowed. |
| `V2-NFR-OPT-031` | Production signoff shall be blocked when required institutional evidence fields are missing or when performance benchmarks exceed configured limits without approved exception. | **Modify** | Optimization reports evidence completeness; final production signoff remains external governance. | Optimization does not own release acceptance or live approval. |
| `V2-NFR-OPT-032` | Candidate hash generation shall benchmark at `10,000 candidates/sec` locally for simple parameters, parameter validation shall benchmark at `5,000 candidates/sec` for simple numeric parameters, repository write throughp… | **Open Decision** | Define benchmark targets only after an approved environment, datasets, and final implementation exist. | The proposed throughput numbers are unsupported by V1 evidence and mix domain and repository benchmarks. |
| `V2-NFR-OPT-033` | Atomic write temporary files shall be created only under approved artifact directories and shall not be treated as valid evidence packages or checkpoints. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-034` | File-backed checkpoint writes shall prevent path traversal through both temporary and final artifact paths. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-035` | Official optimization tools shall not possess live broker credentials, live broker gateway network access, or permission to place or close trades. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-036` | Error codes shall use deterministic enum-style values and optimization-specific errors shall use the `OPT_` prefix. | **Keep** | Retain as a final non-functional or safety requirement. | It is necessary for bounded, reproducible, secure, and deterministic behavior. |
| `V2-NFR-OPT-037` | The module shall include `OPT_ATOMIC_WRITE_FAILED`, `OPT_CHECKPOINT_CORRUPTED`, `OPT_INTRADAY_RULE_DATA_UNAVAILABLE`, `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED`, `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED`, `OPT_PRUNED_BY_HA… | **Modify** | Keep codes for implemented optimization behaviors; move prop-firm/intraday rule errors to Risk and add deferred codes only with their capabilities. | A static error list should not imply unimplemented or out-of-domain behavior. |

### 6.6 Required edge-case coverage

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-EDGE-OPT-001` | Empty parameter grids, empty parameter distributions, and parameter ranges with invalid bounds or steps. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-002` | Parameter spaces that produce zero candidates, duplicate candidates, or too many candidates. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-003` | Candidate records missing `score`, missing parameters, non-numeric scores, NaN scores, or tied scores. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-004` | In-sample and out-of-sample scores missing, reversed, non-numeric, or separated by a zero/negative threshold. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-005` | Walk-forward windows that overlap incorrectly, leave no train/test data, or use invalid date ranges. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-006` | Data shorter than the requested rolling, expanding, train, validation, or test windows. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-007` | Strategy class missing, strategy file missing, strategy class name incorrect, or strategy factory returning a non-class object. | **Modify** | Retain only the portion applicable to approved boundaries and delegate external ownership where required. | The edge case combines retained behavior with rejected/deferred file loading, market-data ownership, session calendars, or infrastructure details. |
| `V2-EDGE-OPT-008` | Backtest engine unavailable, unsupported engine type, missing symbol, invalid initial balance, invalid position size, or failed candidate execution. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-009` | Monte Carlo inputs with no trades, all wins, all losses, zero risk, negative risk, invalid win rate, invalid reward/risk ratio, impossible target balance, or insufficient simulation count. | **Modify** | Retain only the portion applicable to approved boundaries and delegate external ownership where required. | The edge case combines retained behavior with rejected/deferred file loading, market-data ownership, session calendars, or infrastructure details. |
| `V2-EDGE-OPT-010` | Randomized workflows without seeds when reproducibility is required. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-011` | Parallel workers failing, timing out, returning incompatible results, or requiring non-pickleable inputs. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-012` | Scoring functions receiving missing analytics, missing ratios, missing returns, zero drawdown, or non-finite values. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-013` | Robustness checks with empty check lists, missing pass/fail fields, mixed status formats, or contradictory check results. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-014` | Report/package tools receiving payloads with non-serializable objects. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-015` | Database/progress-manager side effects unavailable in background task paths. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-016` | Large optimization requests that could exceed CPU, memory, or runtime limits. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-017` | A checkpoint write interrupted mid-write must not corrupt the latest valid checkpoint. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-018` | A corrupted checkpoint must fail closed or fall back to the previous valid checkpoint with an audit warning. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-019` | A prop-firm profile requiring intraday checks must reject end-of-day-only compliance evidence. | **Reject** | Move prop-firm rule edge cases to the Risk domain. | Optimization may carry compliance evidence but does not evaluate prop-firm rules. |
| `V2-EDGE-OPT-020` | Equivalent parameter spaces with different dictionary insertion order must produce identical `parameter_space_hash` values. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-021` | Bayesian or exploitative optimizer runs must emit an independence warning when only `nominal_trial_count` is available. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-022` | Candidate pruning must preserve partial evidence and must not make failed or abandoned trials disappear from audit history. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-023` | Strict capital deployment must reject candidates that pass a research PBO threshold but fail the stricter production threshold. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-024` | Simulator realism profiles that introduce stochasticity must conflict with deterministic-only noisy-objective policy unless the run switches to an approved repeated-evaluation policy. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-025` | Candidate cache reuse must be blocked when simulator realism profile hash, objective hash, module version, or parameter-space hash changes. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-026` | Sobol or Latin Hypercube sampler unavailability must be explicit and must not silently fall back without evidence metadata. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-027` | Intraday prop-firm rule data unavailable at the required frequency must produce structured failure details with rule name, required evaluation frequency, available data frequency, and profile ID. | **Reject** | Move prop-firm rule edge cases to the Risk domain. | Optimization may carry compliance evidence but does not evaluate prop-firm rules. |
| `V2-EDGE-OPT-028` | Timezone-aware train/test split boundaries, DST transitions, weekend market closures, holiday sessions, and broker session offsets. | **Modify** | Retain only the portion applicable to approved boundaries and delegate external ownership where required. | The edge case combines retained behavior with rejected/deferred file loading, market-data ownership, session calendars, or infrastructure details. |
| `V2-EDGE-OPT-029` | Duplicate, missing, stale, revised, out-of-order, or mixed-frequency market-data rows. | **Modify** | Retain only the portion applicable to approved boundaries and delegate external ownership where required. | The edge case combines retained behavior with rejected/deferred file loading, market-data ownership, session calendars, or infrastructure details. |
| `V2-EDGE-OPT-030` | Cancellation requested during validation, execution, checkpoint write, repository write, report generation, or Monte Carlo simulation. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-031` | Resume requested for an already completed, failed, cancelled, or superseded run. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-032` | Repository permission denied, disk full, stale lock file, path traversal attempt, and artifact checksum mismatch. | **Modify** | Retain only the portion applicable to approved boundaries and delegate external ownership where required. | The edge case combines retained behavior with rejected/deferred file loading, market-data ownership, session calendars, or infrastructure details. |
| `V2-EDGE-OPT-033` | Transient connection loss, connection pool exhaustion, or query timeout during repository-backed checkpoint, resume, or candidate-result operations. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-034` | `dry_run` requested on a calculation-only public tool, with expected behavior defined by the tool contract. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-035` | Optional dependency installed but incompatible with the approved version range. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-036` | Requested advanced sampler unavailable, such as `search_method="sobol"` without the approved dependency, shall return `OPT_SAMPLER_UNAVAILABLE` with fallback metadata or a blocked status, not an unhandled `ImportError`. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-037` | Cache stampede: parallel workers request the same uncached `candidate_hash`; candidate execution shall use local or distributed locking to prevent redundant execution of identical candidates when a repository/cache back… | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |
| `V2-EDGE-OPT-038` | Non-finite or non-JSON-native output values, including `NaN`, `Infinity`, `-Infinity`, `datetime`, `Decimal`, or backend-specific result objects, reach envelope packaging. | **Keep** | Cover in validation or tests for the approved capability. | This is a relevant failure mode for a retained workflow. |
| `V2-EDGE-OPT-039` | Abrupt worker termination during execution, checkpoint write, repository write, or report generation. | **Defer** | Test when the corresponding parallel, repository, advanced sampler, PBO, pruning, cancellation, or background capability is approved. | The referenced capability is deferred from the initial rebuild. |

### 6.7 Required tests

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-TEST-OPT-001` | Registry tests proving `app.services.optimization.__all__` matches the approved public service surface. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-002` | Requirement traceability tests proving every requirement ID maps to at least one test. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-003` | Golden-envelope contract tests for success, warning, rejected, blocked, failed, and cancelled responses. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-004` | Usage-example tests proving examples execute against the public contract and return documented envelope shapes. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-005` | Import-time safety tests proving no broker, database, network, multiprocessing, or heavy execution behavior occurs on import. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-006` | Observability tests proving logs, metrics, and traces include required correlation fields and redact sensitive values. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-007` | Enum consistency tests proving requirements, models, examples, and tests use the same canonical status and final-decision values. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-008` | Dry-run contract tests for every public tool, verifying no persistent side effects, no external calls, correct calculation behavior for calculation-only tools, and consistent envelope schema. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-009` | Network-failure simulation tests for repository adapters, including retry, fail-closed behavior, structured persistent errors, and audit warnings. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-010` | Chaos/resilience tests simulating abrupt worker termination during parallel execution and verifying corrupted or partial checkpoints are rejected and the previous valid checkpoint is used when available. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-011` | Timezone and DST tests for train/test splits crossing daylight-saving boundaries, weekend market closures, holiday sessions, and broker session offsets. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-012` | Sampler dependency tests proving unavailable advanced samplers return `OPT_SAMPLER_UNAVAILABLE` or approved fallback metadata without unhandled import errors. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-013` | Cache-stampede tests proving duplicate `candidate_hash` execution is serialized, deduplicated, or explicitly reported as unsupported by the selected repository/cache profile. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-014` | Callable/docstring tests for every exported optimization service tool. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-015` | Standard-envelope tests for every exported optimization service tool. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-016` | Request-packaging tests proving context fields are separated from business payloads. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-017` | `rank_parameter_sets` tests for descending sort, ties, missing scores, negative scores, and deterministic ordering. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-018` | `detect_overfit_parameters` tests for above-threshold, below-threshold, equal-threshold, missing-score, and invalid-threshold cases. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-019` | `calculate_parameter_stability` tests for stable parameters, unstable parameters, missing values, single candidate, and non-numeric values. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-020` | Robustness-score tests for empty checks, all-pass checks, all-fail checks, mixed checks, and malformed check records. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-021` | Stress-test packaging tests for spread, slippage, commission, cross-market, cross-timeframe, out-of-sample, and Monte Carlo request tools. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-022` | Search-method tests for grid, random, Bayesian, and genetic candidate generation and result summary behavior using small deterministic fixtures. | **Modify** | Test grid and pseudo-random now; retain genetic/Bayesian cases only when those capabilities are activated. | V1 Bayesian is false and genetic is deferred. |
| `V2-TEST-OPT-023` | Execution-helper tests with mock strategy classes and mock backtest engine behavior. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-024` | Strategy-loading tests for valid path/class, missing file, missing class, and invalid class. | **Reject** | Do not add optimization tests for rejected dynamic file loading or Risk-owned prop-firm evaluation. | The underlying requirement is rejected or belongs to another domain. |
| `V2-TEST-OPT-025` | Walk-forward and splitter tests for rolling, expanding, invalid windows, short datasets, and train/test boundary correctness. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-026` | Monte Carlo tests with fixed seeds for trade shuffling, resampling, bootstrap, ruin probability, confidence intervals, parametric simulation, position sizing, consecutive-loss, profit-target, random win-rate, robustness… | **Modify** | Test core shuffle/resample/bootstrap/ruin/interval/parametric/robustness paths now; defer specialized scenarios. | The original test list mirrors speculative schema growth. |
| `V2-TEST-OPT-027` | Parallel tests for worker-count selection, completion estimates, deterministic aggregation, worker failure handling, and non-pickleable input rejection. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-028` | Scoring tests for each objective and fallback behavior when metrics are missing. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-029` | Result/model validation tests for all request/response models and result data structures. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-030` | Serialization tests proving public outputs are JSON-safe, including `NaN`, `Infinity`, `-Infinity`, `datetime`, `Decimal`, and unsupported object handling. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-031` | Safety tests proving optimization tools do not place trades, call live brokers, mutate production strategy state, or bypass governance. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-032` | Security tests proving secrets and credentials are not exposed through errors, reports, logs, or packaged payloads. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-033` | Validation tests for request shape, strategy compatibility, market data quality, parameter-space constraints, objective definitions, evidence-package schema, and unsupported simulator realism shocks. | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-034` | Hashing tests proving canonical JSON, sorted keys, normalized decimals, order-invariant `parameter_space_hash`, simulator realism profile hash inclusion, candidate cache invalidation, and inactive conditional exclusion. | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-035` | Trial-count tests proving `nominal_trial_count` and `effective_trial_count` are labeled distinctly, `trial_count_method` is emitted, and independence warnings appear for Bayesian, exploitative, highly correlated, or hig… | **Modify** | Limit the test to approved capabilities and place external infrastructure/cross-domain assertions in integration suites. | The proposed test combines retained behavior with deferred or externally owned functionality. |
| `V2-TEST-OPT-036` | Walk-forward/CPCV tests proving purging and embargo enforcement for every fold/path and failure behavior when trade-horizon-aware validation is required but embargo cannot be calculated. | **Modify** | Test WFA purging/embargo now; defer CPCV-specific paths. | CPCV is deferred. |
| `V2-TEST-OPT-037` | PBO tests proving production threshold behavior, strict capital threshold behavior, and research-only allowance up to the configured exploratory threshold. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-038` | Atomic write tests proving checkpoint and candidate-result success paths, interrupted checkpoint write recovery, partial checkpoint rejection, corrupted checkpoint rejection, and fallback to the previous valid checkpoin… | **Modify** | Test checkpoint schema/atomic writer contract and integration with approved infrastructure; do not assume domain-owned file persistence. | Safety is retained but concrete persistence ownership is external. |
| `V2-TEST-OPT-039` | Repository tests for in-memory/JSONL fixtures, SQLite local-production behavior, DuckDB/Parquet candidate-history handoff, PostgreSQL-compatible policy boundaries, save/load/resume, cleanup, and candidate cache deduplic… | **Defer** | Repository backend matrix tests belong to the approved infrastructure integration milestone. | No repository backend is approved for this rebuild. |
| `V2-TEST-OPT-040` | Prop-firm tests for intraday max-daily-loss breach detection, intraday exposure breach detection, intraday correlated-exposure breach detection, end-of-day-only evidence rejection when intraday evaluation is required, a… | **Reject** | Do not add optimization tests for rejected dynamic file loading or Risk-owned prop-firm evaluation. | The underlying requirement is rejected or belongs to another domain. |
| `V2-TEST-OPT-041` | Orchestration tests for `ExecutionOrchestrator`, deterministic ordering, quota handling, local sequential behavior, local multiprocessing behavior, worker failure isolation, early-stopping hooks, pruning hooks, and pers… | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-042` | Sampler tests for deterministic pseudo-random behavior, Sobol/LHS deterministic behavior when available, unavailable sampler errors, fallback metadata, and constraint/inactive-conditional handling. | **Defer** | Add when the corresponding repository, orchestration, PBO/CPCV, parallel, or advanced sampler capability is approved. | The implementation is deferred. |
| `V2-TEST-OPT-043` | Production acceptance tests proving no official tool has live-trading capability, can place trades, can close broker positions, has network access to live broker gateways, or reports anything other than `places_trade=Fa… | **Keep** | Include in the test plan for the approved capability. | The test verifies a retained public contract, calculation, safety rule, or deterministic invariant. |
| `V2-TEST-OPT-044` | Performance tests for candidate hash throughput, parameter validation throughput, strict iterator grid expansion without Cartesian product materialization, sequential dummy backtest smoke runs, repository write throughp… | **Open Decision** | Define performance tests after budgets, environment, repository, and execution profile are approved. | Current numeric targets are unapproved and not evidenced by V1. |

### 6.8 Accepted behavior versus simplified/rejected implementation

| V2 area | Accepted behavior | Rejected or simplified implementation |
| --- | --- | --- |
| Public tools | Validated request packaging, lightweight calculations, standard envelope, explicit side effects. | Do not expose every lower-level function or algorithm wrapper; merge method variants and remove accidental V1 exports. |
| Candidate execution | One versioned optimization-facing adapter contract with fail-closed compatibility and structured results. | No direct simulator imports, hard-coded orchestrator/version, service/manager layer, or optimization-owned engine. |
| Search | Lazy grid and seeded pseudo-random baseline with bounded execution and common summaries. | No fake dry-run scoring, false Sobol/LHS labels, or initial Bayesian/genetic dependency stack. |
| Walk-forward | One internal WFA workflow, validated splits, purge/embargo, fold evidence. | No duplicate WFA implementations, direct public compute wrapper, mandatory custom folds, CPCV, or PBO in the initial rebuild. |
| Monte Carlo and robustness | Trade shuffle/resample/bootstrap, parametric simulation, stress calculations, reproducibility evidence. | No public function per variation; no speculative specialized scenario suite without workflows. |
| Scoring | Core metrics, deterministic ranking, DSR and nominal-trial caveats. | No unapproved hard-coded composite policy, universal metric list, topology/effective-trial engine, or production PBO threshold. |
| Evidence | Versioned provenance, candidates, WFA/MC/robustness results, warnings, audit references, chart-ready raw data. | Do not require every institutional field or compute Portfolio/Risk-owned capacity and prop-firm decisions. |
| Persistence | Optimization-owned schemas/protocols and atomic/corruption safety semantics. | No concrete database, filesystem, object-store, migration, credential, or multi-backend implementation in the domain. |
| Background/parallel execution | Future deterministic executor/progress/cancellation contract after policies are approved. | Remove fake task IDs; defer broad `ExecutionOrchestrator`, multiprocessing, pruning, distributed adapters, ETA and CPU recommendation helpers. |
| Dynamic strategies | Approved strategy identifier/handle accepted at the execution adapter boundary. | Reject arbitrary file-path imports and runtime code execution. |
| Portfolio/prop-firm | Carry externally supplied evidence in a handoff when useful. | Reject portfolio weight optimization and prop-firm rule evaluation in optimization. |

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
| --- | --- | --- | --- | --- | --- | --- |
| WF-OPT-001 | Package an optimization or robustness request | Cross-domain | `V1-WF-OPT-001` mechanically works but performs fake dry-run scoring | Public `packaging` tools with standard envelope | Replace | Input boundary: agent/API request → optimization validates and separates context/business payload → output boundary: deterministic package with no execution, network, persistence, background job, or trade side effect. |
| WF-OPT-002 | Execute a bounded parameter sweep | Cross-domain | `V1-WF-OPT-002` broken by missing simulator orchestrator | Grid/random internal execution through adapter with limits/provenance | Replace | Input boundary: approved execution request/profile + adapter → optimization generates/deduplicates/evaluates candidates → output boundary: summary and evidence; Simulation owns execution. |
| WF-OPT-003 | Score, rank, and assess overfit evidence | Internal | `V1-WF-OPT-006` working with valid supplied data | Expanded deterministic scoring and caveats | Modify | Supplied candidate/trade evidence → optimization computes approved metrics, ranking, DSR/nominal-trial warnings → typed result/evidence. |
| WF-OPT-004 | Run walk-forward validation | Cross-domain | `V1-WF-OPT-004` partial and duplicated | Single WFA plus matrix packaging, purge/embargo, WFE evidence | Replace | Approved WFA request + adapter → validated folds → train search/test evaluation → fold/WFE/degradation evidence. Public boundary packages only. |
| WF-OPT-005 | Run Monte Carlo and robustness analysis | Internal | `V1-WF-OPT-005` works for supplied trades | Core MC, stress, ruin/interval summaries, reproducibility | Modify | Supplied realized results → deterministic seeded simulations/stress transforms → robustness/MC evidence with caveats; no broker access. |
| WF-OPT-006 | Build downstream evidence and handoffs | Cross-domain | Missing coherent V1 workflow; reports/save wrappers are disconnected or misleading | Versioned Risk/Portfolio/UI/human-review evidence package | Add | Optimization results → assemble provenance, decisions, warnings, chart-ready data and optional externally supplied evidence → output package; downstream domains decide/render/persist. |
| WF-OPT-007 | Checkpoint, resume, cancel, and progress | Cross-domain | `V1-WF-OPT-007` and `V1-WF-OPT-008` work only as disconnected local utilities | Repository-backed idempotent lifecycle | Defer | Future boundary: execution state → injected repository/infrastructure → validated checkpoint/progress reference. No initial implementation until policies are approved. |
| WF-OPT-008 | Dynamic strategy-file optimization | Cross-domain | `V1-WF-OPT-003` broken and unsafe | V2 repeats file loading requirements | Remove | No final workflow. Approved strategy identifiers/handles enter through WF-OPT-002/004 adapter requests. |
| WF-OPT-009 | Background task registration | Cross-domain | `V1-WF-OPT-009` returns fake IDs only | Real task coordination, progress, polling, cancellation | Remove / Defer replacement | Delete V1 stubs after caller verification. A real execution gateway may be added later under WF-OPT-007/approved orchestration. |

### `WF-OPT-001` — Package an Optimization or Robustness Request

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Caller payload → `run_parameter_sweep` or a related wrapper → V1 may validate and then run a dry-run search that scores empty trades → response.
```

**V2 proposal:**

```text
Public tools are classified as packaging or lightweight calculation and must return a standard side-effect-free envelope.
```

**Final decision:**

```text
Replace the V1 dry-run sweep with true request packaging. Calculation-only tools still calculate; packaging tools never execute, persist, schedule, or call external systems.
```

**Reason:** This removes meaningless empty-trade scores and makes the public boundary honest.

### `WF-OPT-002` — Execute a Bounded Parameter Sweep

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Search algorithm → direct import of simulator engine/orchestrator → candidate execution → deal pairing → scoring. The orchestrator import is missing.
```

**V2 proposal:**

```text
Execution through a versioned adapter, bounded by an approved profile, with reproducibility and evidence.
```

**Final decision:**

```text
Replace direct imports with `BacktestExecutionAdapter`. Optimization owns candidate generation, deduplication, scoring, and summary; Simulation owns backtest execution.
```

**Reason:** It preserves the real business workflow while fixing the broken boundary with the smallest necessary interface.

### `WF-OPT-003` — Score, Rank, and Assess Overfit Evidence

**Scope:** `Internal`

**V1 behaviour:**

```text
Supplied trades/candidates → score functions → DSR/MTB → ranking/Pareto.
```

**V2 proposal:**

```text
Broader objective, trial-count, and anti-overfitting evidence.
```

**Final decision:**

```text
Preserve core metrics and deterministic ranking; correct invalid-input behavior and trial semantics; defer advanced topology/PBO gates.
```

**Reason:** The V1 calculations are proven, but V2 overextends them into unapproved institutional policy.

### `WF-OPT-004` — Walk-Forward Validation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Two implementations split windows, optimize train windows, evaluate OOS, and aggregate; dry-run is noninformative and real mode is broken.
```

**V2 proposal:**

```text
Rolling/anchored/expanding/custom modes, purging/embargo, WFE, CPCV/PBO.
```

**Final decision:**

```text
Create one WFA workflow with rolling and anchored/expanding modes, purging/embargo, and fold/WFE evidence. Defer custom/CPCV/PBO.
```

**Reason:** This removes duplication and keeps the smallest leakage-aware WFA needed for research.

### `WF-OPT-005` — Monte Carlo and Robustness Analysis

**Scope:** `Internal`

**V1 behaviour:**

```text
Supplied trades → shuffle/resample/skip/bootstrap → path, drawdown, ruin and stress summaries.
```

**V2 proposal:**

```text
Core and many specialized simulations plus prop-firm compliance gates.
```

**Final decision:**

```text
Preserve and harden core MC/stress behavior; add empirical return resampling/confidence intervals; defer specialized scenarios; reject prop-firm evaluation.
```

**Reason:** The core workflow has proven value, while specialized and Risk-owned requirements lack supporting workflows.

### `WF-OPT-006` — Build Versioned Evidence and Handoffs

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
No coherent V1 workflow; `save_optimization_result` falsely claims persistence and report helpers format or package partial data.
```

**V2 proposal:**

```text
Versioned handoffs to Risk Governor, Portfolio Manager, UI/reporting, and human review.
```

**Final decision:**

```text
Add one evidence assembler. It includes optimization-owned evidence and carries optional evidence supplied by other domains without making their decisions.
```

**Reason:** A single evidence package replaces misleading save/report wrappers and supports downstream review without recomputation.

### `WF-OPT-007` — Checkpoint, Resume, Cancel, and Progress

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Atomic checkpoint and in-memory repository utilities are manually called and disconnected from execution.
```

**V2 proposal:**

```text
Idempotent repository-backed lifecycle, cancellation, checkpoint intervals, retry and progress.
```

**Final decision:**

```text
Defer execution. Preserve schemas, corruption checks, and atomic-write safety as migration evidence; activate only after repository and execution-profile approval.
```

**Reason:** The behavior is valuable but production ownership and policies are unresolved.

### `WF-OPT-008` — Dynamic Strategy-File Optimization

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Filesystem path → execute module → missing registry → broken backtest adapter.
```

**V2 proposal:**

```text
V2 proposes retaining path loading and backtest-from-path.
```

**Final decision:**

```text
Remove. Use approved strategy identifiers or handles through the adapter.
```

**Reason:** Arbitrary code loading is unsafe, duplicated, and unnecessary.

### `WF-OPT-009` — Background Task Registration

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Generate UUID string → log → return; no task exists.
```

**V2 proposal:**

```text
Coordinate real background tasks with polling/progress.
```

**Final decision:**

```text
Remove V1 stubs and defer a real replacement until orchestration and repository contracts are approved.
```

**Reason:** Fake task IDs are worse than an explicit unsupported/deferred status.

## 8. Recommended Minimal Capability Structure

The package location is an open system decision. The capability-level structure below intentionally avoids a generic `helpers.py`, monolithic `models.py`, concrete repository adapters, task managers, and one folder per algorithm.

```text
optimization/
├── api/           # Intentional public registry, envelopes, request packages, lightweight tools
├── parameters/    # Parameter definitions, constraints, active parameters, provenance hashes
├── search/        # Bounded grid and seeded pseudo-random internal search
├── execution/     # Versioned BacktestExecutionAdapter contract and optimization result conversion
├── scoring/       # Core objectives, deterministic ranking, DSR and baseline overfit evidence
├── validation/    # Time-series splits and the single walk-forward workflow
├── robustness/    # Monte Carlo, stress calculations, and robustness summaries
├── evidence/      # Versioned evidence, report packages, and downstream handoffs
└── runs/          # Deferred run-state/checkpoint/repository contracts only
```

| Module | Capability | Source | Main decision |
| --- | --- | --- | --- |
| `api/` | Public contracts, packaging, lightweight calculations | Both | Modify/Add/Merge |
| `parameters/` | Parameter schemas, validation, constraints, hashing | Both | Modify |
| `search/` | Grid and pseudo-random search | Both | Modify |
| `execution/` | Backtest adapter contract | Both | Modify/Add |
| `scoring/` | Core scoring, ranking, DSR/MTB evidence | Both | Modify |
| `validation/` | Splits and walk-forward validation | Both | Merge/Modify |
| `robustness/` | Monte Carlo and stress analysis | Both | Modify |
| `evidence/` | Evidence/report/handoff contracts | V2 with V1 report reuse | Add/Merge |
| `runs/` | Run-state/checkpoint/repository protocols | Both | Defer |

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
| ---: | --- | --- | --- | --- |
| 1 | `ParameterRange`, `ParameterSpace` | Refactor | CAP-OPT-003 | Bounds/steps/types/condition cycles/size-limit tests; canonical serialization. |
| 2 | `check_constraints` AST validation | Reuse/Refactor | CAP-OPT-003 | Unsafe node/function tests; rejected-constraint evidence. |
| 3 | `parameter_space_hash`, `get_active_parameters`, `build_candidate_hash` | Refactor | CAP-OPT-003 | Order invariance; 8-decimal normalization; parameter-space hash inclusion; inactive exclusion. |
| 4 | `grid_search` and lazy grid generation | Refactor | CAP-OPT-004 | No full product materialization; bounded memory; evaluator injection; zero/too-many candidate handling. |
| 5 | `random_search` pseudo-random path | Refactor | CAP-OPT-004 | Seed reproducibility; distribution validation; no false Sobol/LHS metadata. |
| 6 | `run_strategy_backtest` / `EngineOptimizationResult` concepts | Replace integration / reuse result shape | CAP-OPT-005 | Adapter contract tests against Simulation; version mismatch; structured failures; no direct imports. |
| 7 | `scoring.py` core metrics and DSR | Refactor | CAP-OPT-006 | Known-value fixtures; invalid data; objective whitelist; nominal-trial semantics; independence warnings. |
| 8 | `rank_candidates` and `rank_parameter_sets` | Merge | CAP-OPT-006 | Tie ordering, missing/non-finite scores, no input mutation. |
| 9 | Rolling/expanding split functions | Refactor | CAP-OPT-007 | Invalid dates/folds; timezone behavior; purge/embargo boundaries; deterministic output. |
| 10 | Both WFA implementations | Replace with one merged workflow | CAP-OPT-008 | Train/OOS adapter fixtures; fold evidence; error propagation; no fake dry-run scores. |
| 11 | Trade shuffle/resample/bootstrap and `parametric_simulation` | Refactor | CAP-OPT-009 | Fixed-seed paths; empty/all-win/all-loss; intervals; seed provenance. |
| 12 | Spread/slippage/commission/skip stress functions | Refactor | CAP-OPT-010 | Validated cost units, malformed trades, public packaging versus internal calculation tests. |
| 13 | `optimization_tool_result`, context/business helpers | Refactor | CAP-OPT-001/002/018 | Golden envelopes; redaction; JSON safety; `places_trade=False`; no side effects. |
| 14 | Report and misleading save wrappers | Replace/Merge | CAP-OPT-011 | Evidence schema/golden fixtures; no recomputation; no persistence claim. |
| 15 | Checkpoint schema/atomic-write behavior | Refactor/Defer | CAP-OPT-012 | Corruption, traversal, atomic replacement, redacted errors; infrastructure boundary. |
| 16 | Repository ABC, in-memory repository, progress tracker | Split/Defer | CAP-OPT-012/013 | Move fixture out of production package; protocol compatibility; idempotency only when activated. |
| 17 | Bayesian wrapper | Remove | None / CAP-OPT-014 deferred | Caller search; migration notice; prove no evidence depends on false algorithm label. |
| 18 | Genetic algorithm | Archive/Defer | CAP-OPT-014 | Preserve deterministic test vectors before removal from initial package. |
| 19 | Dynamic strategy loading | Remove | None | External caller confirmation; Strategy/Simulation registry replacement available. |
| 20 | Task-ID stubs and unused scenario models | Remove | None / deferred capabilities | External caller/serialized-contract confirmation. |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
| --- | --- | --- |
| One public tool per stress, MC, cross-market, cross-timeframe, and OOS variation | Large repetitive API and envelope logic | Use a small number of typed method-based request packagers. |
| Algorithm-specific public execution wrappers | Conflicts with the public packaging milestone and duplicates one internal interface | Keep search engines internal; public sweep packages a request. |
| `service_strategy_class` plus dynamic file loading | Duplicates Strategy ownership and enables arbitrary code execution | Accept approved strategy references/handles at the adapter boundary. |
| Lazy package attribute resolution | Hides public surface and complicates debugging | Use explicit exports and narrow compatibility aliases only when proven necessary. |
| Generic `helpers.py` and monolithic `models.py` | Unrelated responsibilities and accidental public API | Colocate private helpers and contracts with each capability module. |
| True Bayesian, genetic, Sobol, LHS, Optuna, and skopt in the initial rebuild | No demonstrated current workflow; optional dependency and evidence complexity | Ship grid and seeded pseudo-random baseline; defer advanced methods. |
| `100,000+` universal grid guarantee | Numeric claim lacks an approved memory profile and V1 parallel queue is not truly bounded | Require lazy iteration and an approved benchmark/budget before production claims. |
| Duplicate WFA wrappers and implementations | Divergent behavior and response/error contracts | One internal WFA workflow plus public request packaging. |
| Custom folds, CPCV, and PBO immediately | Advanced research capability with unapproved thresholds | Keep rolling/anchored/expanding WFA; defer CPCV/PBO. |
| Full specialized scenario suite | Mostly unused V1 schemas and no workflow evidence | Keep core MC/parametric behavior; defer each specialized scenario individually. |
| Prop-firm rule evaluation inside optimization | Risk ownership violation | Optimization carries Risk-produced compliance evidence only. |
| Portfolio weight optimization and capacity calculation | Portfolio ownership violation and no V1 behavior | Move to Portfolio; optimization provides candidate evidence only. |
| Broad `ExecutionOrchestrator` plus early stopping/pruning/distributed backends | Premature platform layer and unresolved persistence/resource policy | Defer; later use the smallest injected executor contract justified by workflows. |
| Background task functions now | V1 stubs create false task references; no queue/lifecycle approved | No public task API until a real execution gateway exists. |
| Concrete repository backend matrix in optimization | Violates persistence boundary and creates infrastructure coupling | Own schemas/protocols only; infrastructure supplies approved adapters. |
| Every institutional evidence field mandatory | Many fields are unavailable, deferred, or owned by other domains | Versioned baseline evidence with optional typed extensions. |
| Direct report formatting/plotting | Presentation belongs to reporting/UI | Provide report packages and chart-ready raw series/tables. |
| Standalone speedup, CPU-count, and ETA helpers | No business workflow and infrastructure concern | Use execution/observability infrastructure when needed. |
| Preserve all V1 signatures for compatibility | Would freeze accidental 151-name facade | Preserve only approved V2 public contracts; verify external callers before removals. |
| Fixed production limits and benchmarks embedded now | Owner/environment decisions are pending | Fail closed; record open decisions and approve profiles before execution. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities | Escalation |
| --- | --- | --- | --- | --- | --- |
| Open | Final package/import path | V1 uses `app.services.optimization`; V2 target tree uses `tools/optimization`; API text still names the V1 path. | Retain V1 path; move to tools with compatibility alias; approved new path | `CAP-OPT-001..018` | System-level; add to top-level Open Decisions in step 05. |
| Open | Approved public tool contract matrix | V2 marks current tools experimental but signatures/examples conflict with V1 shapes. | Approve names/signatures/status/error schema; version or alias selected legacy names | `CAP-OPT-001..002` | Shared API contract; top-level/ADR. |
| Open | Confirmed external V1 callers and compatibility obligations | V1 audit found no production caller but repository-wide indexed search was unavailable. | Remove accidental exports; temporary deprecation aliases; preserve selected calls | `CAP-OPT-001,014,017` | Domain + release decision. |
| Open | Simulation adapter entry point and version policy | V1 direct imports are missing; V2 proposes `BacktestExecutionAdapter` without a finalized contract. | Simulation-owned implementation with protocol; shared execution contract | `CAP-OPT-005,008` | Cross-domain Simulation; top-level/ADR. |
| Open | Execution resource profile | V2 lists pending max candidates, expansion, runtime, workers, simulations, objective whitelist, payload size, and override owner. | Research-only defaults; multiple trust profiles; no execution until approved | `CAP-OPT-004..010,013` | System-level; top-level Deferred/Open Decisions. |
| Open | Memory and performance acceptance budgets | V2 proposes 100k grids and several throughput values; V1 tests were not run and parallel pending queue is flawed. | Approve benchmark environment/targets; behavior-only acceptance initially | `CAP-OPT-003..004,012` | Owner/architecture decision. |
| Open | Repository backend, artifact root, transaction/atomic-write owner, and retry policy | V1 local helpers work; V2 explicitly leaves backend/ownership pending. | No persistence; local research profile; infrastructure-owned adapter | `CAP-OPT-012..013` | Cross-domain infrastructure; top-level/ADR. |
| Open | Evidence/report schema version and shared handoff contracts | V2 requires versioning but no approved schema version or downstream contract exists. | Optimization evidence v1; shared research evidence contract; per-consumer extensions | `CAP-OPT-011` | Risk/Portfolio/UI cross-domain; top-level/ADR. |
| Open | PBO/CPCV thresholds and ownership | V2 proposes values but states risk-owner approval is pending. | Defer entirely; research-only informational PBO; approved profile thresholds | `CAP-OPT-006..008,014` | Risk/Research cross-domain; top-level decision. |
| Open | Optional sampler/optimizer dependency policy | V1 placeholders are not real implementations; V2 dependency versions are pending. | No optional algorithms; approve SciPy QMC only; approve Optuna/skopt backend | `CAP-OPT-014` | Architecture/dependency decision. |
| Open | Whether genetic search has enough workflow value to retain later | V1 has a deterministic loop but no production caller and broken real execution. | Archive/remove; future internal experimental; approve roadmap capability | `CAP-OPT-014` | Domain-internal unless exposed publicly. |
| Open | Which specialized scenario simulations are actually required | V1 has parametric behavior and unused schemas; V2 proposes five additional suites. | Defer all; approve named subset tied to research workflows | `CAP-OPT-015` | Domain roadmap; cross-domain if sizing/portfolio-related. |

**Escalation note:** Cross-domain/system-shape decisions and deferrals are identified above but were not written into the top-level system document because that document was not an allowed input or output for this step. They must be copied into the top-level Open Decisions or Deferred Capabilities sections during pipeline step 05 and resolved there with ADRs where required.

## 12. Inputs for the Final Domain README

### Approved capabilities

* Intentional public optimization registry and standard non-trading envelope.
* Validated request packaging and lightweight stability/overfit/ranking/robustness calculations.
* Typed parameter spaces, safe constraints, executable-parameter filtering, and canonical hashes.
* Internal bounded grid and seeded pseudo-random search.
* Versioned backtest execution adapter contract and optimization-facing result conversion.
* Core scoring, deterministic ranking, DSR/nominal-trial evidence, and baseline overfit warnings.
* Validated rolling and anchored/expanding splits with purging/embargo.
* One internal walk-forward validation workflow plus public packaging.
* Core Monte Carlo, parametric simulation, and execution-cost robustness analysis.
* Versioned optimization evidence, report packages, and chart-ready handoffs.

### Approved workflows

* `WF-OPT-001` Package an optimization or robustness request.
* `WF-OPT-002` Execute a bounded parameter sweep through the Simulation adapter.
* `WF-OPT-003` Score, rank, and assess overfit evidence.
* `WF-OPT-004` Run walk-forward validation.
* `WF-OPT-005` Run Monte Carlo and robustness analysis over supplied results.
* `WF-OPT-006` Build versioned downstream evidence and handoffs.

### V1 behaviours to preserve

* Parameter boundary/type validation and AST-blocked constraint evaluation (`V1-CAP-OPT-001`).
* Conditional-aware canonical parameter/candidate hashing (`V1-CAP-OPT-002`).
* Lazy grid generation and seeded pseudo-random generation (`V1-CAP-OPT-003..004`).
* Core scores, max drawdown, DSR, ranking/Pareto concepts (`V1-CAP-OPT-009`).
* Rolling/expanding split construction (`V1-CAP-OPT-010`).
* Trade shuffle/resample/bootstrap, stress transformations, and parametric simulation (`V1-CAP-OPT-012,013,019`).
* Checkpoint corruption/path/atomic-write safety semantics (`V1-CAP-OPT-014`) as deferred infrastructure evidence.

### V1 behaviours to modify

* Replace empty-trade dry-run scoring with honest request packaging or an injected evaluator.
* Replace direct simulator imports and hard-coded adapter versions with a versioned protocol.
* Merge duplicate WFA, ranking, Monte Carlo wrapper, and report/save surfaces.
* Unify response/error/serialization behavior and use deterministic `OPT_` codes.
* Correct sampler and Bayesian claims; never silently treat pseudo-random as advanced sampling.
* Separate public packaging from internal calculations and execution.

### V1 behaviours to remove

* Bayesian-labelled random search after external caller verification.
* Dynamic arbitrary strategy-file loading and backtest-from-path.
* Fake background task IDs.
* Misleading `saved=True` wrapper and direct Markdown formatting as domain responsibilities.
* Unused unsupervised, specialized scenario, and portfolio schemas unless a capability is later approved.
* Accidental root exports after approved public-contract and caller review.

### V2 behaviours to add

* Narrow intentional registry with capability stability/behavior metadata.
* Capability-specific validated request packages with context/business separation.
* Versioned `BacktestExecutionAdapter` contract.
* Versioned evidence and chart-ready handoff packages.
* Empirical return resampling, probability-of-ruin, and confidence-interval helpers.
* Explicit provenance, caveats, no-live-authority metadata, and structured dependency errors.

### V2 proposals to reject or defer

* Reject lazy attribute magic and public compute wrappers.
* Reject dynamic file loading, portfolio optimization, and prop-firm rule evaluation in optimization.
* Merge many robustness/MC/OOS public wrappers into method-based packagers.
* Defer true Bayesian/genetic/Sobol/LHS/Optuna/skopt support.
* Defer CPCV/PBO/topology/effective-trial gates and unapproved thresholds.
* Defer background/parallel orchestration, pruning, cancellation, repositories, and distributed backends.
* Defer specialized position-sizing, streak, target, random-pair, and multi-entry simulations.
* Simplify institutional evidence to a versioned baseline with optional extensions.

### Required open decisions before README completion

* Final package path and compatibility alias policy.
* Approved public tool names, signatures, statuses, and shared envelope schema.
* Simulation adapter contract and versioning.
* External V1 caller/compatibility evidence.
* Execution limits/objective whitelist/resource profiles.
* Evidence schema version and downstream handoff contracts.
* Repository/artifact ownership if deferred run lifecycle is mentioned.

## 13. Final Reconciliation Checklist

* [x] every V1 capability received a disposition.
* [x] every V2 ownership, API, functional, non-functional, edge-case, and test requirement received a disposition.
* [x] every V1 workflow was reconciled.
* [x] every proposed V2 workflow was reconciled at capability/workflow level.
* [x] confirmed working V1 behaviour was not discarded without reason.
* [x] unused V1 behaviour was not preserved without reason.
* [x] V2 implementation complexity was not accepted automatically.
* [x] the proposed direction follows the four-level minimal structure.
* [x] capabilities suspected to belong to another domain are flagged for step 05.
* [x] unresolved conflicts are listed under Open Decisions.
* [x] cross-domain open decisions/deferrals are explicitly marked for top-level escalation.
* [x] no code was inspected, changed, or generated in this reconciliation step.
* [x] neither source document was modified.
* [x] the output is sufficient to draft the final domain README once listed blocking open decisions are resolved.

**Top-level escalation status:** Identified but not applied in this step because the top-level system document was outside the permitted inputs and output. Pipeline step 05 must copy and resolve the marked cross-domain/system-shape items.


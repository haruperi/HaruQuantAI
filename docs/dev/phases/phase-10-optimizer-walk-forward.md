# P10 — Optimizer: parameter search, sequential modes, walk-forward and matrix

- **Source:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`; SHA-256 `9abec0aa2faf6bd78b39e80c2dcfb7dfcae62ae412d9b56a77904de6a7b5a54c`.
- **Dependencies:** P06,P08,P09.
- **Scope:** 10 JAR feature tasks, 0 resource tasks, one phase integration task.
- **State:** proposed checklists; all execution, registrations and target contracts require task-level approval.
- **File labels:** existing paths are Modify; absent paths are Create; later shared edits name their earlier proposed owner.
- **Execution standard:** AGENTS.md plan → approval → implementation → tests → walkthrough; canonical Python docstrings, typed public APIs and explicit FR logs.
- **Clean room:** donor signatures guide behavioral research; independently written implementations; no proprietary source in evidence; no parity claim without independent validation.
- **Verification:** commands below are future tasks, not reported passes; isolated stores only; no live-store schema change/restore or Git mutation.

# 10.1 FEAT-OPTIMIZER-APP-OPTIMIZER - AppOptimizer.jar

## 1. Objective

- **Goal:** Mount the Optimizer workspace against real backend capabilities.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar`; 1 class declarations; SHA-256 `9f684b0cad7d363472a82907f07c9ea33b8ff45b2a10036d47ce80e58dc6e3e1`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Optimizer/AppOptimizer.md`; roadmap allocation `FEAT-OPTIMIZER-APP-OPTIMIZER`.
- **Owner:** `app/workspace/Optimizer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Workspace/product registration and backend composition; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/AppOptimizer/AppOptimizer.jar" com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/workspace/Optimizer/workspace.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/workspace/Optimizer/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_app_optimizer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_app_optimizer.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Mount the Optimizer workspace against real backend capabilities; verify discovery, workspace readiness, job/resource ownership and unmount cleanup.
- [ ] **Step 4:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-CONTRACT` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-APP-OPTIMIZER-OPTIMIZER-APP-PLUGIN-INIT-PLUGIN` → `com.strategyquant.plugin.App.impl.Optimizer.OptimizerAppPlugin.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_app_optimizer.py --no-cov`; expect discovery, workspace readiness, job/resource ownership and unmount cleanup; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture discovery, workspace readiness, job/resource ownership and unmount cleanup and visible failures.

# 10.2 FEAT-OPTIMIZER-FITNESS-METHOD-WF-RESULT - FitnessMethodWFResult.jar

## 1. Objective

- **Goal:** Compute the named fitness objective from qualified result inputs.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar`; 3 class declarations; SHA-256 `67db6d1897747953524e8c79b180e1a0566599d337026aea8885d0cf6f3017fa`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/FitnessMethodWFResult.md`; roadmap allocation `FEAT-OPTIMIZER-FITNESS-METHOD-WF-RESULT`.
- **Owner:** `app/plugins/optimization/FitnessMethodWFResult/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/FitnessMethodWFResult/FitnessMethodWFResult.jar" com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/FitnessMethodWFResult/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/FitnessMethodWFResult/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_fitness_method_wf_result.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_fitness_method_wf_result.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Compute the named fitness objective from qualified result inputs; verify objective direction, ties, missing metrics and nonfinite scores.
- [ ] **Step 4:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WF-RESULT-CONTRACT` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WF-RESULT-GET-PREFERRED-POSITION` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult.getPreferredPosition`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-FITNESS-METHOD-WF-RESULT-FITNESS-METHOD-WF-RESULT-INIT-PLUGIN` → `com.strategyquant.plugin.FitnessMethod.impl.WFResult.FitnessMethodWFResult.initPlugin`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_fitness_method_wf_result.py --no-cov`; expect objective direction, ties, missing metrics and nonfinite scores; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture objective direction, ties, missing metrics and nonfinite scores and visible failures.

# 10.3 FEAT-OPTIMIZER-PROJECT-OPTIMIZER - ProjectOptimizer.jar

## 1. Objective

- **Goal:** Implement Optimizer project capabilities with owned lifecycle.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ProjectOptimizer/ProjectOptimizer.jar`; 0 class declarations; SHA-256 `a1bbc8087afb5abee155219a6f6972aea37606fb790bfdd3c121a81aa31c1e3b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/ProjectOptimizer.md`; roadmap allocation `FEAT-OPTIMIZER-PROJECT-OPTIMIZER`.
- **Owner:** `app/plugins/optimization/ProjectOptimizer/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ProjectOptimizer/ProjectOptimizer.jar"`; inspect manifest/resources and target runtime requirements.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ProjectOptimizer/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ProjectOptimizer/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ProjectOptimizer/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ProjectOptimizer/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_project_optimizer.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_project_optimizer.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement Optimizer project capabilities with owned lifecycle; verify project revisions, input/output contracts, failed transitions and cancellation.
- [ ] **Step 4:** `FR-OPTIMIZER-PROJECT-OPTIMIZER-RESOURCE-CONTRIBUTION` → `No compiled class entries; inspect registration/resources`: Verify the resource/manifest contract.
- [ ] **Step 5:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 6:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_project_optimizer.py --no-cov`; expect project revisions, input/output contracts, failed transitions and cancellation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture project revisions, input/output contracts, failed transitions and cancellation and visible failures.

# 10.4 FEAT-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE - ResultsOptimizationProfile.jar

## 1. Objective

- **Goal:** Implement parameter profile/permutation sampling and projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar`; 12 class declarations; SHA-256 `f3fbf5808631df75cf45cdac71080efb9b1c05dfb5d0d800b4fd56a56cd4c62f`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsOptimizationProfile.md`; roadmap allocation `FEAT-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE`.
- **Owner:** `app/plugins/optimization/ResultsOptimizationProfile/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsOptimizationProfile/ResultsOptimizationProfile.jar" com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsOptimizationProfile/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_optimization_profile.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_optimization_profile.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement parameter profile/permutation sampling and projections; verify range endpoints, enumeration order and matrix/result reconciliation.
- [ ] **Step 4:** `FR-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE-OPTIMIZATION-PROFILE-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-RESULTS-OPTIMIZATION-PROFILE-OPTIMIZATION-PROFILE-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.OptimizationProfile.OptimizationProfileServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_optimization_profile.py --no-cov`; expect range endpoints, enumeration order and matrix/result reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture range endpoints, enumeration order and matrix/result reconciliation and visible failures.

# 10.5 FEAT-OPTIMIZER-RESULTS-PROFILE-CHART - ResultsProfileChart.jar

## 1. Objective

- **Goal:** Project the named result series with verified metrics and sampling.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar`; 2 class declarations; SHA-256 `1c0cbb510a72e0b4515803886440ce10c11a6173b9e1ee9b8de46fa7feec84cd`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsProfileChart.md`; roadmap allocation `FEAT-OPTIMIZER-RESULTS-PROFILE-CHART`.
- **Owner:** `app/plugins/optimization/ResultsProfileChart/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsProfileChart/ResultsProfileChart.jar" com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsProfileChart/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsProfileChart/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_profile_chart.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_profile_chart.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Project the named result series with verified metrics and sampling; verify units, timestamp alignment, missing samples and reconciled source totals.
- [ ] **Step 4:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-DO-GET` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet.doGet`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-RESULTS-PROFILE-CHART-PROFILE-CHART-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.ProfileChart.ProfileChartServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_profile_chart.py --no-cov`; expect units, timestamp alignment, missing samples and reconciled source totals; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture units, timestamp alignment, missing samples and reconciled source totals and visible failures.

# 10.6 FEAT-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION - ResultsSequentialOptimization.jar

## 1. Objective

- **Goal:** Implement sequential parameter-search ordering and result retention.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar`; 2 class declarations; SHA-256 `5f8e06aac5494fa88fa6c3f416de208005b056216002cd964e81441714716d5b`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsSequentialOptimization.md`; roadmap allocation `FEAT-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION`.
- **Owner:** `app/plugins/optimization/ResultsSequentialOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSequentialOptimization/ResultsSequentialOptimization.jar" com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSequentialOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_sequential_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_sequential_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement sequential parameter-search ordering and result retention; verify candidate dependencies, repeated passes, stopping and score ordering.
- [ ] **Step 4:** `FR-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-RESULTS-SEQUENTIAL-OPTIMIZATION-SEQUENTIAL-OPTIMIZATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SequentialOptimization.SequentialOptimizationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 7:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_sequential_optimization.py --no-cov`; expect candidate dependencies, repeated passes, stopping and score ordering; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture candidate dependencies, repeated passes, stopping and score ordering and visible failures.

# 10.7 FEAT-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION - ResultsSysParamPermutation.jar

## 1. Objective

- **Goal:** Implement parameter profile/permutation sampling and projections.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar`; 2 class declarations; SHA-256 `c3758eff4b80cc64109fb9f90e44fac51e9f019696d5e21e5c99ad520b82c0bf`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsSysParamPermutation.md`; roadmap allocation `FEAT-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION`.
- **Owner:** `app/plugins/optimization/ResultsSysParamPermutation/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsSysParamPermutation/ResultsSysParamPermutation.jar" com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsSysParamPermutation/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_sys_param_permutation.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_sys_param_permutation.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement parameter profile/permutation sampling and projections; verify range endpoints, enumeration order and matrix/result reconciliation.
- [ ] **Step 4:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-RESULTS-SYS-PARAM-PERMUTATION-SYS-PARAM-PERMUTATION-SERVLET-LOAD-LAST-SETTINGS` → `com.strategyquant.plugin.Results.impl.SysParamPermutation.SysParamPermutationServlet.loadLastSettings`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_sys_param_permutation.py --no-cov`; expect range endpoints, enumeration order and matrix/result reconciliation; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture range endpoints, enumeration order and matrix/result reconciliation and visible failures.

# 10.8 FEAT-OPTIMIZER-RESULTS-WALK-FORWARD - ResultsWalkForward.jar

## 1. Objective

- **Goal:** Implement the named walk-forward partition/result contract.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar`; 5 class declarations; SHA-256 `f6ac8d923375b7997431ac365e906e232bd7dc554601ba9cd98ed15c28e6abea`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Results/ResultsWalkForward.md`; roadmap allocation `FEAT-OPTIMIZER-RESULTS-WALK-FORWARD`.
- **Owner:** `app/plugins/optimization/ResultsWalkForward/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/ResultsWalkForward/ResultsWalkForward.jar" com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/ResultsWalkForward/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/ResultsWalkForward/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_results_walk_forward.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_results_walk_forward.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement the named walk-forward partition/result contract; verify in/out-of-sample boundaries, leakage rejection, aggregation and tie rules.
- [ ] **Step 4:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-CONTRACT` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-EXECUTE` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-RESULTS-WALK-FORWARD-WALK-FORWARD-SERVLET-PRINT-HTML-FORMATED-VALUE` → `com.strategyquant.plugin.Results.impl.WalkForward.WalkForwardServlet.printHtmlFormatedValue`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_results_walk_forward.py --no-cov`; expect in/out-of-sample boundaries, leakage rejection, aggregation and tie rules; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture in/out-of-sample boundaries, leakage rejection, aggregation and tie rules and visible failures.

# 10.9 FEAT-OPTIMIZER-SETTINGS-OPTIMIZATION - SettingsOptimization.jar

## 1. Objective

- **Goal:** Implement validated Optimization settings and lossless configuration round trips.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar`; 2 class declarations; SHA-256 `4bd3b12f7d40c41489b58ac67e6d90191080825446921bd0373a11c74a7eb40d`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Shared/SettingsOptimization.md`; roadmap allocation `FEAT-OPTIMIZER-SETTINGS-OPTIMIZATION`.
- **Owner:** `app/plugins/optimization/SettingsOptimization/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/SettingsOptimization/SettingsOptimization.jar" com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/SettingsOptimization/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/SettingsOptimization/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_settings_optimization.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_settings_optimization.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Implement validated Optimization settings and lossless configuration round trips; verify observed defaults, dependency validation, unknown fields, update conflicts and reload.
- [ ] **Step 4:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-CONTRACT` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-GET-INSTANCE` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet.getInstance`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-SETTINGS-OPTIMIZATION-OPTIMIZATION-SERVLET-EXECUTE` → `com.strategyquant.plugin.Settings.impl.Optimization.OptimizationServlet.execute`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_settings_optimization.py --no-cov`; expect observed defaults, dependency validation, unknown fields, update conflicts and reload; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture observed defaults, dependency validation, unknown fields, update conflicts and reload and visible failures.

# 10.10 FEAT-OPTIMIZER-TASK-OPTIMIZE - TaskOptimize.jar

## 1. Objective

- **Goal:** Execute Optimize through an owned typed task capability.
- **Context / Problem Solved:** This roadmap feature supports the phase workflow: Optimize strategy parameters and calculate walk-forward/profile results.

## 2. Research and donors

- **Donor:** `SQX_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar`; 10 class declarations; SHA-256 `9ca3f14b146b90fbe431f341cb0d9cf3528ff8c8fa3f7d8ddbfcd7511b409e69`.
- **Inspected reference:** `HARUQUANTAI_ROOT/docs/sqx/Optimizer/TaskOptimize.md`; roadmap allocation `FEAT-OPTIMIZER-TASK-OPTIMIZE`.
- **Owner:** `app/plugins/optimization/TaskOptimize/README.md`; proposed IDs require registry reconciliation.
- **Consumed role:** Optimization/WF modes, metrics, results and task/config adapters; downstream .
- **Research command:** `jar tf "$SQX_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar"`; `javap -public -classpath "$SQX_REFERENCE_ROOT/internal/plugins/TaskOptimize/TaskOptimize.jar" com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask`.
- **Gap:** seeds are incomplete; inspect remaining consumed symbols and official docs.
- **Boundary:** domain contracts; host-owned jobs/resources/storage.

## 3. File Changes

- **Create:** `app/plugins/optimization/TaskOptimize/service.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/contracts.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/routes.py`
  - Implement this feature's consumed typed contracts.
- **Create:** `app/plugins/optimization/TaskOptimize/README.md`
  - Own approved feature/FR/decision mappings and status.
- **Create:** `tests/unit/sqx_features/test_optimizer_task_optimize.py`
  - Verify behavior, failures and FR logs.
- **Create:** `tests/reference/sqx_features/optimizer_task_optimize.json`
  - Store versioned paraphrased donor input/output fixtures.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Enumerate/fingerprint classes, consumed calls, resources and registration.
- [ ] **Step 2:** Specify defaults/I/O/errors, classify evidence and approve contracts before coding.
- [ ] **Step 3:** Execute Optimize through an owned typed task capability; verify input handles, start/stop/clone transitions, failure status and retained outputs.
- [ ] **Step 4:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-CONTRACT` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask`: Define typed state, lifecycle and errors.
- [ ] **Step 5:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-GET-TYPE` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask.getType`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 6:** `FR-OPTIMIZER-TASK-OPTIMIZE-OPTIMIZE-TASK-CLONE` → `com.strategyquant.plugin.Task.impl.Optimize.OptimizeTask.clone`: Specify/test inputs, defaults, outputs, side effects and errors.
- [ ] **Step 7:** Wire owned routes/events/discovery; expose unavailable states.
- [ ] **Step 8:** Test semantics, failures, FR logs/redaction and qualified donor comparisons.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/unit/sqx_features/test_optimizer_task_optimize.py --no-cov`; expect input handles, start/stop/clone transitions, failure status and retained outputs; use temporary resources.
- **Manual / Browser Verification:** Use the phase workflow; capture input handles, start/stop/clone transitions, failure status and retained outputs and visible failures.

# 10.11 P10 integration — Optimize strategy parameters and calculate walk-forward/profile results

## 1. Objective

- **Goal:** Optimize strategy parameters and calculate walk-forward/profile results.
- **Context / Problem Solved:** The existing UI needs a real end-to-end backend workflow, beyond isolated JAR adapters.

## 2. Research and donors

- **Roadmap:** `HARUQUANTAI_ROOT/docs/dev/sqx-full-application-roadmap.md`, P10; donor features and FRs are the tasks in this file.
- **Existing code:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`; backend counterparts are proposed.
- **Declared dependencies:** numpy, pandas, polars, pyarrow; new numerical/training packages remain unapproved.
- **Existing tests:** `ui/tests/unit/workspace/Optimizer/optimizerModes.test.ts`; extend actual-backend assertions.
- **Conflict/gap:** frontend existence does not establish functional backend behavior; route/schema/discovery changes need a task plan and approval.
- **Cross-feature ownership:** shared files may host multiple features; keep per-FR traces and delegate persistence/jobs to host capabilities.

## 3. File Changes

- **Modify:** `app/workspace/Optimizer/workspace.py` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `app/workspace/Optimizer/routes.py` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/search.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/parameters.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/walk_forward.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Create:** `app/plugins/optimization/matrix.py`
  - Deliver the phase's typed contracts and integration flow; extend prior approved owners where shared.
- **Modify:** `ui/app/workspace/Optimizer/OptimizerWorkspace.tsx`
  - Bind real capability state, errors and cancellation while preserving the existing layout.
- **Modify:** `ui/app/workspace/Optimizer/optimizerClient.ts`
  - Own typed routes/envelopes for this domain; replace mock execution with authoritative requests.
- **Modify:** `app/workspace/Optimizer/README.md` (proposed earlier in FEAT-OPTIMIZER-APP-OPTIMIZER)
  - Own feature registration/status and phase contract decisions after ratification.
- **Create:** `tests/integration/test_optimizer_walk_forward_workflow.py`
  - Exercise the real phase workflow in isolated stores with failure/cancellation assertions.
- **Create:** `ui/tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`
  - Use an isolated real host to verify UI state and request/output reconciliation.

## 4. Step-by-Step Task Breakdown

- [ ] **Step 1:** Review preceding feature fixtures and owning README registrations; ratify the phase integration contracts and execution plan.
- [ ] **Step 2:** Specify parameter ranges, candidate order, objective/ties, sequential rules and WF partitions.
- [ ] **Step 3:** Implement simple/sequential/profile/matrix search with isolated in/out-of-sample windows.
- [ ] **Step 4:** Connect Optimizer settings, progress and result projections to real reusable runs.
- [ ] **Step 5:** Replace fixture-driven production execution in the affected workflow; retain deterministic fixtures only in tests.
- [ ] **Step 6:** Test positive/failure/cancellation paths and observable FR logs; reload/reconnect and reconcile persisted outputs.
- [ ] **Step 7:** Record exact commands, timestamped artifacts, unresolved gaps and walkthrough; obtain separate owner commit authority.

## 5. Verification & Testing

- **Automated Tests:** `uv run pytest tests/integration/test_optimizer_walk_forward_workflow.py --no-cov`; `npm --prefix ui run test -- tests/unit/workspace/Optimizer/optimizerModes.test.ts`; `npm --prefix ui run test:ui -- tests/e2e/sqx-optimizer-walk-forward-backend.spec.ts`. Assert candidate enumeration, objective ordering, WF window boundaries and matrix reconciliation; reject empty range, invalid partition, data leakage, tied score and cancellation.
- **Manual / Browser Verification:** Run a small parameter grid; inspect each candidate; run a WF matrix; confirm out-of-sample rows and repeatability.

## Phase completion gate

- [ ] Reconcile all allocated FEAT/FR dispositions, donor fixtures and ownership gaps.
- [ ] Run Ruff format/check and strict Mypy on the approved changed Python paths; verify branch-aware coverage ≥80% across retained application source at release.
- [ ] For affected UI: `npm --prefix ui run typecheck`, `npm --prefix ui run test`, `npm --prefix ui run build`.
- [ ] Record real workflow observations, timestamps, failure artifacts and remaining gaps in the walkthrough.
- [ ] Obtain the next task/phase approval; commits and external/destructive actions retain separate owner gates.

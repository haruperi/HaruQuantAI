# Agentic Rebuild — Phase 6 Sandbox and Calibration

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

### AGT-6.19 — `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS` — Sandboxed Source Artifact Fallback

**Goal:** As an explicit fallback after a validated DSL gap, author and test source artifacts in an attested staging sandbox; capture files, hashes, dependencies, SBOM, tests, search history, provenance, and cleanup. Generated code is never hot-loaded.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.06`, `AGT-5.16`.
**Phase-0 blockers that must already be closed:** P0.4 real sandbox/isolation provider; P0.7 DSL-gap proof contract; P0.2 hybrid retention representation.
**Provides:** `agentic.sandbox-artifacts@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.workflows@1`, `agentic.operations@1`, `agentic.strategy-specs@1`.
**Optional capabilities:** —.
**External prerequisites:** `plugins.sandbox@1 (proposed owner key)`, `workspace.artifact-staging@1 (proposed owner key)`, `workspace.static-analysis@1 (proposed owner key)`.
**State:** PROVISIONAL: namespace `agentic.sandbox_artifacts`, schema version `1`; retain metadata and clean bytes through business policy using a Kernel-supported state retention enum.
**Role contributions:** `sandbox_code_author`.
**Primary method:** `AgenticSandboxArtifactAuthoring.author_sandbox_artifacts(request)`.
**Operations:** `AUTHOR`, `INSPECT`, `CLEANUP`.
**Success/domain outcomes:** `SandboxArtifactReceipt`, `SandboxArtifactView`, `SandboxCleanupReceipt`.
**Events:** `SandboxArtifactStaged`, `SandboxArtifactCleaned`.

**Normalized donor bundle inputs**

- `app/agentic/agents/engineering/coder/**`
- `tests/agentic/unit/test_coder.py`
- `tests/agentic/integration/test_code_artifact.py`
- `tests/agentic/usage/16_coding.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/sandbox_artifacts.py
app/services/agentic/author_sandbox_artifacts/README.md
app/services/agentic/author_sandbox_artifacts/__init__.py
app/services/agentic/author_sandbox_artifacts/manifest.py
app/services/agentic/author_sandbox_artifacts/config.py
app/services/agentic/author_sandbox_artifacts/feature.py
app/services/agentic/author_sandbox_artifacts/sandbox_artifact_authoring.py
app/services/agentic/author_sandbox_artifacts/dsl_gap_validation.py
app/services/agentic/author_sandbox_artifacts/sandbox_lease.py
app/services/agentic/author_sandbox_artifacts/artifact_manifest.py
app/services/agentic/author_sandbox_artifacts/cleanup.py
app/services/agentic/author_sandbox_artifacts/migrations.py
app/services/agentic/author_sandbox_artifacts/_store.py
app/services/agentic/author_sandbox_artifacts/roles/sandbox_code_author/role.json
app/services/agentic/author_sandbox_artifacts/roles/sandbox_code_author/prompt.md
tests/contracts/agentic/test_sandbox_artifacts.py
tests/services/agentic/author_sandbox_artifacts/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/sandbox_artifacts.py` with the exact capability key `agentic.sandbox-artifacts@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `sandbox_profile_id`, `max_files`, `max_bytes`, `max_cpu_seconds`, `max_memory_mb`, `network_policy`, `allowed_languages`, `staging_retention_days`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Require a validated DSL-gap report, authenticated exact code specification, typed human action where policy requires it, and a real attested sandbox lease.
- [ ] Bind the lease to ephemeral, credential-free, network-denied/allowlisted, CPU/memory/storage/time-bounded, staging-only execution.
- [ ] Validate every raw path before parsing and every resolved path after resolution; reject traversal, absolute/drive/UNC/device paths, reserved names, and symlink escape.
- [ ] Record files/digests, dependencies and sources, SBOM, tests/results, static analysis, prompt/model/tool lineage, complete search history, specification digest, and cleanup receipt.
- [ ] Never import, hot-load, register, deploy, or execute generated code in the production application. Output is staged for receiver/human review only.
- [ ] Retain audit metadata while cleaning ephemeral/staged bytes according to the P0.2 state decision and Workspace artifact policy.

**Owned functional requirements**

- [ ] **FR-AGT-PROVE_DSL_GAP** — Require a validated receiver-owned unsupported-expression report for the approved requirement before source generation can begin. Side effects: Read-only receipt validation. Evidence: Missing, changed, forged, expired, and overbroad gap tests.
- [ ] **FR-AGT-AUTHOR_SANDBOX_ARTIFACTS** — Require authenticated specification and a lease attesting ephemeral isolation, credential absence, staging-only writes, bounded resources, and denied or allowlisted egress before any model call or file write. Side effects: External model call and sandbox/staging writes. Evidence: Lease, symlink/path, credential, egress, resource, and pre-call gating tests.
- [ ] **FR-AGT-RECORD_ARTIFACT_MANIFEST** — Record every file path/hash, dependency/SBOM item, test/static-analysis result, prompt/model/tool provenance, complete search history, and aggregate manifest digest. Side effects: Metadata persistence. Evidence: Manifest completeness, tamper, path, dependency, and reproducibility tests.
- [ ] **FR-AGT-ENFORCE_STAGING_ONLY** — Never import, execute in the application process, register, deploy, or mutate the repository/production runtime directly; accepted use requires receiver-owned intake. Side effects: Sandbox execution only. Evidence: Import, repository write, runtime load, deployment, and receiver-boundary negative tests.
- [ ] **FR-AGT-CLEANUP_SANDBOX_ARTIFACTS** — Release sandbox resources and staged bytes according to owner retention while preserving required immutable metadata and cleanup evidence. Side effects: Resource cleanup and cleanup-record write. Evidence: Cancellation, failure, replacement, LIFO cleanup, and physical-removal tests.

**Mandatory focused tests**

- [ ] DSL-gap proof.
- [ ] lease/isolation attestation.
- [ ] credential/network/resource controls.
- [ ] path traversal/symlink attacks.
- [ ] SBOM/test/search history.
- [ ] no import/hot-load/deploy.
- [ ] timeout/cancel/cleanup.
- [ ] mid-generation removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS`.

**Executable usage:** `uv run python -m app.services.agentic.author_sandbox_artifacts.sandbox_artifact_authoring`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.author_sandbox_artifacts.sandbox_artifact_authoring
uv run pytest --no-cov tests/contracts/agentic/test_sandbox_artifacts.py tests/services/agentic/author_sandbox_artifacts/
uv run ruff format --check app/contracts/agentic/sandbox_artifacts.py app/services/agentic/author_sandbox_artifacts tests/contracts/agentic/test_sandbox_artifacts.py tests/services/agentic/author_sandbox_artifacts
uv run ruff check app/contracts/agentic/sandbox_artifacts.py app/services/agentic/author_sandbox_artifacts tests/contracts/agentic/test_sandbox_artifacts.py tests/services/agentic/author_sandbox_artifacts
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS
```

**Removal acceptance:** Revoke sandbox leases, stop generation, clean ephemeral resources, preserve immutable metadata required by retention, and leave DSL-first authoring available.

**Proposed commit:** `feat(agentic): implement sandboxed source artifact fallback`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-6.20 — `FEAT-AGT-CALIBRATE_OUTCOMES` — Post-Horizon Outcome Calibration

**Goal:** Match forecasts and recommendations to later receiver-owned outcomes; score calibration/error/invalidation, compare baselines, attribute latency/cost/value to roles and topologies, and produce change candidates without self-modifying production.

**Depends on:** `AGT-1.02`, `AGT-2.09`, `AGT-3.11`.
**Phase-0 blockers that must already be closed:** P0.5/P0.6/P0.7 matured outcome reference contracts; P0.9 calibration-to-eligibility governance.
**Provides:** `agentic.outcome-calibration@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.claims@1`, `agentic.operations@1`, `agentic.profile-evaluation@1`.
**Optional capabilities:** —.
**External prerequisites:** receiver-owned outcome evidence from Data, Analytics, Simulation, Optimization, Strategy, Portfolio, Risk, and Trading.
**State:** namespace `agentic.outcome_calibration`, schema version `1`, retention `RETAIN`.
**Role contributions:** —.
**Primary method:** `AgenticOutcomeCalibration.calibrate_agentic_outcomes(request)`.
**Operations:** `CALIBRATE_FORECAST`, `CALIBRATE_RECOMMENDATION`, `INSPECT`.
**Success/domain outcomes:** `ForecastCalibrationResult`, `RecommendationCalibrationResult`, `OutcomeCalibrationView`.
**Events:** `OutcomeCalibrationCompleted`, `AgenticChangeCandidateCreated`.

**Normalized donor bundle inputs**

- `ADD_TO_V3 primary behavior`
- `behavioral clues only: evaluation-manager, operations and historic result/provenance tests`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/outcome_calibration.py
app/services/agentic/calibrate_outcomes/README.md
app/services/agentic/calibrate_outcomes/__init__.py
app/services/agentic/calibrate_outcomes/manifest.py
app/services/agentic/calibrate_outcomes/config.py
app/services/agentic/calibrate_outcomes/feature.py
app/services/agentic/calibrate_outcomes/outcome_calibration.py
app/services/agentic/calibrate_outcomes/outcome_matching.py
app/services/agentic/calibrate_outcomes/scoring.py
app/services/agentic/calibrate_outcomes/value_attribution.py
app/services/agentic/calibrate_outcomes/change_candidates.py
app/services/agentic/calibrate_outcomes/migrations.py
app/services/agentic/calibrate_outcomes/_store.py
tests/contracts/agentic/test_outcome_calibration.py
tests/services/agentic/calibrate_outcomes/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/outcome_calibration.py` with the exact capability key `agentic.outcome-calibration@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-CALIBRATE_OUTCOMES"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `minimum_closed_horizon_count`, `calibration_window_days`, `baseline_refs`, `scoring_rules`, `attribution_method`, `change_candidate_threshold`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Require forecasts/recommendations to have immutable target, probability or bounded distribution, horizon, observation rule, invalidation, expected regime, expected economic effect, and provenance before outcomes mature.
- [ ] Bind matured outcomes from authoritative owners, including direction/magnitude error, invalidation timing, realized costs/slippage where applicable, regime, receiver rejection/amendment, and deterministic/single-agent baselines.
- [ ] Compute appropriate deterministic calibration and utility metrics, including probability calibration, magnitude error, unsupported-claim rate, reversal rate, receiver-rejection rate, cost-adjusted value of information, latency, reliability, and incremental utility.
- [ ] Do not accept raw P&L as sufficient evidence of quality.
- [ ] Emit evidence-backed change candidates only; never mutate prompts, manifests, model profiles, permissions, mandates, thresholds, or eligibility directly.

**Owned functional requirements**

- [ ] **FR-AGT-MATCH_OUTCOMES** — Match forecast target/horizon/observation rule and recommendation expectations to authoritative later outcomes without hindsight rewriting of the original record. Side effects: Read-only receiver calls and outcome-link write. Evidence: Horizon, revision, unmatched, multiple candidate, and no-hindsight tests.
- [ ] **FR-AGT-SCORE_CALIBRATION** — Compute declared probabilistic/directional/magnitude/error, invalidation timing, receiver rejection/amendment, latency, and cost metrics with finite deterministic arithmetic. Side effects: Score persistence. Evidence: Brier/log-loss where configured, missing outcome, non-finite, and repeatability tests.
- [ ] **FR-AGT-ATTRIBUTE_INCREMENTAL_VALUE** — Compare deterministic and single-agent baselines and attribute uncertainty-adjusted incremental value/cost to roles, rounds, prompts, models, tools, and topology without using raw P&L alone. Side effects: Attribution persistence. Evidence: Baseline parity, luck/P&L counterexample, cost, ablation, and attribution tests.
- [ ] **FR-AGT-PROPOSE_PROFILE_CHANGES** — Emit candidate role/prompt/model/tool/topology changes with evidence; never modify mandates, permissions, thresholds, prompts, or eligibility directly. Side effects: Change-candidate write and event. Evidence: Self-modification, insufficient sample, missing evaluation, and promotion-boundary tests.

**Mandatory focused tests**

- [ ] pre-outcome immutability.
- [ ] horizon maturity.
- [ ] authoritative outcome binding.
- [ ] probability/distribution scoring.
- [ ] P&L-only refusal.
- [ ] baseline/cost/value attribution.
- [ ] regime/invalidation/rejection.
- [ ] no self-modification.
- [ ] restart/removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-CALIBRATE_OUTCOMES`.

**Executable usage:** `uv run python -m app.services.agentic.calibrate_outcomes.outcome_calibration`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.calibrate_outcomes.outcome_calibration
uv run pytest --no-cov tests/contracts/agentic/test_outcome_calibration.py tests/services/agentic/calibrate_outcomes/
uv run ruff format --check app/contracts/agentic/outcome_calibration.py app/services/agentic/calibrate_outcomes tests/contracts/agentic/test_outcome_calibration.py tests/services/agentic/calibrate_outcomes
uv run ruff check app/contracts/agentic/outcome_calibration.py app/services/agentic/calibrate_outcomes tests/contracts/agentic/test_outcome_calibration.py tests/services/agentic/calibrate_outcomes
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-CALIBRATE_OUTCOMES
```

**Removal acceptance:** Core Agentic work remains, but no new post-outcome calibration or evidence-backed change candidates are produced. Historical calibration evidence remains retained.

**Proposed commit:** `feat(agentic): implement post-horizon outcome calibration`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

---

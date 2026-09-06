# Agentic Rebuild — Phase 4 Research Governance and Design

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

### AGT-4.14 — `FEAT-AGT-GOVERN_RESEARCH_SEARCH` — Research Campaign and Search Governance

**Goal:** Pre-register Agentic-generated research campaigns; bind hypothesis families, dataset families, variants, failed attempts, amendments, search budgets, and holdout reservation receipts; prevent trivial hash changes from resetting search history.

**Depends on:** `AGT-1.02`, `AGT-2.06`.
**Phase-0 blockers that must already be closed:** P0.6 campaign, hypothesis-family, dataset-family, search and holdout ownership.
**Provides:** `agentic.research-search@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.workflows@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `research.campaigns@1 (proposed owner key)`, `research.holdout@1 (proposed owner key)`, `simulation.experiments@1 (proposed owner key)`, `optimization.search@1 (proposed owner key)`.
**State:** namespace `agentic.research_search`, schema version `1`, retention `RETAIN`.
**Role contributions:** —.
**Primary method:** `AgenticResearchSearchGovernance.govern_research_search(request)`.
**Operations:** `REGISTER_CAMPAIGN`, `REGISTER_FAMILY`, `REGISTER_VARIANT`, `RECORD_ATTEMPT`, `RESERVE_HOLDOUT`, `CLOSE_CAMPAIGN`, `INSPECT`.
**Success/domain outcomes:** `ResearchCampaign`, `HypothesisFamilyReceipt`, `ResearchVariantReceipt`, `ResearchAttemptReceipt`, `HoldoutReservationReceipt`, `CampaignClosureReceipt`, `ResearchSearchView`.
**Events:** `ResearchCampaignOpened`, `ResearchAttemptRecorded`, `HoldoutReserved`, `ResearchCampaignClosed`.

**Normalized donor bundle inputs**

- `app/agentic/agents/experimentation/experiment_designer/**`
- `app/agentic/agents/experimentation/optimization_coordinator/**`
- `app/agentic/migrations/experimentation.py`
- `tests/agentic/integration/test_experiment_coordination.py`
- `tests/agentic/integration/test_bounded_optimization.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/research_search.py
app/services/agentic/govern_research_search/README.md
app/services/agentic/govern_research_search/__init__.py
app/services/agentic/govern_research_search/manifest.py
app/services/agentic/govern_research_search/config.py
app/services/agentic/govern_research_search/feature.py
app/services/agentic/govern_research_search/research_search_governance.py
app/services/agentic/govern_research_search/campaign_models.py
app/services/agentic/govern_research_search/near_duplicate.py
app/services/agentic/govern_research_search/budget_accounting.py
app/services/agentic/govern_research_search/holdout.py
app/services/agentic/govern_research_search/migrations.py
app/services/agentic/govern_research_search/_store.py
tests/contracts/agentic/test_research_search.py
tests/services/agentic/govern_research_search/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/research_search.py` with the exact capability key `agentic.research-search@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-GOVERN_RESEARCH_SEARCH"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_campaigns`, `max_variants_per_family`, `max_total_attempts`, `max_holdout_looks`, `near_duplicate_threshold`, `require_failure_reason`, `reservation_ttl_seconds`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register immutable research campaign, hypothesis-family, dataset-family, search-budget, and holdout identities before governed trials.
- [ ] Record every attempted variant, prompt/model/tool/profile lineage, parameter/feature change, amendment, completion/failure reason, and consumed budget.
- [ ] Enforce conservation: attempted equals completed plus failed; null and negative results remain visible.
- [ ] Classify near-duplicate hypotheses/specifications deterministically and charge them to the same family/campaign/holdout budget unless material independence is proven.
- [ ] Bind holdout reservation/consumption to campaign, hypothesis family, dataset family, holdout, request/protocol digest, principal, purpose, and expiry; rehashing or renaming cannot reset scarcity.
- [ ] Record multiple-testing, sequential-testing/alpha-spending, embargo/purge, economic-cost, and termination policies where applicable.

**Owned functional requirements**

- [ ] **FR-AGT-REGISTER_RESEARCH_CAMPAIGNS** — Bind research_campaign_id, hypothesis_family_id, dataset_family_id, search_budget_id, objective, owners, horizon, and pre-registration digest before generated variants run. Side effects: Transactional campaign/family write. Evidence: Identity, immutability, duplicate, and pre-registration tests.
- [ ] **FR-AGT-ACCOUNT_RESEARCH_VARIANTS** — Classify near-duplicate variants deterministically and charge attempts, parameter/feature/prompt/model changes, amendments, and researcher degrees of freedom to the appropriate family/campaign. Side effects: Variant and budget writes. Evidence: Trivial hash reset, similarity threshold, amendment, and budget reconciliation tests.
- [ ] **FR-AGT-PRESERVE_FAILED_ATTEMPTS** — Record every attempted/completed/failed/cancelled/invalid trial with reason; attempted must reconcile exactly to terminal attempt categories. Side effects: Append-only attempt write. Evidence: Hidden failure, reconciliation, null-result, and concurrent-attempt tests.
- [ ] **FR-AGT-GOVERN_HOLDOUT_REQUESTS** — Request authoritative holdout reservation/consumption from the receiver owner and bind receipts to campaign/family/dataset identities; local hashes never authorize reuse. Side effects: Receiver call through lease and receipt write. Evidence: Reuse, near-duplicate, expired reservation, race, and receiver-denial tests.

**Mandatory focused tests**

- [ ] campaign/family/dataset identities.
- [ ] all-attempt conservation.
- [ ] near-duplicate evasion.
- [ ] cross-hash holdout reuse.
- [ ] multiple testing/amendments.
- [ ] concurrent reservations.
- [ ] exhausted budget.
- [ ] restart/removal scarcity.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-GOVERN_RESEARCH_SEARCH`.

**Executable usage:** `uv run python -m app.services.agentic.govern_research_search.research_search_governance`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.govern_research_search.research_search_governance
uv run pytest --no-cov tests/contracts/agentic/test_research_search.py tests/services/agentic/govern_research_search/
uv run ruff format --check app/contracts/agentic/research_search.py app/services/agentic/govern_research_search tests/contracts/agentic/test_research_search.py tests/services/agentic/govern_research_search
uv run ruff check app/contracts/agentic/research_search.py app/services/agentic/govern_research_search tests/contracts/agentic/test_research_search.py tests/services/agentic/govern_research_search
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-GOVERN_RESEARCH_SEARCH
```

**Removal acceptance:** Block new Agentic-designed experiment/optimization work and holdout requests; preserve existing campaign, failure, search, and receipt evidence.

**Proposed commit:** `feat(agentic): implement research campaign and search governance`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-4.15 — `FEAT-AGT-DESIGN_RESEARCH` — Falsifiable Research Design

**Goal:** Convert supported claims and synthesis into falsifiable hypotheses and receiver-owned experiment/search request candidates with immutable inputs, splits, embargo, costs, seeds, baselines, metrics, stop rules, uncertainty, and failure handling.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.06`, `AGT-3.11`, `AGT-3.13`, `AGT-4.14`.
**Phase-0 blockers that must already be closed:** P0.6 Research/Simulation/Optimization request contracts.
**Provides:** `agentic.research-design@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.claims@1`, `agentic.synthesis@1`, `agentic.research-search@1`, `agentic.workflows@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `research.protocols@1 (proposed owner key)`, `simulation.experiments@1 (proposed owner key)`, `optimization.search@1 (proposed owner key)`.
**State:** `None`.
**Role contributions:** `hypothesis_designer`, `experiment_designer`, `bounded_search_designer`.
**Primary method:** `AgenticResearchDesign.design_research(request)`.
**Operations:** `DESIGN_HYPOTHESIS`, `DESIGN_EXPERIMENT`, `DESIGN_SEARCH`.
**Success/domain outcomes:** `HypothesisCandidate`, `ExperimentRequestCandidate`, `SearchRequestCandidate`.
**Events:** `ResearchDesignCompleted`.

**Normalized donor bundle inputs**

- `app/agentic/agents/strategy_desk/strategy_thesis_analyst/**`
- `app/agentic/agents/experimentation/experiment_designer/**`
- `app/agentic/agents/experimentation/optimization_coordinator/**`
- `corresponding unit/integration/usage tests`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/research_design.py
app/services/agentic/design_research/README.md
app/services/agentic/design_research/__init__.py
app/services/agentic/design_research/manifest.py
app/services/agentic/design_research/config.py
app/services/agentic/design_research/feature.py
app/services/agentic/design_research/research_design.py
app/services/agentic/design_research/research_design_validation.py
app/services/agentic/design_research/receiver_mapping.py
app/services/agentic/design_research/roles/hypothesis_designer/role.json
app/services/agentic/design_research/roles/hypothesis_designer/prompt.md
app/services/agentic/design_research/roles/experiment_designer/role.json
app/services/agentic/design_research/roles/experiment_designer/prompt.md
app/services/agentic/design_research/roles/bounded_search_designer/role.json
app/services/agentic/design_research/roles/bounded_search_designer/prompt.md
tests/contracts/agentic/test_research_design.py
tests/services/agentic/design_research/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/research_design.py` with the exact capability key `agentic.research-design@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-DESIGN_RESEARCH"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `allowed_request_types`, `require_pre_registration`, `require_baseline`, `require_cost_model`, `require_embargo`, `max_design_iterations`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register Hypothesis Designer, Experiment Designer, and Bounded Search Designer role artifacts with exact eligibility and disposal.
- [ ] Compose falsifiable hypothesis candidates from supported claim graphs with mechanism, prerequisites, confounders, assumptions, horizon, rejection criterion, required data, leakage constraints, and campaign/family identity.
- [ ] Map experiment candidates to the exact Research/Simulation owner contract and include immutable inputs, splits, embargo, costs, seeds, baselines, metrics, stop rules, and evidence classes.
- [ ] Map search candidates to the exact Optimization owner contract and include declared space, objective, method, trial/search budget, early stop, robustness/stability/overfit criteria, and holdout policy.
- [ ] Submit candidates unchanged for receiver validation or return typed rejection; never duplicate receiver engines or alter results.

**Owned functional requirements**

- [ ] **FR-AGT-DESIGN_FALSIFIABLE_HYPOTHESES** — Require statement, asset/data scope, horizon, mechanism, evidence, prerequisites, confounders, falsifier, rejection criterion, and campaign/family binding. Side effects: Model call and workflow/operations write. Evidence: Falsifiability, missing criterion, scope, evidence, and prohibited-execution-field tests.
- [ ] **FR-AGT-COMPOSE_EXPERIMENT_REQUESTS** — Map a pre-registered hypothesis into the receiver-owned experiment schema with immutable inputs, time splits, embargo, costs, seeds, baseline, metrics, stop/failure rules, and evidence classes. Side effects: Receiver-schema validation; no execution unless separately authorized by workflow/tool governance. Evidence: Contract mapping, no-invented-field, tamper, and receiver-rejection tests.
- [ ] **FR-AGT-COMPOSE_SEARCH_REQUESTS** — Map an approved experiment into a bounded receiver-owned optimization request with parameter space, method, objective, trial budget, early stop, robustness evidence, and holdout policy. Side effects: Receiver-schema validation. Evidence: Unbounded space, hidden trial, objective, early-stop, and holdout tests.
- [ ] **FR-AGT-BIND_RESEARCH_PROTOCOLS** — Bind every candidate to claim graph, synthesis, campaign/family, dataset versions, policy/configuration, role/model/prompt, and receiver schema versions. Side effects: Provenance write. Evidence: Lineage completeness and changed-input tests.

**Mandatory focused tests**

- [ ] hypothesis completeness/falsifiability.
- [ ] exact receiver schema.
- [ ] experiment/search completeness.
- [ ] unsupported/contested/dissent refusal.
- [ ] budget/holdout refusal.
- [ ] unchanged receiver request/result.
- [ ] role removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-DESIGN_RESEARCH`.

**Executable usage:** `uv run python -m app.services.agentic.design_research.research_design`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.design_research.research_design
uv run pytest --no-cov tests/contracts/agentic/test_research_design.py tests/services/agentic/design_research/
uv run ruff format --check app/contracts/agentic/research_design.py app/services/agentic/design_research tests/contracts/agentic/test_research_design.py tests/services/agentic/design_research
uv run ruff check app/contracts/agentic/research_design.py app/services/agentic/design_research tests/contracts/agentic/test_research_design.py tests/services/agentic/design_research
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-DESIGN_RESEARCH
```

**Removal acceptance:** Retain interpretation/research records but stop new Agentic-designed hypotheses, experiments, and search requests.

**Proposed commit:** `feat(agentic): implement falsifiable research design`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

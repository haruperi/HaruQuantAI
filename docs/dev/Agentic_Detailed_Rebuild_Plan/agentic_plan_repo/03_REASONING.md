# Agentic Rebuild — Phase 3 Claims, Deliberation, and Synthesis

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

### AGT-3.11 — `FEAT-AGT-MANAGE_CLAIMS` — Claim-and-Evidence Graph

**Goal:** Create and maintain the canonical structured reasoning record: typed claims, evidence links, assumptions, falsifiers, contradictions, dependencies, uncertainty, validity intervals, forecasts, recommendations, and status propagation.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.05`, `AGT-2.06`, `AGT-2.07`.
**Phase-0 blockers that must already be closed:** P0.5 canonical evidence references and derivation owners; P0.2 claim-state retention decision.
**Provides:** `agentic.claims@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.context@1`, `agentic.workflows@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `receiver-owned evidence references`, `receiver-owned deterministic derivation records`.
**State:** namespace `agentic.claims`, schema version `1`, retention `RETAIN`.
**Role contributions:** `analytics_evidence_reviewer`, `fundamental_analyst`, `sentiment_analyst`, `technical_structure_analyst`, `quantitative_analyst`.
**Primary method:** `AgenticClaimGraph.manage_claim_graphs(request)`.
**Operations:** `CREATE_GRAPH`, `APPEND_CLAIM`, `RELATE_CLAIMS`, `TRANSITION_CLAIM`, `ASSESS_RELIABILITY`, `INSPECT_GRAPH`.
**Success/domain outcomes:** `ClaimGraph`, `ClaimReceipt`, `ClaimRelationReceipt`, `ClaimStatusReceipt`, `ClaimReliabilityAssessment`, `ClaimGraphView`.
**Events:** `ClaimCreated`, `ClaimRelated`, `ClaimStatusChanged`, `ClaimExpired`.

**Normalized donor bundle inputs**

- `app/agentic/context_memory/models.py`
- `app/agentic/context_memory/repository.py`
- `app/agentic/agents/experimentation/simulation_interpreter/**`
- `app/agentic/agents/market_intelligence/**`
- `app/agentic/agents/market_analysis/**`
- `relevant analyst unit tests`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/claims.py
app/services/agentic/manage_claims/README.md
app/services/agentic/manage_claims/__init__.py
app/services/agentic/manage_claims/manifest.py
app/services/agentic/manage_claims/config.py
app/services/agentic/manage_claims/feature.py
app/services/agentic/manage_claims/claim_graph.py
app/services/agentic/manage_claims/claim_models.py
app/services/agentic/manage_claims/relations.py
app/services/agentic/manage_claims/status_propagation.py
app/services/agentic/manage_claims/reliability.py
app/services/agentic/manage_claims/migrations.py
app/services/agentic/manage_claims/_store.py
app/services/agentic/manage_claims/roles/analytics_evidence_reviewer/role.json
app/services/agentic/manage_claims/roles/analytics_evidence_reviewer/prompt.md
app/services/agentic/manage_claims/roles/fundamental_analyst/role.json
app/services/agentic/manage_claims/roles/fundamental_analyst/prompt.md
app/services/agentic/manage_claims/roles/sentiment_analyst/role.json
app/services/agentic/manage_claims/roles/sentiment_analyst/prompt.md
app/services/agentic/manage_claims/roles/technical_structure_analyst/role.json
app/services/agentic/manage_claims/roles/technical_structure_analyst/prompt.md
app/services/agentic/manage_claims/roles/quantitative_analyst/role.json
app/services/agentic/manage_claims/roles/quantitative_analyst/prompt.md
tests/contracts/agentic/test_claims.py
tests/services/agentic/manage_claims/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/claims.py` with the exact capability key `agentic.claims@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-MANAGE_CLAIMS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_claims_per_graph`, `max_relations_per_claim`, `default_claim_ttl_seconds`, `allowed_claim_types`, `status_propagation_mode`, `require_falsifier_for_forecasts`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Implement graph identity, typed claims, evidence/derivation references, relations, status history, validity/expiry, assumptions, confounders, falsifiers, scope, author profile, and provenance.
- [ ] Keep `OBSERVED_FACT`, `DETERMINISTIC_DERIVATION`, `MODEL_INFERENCE`, `FORECAST`, and `RECOMMENDATION` structurally distinct and prevent model output from becoming a fact by declaration.
- [ ] Implement typed support, contradiction, derivation, dependency, invalidation, and supersession relations; reject cycles where dependency semantics require acyclicity.
- [ ] Propagate evidence revision/expiry/refutation through dependent claims with append-only status transitions.
- [ ] Compute reliability from evidence, statistical, epistemic, operational, and calibrated-profile dimensions; never use model self-confidence as authority.
- [ ] Register the five evidence-analyst roles and prove they interpret receiver-owned evidence without recomputing or replacing it.

**Owned functional requirements**

- [ ] **FR-AGT-CREATE_TYPED_CLAIMS** — Represent OBSERVED_FACT, DETERMINISTIC_DERIVATION, MODEL_INFERENCE, FORECAST, and RECOMMENDATION separately with validity, assumptions, confounders, uncertainty, provenance, and author. Side effects: Model call through specialist role and claim persistence. Evidence: Type, prohibited-promotion, required-field, and schema tests.
- [ ] **FR-AGT-LINK_CLAIM_EVIDENCE** — Bind every material claim to exact evidence/derivation references and content hashes; unsupported claims remain UNKNOWN or are refused. Side effects: Persistence write. Evidence: Missing evidence, tamper, duplicate, wrong-owner, and point-in-time tests.
- [ ] **FR-AGT-PROPAGATE_CLAIM_STATUS** — Apply SUPPORTED, CONTESTED, REFUTED, UNKNOWN, and EXPIRED transitions and propagate source revision/expiry/invalidation through dependent claims without rewriting history. Side effects: Append-only status write and events. Evidence: Transition, dependency cycle, expiry, correction, and revision tests.
- [ ] **FR-AGT-ASSESS_CLAIM_RELIABILITY** — Compute reliability from evidence coverage/quality, statistical, epistemic, operational, and historical calibration evidence; do not use model self-confidence as authority. Side effects: Deterministic assessment write. Evidence: Calibration, missing dimension, conflicting evidence, and deterministic-repeatability tests.

**Mandatory focused tests**

- [ ] claim type/status.
- [ ] fact-promotion prohibition.
- [ ] evidence tamper.
- [ ] relation cycles.
- [ ] expiry/revision propagation.
- [ ] deterministic reliability.
- [ ] no upstream recomputation.
- [ ] five role contributions.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Additive migration checksum/order, strict schema constraints, idempotent migration, transaction rollback, restart reconstruction, expected-version/uniqueness, retention/export/purge, legacy import, and removal-with-retained-state tests.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-MANAGE_CLAIMS`.

**Executable usage:** `uv run python -m app.services.agentic.manage_claims.claim_graph`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.manage_claims.claim_graph
uv run pytest --no-cov tests/contracts/agentic/test_claims.py tests/services/agentic/manage_claims/
uv run ruff format --check app/contracts/agentic/claims.py app/services/agentic/manage_claims tests/contracts/agentic/test_claims.py tests/services/agentic/manage_claims
uv run ruff check app/contracts/agentic/claims.py app/services/agentic/manage_claims tests/contracts/agentic/test_claims.py tests/services/agentic/manage_claims
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-MANAGE_CLAIMS
```

**Removal acceptance:** Stop new structured reasoning. Preserve retained claim graphs for audit/export. No transcript fallback becomes canonical.

**Proposed commit:** `feat(agentic): implement claim-and-evidence graph`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-3.12 — `FEAT-AGT-DELIBERATE_RESEARCH` — Independent Challenge and Deliberation

**Goal:** Run independent challenge, counterclaim, bounded rebuttal, deterministic evidence requests, dissent preservation, critic-correlation disclosure, and explicit stop conditions. Deliberation cannot authorize or size.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.06`, `AGT-3.11`.
**Phase-0 blockers that must already be closed:** P0.9 independence/eligibility bootstrap; P0.5 deterministic challenge tools.
**Provides:** `agentic.deliberation@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.workflows@1`, `agentic.claims@1`, `agentic.operations@1`.
**Optional capabilities:** `deterministic challenge/evaluation tools`.
**External prerequisites:** —.
**State:** BLOCKED BY AGT-0.02: ratify whether deliberation is retained by this feature or only by workflow/claims/operations owners.
**Role contributions:** `causality_challenger`, `leakage_challenger`, `robustness_challenger`, `risk_challenger`, `compliance_challenger`, `operations_security_challenger`.
**Primary method:** `AgenticDeliberation.deliberate_research(request)`.
**Operations:** `START`, `CONTINUE`, `CANCEL`, `INSPECT`.
**Success/domain outcomes:** `DeliberationRecord`, `DeliberationCancellationReceipt`, `DeliberationView`.
**Events:** `DeliberationRoundStarted`, `ChallengeRecorded`, `DissentRecorded`, `DeliberationStopped`.

**Normalized donor bundle inputs**

- `app/agentic/deliberation/**`
- `tests/agentic/unit/test_deliberation.py`
- `tests/agentic/integration/test_research_council.py`
- `tests/agentic/usage/07_deliberation.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/deliberation.py
app/services/agentic/deliberate_research/README.md
app/services/agentic/deliberate_research/__init__.py
app/services/agentic/deliberate_research/manifest.py
app/services/agentic/deliberate_research/config.py
app/services/agentic/deliberate_research/feature.py
app/services/agentic/deliberate_research/research_deliberation.py
app/services/agentic/deliberate_research/deliberation_models.py
app/services/agentic/deliberate_research/independence.py
app/services/agentic/deliberate_research/stop_conditions.py
app/services/agentic/deliberate_research/roles/causality_challenger/role.json
app/services/agentic/deliberate_research/roles/causality_challenger/prompt.md
app/services/agentic/deliberate_research/roles/leakage_challenger/role.json
app/services/agentic/deliberate_research/roles/leakage_challenger/prompt.md
app/services/agentic/deliberate_research/roles/robustness_challenger/role.json
app/services/agentic/deliberate_research/roles/robustness_challenger/prompt.md
app/services/agentic/deliberate_research/roles/risk_challenger/role.json
app/services/agentic/deliberate_research/roles/risk_challenger/prompt.md
app/services/agentic/deliberate_research/roles/compliance_challenger/role.json
app/services/agentic/deliberate_research/roles/compliance_challenger/prompt.md
app/services/agentic/deliberate_research/roles/operations_security_challenger/role.json
app/services/agentic/deliberate_research/roles/operations_security_challenger/prompt.md
tests/contracts/agentic/test_deliberation.py
tests/services/agentic/deliberate_research/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/deliberation.py` with the exact capability key `agentic.deliberation@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-DELIBERATE_RESEARCH"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_participants`, `max_rounds`, `max_counterclaims_per_claim`, `default_rebuttal_rounds`, `require_independent_first_pass`, `minimum_independence_score`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register six challenger profiles and select them by deterministic task/risk policy, not by a proposer or model voting for reviewers.
- [ ] Commit each challenger first-pass assessment after providing objective, evidence snapshot, and normalized claim IDs but before exposing proposer narrative.
- [ ] Record provider/model/prompt/context/evidence/decoding correlations; warn or refuse when the required independence level is not achieved.
- [ ] Persist/retain challenge, counterclaim, rebuttal, dissent, unresolved conflict, tool evidence, participants, rounds, budgets, and stop reason in the owner selected in P0.2.
- [ ] Stop on objective completion, insufficient evidence, material conflict, limits, deadline, budget, policy denial, incident, dependency removal, or cancellation.
- [ ] Reject authorization, position-size, order, fill, and risk-approval semantics from deliberation outputs.

**Owned functional requirements**

- [ ] **FR-AGT-COLLECT_INDEPENDENT_CHALLENGES** — Require challengers to assess objective, evidence, and normalized claim IDs before seeing proposer narrative; disclose shared provider/model/prompt/context/evidence correlation. Side effects: Model/tool calls and workflow writes. Evidence: Anchoring, visibility ordering, correlation, and independence-score tests.
- [ ] **FR-AGT-PRESERVE_DELIBERATION_DISSENT** — Persist counterclaims, unresolved challenges, minority dissent, insufficient evidence, and material disagreement; consensus cannot erase them or create authorization. Side effects: Claim/workflow/operations writes. Evidence: Dissent, majority-vote, authorization-language, and no-position-size tests.
- [ ] **FR-AGT-BOUND_DELIBERATION** — Enforce participants, roles, rounds, fan-out, deadlines, tools, tokens, cost, and stop conditions from deterministic profiles; callers/models cannot widen them. Side effects: Bounded model/tool calls. Evidence: Limit, runaway-loop, deadline, budget, and caller-override tests.
- [ ] **FR-AGT-STOP_LOW_VALUE_DELIBERATION** — Stop on objective completion, insufficient evidence, unresolved material conflict, deadline, budget, policy denial, incident, cancellation, or low expected value of another round. Side effects: Workflow transition. Evidence: Stop-condition and value-of-information tests.

**Mandatory focused tests**

- [ ] blind first pass.
- [ ] independence correlation.
- [ ] distinct-model policy.
- [ ] challenge mode coverage.
- [ ] dissent preservation.
- [ ] bounds/stop conditions.
- [ ] no authorization/size.
- [ ] mid-round removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-DELIBERATE_RESEARCH`.

**Executable usage:** `uv run python -m app.services.agentic.deliberate_research.research_deliberation`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.deliberate_research.research_deliberation
uv run pytest --no-cov tests/contracts/agentic/test_deliberation.py tests/services/agentic/deliberate_research/
uv run ruff format --check app/contracts/agentic/deliberation.py app/services/agentic/deliberate_research tests/contracts/agentic/test_deliberation.py tests/services/agentic/deliberate_research
uv run ruff check app/contracts/agentic/deliberation.py app/services/agentic/deliberate_research tests/contracts/agentic/test_deliberation.py tests/services/agentic/deliberate_research
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-DELIBERATE_RESEARCH
```

**Removal acceptance:** Single-specialist workflows may remain. Council/challenge-required workflows become unready; active deliberations stop at a checkpoint with dissent/evidence preserved.

**Proposed commit:** `feat(agentic): implement independent challenge and deliberation`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-3.13 — `FEAT-AGT-SYNTHESIZE_RESEARCH` — Research Synthesis

**Goal:** Produce typed research and decision-support summaries from claim graphs and deliberation evidence while preserving contested/refuted claims, dissent, limitations, uncertainty, and insufficient-evidence outcomes.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.05`, `AGT-3.11`, `AGT-3.12`.
**Phase-0 blockers that must already be closed:** P0.2 synthesis/claim binding contracts.
**Provides:** `agentic.synthesis@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.claims@1`, `agentic.deliberation@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** —.
**State:** `None`.
**Role contributions:** `research_synthesizer`.
**Primary method:** `AgenticResearchSynthesis.synthesize_research(request)`.
**Operations:** `SYNTHESIZE`.
**Success/domain outcomes:** `ResearchSynthesis`, `ResearchInsufficientEvidence`.
**Events:** `ResearchSynthesisCompleted`.

**Normalized donor bundle inputs**

- `app/agentic/deliberation/**`
- `app/agentic/agents/strategy_desk/strategy_thesis_analyst/**`
- `tests/agentic/unit/test_deliberation.py`
- `tests/agentic/unit/test_strategy_thesis_analyst.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/synthesis.py
app/services/agentic/synthesize_research/README.md
app/services/agentic/synthesize_research/__init__.py
app/services/agentic/synthesize_research/manifest.py
app/services/agentic/synthesize_research/config.py
app/services/agentic/synthesize_research/feature.py
app/services/agentic/synthesize_research/research_synthesis.py
app/services/agentic/synthesize_research/synthesis_validation.py
app/services/agentic/synthesize_research/roles/research_synthesizer/role.json
app/services/agentic/synthesize_research/roles/research_synthesizer/prompt.md
tests/contracts/agentic/test_synthesis.py
tests/services/agentic/synthesize_research/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/synthesis.py` with the exact capability key `agentic.synthesis@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-SYNTHESIZE_RESEARCH"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `max_summary_chars`, `require_dissent_section`, `require_uncertainty_breakdown`, `allow_partial_synthesis`, `max_cited_claims`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Consume only canonical claim graphs and optional deliberation records; bind every cited claim/evidence/status to supplied records rather than model-created references.
- [ ] Separate supported conclusion, contested/refuted/unknown/expired claims, assumptions, uncertainty dimensions, invalidation, unanswered questions, partial coverage, and dissent.
- [ ] Force contested or insufficient-evidence disposition while material dissent remains unresolved.
- [ ] Reject uncited material claims and any code, broker, order, fill, risk approval, authoritative size, or kill-switch language.
- [ ] Register and exactly dispose the Research Synthesizer role artifact.

**Owned functional requirements**

- [ ] **FR-AGT-SYNTHESIZE_CLAIM_GRAPHS** — Build conclusions only from supplied claim/deliberation records and cite exact claim/evidence IDs; never invent evidence or silently recompute receiver results. Side effects: Model call and workflow/operations write. Evidence: Citation, omitted-claim, invented-evidence, and no-recomputation tests.
- [ ] **FR-AGT-PRESERVE_SYNTHESIS_UNCERTAINTY** — Separate evidence, statistical, epistemic, operational, and calibrated reliability; include contested/refuted claims, dissent, limitations, and open questions. Side effects: None beyond result write. Evidence: Uncertainty, dissent, contested-claim, and partial-coverage tests.
- [ ] **FR-AGT-REFUSE_UNSUPPORTED_SYNTHESIS** — Return insufficient evidence or refusal when minimum support, freshness, trust, or required challenge is absent; agreement alone cannot promote a recommendation. Side effects: Workflow terminal/refusal write. Evidence: Missing evidence, stale evidence, consensus-only, and required-challenge tests.

**Mandatory focused tests**

- [ ] claim/evidence binding.
- [ ] no invented citations.
- [ ] uncertainty and dissent.
- [ ] material dissent outcome.
- [ ] partial coverage.
- [ ] prohibited authority fields.
- [ ] role/provider removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-SYNTHESIZE_RESEARCH`.

**Executable usage:** `uv run python -m app.services.agentic.synthesize_research.research_synthesis`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.synthesize_research.research_synthesis
uv run pytest --no-cov tests/contracts/agentic/test_synthesis.py tests/services/agentic/synthesize_research/
uv run ruff format --check app/contracts/agentic/synthesis.py app/services/agentic/synthesize_research tests/contracts/agentic/test_synthesis.py tests/services/agentic/synthesize_research
uv run ruff check app/contracts/agentic/synthesis.py app/services/agentic/synthesize_research tests/contracts/agentic/test_synthesis.py tests/services/agentic/synthesize_research
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-SYNTHESIZE_RESEARCH
```

**Removal acceptance:** Claim graphs and deliberation remain auditable, but no new final Agentic synthesis is produced.

**Proposed commit:** `feat(agentic): implement research synthesis`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

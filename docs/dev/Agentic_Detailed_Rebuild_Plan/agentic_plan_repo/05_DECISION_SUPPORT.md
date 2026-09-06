# Agentic Rebuild — Phase 5 Decision Support

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

### AGT-5.16 — `FEAT-AGT-COMPOSE_STRATEGY_SPECS` — JSON Strategy and Indicator DSL Composition

**Goal:** Convert approved hypotheses and synthesis into receiver-owned JSON strategy/indicator DSL candidates, report unsupported expressions, and preserve evidence, constraints, test vectors, search history, and provenance. DSL is the default artifact path.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.05`, `AGT-3.11`, `AGT-3.13`, `AGT-4.14`.
**Phase-0 blockers that must already be closed:** P0.7 Strategy/Indicators JSON DSL and candidate-intake contracts.
**Provides:** `agentic.strategy-specs@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.claims@1`, `agentic.synthesis@1`, `agentic.research-search@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `strategy.dsl@1 (proposed owner key)`, `indicators.dsl@1 (proposed owner key)`, `strategy.candidate-intake@1 (proposed owner key)`.
**State:** `None`.
**Role contributions:** `strategy_dsl_author`.
**Primary method:** `AgenticStrategySpecComposition.compose_strategy_specs(request)`.
**Operations:** `COMPOSE`, `VALIDATE_HANDOFF`.
**Success/domain outcomes:** `StrategySpecCandidate`, `StrategySpecHandoffReceipt`, `UnsupportedExpressionReport`.
**Events:** `StrategySpecComposed`.

**Normalized donor bundle inputs**

- `ADD_TO_V3 primary behavior`
- `behavioral clues only: strategy-thesis and coder donor bundles; do not reuse Python generation as the default`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/strategy_specs.py
app/services/agentic/compose_strategy_specs/README.md
app/services/agentic/compose_strategy_specs/__init__.py
app/services/agentic/compose_strategy_specs/manifest.py
app/services/agentic/compose_strategy_specs/config.py
app/services/agentic/compose_strategy_specs/feature.py
app/services/agentic/compose_strategy_specs/strategy_spec_composition.py
app/services/agentic/compose_strategy_specs/dsl_mapping.py
app/services/agentic/compose_strategy_specs/dsl_validation.py
app/services/agentic/compose_strategy_specs/roles/strategy_dsl_author/role.json
app/services/agentic/compose_strategy_specs/roles/strategy_dsl_author/prompt.md
tests/contracts/agentic/test_strategy_specs.py
tests/services/agentic/compose_strategy_specs/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/strategy_specs.py` with the exact capability key `agentic.strategy-specs@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-COMPOSE_STRATEGY_SPECS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `dsl_schema_major`, `max_nodes`, `max_parameters`, `require_test_vectors`, `allow_indicator_specs`, `unsupported_expression_policy`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register Strategy DSL Author and load the exact Strategy/Indicators schema capability selected in P0.7.
- [ ] Compose only declarative, schema-permitted building blocks, inputs, parameters, signals, state, entry/exit, management, constraints, and metadata.
- [ ] Run deterministic schema and semantic preflight validation after each model output; bound correction attempts and retain failed candidate evidence.
- [ ] Return `UnsupportedExpressionReport` when the DSL cannot express the requirement. Do not silently switch to source-code generation.
- [ ] Handoff a content-addressed candidate to the receiver; Strategy/Indicators owns semantic validation, compilation, registration, versioning, lifecycle, and production use.

**Owned functional requirements**

- [ ] **FR-AGT-COMPOSE_STRATEGY_DSL** — Produce only the receiver-owned schema using declared building blocks, parameters, data/indicator references, signal/exit/risk-request semantics, tests, and provenance; no arbitrary executable code. Side effects: Model call and schema validation. Evidence: Schema, unknown block, parameter, determinism, and prohibited-code tests.
- [ ] **FR-AGT-VALIDATE_DSL_HANDOFF** — Submit the candidate only through Strategy/Indicators validation/intake and treat receipt/rejection as authoritative; Agentic cannot compile, register, or promote it. Side effects: Receiver call through governed capability lease. Evidence: Receiver rejection, idempotency, no privileged route, and authority tests.
- [ ] **FR-AGT-REPORT_UNSUPPORTED_EXPRESSIONS** — Return an explicit structured DSL gap when the requirement cannot be represented; never silently encode custom semantics or switch to code. Side effects: None beyond result. Evidence: Unsupported-expression and no-silent-fallback tests.
- [ ] **FR-AGT-PRESERVE_DSL_PROVENANCE** — Bind the candidate to hypothesis, claims, campaign/search history, role/model/prompt, DSL schema/compiler versions, config, and test vectors. Side effects: Workflow/operations write. Evidence: Lineage, changed schema, search-history, and reproducibility tests.

**Mandatory focused tests**

- [ ] exact schema/version.
- [ ] deterministic validation.
- [ ] bounded correction.
- [ ] unsupported expression.
- [ ] no arbitrary code/broker/approval.
- [ ] receiver rejection/acceptance truth.
- [ ] role/removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-COMPOSE_STRATEGY_SPECS`.

**Executable usage:** `uv run python -m app.services.agentic.compose_strategy_specs.strategy_spec_composition`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.compose_strategy_specs.strategy_spec_composition
uv run pytest --no-cov tests/contracts/agentic/test_strategy_specs.py tests/services/agentic/compose_strategy_specs/
uv run ruff format --check app/contracts/agentic/strategy_specs.py app/services/agentic/compose_strategy_specs tests/contracts/agentic/test_strategy_specs.py tests/services/agentic/compose_strategy_specs
uv run ruff check app/contracts/agentic/strategy_specs.py app/services/agentic/compose_strategy_specs tests/contracts/agentic/test_strategy_specs.py tests/services/agentic/compose_strategy_specs
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-COMPOSE_STRATEGY_SPECS
```

**Removal acceptance:** Stop Agentic DSL authoring. Existing Strategy/Indicators definitions and accepted artifacts remain unaffected.

**Proposed commit:** `feat(agentic): implement json strategy and indicator dsl composition`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-5.17 — `FEAT-AGT-ADVISE_PORTFOLIO` — Portfolio and Risk Advisory

**Goal:** Produce expiring non-binding allocation/risk advice and questions from current receiver evidence while preserving independent challenge and mandate, barrier, tail, concentration, liquidity, correlation, model, operational, and compliance concerns.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.07`, `AGT-3.11`, `AGT-3.12`, `AGT-3.13`.
**Phase-0 blockers that must already be closed:** P0.7 Analytics/Portfolio/Risk/account evidence and review contracts.
**Provides:** `agentic.portfolio-advisory@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.context@1`, `agentic.claims@1`, `agentic.deliberation@1`, `agentic.synthesis@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `analytics.portfolio-evidence@1 (proposed owner key)`, `portfolio.evidence@1 (proposed owner key)`, `portfolio.review@1 (proposed owner key)`, `risk.evidence@1 (proposed owner key)`, `risk.review@1 (proposed owner key)`, `data.account-evidence@1 (proposed owner key)`.
**State:** `None`.
**Role contributions:** `portfolio_advisory_synthesizer`.
**Primary method:** `AgenticPortfolioAdvisory.advise_portfolio(request)`.
**Operations:** `ADVISE`.
**Success/domain outcomes:** `PortfolioAdvisory`, `PortfolioAdvisoryInsufficientEvidence`.
**Events:** `PortfolioAdvisoryCompleted`.

**Normalized donor bundle inputs**

- `app/agentic/agents/portfolio_risk_advisory/portfolio_risk_advisor/**`
- `tests/agentic/unit/test_portfolio_risk_advisor.py`
- `tests/agentic/integration/test_advisory_council.py`
- `tests/agentic/usage/19_advisory.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/portfolio_advisory.py
app/services/agentic/advise_portfolio/README.md
app/services/agentic/advise_portfolio/__init__.py
app/services/agentic/advise_portfolio/manifest.py
app/services/agentic/advise_portfolio/config.py
app/services/agentic/advise_portfolio/feature.py
app/services/agentic/advise_portfolio/portfolio_advisory.py
app/services/agentic/advise_portfolio/advisory_validation.py
app/services/agentic/advise_portfolio/roles/portfolio_advisory_synthesizer/role.json
app/services/agentic/advise_portfolio/roles/portfolio_advisory_synthesizer/prompt.md
tests/contracts/agentic/test_portfolio_advisory.py
tests/services/agentic/advise_portfolio/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/portfolio_advisory.py` with the exact capability key `agentic.portfolio-advisory@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-ADVISE_PORTFOLIO"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `advisory_ttl_seconds`, `max_instruments`, `max_accounts`, `require_risk_challenge`, `require_current_account_snapshot`, `maximum_evidence_age_seconds`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register Portfolio Advisory Synthesizer and require current Portfolio, Risk, Analytics, account, mandate, and observation-time evidence.
- [ ] Use relevant evidence analysts and required Risk/Compliance challengers through existing capabilities rather than embedding duplicate prompts or logic.
- [ ] Produce expiring non-binding concerns, trade-offs, relative preferences or bounded ranges only where receiver contracts allow, uncertainty, evidence, questions, and dissent.
- [ ] Structurally prohibit lot size, quantity, notional, order, price, execution instruction, risk approval, verdict-by-absence, and kill-switch actions.
- [ ] Do not call Portfolio/Risk mutation paths. Any future receiver review uses exact public contracts and full owner validation.

**Owned functional requirements**

- [ ] **FR-AGT-ADVISE_PORTFOLIO_ALLOCATION** — Use current allocation, account, analytics, mandate, and risk evidence to produce non-binding weights/ranges, constraints, questions, uncertainty, evidence, and strict expiry without lot size, order, or approval fields. Side effects: Read-only receiver calls and model call. Evidence: Freshness, scope, no-execution-field, expiry, and non-binding tests.
- [ ] **FR-AGT-CHALLENGE_PORTFOLIO_RISK** — Cover mandate, barrier, tail, concentration, liquidity, correlation, leverage, operational, model, compliance, and data risks through independent challenge. Side effects: Model/tool calls via deliberation. Evidence: Risk-kind set equality, dissent, and no-approval tests.
- [ ] **FR-AGT-EXPIRE_PORTFOLIO_ADVICE** — Make every advisory strictly expiring; stale evidence or elapsed expiry prevents reuse or receiver submission. Side effects: None; receiver call denied when stale. Evidence: Already-expired, boundary-time, stale-source, and clock tests.
- [ ] **FR-AGT-PRESERVE_PORTFOLIO_AUTHORITY** — Any receiver request uses Portfolio/Risk-owned contracts and full normal controls; absence of criticism or low severity is never consent. Side effects: Optional receiver review call through lease. Evidence: Receiver rejection, missing authorization, and no implicit approval tests.

**Mandatory focused tests**

- [ ] fresh current evidence.
- [ ] non-binding schema.
- [ ] required challenge set equality.
- [ ] strict expiry.
- [ ] no approval/size/order.
- [ ] receiver authority.
- [ ] role/dependency removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ADVISE_PORTFOLIO`.

**Executable usage:** `uv run python -m app.services.agentic.advise_portfolio.portfolio_advisory`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.advise_portfolio.portfolio_advisory
uv run pytest --no-cov tests/contracts/agentic/test_portfolio_advisory.py tests/services/agentic/advise_portfolio/
uv run ruff format --check app/contracts/agentic/portfolio_advisory.py app/services/agentic/advise_portfolio tests/contracts/agentic/test_portfolio_advisory.py tests/services/agentic/advise_portfolio
uv run ruff check app/contracts/agentic/portfolio_advisory.py app/services/agentic/advise_portfolio tests/contracts/agentic/test_portfolio_advisory.py tests/services/agentic/advise_portfolio
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-ADVISE_PORTFOLIO
```

**Removal acceptance:** Portfolio and Risk continue deterministically; Agentic no longer produces portfolio/risk advice. Existing advisory evidence remains in workflow/operations records.

**Proposed commit:** `feat(agentic): implement portfolio and risk advisory`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

### AGT-5.18 — `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS` — Strategy Proposal Composition and Handoff

**Goal:** Compose and optionally submit an untrusted Strategy-owned proposal carrying thesis, evidence, horizon, invalidation, uncertainty, evaluation scope, and expiry. It has no broker-native fields, approval, order, fill, or authoritative size.

**Depends on:** `AGT-1.02`, `AGT-1.03`, `AGT-1.04`, `AGT-1.05`, `AGT-2.07`, `AGT-3.11`, `AGT-3.13`.
**Phase-0 blockers that must already be closed:** P0.7 Strategy proposal-intake and receipt contracts.
**Provides:** `agentic.strategy-proposals@1`.
**Internal required capabilities:** `agentic.mandate@1`, `agentic.roles@1`, `agentic.model-inference@1`, `agentic.tool-governance@1`, `agentic.context@1`, `agentic.claims@1`, `agentic.synthesis@1`, `agentic.operations@1`.
**Optional capabilities:** —.
**External prerequisites:** `strategy.proposal-intake@1 (proposed owner key)`.
**State:** `None`.
**Role contributions:** `strategy_proposal_synthesizer`.
**Primary method:** `AgenticStrategyProposalComposition.compose_strategy_proposals(request)`.
**Operations:** `COMPOSE`, `SUBMIT`.
**Success/domain outcomes:** `StrategyProposalCandidate`, `StrategyProposalReceipt`.
**Events:** `StrategyProposalComposed`, `StrategyProposalSubmitted`.

**Normalized donor bundle inputs**

- `app/agentic/agents/strategy_desk/trader/**`
- `tests/agentic/unit/test_trader.py`
- `tests/agentic/integration/test_trade_proposal.py`
- `tests/agentic/usage/20_trade_proposals.py`

The Planner must narrow globs to an exact file manifest before execution. `ADD_TO_V3` rows use donor material only as behavioral context and never as parity proof.

**Allowed production paths**

```text
app/contracts/agentic/strategy_proposals.py
app/services/agentic/compose_strategy_proposals/README.md
app/services/agentic/compose_strategy_proposals/__init__.py
app/services/agentic/compose_strategy_proposals/manifest.py
app/services/agentic/compose_strategy_proposals/config.py
app/services/agentic/compose_strategy_proposals/feature.py
app/services/agentic/compose_strategy_proposals/strategy_proposal_composition.py
app/services/agentic/compose_strategy_proposals/proposal_validation.py
app/services/agentic/compose_strategy_proposals/receiver_handoff.py
app/services/agentic/compose_strategy_proposals/roles/strategy_proposal_synthesizer/role.json
app/services/agentic/compose_strategy_proposals/roles/strategy_proposal_synthesizer/prompt.md
tests/contracts/agentic/test_strategy_proposals.py
tests/services/agentic/compose_strategy_proposals/**
pyproject.toml                     # exact entry point only
.importlinter                      # exact feature boundary only
app/services/agentic/README.md     # this feature status/evidence only
docs/CHANGELOG.md                  # accepted release-visible entry only
```

**Manifest and configuration**

- [ ] Create `app/contracts/agentic/strategy_proposals.py` with the exact capability key `agentic.strategy-proposals@1` and protocol/action shape ratified in Phase 0.
- [ ] Make `SPEC.feature_id == "FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS"`, `domain == "agentic"`, and match required/optional/state values above exactly.
- [ ] Accept exactly these feature configuration keys: `proposal_ttl_seconds`, `max_proposals_per_run`, `require_strategy_receipt`, `require_evidence_graph`, `allowed_evaluation_scopes`.
- [ ] Reject unknown and authority-widening configuration before any effect is acquired or provider is staged.
- [ ] Use the repository-standard `feature()` zero-argument factory and register one stable entry-point name.

**Feature-specific implementation steps**

- [ ] Register Strategy Proposal Synthesizer and compose the exact Strategy-owned intake request from supported thesis/synthesis evidence.
- [ ] Include scope/instrument, intended behavior or direction, horizon, invalidation, evidence, uncertainty, assumptions, requested evaluation, and strict expiry.
- [ ] Make broker-native fields, order type, price, lot, quantity, notional, risk approval, execution status, and fill unrepresentable.
- [ ] Submit unchanged through Strategy intake using a capability lease and receiver idempotency; import no Strategy implementation.
- [ ] Treat receiver receipt, rejection, or expiry as the complete Agentic outcome and never present it as strategy acceptance, TradeIntent, approval, order, or fill.

**Owned functional requirements**

- [ ] **FR-AGT-COMPOSE_STRATEGY_PROPOSALS** — Compose thesis, instrument/scope, direction or behavior, horizon, invalidation, evidence, uncertainty, requested evaluation scope, and expiry with no broker, order, fill, approval, price, quantity, lot, notional, or authoritative size fields. Side effects: Model call and schema validation. Evidence: Required field, prohibited field, expiry, and claim-lineage tests.
- [ ] **FR-AGT-SUBMIT_STRATEGY_PROPOSALS** — Map and submit only through Strategy-owned intake under a capability lease and normal identity, scope, freshness, idempotency, and validation rules. Side effects: Receiver call and operations write. Evidence: No privileged route, lease, idempotency, receiver rejection, and cross-domain import tests.
- [ ] **FR-AGT-RECORD_STRATEGY_RECEIPTS** — Treat Strategy receipt, rejection, or expiry as the complete Agentic outcome; never present it as intent, approval, order, or fill truth. Side effects: Workflow/operations write. Evidence: Outcome truth, rejection mapping, expiry, and no-order/fill tests.
- [ ] **FR-AGT-PRESERVE_STRATEGY_AUTHORITY** — Agentic cannot evaluate the strategy into a TradeIntent, approve it, register it, or call Risk/Trading/Brokers directly. Side effects: None. Evidence: Capability and import-negative tests.

**Mandatory focused tests**

- [ ] proposal completeness.
- [ ] prohibited execution fields.
- [ ] exact receiver mapping.
- [ ] lease/idempotency.
- [ ] receipt truth.
- [ ] expiry/stale/dissent/unavailable refusal.
- [ ] mid-handoff removal.
- [ ] Contract immutability/serialization/compatibility and prohibited-field tests.
- [ ] Config defaults, valid boundary values, wrong types, unknown keys, and widening attempts.
- [ ] Mount with dependencies, missing required dependency, optional dependency lifecycle where applicable, staged-publication rollback, repeated close, 100 churn cycles, transactional replacement, runtime-task failure, readiness, and exact cleanup.
- [ ] Role manifest/prompt/composite hash, schema/tool/profile binding, eligibility, prompt mutation, exact registration/disposal, and role-removal degradation tests.
- [ ] Physical deletion: `uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS`.

**Executable usage:** `uv run python -m app.services.agentic.compose_strategy_proposals.strategy_proposal_composition`. The harness must cover at least one success and one fail-closed/declared-degraded scenario without network, credentials, live trading, or production mutation.

**Targeted verification before review**

```powershell
uv run python -m app.services.agentic.compose_strategy_proposals.strategy_proposal_composition
uv run pytest --no-cov tests/contracts/agentic/test_strategy_proposals.py tests/services/agentic/compose_strategy_proposals/
uv run ruff format --check app/contracts/agentic/strategy_proposals.py app/services/agentic/compose_strategy_proposals tests/contracts/agentic/test_strategy_proposals.py tests/services/agentic/compose_strategy_proposals
uv run ruff check app/contracts/agentic/strategy_proposals.py app/services/agentic/compose_strategy_proposals tests/contracts/agentic/test_strategy_proposals.py tests/services/agentic/compose_strategy_proposals
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS
```

**Removal acceptance:** Stop Agentic strategy-proposal composition/submission. Research and deterministic Strategy/Trading continue unchanged.

**Proposed commit:** `feat(agentic): implement strategy proposal composition and handoff`

**Rollback:** disable/unregister the feature and revert the code/entry-point commit. Preserve any committed retained state and record a migration tombstone or compatibility reader; revoke/close all current-generation capabilities, tasks, subscriptions, leases, roles, clients, and staged resources.

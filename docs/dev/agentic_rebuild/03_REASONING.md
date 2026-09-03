# Agentic Rebuild — Phase 3 Claims, Deliberation, and Synthesis

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** Phase 2 workflows/context plus Phase 1 authority and invocation capabilities  
> **Authority:** `app/services/agentic/README.md`

## Purpose

Replace transcript-first multi-agent reasoning with a canonical claim-and-evidence graph, independent challenge, preserved dissent, and typed synthesis. The phase creates eleven role contributions: five evidence analysts, six challengers, and one synthesizer. These roles interpret or challenge owner evidence; they do not silently calculate substitute domain results or authorize outcomes.

---

## AGT-3.11 — `FEAT-AGT-MANAGE_CLAIMS`

**Provides:** `agentic.claims@1`  
**Requires:** mandate, operations, roles, model inference, workflows, context, and ratified persistence.  
**Optional:** governed tools and outcome-calibration evidence.  
**State:** `agentic.claims`, schema v1, `RETAIN`.  
**Primary module:** `claim_graph.py`.  
**Roles:** `analytics_evidence_reviewer`, `fundamental_analyst`, `sentiment_analyst`, `technical_structure_analyst`, `quantitative_analyst`.

**Donor evidence to normalize**

```text
app/agentic/context_memory/models.py
app/agentic/context_memory/repository.py
app/agentic/agents/experimentation/simulation_interpreter/**
app/agentic/agents/market_intelligence/fundamental_analyst/**
app/agentic/agents/market_intelligence/sentiment_analyst/**
app/agentic/agents/market_analysis/technical_analyst/**
app/agentic/agents/market_analysis/quantitative_analyst/**
relevant tests/agentic/unit and integration cases
```

The Planner must split this shared donor material into exact files and record every shared consumer before implementation.

**Production paths**

```text
app/contracts/agentic/claims.py
app/services/agentic/manage_claims/
  README.md __init__.py manifest.py config.py feature.py
  claim_graph.py claim_models.py relations.py reliability.py expiry.py
  migrations.py _store.py
  roles/analytics_evidence_reviewer/{role.json,prompt.md}
  roles/fundamental_analyst/{role.json,prompt.md}
  roles/sentiment_analyst/{role.json,prompt.md}
  roles/technical_structure_analyst/{role.json,prompt.md}
  roles/quantitative_analyst/{role.json,prompt.md}
tests/contracts/agentic/test_claims.py
tests/services/agentic/manage_claims/**
```

**Config keys:** `max_claims_per_graph`, `max_relations_per_graph`, `max_statement_chars`, `max_evidence_refs_per_claim`, `expiry_scan_seconds`, `accepted_claim_schema_versions`.

**Implementation**

- [ ] Represent `OBSERVED_FACT`, `DETERMINISTIC_DERIVATION`, `MODEL_INFERENCE`, `FORECAST`, and `RECOMMENDATION` as distinct types or discriminated variants.
- [ ] Require material claims to carry statement, scope, validity/horizon, evidence and derivation refs, available/observed time, assumptions, confounders, falsifier, supporting/contradicting/dependency relations, uncertainty, author profile, provenance, and status as applicable.
- [ ] Support statuses `SUPPORTED`, `CONTESTED`, `REFUTED`, `UNKNOWN`, and `EXPIRED` through append-only transitions.
- [ ] Make relation semantics explicit: support, contradict, derive, depend, invalidate, and supersede; reject forbidden dependency cycles.
- [ ] Propagate source revision, expiry, refutation, or invalidation through dependent claims without rewriting history.
- [ ] Compute reliability deterministically from evidence coverage/quality, statistical, epistemic, operational, and historically calibrated profile evidence; ignore model self-confidence as authority.
- [ ] Evidence analysts receive exact owner projections and return typed claims only. They may not recalculate an indicator, metric, simulation, optimization, portfolio, Risk, Trading, or broker result when an owner result exists.
- [ ] Refuse non-finite, incompatible, stale, misaligned, leakage-unsafe, unlicensed, or inapplicable evidence according to each role policy.
- [ ] Register all five roles through `agentic.roles@1`, but enable only the Analytics Evidence Reviewer in the first Chat Bot vertical slice.

**Role-specific acceptance**

- **Analytics Evidence Reviewer:** consumes completed versioned Analytics/Simulation/Optimization evidence, cites exact refs, and recomputes nothing.
- **Fundamental Analyst:** requires point-in-time licensed issuer/macro/regulatory evidence and asset-class applicability.
- **Sentiment Analyst:** receives only governed deduplicated text projections after injection/manipulation filtering and separates coverage, measured polarity/event class, uncertainty, and unsupported narrative.
- **Technical and Market-Structure Analyst:** binds instrument, venue, timeframe, session, window, indicator versions, and data-quality evidence and states confirmation/invalidation/leakage constraints.
- **Quantitative Analyst:** uses deterministic estimator/catalog operations and reports sample, estimator, interval/uncertainty, multiple-testing exposure, assumptions, and limitations.

**Tests**

- type/status construction and prohibition on inference-to-fact promotion;
- missing/tampered/wrong-owner evidence;
- relation direction, duplicate relation, cycle, propagation, revision, expiry, supersession;
- deterministic reliability and missing uncertainty dimension;
- role applicability, point-in-time, licensing, injection, canonical-indicator, estimator, sample, non-finite, and leakage cases;
- prompt/manifest integrity and exact role disposal;
- migration/restart/concurrency/import/retention/export;
- provider/context/tool removal and graceful refusal;
- churn, replacement, retained-state removal, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.manage_claims.claim_graph`  
**Commit:** `feat(agentic): implement claim-and-evidence graph`

**Removal:** stop claim mutation and new analyst work, unregister the five roles, preserve committed graphs, and make claim-dependent workflows unready.

---

## AGT-3.12 — `FEAT-AGT-DELIBERATE_RESEARCH`

**Provides:** `agentic.deliberation@1`  
**Requires:** mandate, roles, model inference, tool governance, workflows, claims, operations.  
**Optional:** exact deterministic challenge/evaluation tools.  
**State:** Phase 0 must resolve the README inconsistency; if durable, own a feature-local `agentic.deliberation` namespace, otherwise persist final records through the operations/workflow owner.  
**Primary module:** `research_deliberation.py`.  
**Roles:** `causality_challenger`, `leakage_challenger`, `robustness_challenger`, `risk_challenger`, `compliance_challenger`, `operations_security_challenger`.

**Donor evidence to normalize**

```text
app/agentic/deliberation/**
app/agentic/agents/operations/evaluation_manager/** critique behavior only
app/agentic/agents/portfolio_risk_advisory/** challenge behavior only
tests/agentic/unit/test_deliberation.py
relevant council/advisory integration tests
```

**Production paths**

```text
app/contracts/agentic/deliberation.py
app/services/agentic/deliberate_research/
  README.md __init__.py manifest.py config.py feature.py
  research_deliberation.py deliberation_models.py independence.py stop_conditions.py
  optional migrations.py _store.py only if Phase 0 assigns durable state
  roles/<six challenger role ids>/{role.json,prompt.md}
tests/contracts/agentic/test_deliberation.py
tests/services/agentic/deliberate_research/**
```

**Config keys:** `max_participants`, `max_rounds`, `max_counterclaims_per_claim`, `default_rebuttal_rounds`, `require_independent_first_pass`, `minimum_independence_score`.

**Implementation**

- [ ] Select challenge modes deterministically from task/materiality/risk policy, not from model persuasion.
- [ ] Give challengers the objective, evidence snapshot, and normalized claim IDs before exposing proposer narrative.
- [ ] Commit each independent first pass before rebuttal context becomes available.
- [ ] Record same provider, base model, prompt family, context order, evidence subset, tool results, and decoding-policy correlation.
- [ ] Warn, degrade, or refuse when required independence is not achieved; high-risk workflows may require a distinct evaluated model family or deterministic adversarial test.
- [ ] Preserve every challenge, counterclaim, rebuttal, unresolved dissent, evidence request/result, participant, round, budget, and stop reason.
- [ ] Stop on completion, insufficient evidence, material unresolved conflict, max rounds/fan-out, deadline, budget, policy denial, incident, dependency removal, or cancellation.
- [ ] Never convert consensus, majority vote, challenge success, or silence into authorization or position size.
- [ ] Register six challenger profiles with exact disposal and independent eligibility evidence.

**Tests**

- blind-first challenge and no proposer leakage before commit;
- correlation calculation, warning, and distinct-family high-risk rule;
- deterministic challenger selection and complete challenge-mode coverage;
- dissent preservation and no authorization/size language;
- bounds, stop conditions, cancellation, provider/tool loss, and mid-round removal;
- restart/durable record if selected, or operations/workflow record parity if stateless;
- role mutation/hash failure, exact disposal, replacement, and physical removal.

**Usage:** `uv run python -m app.services.agentic.deliberate_research.research_deliberation`  
**Commit:** `feat(agentic): implement independent challenge and deliberation`

**Removal:** preserve committed assessments/dissent, cancel or checkpoint active rounds, unregister challengers, and retain low-risk single-specialist workflows only where policy permits.

---

## AGT-3.13 — `FEAT-AGT-SYNTHESIZE_RESEARCH`

**Provides:** `agentic.synthesis@1`  
**Requires:** mandate, operations, roles, model inference, context, claims.  
**Optional:** deliberation and profile evaluation.  
**State:** none unless Phase 0 explicitly assigns durable synthesis records; normal persistence is through workflow/operations evidence.  
**Primary module:** `research_synthesis.py`.  
**Role:** `research_synthesizer`.

**Donor evidence to normalize**

```text
app/agentic/deliberation/** synthesis behavior
app/agentic/agents/strategy_desk/strategy_thesis_analyst/** selected synthesis behavior
relevant tests/agentic/unit/test_deliberation.py and thesis tests
```

**Production paths**

```text
app/contracts/agentic/synthesis.py
app/services/agentic/synthesize_research/
  README.md __init__.py manifest.py config.py feature.py
  research_synthesis.py synthesis_validation.py
  roles/research_synthesizer/{role.json,prompt.md}
tests/contracts/agentic/test_synthesis.py
tests/services/agentic/synthesize_research/**
```

**Config keys:** `max_output_chars`, `max_cited_claims`, `require_dissent_preservation`, `require_reliability_breakdown`, `allow_partial_coverage`.

**Implementation**

- [ ] Consume only canonical claim graphs and optional deliberation records; evidence IDs/statuses must derive from supplied records.
- [ ] Separate supported conclusions, contested/refuted/unknown/expired claims, assumptions, uncertainty dimensions, invalidation, unanswered questions, coverage gaps, and dissent.
- [ ] Unresolved material dissent forces a contested or insufficient-evidence disposition.
- [ ] Reject invented citations, unsupported material claims, hidden promotion of claim status, and model-provided deterministic values.
- [ ] Make code, orders, fills, broker fields, Risk approval, authoritative size, kill-switch action, or production registration unrepresentable in synthesis output.
- [ ] Register the Research Synthesizer role and verify exact claim/deliberation binding after model output.

**Tests**

- no invented claim/evidence IDs;
- status, reliability, coverage, invalidation, and dissent preservation;
- material dissent outcome and partial-coverage policy;
- unsupported claim/refusal and schema bounds;
- prohibited authority/execution fields;
- missing role/model/context/deliberation behavior;
- cancellation, exact role disposal, replacement, and physical removal.

**Usage:** `uv run python -m app.services.agentic.synthesize_research.research_synthesis`  
**Commit:** `feat(agentic): implement research synthesis`

**Removal:** cancel synthesis and unregister the role while leaving claims, specialist results, deliberation records, and deterministic domains accessible.

---

## Phase 3 exit gate

- [ ] Claim graph is the canonical machine-readable reasoning record; transcripts and hidden reasoning are unnecessary for replay/audit.
- [ ] All five claim types and five statuses are enforced and source changes propagate without history rewrite.
- [ ] All five evidence analysts use exact owner evidence and refuse rather than silently recalculate.
- [ ] All six challenger profiles perform independent first pass and record correlation/dissent.
- [ ] Research synthesis is claim-bound, dissent-preserving, uncertainty-aware, and non-authoritative.
- [ ] The first Analytics Evidence Reviewer → Research Synthesizer specialist path is ready for Chat Bot integration.
- [ ] All three features pass targeted quality, lifecycle, replacement, removal, and primary-module usage evidence.

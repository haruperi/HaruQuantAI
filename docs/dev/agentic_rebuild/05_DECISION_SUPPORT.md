# Agentic Rebuild — Phase 5 Decision Support

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** canonical claims/synthesis and ratified receiver contracts  
> **Authority:** Strategy, Indicators, Portfolio, Risk, and Agentic owner specifications

## Purpose

Deliver three non-authoritative outputs: JSON Strategy/Indicator DSL candidates, expiring portfolio/risk advice, and Strategy proposal candidates. Agentic owns composition and provenance only. Receiver domains own schema validation, calculation, acceptance, lifecycle, Risk decisions, TradeIntent creation, execution, orders, and fills.

---

## AGT-5.16 — `FEAT-AGT-COMPOSE_STRATEGY_SPECS`

**Provides:** `agentic.strategy-specs@1`  
**Requires:** mandate, operations, roles, model inference, claims, synthesis, research-search lineage, and exact Strategy/Indicators DSL schema/validation capabilities.  
**Optional:** context, governed tools, research-design candidate refs.  
**State:** none.  
**Primary module:** `strategy_spec_composition.py`.  
**Role:** `strategy_dsl_author`.  
**Operations:** `COMPOSE`, `VALIDATE_HANDOFF`.

**Donor evidence to normalize**

```text
No direct legacy JSON DSL feature
Selected hypothesis/thesis and coder contract tests as behavior clues only
Current Strategy Builder/DSL specifications are authoritative when available
```

**Production paths**

```text
app/contracts/agentic/strategy_specs.py
app/services/agentic/compose_strategy_specs/
  README.md __init__.py manifest.py config.py feature.py
  strategy_spec_composition.py schema_binding.py candidate_validation.py
  roles/strategy_dsl_author/{role.json,prompt.md}
tests/contracts/agentic/test_strategy_specs.py
tests/services/agentic/compose_strategy_specs/**
```

**Config keys:** `max_spec_bytes`, `accepted_dsl_major_versions`, `max_validation_attempts`, `require_hypothesis_reference`, `allow_indicator_spec_candidates`.

**Implementation**

- [ ] Resolve an exact receiver-owned Strategy or Indicator DSL schema/version before model invocation.
- [ ] Bind the candidate to approved hypothesis/claim/synthesis IDs, schema digest, role/prompt/model provenance, campaign/search history, and request identity.
- [ ] Generate only declarative building blocks, parameters, inputs, transforms, signals, state, entries/exits, management rules, constraints, and metadata permitted by that schema.
- [ ] Make compiled objects, arbitrary source files, broker operations, order fields, credentials, approvals, position sizes, and production lifecycle actions unrepresentable.
- [ ] Run deterministic schema and semantic pre-validation after model output; correction attempts are bounded and every failed candidate remains observable.
- [ ] Return an `UnsupportedExpressionReport` when the DSL cannot represent the requirement.
- [ ] Never auto-switch to source generation. Code fallback requires a new authenticated request, a proven DSL gap, a capability lease, and the Phase 6 sandbox feature.
- [ ] Submit only through the receiver-owned validation/intake capability and preserve the receiver receipt unchanged.
- [ ] Strategy/Indicators alone compile, register, version, promote, retire, or execute accepted artifacts.

**Tests**

- exact schema/version/digest binding;
- missing/unsupported receiver schema and provider removal;
- required hypothesis/claim lineage;
- deterministic validation and correction-attempt ceiling;
- unsupported-expression path;
- prohibited source/broker/order/approval/size/compiled fields;
- receiver rejection/acceptance truth and no false registration;
- prompt/manifest integrity, role eligibility, cancellation, replacement, churn, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.compose_strategy_specs.strategy_spec_composition`  
**Commit:** `feat(agentic): implement json strategy and indicator dsl composition`

**Removal:** stop new composition and unregister the role; receiver-owned schemas and accepted artifacts remain unaffected.

---

## AGT-5.17 — `FEAT-AGT-ADVISE_PORTFOLIO`

**Provides:** `agentic.portfolio-advisory@1`  
**Requires:** mandate, operations, roles, model inference, context, claims, synthesis, and exact current Portfolio/Risk/Analytics/account-evidence capabilities.  
**Optional:** governed tools and deliberation; challenge becomes required by configured task/materiality policy.  
**State:** none; advice is retained only through workflow/operations evidence and expires strictly.  
**Primary module:** `portfolio_advisory.py`.  
**Role:** `portfolio_advisory_synthesizer`.  
**Operation:** `ADVISE`.

**Donor evidence to normalize**

```text
app/agentic/agents/portfolio_risk_advisory/portfolio_risk_advisor/**
relevant advisory, Risk-critic, deliberation, and receiver-rejection tests
```

**Production paths**

```text
app/contracts/agentic/portfolio_advisory.py
app/services/agentic/advise_portfolio/
  README.md __init__.py manifest.py config.py feature.py
  portfolio_advisory.py advisory_validation.py evidence_binding.py
  roles/portfolio_advisory_synthesizer/{role.json,prompt.md}
tests/contracts/agentic/test_portfolio_advisory.py
tests/services/agentic/advise_portfolio/**
```

**Config keys:** `max_advisory_bytes`, `max_evidence_age_seconds`, `max_advisory_lifetime_seconds`, `require_risk_challenge`, `require_compliance_challenge`.

**Implementation**

- [ ] Require current Portfolio allocation/state, account/position evidence, Analytics evidence, mandate scope, and authoritative Risk evidence for the exact requested scope.
- [ ] Treat absent/unreadable observation time as stale and refuse.
- [ ] Bind every concern, trade-off, relative preference or bounded range, question, uncertainty, and expiry to exact owner evidence and claims.
- [ ] Require Risk and/or Compliance challenge by set equality when policy says so; missing challenge refuses rather than implying consent.
- [ ] Preserve dissent and unanswered questions.
- [ ] Make lot size, quantity, notional, exact executable price, order, TradeIntent, Risk approval, verdict-by-absence, kill-switch action, and broker field unrepresentable.
- [ ] Expiry is strict; expired advice is never refreshed by Chat Bot or another role without a new request and current evidence.
- [ ] Any downstream Portfolio/Risk request uses receiver-owned contracts and complete normal controls; Agentic advice itself is never a decision.

**Tests**

- fresh/stale/missing/wrong-account/wrong-scope evidence;
- current allocation/account/Risk/Analytics binding;
- non-binding schema and prohibited execution/approval fields;
- challenge set equality, dissent, and missing-challenge refusal;
- strict expiry and no silent refresh;
- receiver rejection/authority truth;
- context/tool/deliberation/role/provider loss;
- cancellation, replacement, churn, and physical removal.

**Usage:** `uv run python -m app.services.agentic.advise_portfolio.portfolio_advisory`  
**Commit:** `feat(agentic): implement portfolio and risk advisory`

**Removal:** stop new advice and unregister the role; Portfolio and Risk continue normally, and prior advice expires while remaining only as audit/workflow evidence.

---

## AGT-5.18 — `FEAT-AGT-COMPOSE_STRATEGY_PROPOSALS`

**Provides:** `agentic.strategy-proposals@1`  
**Requires:** mandate, operations, roles, model inference, context, claims, synthesis, exact Strategy proposal-intake capability; governed tool lease is required for submission.  
**Optional:** research-design and strategy-spec candidate refs.  
**State:** none; receiver and workflow/operations own durable receipts.  
**Primary module:** `strategy_proposal_composition.py`.  
**Role:** `strategy_proposal_synthesizer`.  
**Operations:** `COMPOSE`, `SUBMIT`.

**Donor evidence to normalize**

```text
app/agentic/agents/strategy_desk/trader/**
legacy TradeProposal/TradeProposalReceipt contracts and tests
relevant Strategy proposal-intake integration tests
```

The old “Trader” name is retired. Preserve only proposal composition/handoff behavior under the new Strategy Proposal Synthesizer identity.

**Production paths**

```text
app/contracts/agentic/strategy_proposals.py
app/services/agentic/compose_strategy_proposals/
  README.md __init__.py manifest.py config.py feature.py
  strategy_proposal_composition.py receiver_handoff.py proposal_validation.py
  roles/strategy_proposal_synthesizer/{role.json,prompt.md}
tests/contracts/agentic/test_strategy_proposals.py
tests/services/agentic/compose_strategy_proposals/**
```

**Config keys:** `max_proposal_bytes`, `max_proposal_lifetime_seconds`, `require_research_synthesis`, `require_receiver_schema_resolution`, `max_handoff_attempts`.

**Implementation**

- [ ] Compose a candidate carrying thesis/synthesis, instrument and allowed scope, intended direction or behavior, horizon, invalidation, evidence/claims, uncertainty, assumptions, requested evaluation scope, campaign/search history, and strict expiry.
- [ ] Make broker-native fields, order type, executable price, quantity, lot size, notional, Risk approval, TradeIntent, order status, fill, and kill-switch action structurally absent.
- [ ] Resolve and map to the exact Strategy-owned intake contract/version; do not duplicate that contract in Agentic.
- [ ] Submit unchanged through Strategy’s capability under a request-bound lease and normal identity, freshness, scope, idempotency, and validation rules.
- [ ] Do not import Strategy implementation or obtain a privileged validation path.
- [ ] Return only the receiver-declared receipt, rejection, or expiry semantics.
- [ ] Never represent receipt/acceptance as strategy registration, Risk approval, TradeIntent, order, or fill.
- [ ] Refuse stale, expired, unsupported, out-of-scope, required-dissent-unresolved, receiver-unavailable, or lease-denied proposals without an alternate route.

**Tests**

- proposal completeness, digest, claim/synthesis lineage, and expiry;
- prohibited broker/order/price/size/approval/intent/fill fields;
- exact receiver contract/version mapping and no implementation import;
- request-bound lease, denied-call-never-invoked, idempotency, bounded retry;
- receiver rejection/acceptance/expiry truth;
- no direct Risk/Trading/Brokers capability;
- stale/dissent/unavailable refusal;
- mid-handoff cancellation/removal, role disposal, replacement, churn, physical deletion.

**Usage:** `uv run python -m app.services.agentic.compose_strategy_proposals.strategy_proposal_composition`  
**Commit:** `feat(agentic): implement strategy proposal composition and handoff`

**Removal:** stop new proposals/handoffs and unregister the role; Strategy-owned requests/records and every downstream deterministic control remain unchanged.

---

## Phase 5 workflows

### `WF-AGT-COMPOSE_STRATEGY_SPEC`

```text
approved hypothesis/claims + exact receiver DSL schema
→ Strategy DSL Author
→ deterministic schema validation and bounded correction
→ receiver semantic validation/intake
→ candidate receipt or UnsupportedExpressionReport
```

### `WF-AGT-ADVISE_PORTFOLIO`

```text
fresh Portfolio/Risk/Analytics/account evidence
→ relevant analysts/claim graph
→ required Risk/Compliance challenge
→ Portfolio Advisory Synthesizer
→ expiring non-binding advisory or insufficient evidence
```

### `WF-AGT-COMPOSE_STRATEGY_PROPOSAL`

```text
supported synthesis/thesis
→ Strategy Proposal Synthesizer
→ deterministic schema/prohibited-field/expiry checks
→ request-bound capability lease
→ Strategy-owned intake
→ receipt/rejection/expiry only
```

Every workflow must preserve identity, evidence, uncertainty, dissent, provenance, idempotency, cancellation, deadline, and receiver ownership.

---

## Phase 5 exit gate

- [ ] JSON DSL is the normal artifact-authoring path and receiver schemas are authoritative.
- [ ] Unsupported DSL requirements produce a typed report rather than automatic source generation.
- [ ] Portfolio advice is fresh, expiring, challenge-tested, and structurally non-binding.
- [ ] Strategy proposals lack all execution/approval fields and enter only the normal Strategy intake.
- [ ] No feature requires or resolves a Brokers capability.
- [ ] All three roles pass prompt/manifest integrity, evaluation, exact disposal, and removal evidence.
- [ ] All three features and workflows pass targeted contract, lifecycle, authority-negative, receiver, quality, usage, replacement, and physical-removal gates.

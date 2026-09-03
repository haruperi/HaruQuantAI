# Agentic Rebuild — Phase 4 Governed Research

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** workflow/operations foundation and canonical claims/synthesis  
> **Authority:** current Research, Simulation, Optimization, and Agentic owner specifications

## Purpose

Create campaign-level anti-overfitting governance and convert supported claim graphs into falsifiable receiver-owned research candidates. Agentic may design and account for research; it does not become the authoritative owner of Simulation runs, Optimization trials, dataset truth, or holdout allocation.

---

## AGT-4.14 — `FEAT-AGT-GOVERN_RESEARCH_SEARCH`

**Provides:** `agentic.research-search@1`  
**Requires:** `agentic.mandate@1`, `agentic.operations@1`, `agentic.workflows@1`, ratified persistence/clock/digest and receiver holdout/campaign contracts.  
**State:** `agentic.research_search`, schema v1, `RETAIN`.  
**Primary module:** `research_search_governance.py`.  
**Operations:** `REGISTER_CAMPAIGN`, `REGISTER_FAMILY`, `REGISTER_VARIANT`, `RECORD_ATTEMPT`, `RESERVE_HOLDOUT`, `CLOSE_CAMPAIGN`, `INSPECT`.

**Donor evidence to normalize**

```text
app/agentic/agents/experimentation/experiment_designer/**
app/agentic/agents/experimentation/optimization_coordinator/**
app/agentic/migrations/experimentation.py or equivalent
legacy holdout-use and trial-ledger tests
```

The old exact-`spec_hash` holdout mechanism is useful historical evidence but is not sufficient V3 policy. It must be preserved as a legacy receipt and superseded by campaign/family/dataset/holdout accounting.

**Production paths**

```text
app/contracts/agentic/research_search.py
app/services/agentic/govern_research_search/
  README.md __init__.py manifest.py config.py feature.py
  research_search_governance.py near_duplicate_policy.py holdout_policy.py
  campaign_models.py migrations.py _store.py
tests/contracts/agentic/test_research_search.py
tests/services/agentic/govern_research_search/**
```

**Config keys:** `max_open_campaigns`, `max_variants_per_family`, `max_attempts_per_campaign`, `near_duplicate_threshold`, `max_holdout_reservations`, `require_failure_reason`, `require_multiple_testing_policy`.

**Implementation**

- [ ] Register immutable `research_campaign_id`, `hypothesis_family_id`, `dataset_family_id`, `search_budget_id`, and `holdout_id` before governed trials.
- [ ] Bind every variant to objective, claim/hypothesis lineage, prompt/model/tool/profile versions, parameters/features, requested receiver operation, amendments, and budget.
- [ ] Record every attempt, completion, failure, null result, abandonment, and reason; enforce attempted = completed + failed + explicitly cancelled/expired according to the ratified conservation model.
- [ ] Classify near-duplicate hypotheses/specifications deterministically and charge them to the same family/campaign/holdout budget unless policy proves material independence.
- [ ] Prevent text changes, reordering, renamed IDs, superficial parameter changes, prompt changes, or new hashes from resetting campaign or holdout scarcity.
- [ ] Coordinate holdout reservation/consumption with the canonical receiver owner; Agentic stores owner receipts and cannot independently allocate or free holdout.
- [ ] Bind reservation to campaign, hypothesis family, dataset family, holdout, protocol/request digest, principal, purpose, issue/expiry, and consumed status.
- [ ] Record multiple-testing, false-discovery, sequential/alpha-spending, embargo/purge, cost, null-result, and predeclared termination policy where applicable.
- [ ] Refuse absent history, exhausted budget, conflicting reservation, undeclared amendment, unverifiable family, or receiver unavailability before execution.
- [ ] Own additive strict migrations, concurrency/uniqueness rules, restart reconstruction, export, and legacy receipt import.

**Tests**

- identity/digest and immutable registration;
- attempted/completed/failed/null conservation;
- near-duplicate evasion using rename, reorder, tiny parameter changes, new prompts/models, and new hashes;
- concurrent reservation and double-consumption attempts;
- reservation expiry versus consumed budget;
- cross-campaign/dataset/family scope rules;
- multiple-testing/embargo/termination metadata;
- owner receipt tamper/unavailable behavior;
- migration/restart/import/export/retention;
- removal preserves scarcity and cannot reset consumed budget;
- churn, replacement, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.govern_research_search.research_search_governance`  
**Commit:** `feat(agentic): implement research campaign and search governance`

**Removal:** refuse new governed trials/holdouts, preserve all campaign/attempt/receipt history, and never free consumed scarcity by feature removal.

---

## AGT-4.15 — `FEAT-AGT-DESIGN_RESEARCH`

**Provides:** `agentic.research-design@1`  
**Requires:** mandate, operations, roles, model inference, context, claims, research search; exact Research/Simulation/Optimization candidate-validation contracts.  
**Optional:** deliberation, synthesis, governed tools.  
**State:** none.  
**Primary module:** `research_design.py`.  
**Roles:** `hypothesis_designer`, `experiment_designer`, `bounded_search_designer`.  
**Operations:** `DESIGN_HYPOTHESIS`, `DESIGN_EXPERIMENT`, `DESIGN_SEARCH`.

**Donor evidence to normalize**

```text
app/agentic/agents/strategy_desk/strategy_thesis_analyst/**
app/agentic/agents/experimentation/experiment_designer/**
app/agentic/agents/experimentation/optimization_coordinator/**
relevant hypothesis, experiment, sweep, simulation, and optimization tests/usage
```

**Production paths**

```text
app/contracts/agentic/research_design.py
app/services/agentic/design_research/
  README.md __init__.py manifest.py config.py feature.py
  research_design.py hypothesis_design.py experiment_design.py search_design.py
  candidate_binding.py
  roles/hypothesis_designer/{role.json,prompt.md}
  roles/experiment_designer/{role.json,prompt.md}
  roles/bounded_search_designer/{role.json,prompt.md}
tests/contracts/agentic/test_research_design.py
tests/services/agentic/design_research/**
```

**Config keys:** `max_hypotheses_per_request`, `max_candidate_bytes`, `require_receiver_schema_resolution`, `require_registered_campaign`, `allow_search_design`.

**Implementation**

- [ ] Hypothesis candidates bind supported claim IDs, asset/account/venue scope, horizon, mechanism, prerequisites, assumptions, confounders, falsifier/rejection criterion, required data, leakage constraints, campaign/family identity, and contested status where applicable.
- [ ] Reject a hypothesis without a falsifier, registered campaign/family, sufficient evidence, or explicit contested disposition.
- [ ] Experiment candidates target an exact receiver-owned contract/version and bind immutable inputs, dataset/time splits, embargo/purge, costs/slippage, seeds/randomness, baselines, metrics, uncertainty, stop rules, evidence classes, and falsification outcomes.
- [ ] Search candidates target an exact Optimization contract/version and bind declared parameter/feature space, objective, search method, trial/search budget, early stop, robustness/stability/overfit requirements, multiple-testing policy, and holdout policy.
- [ ] Submit only through receiver-owned validation capability under a capability lease; the receiver may accept, reject, normalize only where its contract permits, or return incompatibility.
- [ ] Preserve the exact candidate and receiver receipt; never rewrite a result to match the proposal.
- [ ] Do not reconstruct Research, Simulation, or Optimization contracts inside Agentic.
- [ ] Register the three role contributions with hash, eligibility, tool, schema, and exact-disposer evidence.

**Tests**

- required hypothesis fields, falsifiability, confounders, applicability, and contested evidence;
- absent/exhausted/unregistered campaign or family;
- exact receiver contract/version resolution and unsupported version;
- experiment split/embargo/cost/seed/baseline/metric/stop completeness;
- search space/objective/budget/early-stop/robustness/holdout completeness;
- candidate digest immutability and unchanged receiver request;
- receiver rejection/tamper/unavailable behavior;
- no invented Simulation/Optimization result;
- prompt/manifest mutation, role eligibility, exact disposal;
- capability loss, cancellation, replacement, churn, and physical removal.

**Usage:** `uv run python -m app.services.agentic.design_research.research_design`  
**Commit:** `feat(agentic): implement falsifiable research design`

**Removal:** cancel design work and unregister the three roles; preserve campaign history and any receiver-owned run/result records.

---

## Phase 4 integration workflows

### `WF-AGT-DESIGN_RESEARCH`

```text
supported claim graph
→ register/resolve campaign + hypothesis family
→ Hypothesis Designer candidate
→ deterministic completeness/falsifier checks
→ Experiment Designer candidate
→ receiver-owned Research/Simulation validation
→ exact receipt or refusal
```

### `WF-AGT-GOVERNED_SEARCH`

```text
validated experiment identity
→ resolve search budget and holdout policy
→ Bounded Search Designer candidate
→ deterministic near-duplicate/accounting check
→ receiver-owned Optimization validation/execution
→ record every attempt/failure/null and owner receipts
→ claim/synthesis interpretation; never rank-only success
```

**Workflow acceptance**

- idempotent campaign/candidate submission;
- point-in-time and leakage-safe evidence;
- all-trial conservation and stable scarcity across restart/removal;
- receiver authority and exact request/result binding;
- cancellation/deadline/budget/provider/tool/dependency failures;
- no silent alternative search or holdout route.

---

## Phase 4 exit gate

- [ ] Campaign, family, dataset, search-budget, and holdout identities are exact and immutable.
- [ ] Near-duplicate and rehash/rename evasion cannot reset trial or holdout accounting.
- [ ] Every failed/null/abandoned trial remains visible.
- [ ] Hypotheses are falsifiable and experiments/searches target exact receiver contracts.
- [ ] Research, Simulation, and Optimization remain authoritative for validation, execution, and results.
- [ ] Three designer roles pass prompt integrity, eligibility, removal, and evaluation evidence.
- [ ] Both features and both workflows pass targeted lifecycle, persistence where applicable, replacement, physical removal, quality, and usage gates.

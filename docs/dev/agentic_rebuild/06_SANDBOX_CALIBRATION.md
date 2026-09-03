# Agentic Rebuild — Phase 6 Sandbox Fallback and Outcome Calibration

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** evaluated model/tool/workflow foundation; JSON DSL for sandbox fallback; outcome owner contracts for calibration  
> **Authority:** `app/services/agentic/README.md` and ratified Plugins/Workspace/receiver contracts

## Purpose

Add two optional capabilities after the safer core is operational: a staging-only source-artifact fallback when the JSON DSL is demonstrably insufficient, and deterministic post-horizon calibration of forecasts/recommendations. Neither capability may self-deploy, self-promote, self-modify, or bypass receiver authority.

---

## AGT-6.19 — `FEAT-AGT-AUTHOR_SANDBOX_ARTIFACTS`

**Provides:** `agentic.sandbox-artifacts@1`  
**Requires:** mandate, operations, roles, model inference, tool governance, workflows, strategy-spec composition, and a real ratified sandbox/isolation/staging capability.  
**State:** feature-local metadata namespace using the Phase-0-supported retention enum; staged/ephemeral bytes follow explicit TTL/cleanup, never an invented `RETAIN_METADATA` enum.  
**Primary module:** `sandbox_artifact_authoring.py`.  
**Role:** `sandbox_code_author`.  
**Operations:** `AUTHOR`, `INSPECT`, `CLEANUP`.

**Donor evidence to normalize**

```text
app/agentic/agents/engineering/coder/**
legacy CodeSpecification, CodeArtifact, SandboxResult, path-security, artifact-store tests
relevant code-artifact and promotion integration tests
```

The donor’s useful staging, hashing, provenance, dependency, and path-validation behavior may be adapted. Any claim that the old sandbox was genuinely ephemeral, credential-free, or network-denied requires inspected runtime evidence; absent that evidence, record `DONOR_UNAVAILABLE` for isolation parity.

**Production paths**

```text
app/contracts/agentic/sandbox_artifacts.py
app/services/agentic/author_sandbox_artifacts/
  README.md __init__.py manifest.py config.py feature.py
  sandbox_artifact_authoring.py path_security.py artifact_manifest.py
  sandbox_binding.py cleanup.py migrations.py _store.py
  roles/sandbox_code_author/{role.json,prompt.md}
tests/contracts/agentic/test_sandbox_artifacts.py
tests/services/agentic/author_sandbox_artifacts/**
```

**Config keys:** `sandbox_profile_id`, `max_files`, `max_bytes`, `max_cpu_seconds`, `max_memory_mb`, `max_storage_mb`, `sandbox_timeout_seconds`, `network_policy`, `allowed_languages`, `allowed_dependency_sources`, `staging_ttl_seconds`.

**Implementation**

- [ ] Require an authenticated exact source specification, the receiver/schema reason JSON DSL is insufficient, and the typed human action required by policy.
- [ ] Acquire a request-bound sandbox lease attesting ephemeral isolation, credential absence, network denial or explicit egress allowlist, process/user isolation, filesystem boundary, CPU/memory/storage/time ceilings, and staging-only writes.
- [ ] Refuse when any required isolation property is unknown or merely claimed by model output.
- [ ] Validate every declared raw path before parsing and every resolved path after resolution.
- [ ] Reject traversal, absolute paths, drive/UNC/device paths, reserved names, normalization collisions, symlink/hardlink escape, path case collisions, and writes outside the leased staging root.
- [ ] Resolve dependencies only from approved sources, pin versions/hashes where policy requires, and record a complete dependency manifest/SBOM.
- [ ] Generate and execute tests/static checks only inside the sandbox lease; record command identity, environment, exit status, bounded output digests, and resource use.
- [ ] Produce a content-addressed manifest containing specification digest, all files/hashes, dependencies/SBOM, tests/results, static checks, role/prompt/model/tool lineage, complete search/revision history, lease identity, and cleanup policy.
- [ ] Never import, hot-load, install, register, deploy, or execute generated code in the production application.
- [ ] Stage only for receiver/human review. Any future receiver acceptance is a separate receiver-owned workflow.
- [ ] Cleanup must be idempotent and auditable; partial cleanup is an incident, not silent success.
- [ ] Register the Sandbox Code Author only when a real sandbox provider is ready and evaluated.

**Tests**

- missing/invalid DSL-gap evidence and missing human action;
- absent/under-attested/expired/wrong-object lease;
- credential/network/process/filesystem/resource isolation;
- raw/resolved traversal, absolute/UNC/device/reserved, normalization/case collision, symlink/hardlink escape;
- dependency source/version/hash/SBOM rules;
- timeout, CPU/memory/storage/file/byte limits;
- test/static-check failure and bounded output;
- no import/hot-load/install/register/deploy/production execution;
- content-addressed manifest and full provenance/search history;
- cancellation, provider loss, partial failure, idempotent cleanup, removal mid-generation;
- state migration/restart/TTL/retained metadata according to ratified policy;
- role hash/eligibility/disposal, replacement, churn, and physical deletion.

**Usage:** `uv run python -m app.services.agentic.author_sandbox_artifacts.sandbox_artifact_authoring` using a deterministic fake sandbox that performs no host mutation outside a temporary test directory.  
**Commit:** `feat(agentic): implement sandboxed source artifact fallback`

**Removal:** stop intake, revoke leases, cancel sandboxes, unregister the role, clean eligible ephemeral/staged resources, retain only policy-approved metadata/audit, and never remove receiver-owned artifacts.

---

## AGT-6.20 — `FEAT-AGT-CALIBRATE_OUTCOMES`

**Provides:** `agentic.outcome-calibration@1`  
**Requires:** mandate, operations, profile evaluation, claims, ratified persistence/clock, and exact receiver-owned matured outcome capabilities.  
**Optional:** workflow/role/topology and cost evidence.  
**State:** `agentic.outcome_calibration`, schema v1, `RETAIN`.  
**Primary module:** `outcome_calibration.py`.  
**Operations:** `CALIBRATE_FORECAST`, `CALIBRATE_RECOMMENDATION`, `INSPECT`.

**Donor evidence to normalize**

```text
No direct complete legacy post-horizon calibration feature
Selected evaluation-manager, analytics-interpretation, trace/cost, proposal/advisory records as behavioral inputs only
ADD_TO_V3 for scoreable forecasts, matured outcome binding, and change candidates
```

**Production paths**

```text
app/contracts/agentic/outcome_calibration.py
app/services/agentic/calibrate_outcomes/
  README.md __init__.py manifest.py config.py feature.py
  outcome_calibration.py scoring.py baseline_value.py outcome_binding.py
  change_candidates.py migrations.py _store.py
tests/contracts/agentic/test_outcome_calibration.py
tests/services/agentic/calibrate_outcomes/**
```

**Config keys:** `accepted_forecast_schema_versions`, `minimum_matured_outcomes`, `maximum_outcome_age_seconds`, `calibration_windows`, `required_baselines`, `change_candidate_thresholds`.

**Implementation**

- [ ] Require a scoreable forecast or recommendation created before the outcome and carrying target, probability/bounded distribution, horizon, observation rule, invalidation, expected regime, expected economic effect, and immutable provenance.
- [ ] Reject forecasts authored or materially amended after the outcome cutoff.
- [ ] Resolve matured outcome truth only through the semantic owner and bind owner ID/version/hash, observation time, finality/revision state, regime, transaction costs/slippage where relevant, receiver rejection/amendment, and deterministic/single-agent baseline outcome.
- [ ] Refuse immature, provisional, wrong-scope, wrong-owner, stale, incompatible, or unverifiable outcomes rather than score them as neutral.
- [ ] Compute appropriate deterministic calibration/error measures such as Brier/log score for probabilistic forecasts, interval coverage, direction/magnitude error, invalidation timing, unsupported-claim rate, reversal rate, receiver rejection/amendment rate, latency, reliability, observed cost, cost-adjusted value of information, and incremental utility over matched baselines.
- [ ] Keep raw P&L as one outcome component only; it cannot replace calibration, baseline, uncertainty, regime, and cost analysis.
- [ ] Aggregate only across compatible profile/workflow/task/regime cohorts and preserve sample size and uncertainty.
- [ ] Create an immutable evidence-backed `AgenticChangeCandidate` for role, prompt, model, tool, workflow, or topology changes when configured criteria are met.
- [ ] Never edit production prompts, role manifests, provider profiles, permissions, mandate, thresholds, workflow graphs, or eligibility directly. Change candidates return to the normal human/evaluation/change process.
- [ ] Preserve corrected/revised outcomes by appending and referencing prior calibration rather than overwriting.

**Tests**

- pre-outcome immutability and post-outcome amendment rejection;
- horizon maturity and observation-rule boundary;
- owner identity/version/hash/finality and revision behavior;
- probabilistic, interval, categorical, direction, and magnitude scoring;
- invalidation timing, regime, costs/slippage, rejection/amendment;
- deterministic and single-agent baseline parity;
- P&L-only refusal and value-of-information arithmetic;
- compatible cohort/sample/uncertainty constraints;
- no self-modification from change candidate;
- migration/restart/correction/export/retention;
- missing receiver/profile evidence, cancellation, replacement, churn, retained-state removal, physical deletion.

**Usage:** `uv run python -m app.services.agentic.calibrate_outcomes.outcome_calibration`  
**Commit:** `feat(agentic): implement post-horizon outcome calibration`

**Removal:** stop new scoring/change candidates, preserve committed calibration history, and never fabricate neutral performance for missing outcomes.

---

## Phase 6 workflows

### `WF-AGT-AUTHOR_SANDBOX_ARTIFACT`

```text
receiver/schema-confirmed DSL gap + authenticated source specification
→ typed human action when required
→ request-bound real sandbox lease
→ Sandbox Code Author
→ path/dependency/static/test/resource validation
→ content-addressed staging manifest
→ cleanup evidence
```

### `WF-AGT-CALIBRATE_OUTCOME`

```text
immutable pre-outcome forecast/recommendation
→ horizon maturity check
→ owner-owned outcome + baseline retrieval
→ deterministic calibration/error/value scoring
→ profile/workflow/topology attribution
→ optional non-self-applying change candidate
```

**Workflow acceptance**

- exact object/lease/human-action binding;
- no production code loading or deployment;
- complete artifact/search/SBOM/provenance evidence;
- authoritative outcome and matched baseline binding;
- deterministic repeatability and correction history;
- cancellation, incident containment, provider/receiver removal, and cleanup.

---

## Phase 6 exit gate

- [ ] Source generation cannot start without a proven DSL gap and fully attested real sandbox lease.
- [ ] Every generated artifact is staging-only, content-addressed, reproducible, bounded, and cleaned by explicit policy.
- [ ] No generated code is imported, registered, deployed, or executed by the production application.
- [ ] Forecasts/recommendations are scoreable before outcomes and bound to authoritative matured results.
- [ ] Calibration measures uncertainty, baselines, cost, regime, and incremental utility; raw P&L is insufficient.
- [ ] Learning creates only governed change candidates and never self-modifies production behavior.
- [ ] Both features pass contract, security, lifecycle, persistence, replacement, role/provider/receiver removal, physical deletion, quality, and usage evidence.

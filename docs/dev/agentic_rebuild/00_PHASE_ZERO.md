# Agentic Rebuild — Phase 0 Readiness

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts  
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

## 6. Phase 0 — Contract, Ownership, Provider, and Donor Readiness

### AGT-0.01 — Freeze baseline and normalize the legacy donor

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Record baseline `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`, donor `d9c614f20939f76bc1d8020ea8837da29eb2a9da`, donor tree/test SHAs, and deletion commit `4fef8b614cba073180d4dc9bedf5ec0dc19b956a` in a tracked migration intake record.
- [ ] Extract `app/agentic/`, `tests/agentic/`, fixtures, usage programs, and relevant supporting docs into a read-only raw staging area, excluding caches, build outputs, secrets, local databases, and generated artifacts.
- [ ] Produce a complete source manifest and SHA-256 inventory; prove a second extraction is byte-identical.
- [ ] Split the raw tree into the 20 normalized feature/slice bundles listed in this plan, marking shared donor files and consumers.
- [ ] Update the legacy disposition matrix from specification-level to source/test-level evidence; do not claim parity yet.

**Expected changed paths**

- `docs/dev/agentic_migration/LEGACY_SOURCE_MANIFEST.md`
- `docs/dev/agentic_migration/legacy_source_manifest.json`
- `.migration/agentic/<task-id>/** (gitignored)`

**Proposed commit:** `docs(agentic): pin and inventory the legacy donor`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.02 — Reconcile Agentic internal contracts, state, events, and factory conventions

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Compare the committed authoritative README, approved architecture artifacts, Kernel types, current feature examples, and validator behavior.
- [ ] Ratify the exact public contract file inventory, shared primitive ownership, naming conventions, failure union, canonical digest algorithm, and event location/dispatch modes.
- [ ] Use the current in-repository zero-argument entry-point factory convention `feature()` unless a separate project-wide architecture change is approved; update stale `create_feature` wording where it implies a required symbol.
- [ ] Translate every proposed retention phrase to supported `StateDeclaration` vocabulary. Use business TTL/byte cleanup inside the feature rather than inventing retention enums.
- [ ] Resolve whether deliberation, synthesis, and Chat Bot conversations require feature-owned durable state; make the feature registry, state table, feature sections, and future manifests agree.
- [ ] Ratify role artifact JSON schema, prompt normalization, composite hash, contribution handle, and eligibility-reference semantics.

**Expected changed paths**

- `app/services/agentic/README.md`
- `app/contracts/README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT.md`

**Proposed commit:** `docs(agentic): reconcile internal contract and state conventions`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.03 — Ratify Workspace/System prerequisites

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Inventory current Workspace capability keys and operations; do not use proposed `workspace.settings@1`, `workspace.auth-context@1`, `workspace.persistence@1`, `workspace.worker-admission@1`, `workspace.retention@1`, `workspace.artifact-staging@1`, or `workspace.secret-resolution@1` until an owner defines or maps them.
- [ ] Select or specify exact owners for authenticated principal/session, workspace settings, clock/ID generation, opaque secret references, migrations/transactions, writer fencing, worker admission, retention/legal hold, artifact staging, and diagnostic/export storage.
- [ ] Define the minimum read/write operations Agentic stateful features need; avoid exposing raw SQLite connections or generic unrestricted SQL when a bounded transaction/migration port is required.
- [ ] Define startup/readiness behavior when Workspace capabilities are absent, removed, or replaced.
- [ ] Add owner-domain specification gaps as separate Workspace/System Tasks before the first consuming Agentic feature.

**Expected changed paths**

- `app/services/workspace/README.md`
- `app/contracts/workspace/**`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`

**Proposed commit:** `docs(workspace): ratify Agentic prerequisite capabilities`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.04 — Ratify Plugins, model-provider, role-contribution, and sandbox boundaries

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Map the proposed role-contribution dependency to the current `plugins.register-contributions@1` contract or specify a narrower replacement; do not invent `plugins.contributions@1` locally.
- [ ] Define a provider-neutral model-runtime provider contract owned outside Agentic implementation and determine whether it belongs to Plugins or a separately installed provider distribution.
- [ ] Move Google ADK from domain identity to an optional provider. Prefer an optional dependency extra/separate provider package so the base HaruQuantAI install and deterministic Agentic tests do not require ADK.
- [ ] Map sandbox requirements to `plugins.sandbox-permissions@1`, `plugins.isolate-analysis@1`, Workspace isolation/staging, or define an owner gap if those contracts cannot attest all required properties.
- [ ] Define provider discovery, explicit selection, health, generation, replacement, cleanup, and unavailable behavior without provider types crossing contracts.

**Expected changed paths**

- `app/services/plugins/README.md`
- `app/contracts/plugins/**`
- `pyproject.toml`
- `uv.lock`
- `docs/dev/agentic_firm/14_google_adk_and_model_providers.md`

**Proposed commit:** `docs(plugins): ratify Agentic provider and sandbox boundaries`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.05 — Ratify evidence and deterministic-calculation boundaries

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Inventory exact current Data, Catalogue, Indicators, Analytics, Research, Portfolio, Risk, Strategy, and Trading read capabilities relevant to Agentic workflows.
- [ ] Define small immutable evidence projections with owner identity, schema version, availability/observation time, data quality, lineage/content hash, applicability, freshness, and licensing/trust where applicable.
- [ ] Select exact capabilities for Analytics result interpretation, fundamental evidence, sentiment/news evidence, technical/indicator evidence, quantitative estimators, account/position evidence, and realized outcomes.
- [ ] Specify which missing evidence yields refusal and which yields explicit partial coverage for each role/workflow.
- [ ] Confirm no Agentic feature imports receiver implementations or reconstructs calculations from raw data when an owner result exists.

**Expected changed paths**

- `app/contracts/data/**`
- `app/contracts/catalogue/**`
- `app/contracts/indicator/**`
- `app/contracts/analytics/**`
- `app/contracts/research/**`
- `app/contracts/portfolio/**`
- `app/contracts/risk/**`
- `app/contracts/strategy/**`
- `app/contracts/trading/**`

**Proposed commit:** `docs(agentic): ratify deterministic evidence dependencies`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.06 — Ratify Research, Simulation, Optimization, campaign, and holdout ownership

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Decide the canonical owner and exact contracts for research objectives, hypotheses/protocols, campaigns, dataset families, experiment requests/results, optimization searches/trials/results, holdout definitions, reservations, and consumption.
- [ ] Ensure Agentic `research-search` stores only its campaign/search accounting and owner receipts; it must not become a second Simulation/Optimization run ledger or authoritative holdout allocator.
- [ ] Define near-duplicate classification inputs and the cross-owner transaction/reconciliation used to prevent a rename or hash change from resetting scarcity.
- [ ] Define idempotency, concurrency, reservation expiry, consumed-budget behavior, multiple-testing metadata, and failure/null-result retention.
- [ ] Add receiver-domain specification Tasks before `GOVERN_RESEARCH_SEARCH` and `DESIGN_RESEARCH` if current contracts are insufficient.

**Expected changed paths**

- `app/services/research/README.md`
- `app/contracts/research/**`
- `app/services/simulator/README.md`
- `app/contracts/simulator/**`
- `app/services/optimization/README.md`
- `app/contracts/optimization/**`

**Proposed commit:** `docs(research): ratify Agentic research and holdout boundaries`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.07 — Ratify Strategy, Indicators, Portfolio, Risk, and outcome boundaries

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Ratify JSON Strategy and Indicator DSL schemas, semantic validation, compilation, candidate intake, unsupported-expression result, and artifact ownership.
- [ ] Ratify Strategy proposal intake and receipt semantics; prove it cannot be interpreted as TradeIntent, Risk approval, order, or fill.
- [ ] Ratify current Portfolio/Analytics/account evidence and Portfolio/Risk review contracts used by non-binding advisory.
- [ ] Ratify matured outcome references and observation rules for Strategy, Simulation, Optimization, Portfolio, Risk, Trading, and Analytics calibration.
- [ ] Confirm Agentic has no direct Brokers dependency and all consequential paths remain Strategy → Risk → Trading → Brokers.

**Expected changed paths**

- `app/services/strategy/README.md`
- `app/contracts/strategy/**`
- `app/services/indicators/README.md`
- `app/contracts/indicator/**`
- `app/services/portfolio/README.md`
- `app/contracts/portfolio/**`
- `app/services/risk/README.md`
- `app/contracts/risk/**`

**Proposed commit:** `docs(agentic): ratify decision-support receiver boundaries`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.08 — Ratify D-IFACE/UI Chat Bot companion features

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Define the D-IFACE feature ID, capability, authenticated chat-turn request/result, cancellation, conversation inspection, typed human-action endpoints, and bounded event-stream/replay cursor.
- [ ] Define `WorkspaceContextSnapshot` and `AssistantContextContribution` ownership, schemas, redaction rules, versioning, size limits, source widget identity, and exact contribution disposal.
- [ ] Define the UI Chat Bot widget manifest, lifecycle, focus/accessibility, loading/streaming/refusal/error/degraded states, specialist attribution, evidence links, and removal behavior.
- [ ] Decide conversation-state ownership: D-IFACE/Workspace session store versus an Agentic `operator_conversations` namespace. If Agentic state is required, use a supported purge-on-uninstall policy and explicit TTL.
- [ ] Prove removing a widget removes its future context contribution, removing Chat Bot leaves the UI usable, and removing D-IFACE does not remove internal Agentic capabilities.

**Expected changed paths**

- `app/services/interfaces/README.md or successor D-IFACE registry`
- `app/contracts/interfaces/**`
- `app/ui/README.md`
- `app/contracts/ui/**`
- `app/services/agentic/README.md`

**Proposed commit:** `docs(interfaces): specify Chat Bot transport and UI context`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.09 — Ratify evaluation and eligibility bootstrap

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Define registered, enabled, bootstrap-evaluable, eligible, suspended, and revoked role/model/profile states without circular authority.
- [ ] Create a deterministic bootstrap provider/profile usable only for contract and evaluation harnesses, not production research or decision support.
- [ ] Define how the first real provider/profile receives owner-approved seed evaluation evidence before `EVALUATE_PROFILES` is active, and how the feature subsequently owns normal eligibility decisions.
- [ ] Define human rubric identity, deterministic grader ownership, model-grader calibration minimums, expiry/re-evaluation, emergency revocation, and council-ablation thresholds.
- [ ] Prove no profile can evaluate or promote itself in isolation and no bootstrap flag confers receiver or live-trading authority.

**Expected changed paths**

- `app/services/agentic/README.md`
- `docs/dev/agentic_firm/04_evaluation_standard.md`
- `docs/dev/agentic_firm/10_agent_standard.md`

**Proposed commit:** `docs(agentic): specify profile eligibility bootstrap`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.10 — Prepare architecture tooling, registration, configuration, and dependency policy

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Add the planned Agentic feature package patterns to architecture-check, Import Linter, feature-documentation validation, discovery tests, and physical-removal tooling specifications.
- [ ] Reserve 20 stable entry-point names and require the current `feature()` factory convention.
- [ ] Define application configuration examples for feature enablement and explicit provider selection without a root Agentic settings module.
- [ ] Move or plan removal of unconditional Google ADK dependency according to P0.4; keep a deterministic model provider available to tests.
- [ ] Define Agentic profile-readiness expectations for offline/research/backtest/live without making optional Agentic capabilities mandatory for deterministic live safety.

**Expected changed paths**

- `pyproject.toml`
- `.importlinter`
- `scripts/architecture_check.py`
- `scripts/validate_feature_docs.py`
- `scripts/verify_feature_removal.py`
- `tests/composition/**`

**Proposed commit:** `build(agentic): prepare feature tooling and optional provider policy`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.11 — Migrate documentation authority and retire stale architecture claims

**Type:** specification/intake/tooling Task; no Agentic production business behavior.

**Checklist**
- [ ] Update `docs/dev/agentic_firm/README.md` and all supporting files to point to `app/services/agentic/README.md` as authority.
- [ ] Replace the stale 22-numbered implementation plan with a pointer to this semantic feature plan and mark the old package/role hierarchy as donor evidence.
- [ ] Update `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `app/services/README.md`, `app/contracts/README.md`, and `docs/CHANGELOG.md` to remove claims that deleted Agentic code is implemented.
- [ ] Preserve supporting policy content where compatible; do not rewrite historical research findings merely to fit the new architecture.
- [ ] Add stable links among the authoritative README, this plan, the donor manifest, and the source-level disposition ledger.

**Expected changed paths**

- `docs/dev/agentic_firm/**`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `app/services/README.md`
- `app/contracts/README.md`
- `docs/CHANGELOG.md`

**Proposed commit:** `docs(agentic): migrate documentation authority to focused features`

**Exit:** every stated decision is recorded in its semantic owner; no downstream Executor needs to guess.

### AGT-0.GATE — Phase-0 implementation authorization gate

All boxes must be checked before `AGT-1.00`:

- [ ] The exact 20-feature registry, capability IDs, contract files, factory symbol, event location, state declarations, and supported retention policies agree across the Agentic README, Contracts README, this plan, and tooling.
- [ ] Every proposed external capability key is replaced by an existing exact key or an accepted owner-domain specification Task.
- [ ] D-IFACE and UI Chat Bot companion contracts are accepted.
- [ ] Model provider and sandbox provider packaging are accepted; base tests need no paid/network provider.
- [ ] Eligibility bootstrap is non-circular, deterministic, and non-authoritative.
- [ ] Donor source/test bundles are pinned, hashed, scoped, and ready, or each affected Task records `DONOR_UNAVAILABLE`.
- [ ] State migration/import rules preserve evidence without reintroducing Agentic authority for receiver-owned records.
- [ ] Stale documentation and dependency comments no longer claim the deleted implementation is active.
- [ ] Architecture, import, documentation, and removal tools are ready to recognize the new packages.
- [ ] Owner explicitly authorizes production implementation.

**Proposed commit:** `docs(agentic): close rebuild phase-zero gates`

---

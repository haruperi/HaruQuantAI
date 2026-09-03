# Agentic Rebuild — Phase 7 Integration and Acceptance

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)  
> **Prerequisite:** the features required by each workflow  
> **Authority:** current Agentic, D-IFACE, UI, and receiver-domain specifications

## 9. Phase 7 — Vertical Slices, Companion Features, and Domain Completion

### AGT-7.01 — First read-only Chat Bot vertical slice

**Goal:** deliver the first useful end-to-end slice without strategy, portfolio, Risk, Trading, Brokers, holdout, or source-code authority.

```text
ENFORCE_MANDATE
→ OPERATE_RUNS
→ REGISTER_ROLES
→ GOVERN_TOOL_CALLS
→ INVOKE_MODELS
→ RUN_WORKFLOWS
→ ASSEMBLE_CONTEXT
→ MANAGE_CLAIMS (Analytics Evidence Reviewer only)
→ SYNTHESIZE_RESEARCH
→ ASSIST_OPERATOR
→ D-IFACE/UI companion
```

**Checklist**

- [ ] Mount only the exact capabilities above with the offline deterministic provider and one eligible specialist profile.
- [ ] Capture a fresh typed context contribution from an Analytics/Simulation result widget.
- [ ] Prove a safe UI-definition question is answered directly from public widget metadata.
- [ ] Prove a result-interpretation question is routed deterministically to `analytics_evidence_reviewer`.
- [ ] Refresh material values through the authoritative Analytics/Simulation capability before claim creation.
- [ ] Build a claim graph and synthesis, then return one answer in the same conversation with specialist/version attribution, evidence refs, uncertainty, refusal/failure, and provenance.
- [ ] Exercise unsupported specialist, stale context, removed widget, model unavailable, evidence unavailable, cancellation, and Agentic feature removal.
- [ ] Prove the UI remains usable and deterministic domains remain healthy when Chat Bot or all Agentic features are absent.

**Integration tests**

```text
tests/system/agentic/test_chat_bot_direct_answer.py
tests/system/agentic/test_chat_bot_specialist_handoff.py
tests/system/agentic/test_chat_bot_context_refresh.py
tests/system/agentic/test_chat_bot_feature_removal.py
```

**Commit:** `test(agentic): verify the first read-only chat bot vertical slice`

---

### AGT-X-IFACE-01 — D-IFACE Agentic and Chat Bot gateway companion

**Owner:** D-IFACE/API, not Agentic.

**Checklist**

- [ ] Implement the Phase-0-ratified authenticated Chat Bot capability and wire schemas.
- [ ] Expose submit turn, cancel turn, inspect conversation, stream events with bounded replay/resume, and typed human-action decision operations.
- [ ] Resolve Agentic capabilities through the composition graph; import no Agentic implementation.
- [ ] Enforce authentication/session/user/account scope, rate/size limits, request/correlation/idempotency IDs, cancellation, backpressure, stable failure mapping, and redaction.
- [ ] Never expose prompts, credentials, provider objects, hidden reasoning, unrestricted traces, or raw persistence rows.
- [ ] Map capability unavailable/degraded states without inventing a fallback response.
- [ ] Pass interface contract, transport, streaming order, reconnect, cancellation, auth, rate-limit, and Agentic-removal tests.

**Expected paths:** exact D-IFACE feature package, `app/contracts/interfaces/**`, interface tests, entry point, owner README/changelog.

**Commit:** `feat(interfaces): expose agentic chat bot gateway`

---

### AGT-X-UI-01 — UI Chat Bot widget and context-contribution companion

**Owner:** UI, not Agentic.

**Checklist**

- [ ] Implement one removable widget named exactly **Chat Bot** using only generated/public contracts and UI-local modules.
- [ ] Add a typed contribution registry in which each widget registers only its declared public context schema and receives an exact disposer.
- [ ] Build a fresh `WorkspaceContextSnapshot` per turn from route/page, focused widget, public selected entity refs, filters, timeframe/session/date, visible safe status/error codes, permissions, redaction metadata, contribution versions, and observation time.
- [ ] Exclude raw DOM, credentials, provider objects, private service state, unrestricted screenshots, and executable content.
- [ ] Render loading, streaming, direct answer, specialist routing, specialist attribution, evidence refs, uncertainty, partial coverage, refusal, failure, cancellation, degraded/unavailable, and retry-safe states accessibly.
- [ ] Present navigation suggestions without executing them automatically.
- [ ] Removing a widget must remove its contribution from the next snapshot; removing Chat Bot must not affect the workspace; removing D-IFACE/Agentic must show an explicit unavailable state.
- [ ] Pass keyboard/focus/screen-reader, responsive, context cleanup, stream ordering, cancellation, stale-turn, and physical-removal tests.

**Expected paths:** exact UI feature/widget package, generated contract adapters, UI tests, UI README/registry/changelog.

**Commit:** `feat(ui): add contextual chat bot widget`

---

### AGT-7.02 — Adaptive research and deliberation workflows

**Workflows:** `WF-AGT-REVIEW_EVIDENCE`, `WF-AGT-RESEARCH_OBJECTIVE`, `WF-AGT-EVALUATE_PROFILE`, and challenge parts of advisory/design.

**Checklist**

- [ ] Verify deterministic baseline, single-specialist, challenger, and council escalation under the same task policy.
- [ ] Prove no unnecessary council is started when a deterministic or one-specialist result is sufficient.
- [ ] Exercise all five evidence analyst profiles with owner evidence and all six challengers with blind-first assessment.
- [ ] Preserve claim types/statuses, source revisions/expiry, uncertainty, counterclaims, correlation, and dissent through synthesis.
- [ ] Run deterministic-only, best single-agent, full-council, each-role-removed, and no-peer-visibility ablations.
- [ ] Keep councils disabled until uncertainty-adjusted benefit exceeds latency, cost, and failure surface.
- [ ] Test role/model/tool/evidence removal during every stage and verify precise degraded/refused outcomes.

**Commit:** `test(agentic): verify adaptive research and deliberation workflows`

---

### AGT-7.03 — Research design, search, DSL, advisory, proposal, sandbox, and calibration workflows

**Workflows:** `WF-AGT-DESIGN_RESEARCH`, `WF-AGT-GOVERNED_SEARCH`, `WF-AGT-COMPOSE_STRATEGY_SPEC`, `WF-AGT-ADVISE_PORTFOLIO`, `WF-AGT-COMPOSE_STRATEGY_PROPOSAL`, `WF-AGT-AUTHOR_SANDBOX_ARTIFACT`, `WF-AGT-CALIBRATE_OUTCOME`.

**Checklist**

- [ ] Run supported claim → campaign/family → falsifiable hypothesis → experiment candidate → receiver validation.
- [ ] Run validated experiment → bounded search candidate → all-trial recording → Optimization result interpretation without rank-only success.
- [ ] Prove near-duplicate/rehash/rename paths cannot reset search or holdout accounting.
- [ ] Run hypothesis → JSON DSL candidate → deterministic validation → receiver receipt or unsupported-expression report.
- [ ] Run fresh portfolio/Risk evidence → required challenges → expiring non-binding advice.
- [ ] Run synthesis → Strategy proposal candidate → request-bound lease → Strategy receipt/rejection/expiry, never TradeIntent/order/fill.
- [ ] Run proven DSL gap → typed human action → real sandbox lease → staged content-addressed artifact → cleanup.
- [ ] Run immutable forecast/recommendation → matured owner outcome/baselines → deterministic calibration/value → non-self-applying change candidate.
- [ ] Exercise cancellation, deadline, budget, provider/tool/receiver absence, tamper, replay, and feature removal for each workflow.

**Commit:** `test(agentic): verify governed research and decision-support workflows`

---

### AGT-7.04 — Security, threat-model, and authority-negative suite

**Checklist**

- [ ] Prompt, retrieved-text, page/widget, memory, peer-message, tool-result, and remote-provider injection attacks.
- [ ] Poisoned, contradictory, stale, revised, unlicensed, wrong-scope, and look-ahead evidence.
- [ ] Forged/replayed/expired/wrong-object/wrong-environment human action and capability lease.
- [ ] Privilege escalation through role title, prompt, tool registration, fallback, workflow graph, context, memory, or receiver mapping.
- [ ] Secret exfiltration through contracts, logs, events, prompts, traces, exports, provider errors, sandbox output, and UI streaming.
- [ ] Unbounded loop/fan-out/retry/queue/context/output/token/tool/cost/compute/storage behavior.
- [ ] Sandbox path, symlink, filesystem, process, credential, egress, dependency, resource, and cleanup attacks.
- [ ] Holdout/search evasion through renaming, rehashing, prompt/model changes, parameter variation, restart, removal, or new campaign abuse.
- [ ] Provider/model silent substitution and unqualified fallback.
- [ ] Static/runtime proof that no Agentic path imports broker SDKs, resolves broker mutation, creates orders, approves Risk, clears kill switches, or deploys production artifacts.

**Expected tests:** `tests/security/agentic/**`, contract prohibited-field tests, architecture/import scans, system authority-negative tests.

**Commit:** `test(agentic): add security and authority-negative acceptance suite`

---

### AGT-7.05 — Complete removability, replacement, and durability matrix

**Checklist**

- [ ] For each of 20 features: cold start absent, enable, disable, 100 churn cycles, failed mount rollback, dependency loss, optional provider arrival/removal/recovery, config remount, shadow replacement success/failure, runtime-task failure, and physical deletion.
- [ ] Verify exact cleanup of capabilities, tasks, subscriptions, callbacks, contribution handles, leases, clients, sandboxes, files, waits, and provider generations.
- [ ] Verify stateful features preserve/purge state exactly as declared, survive restart, reject incompatible schema, and do not auto-down-migrate.
- [ ] Remove each analyst/challenger/synthesizer role and verify only declared workflows degrade.
- [ ] Remove Chat Bot, D-IFACE gateway, UI widget, model provider, sandbox provider, and memory independently.
- [ ] Delete the complete Agentic domain and prove kernel/composition/UI shell/deterministic domains start, accepted deterministic behavior remains, and Risk/Trading/Brokers safety is unchanged.
- [ ] Run retained-state owner-uninstall and reinstallation/replacement scenarios.

**Expected tests:** `tests/removal/agentic/**`, composition replacement/readiness tests, state migration/restart tests, feature-removal script fixtures.

**Commit:** `test(agentic): verify domain-wide durability and removability`

---

### AGT-7.06 — Documentation reconciliation and final release gate

**Checklist**

- [ ] Update every feature status/README with exact runtime evidence; leave incomplete features `Missing` or `Partial` truthfully.
- [ ] Reconcile `app/services/agentic/README.md`, `app/contracts/README.md`, `app/services/README.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`, D-IFACE/UI registries, and supporting `docs/dev/agentic_firm/` documents.
- [ ] Update source-level donor disposition and prove every in-scope donor behavior/test is covered, adapted, superseded, retired with parity, or explicitly added to V3.
- [ ] Prove no application/test/build/package/runtime path imports `.migration` and delete approved nonshared normalized bundles before review.
- [ ] Verify all 20 entry points, contracts, manifests, configs, state declarations, role artifacts, workflows, events, usage commands, and removal results agree with documentation.
- [ ] Run the full repository gate exactly once after targeted work is complete.
- [ ] Record final release evidence and any intentionally deferred feature without overstating completion.

**Commit:** `docs(agentic): reconcile rebuilt domain and release evidence`

---

## 10. Verification Strategy

### Fast task iteration

During a feature Task:

```powershell
uv run pytest --no-cov <exact contract and feature tests>
uv run ruff format --check <exact changed Python paths>
uv run ruff check <exact changed Python paths>
uv run python -m app.services.agentic.<feature>.<primary_module>
```

Do not run bare `pytest` or the full repository gate while iterating.

### Individual pre-review checks

Each feature runs:

```powershell
uv run pytest --no-cov <exact focused tests>
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run python scripts/verify_feature_removal.py --feature <FEATURE_ID>
```

Use the exact current script arguments verified during Phase 0; documentation examples are not passing evidence until executed.

### Final gate

```powershell
uv run python scripts/ci_check.py
```

The final gate must include branch coverage at or above the configured floor, warning-free deterministic tests, contracts/manifest/config/documentation drift, import architecture, entry-point discovery, lifecycle/replacement/readiness, security, D-IFACE/UI, state durability, primary usage, and physical-removal evidence.

---

## 11. Git, Review, and Rollback Policy

### Branch and review

- One Task branch and one atomic accepted feature commit per focused feature or explicitly named companion Task.
- Planner, Executor, and Reviewer use the normal HaruQuantAI workflow unless the Owner explicitly authorizes a documentation-only bypass.
- Allowed paths, donor bundle, dependencies, migration ownership, tests, and commit message are frozen in the Task spec.
- Review compares implementation against current owner contracts and the authoritative README, not donor structure.

### Commit policy

- Do not combine sibling features because they share a contract file or migration concern.
- A shared contract-foundation change is `AGT-1.00`; later feature contracts are owned by their feature Task.
- Receiver-domain spec/contract Tasks and D-IFACE/UI companions remain separate commits under their semantic owners.
- Do not mark a tracker row complete without executable evidence paths and accepted commit SHA.

### Rollback policy

- Prefer disable/unregister and provider rollback over history rewrite.
- Revoke leases and human waits, cancel/drain managed work, unregister exact contributions, close clients/sandboxes/subscriptions, and publish readiness changes.
- Preserve append-only/audit/search/holdout/calibration evidence according to retention policy.
- Never destructively down-migrate committed evidence merely to roll back code.
- Restore the previous compatible provider generation when replacement fails; do not silently substitute an unevaluated model/tool/provider.
- Receiver-owned artifacts and deterministic decisions are never deleted by Agentic rollback.

---

## Phase 7 completion gate

- [ ] All 20 focused feature Tasks are complete or truthfully deferred without claiming domain completion.
- [ ] All 22 role profiles are hash-verified, evaluated, explicitly eligible where enabled, and exactly removable.
- [ ] All 12 workflows have executable integration evidence and documented failure/degradation paths.
- [ ] Chat Bot uses fresh typed context, deterministic routing, same-conversation handoff, and no direct mutation authority.
- [ ] Security/authority-negative, durability/replacement, retained-state, and full-domain deletion suites pass.
- [ ] JSON DSL is primary; sandbox source is exceptional and staging-only.
- [ ] Claim/dissent/failure/null/search/holdout/calibration evidence cannot be silently erased.
- [ ] No direct Agentic-to-Brokers path exists.
- [ ] Documentation and runtime truth agree.
- [ ] The final repository CI gate passes.

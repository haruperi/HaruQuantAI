# Agentic Rebuild — Phase 7 Integration and Acceptance

> **Parent plan:** [`docs/dev/AGENTIC_REBUILD_PLAN.md`](../AGENTIC_REBUILD_PLAN.md)
> **Authority:** `app/services/agentic/README.md` and current owner-domain contracts
> **Baseline:** `068d8af0e5b4dfb8dece8e988e2960f41afdc75e`

## 9. Phase 7 — Vertical Slices, Companion Features, and Domain Completion

### AGT-7.01 — First read-only Chat Bot vertical slice

**Depends on:** `AGT-1.01`–`AGT-1.05`, `AGT-2.06`, `AGT-2.07`, `AGT-3.11`, `AGT-3.13`, `AGT-2.10`, and accepted D-IFACE/UI companion contracts.

- [ ] Compose mandate, operations, roles, tool governance, deterministic/evaluated model provider, workflows, context, claims, synthesis, and operator assistance through capability keys only.
- [ ] Enable initially only `chat_bot`, `analytics_evidence_reviewer`, and `research_synthesizer` role profiles.
- [ ] Demonstrate: user focuses a result widget, asks what it shows, Chat Bot explains safe metadata, then asks why the run performed poorly, Chat Bot delegates to Analytics Evidence Reviewer, authoritative Analytics evidence is fetched, claims are created, synthesis returns, and Chat Bot presents one attributed answer.
- [ ] Prove stale browser values cannot override Analytics truth.
- [ ] Prove missing Analytics capability yields typed unavailable/partial behavior rather than recomputation.
- [ ] Remove the result widget and prove its context contribution disappears on the next turn.
- [ ] Remove `ASSIST_OPERATOR` and prove UI/workstation remains usable.
- [ ] Remove the model provider and prove deterministic domains remain healthy and Chat Bot is explicitly unavailable.
- [ ] Record end-to-end latency, token/cost, trace, cancellation, and cleanup evidence.

**Proposed commit:** `test(agentic): verify the read-only Chat Bot vertical slice`

### AGT-X-IFACE-01 — D-IFACE Agentic and Chat Bot gateway companion

This is an Interfaces-domain feature Task, not an Agentic feature.

- [ ] Implement authenticated submit/inspect/cancel/human-action/trace/replay/quarantine/readiness/evidence-export operations required by the ratified interface contract.
- [ ] Implement Chat Bot turn submission, cancellation, conversation inspection, bounded streaming with sequence/cursor/resume, and stable `CAPABILITY_UNAVAILABLE` behavior.
- [ ] Resolve Agentic capability keys dynamically through `FeatureContext`; import no Agentic implementation.
- [ ] Apply transport rate/size limits, principal/session binding, request/correlation IDs, cancellation, backpressure, and redaction.
- [ ] Preserve provider/feature generation, specialist attribution, evidence references, refusal/failure, and dissent in wire mapping.
- [ ] Add interface README, usage harness, contract/wire parity, authentication, streaming, removal, and absence tests.

**Proposed commit:** `feat(interfaces): expose Agentic and Chat Bot capabilities`

### AGT-X-UI-01 — UI Chat Bot widget and context contribution companion

This is a UI-domain feature Task, not an Agentic feature.

- [ ] Add a removable widget named exactly **Chat Bot** under the UI feature ownership ratified in P0.8.
- [ ] Implement a typed context-contribution registry with exact disposer, contribution version, page/widget identity, selected public entity references, filters, timeframe/session/date, safe visible status/error codes, redaction metadata, and observation time.
- [ ] Never send full DOM, credentials, unrestricted screenshots, provider objects, or arbitrary executable content.
- [ ] Refresh the snapshot per message and discard contributions from unmounted widgets.
- [ ] Render loading, streamed answer, specialist routing, specialist attribution, evidence links, partial coverage, refusal, unavailable, unauthorized, stale, cancelled, error, and retry states accessibly.
- [ ] Chat Bot initially offers read context, answer, explain, delegate, summarize, and navigation suggestions only; no direct business or widget mutation.
- [ ] Add component, workspace, focus/keyboard, accessibility, context-disposal, temporal order/resume, interface parity, browser, and removal tests.

**Proposed commit:** `feat(ui): add contextual Chat Bot widget`

### AGT-7.02 — Adaptive research and deliberation workflows

**Depends on:** `MANAGE_CLAIMS`, `DELIBERATE_RESEARCH`, `SYNTHESIZE_RESEARCH`, relevant evidence capabilities, and `EVALUATE_PROFILES`.

- [ ] Verify deterministic-only, one-specialist, specialist-plus-challenger, and bounded-council paths.
- [ ] Prove escalation is caused by materiality/uncertainty/value policy, not by model request.
- [ ] Verify blind first pass, correlation disclosure, evidence requests through leases, bounded rebuttal, preserved dissent, and stop conditions.
- [ ] Run council ablation and keep councils disabled unless incremental uncertainty-adjusted benefit exceeds cost, latency, and failure surface.
- [ ] Verify no research result can authorize, size, register, or execute a trade.

**Proposed commit:** `test(agentic): verify adaptive research workflows`

### AGT-7.03 — Research design, search, DSL, advisory, proposal, sandbox, and calibration workflows

- [ ] Verify hypothesis → campaign/family registration → experiment request → receiver result → search request → all-trial ledger → holdout receipt → synthesis.
- [ ] Verify near-duplicate and renamed hypotheses consume the same approved family/holdout budget.
- [ ] Verify JSON DSL candidate → receiver validation/receipt and unsupported-expression → separately approved sandbox fallback.
- [ ] Verify portfolio advisory expires and remains non-binding with no executable quantity or approval.
- [ ] Verify Strategy proposal intake uses a capability lease and receipt never becomes TradeIntent/order/fill.
- [ ] Verify sandbox output remains staging-only and survives no feature-removal leak.
- [ ] Verify matured outcome calibration uses authoritative outcomes/baselines and produces only a change candidate.

**Proposed commit:** `test(agentic): verify governed decision-support workflows`

### AGT-7.04 — Security, threat-model, and authority-negative suite

- [ ] Prompt, memory, page/widget, peer, tool-result, and retrieved-document injection.
- [ ] Poisoned, contradictory, stale, revised, unlicensed, cross-account, cross-user, and out-of-scope evidence.
- [ ] Forged/replayed/expired/mutated human action and capability lease.
- [ ] Provider/model substitution, credential leakage, region/privacy mismatch, and output-schema smuggling.
- [ ] Role/prompt hash mutation, wildcard scope, conflict-of-interest, self-evaluation, and eligibility forgery.
- [ ] Research-budget/holdout evasion by rename, rehash, parameter tweak, family split, concurrent request, and restart.
- [ ] Sandbox path traversal, symlink escape, network/credential/resource violation, dependency-source spoofing, and cleanup failure.
- [ ] Static scan proving no Agentic contract/package names Brokers mutation capabilities, SDKs, order/fill types, kill-switch clear, Risk approval, or deployment operations.

**Proposed commit:** `test(agentic): add adversarial security and authority suite`

### AGT-7.05 — Complete removability, replacement, and durability matrix

- [ ] Run targeted physical-removal verification for all 20 features.
- [ ] Verify required-consumer blocking and optional-consumer remount for every graph edge.
- [ ] Verify transactional replacement success, shadow failure rollback, health failure, consumer remount, quiesce/drain, and degraded old-scope cleanup.
- [ ] Verify runtime task failure withdraws only the failed owner and affected consumers.
- [ ] Verify restart reconstruction for every stateful feature and no terminal workflow reopening.
- [ ] Verify entire `app/services/agentic/` deletion keeps `haruquantai --status`, composition, UI shell, and deterministic safety domains operational.
- [ ] Verify no stale roles, context contributions, leases, model clients, tasks, listeners, sandboxes, staged bytes, or provider-generation references survive removal.
- [ ] Verify retained state remains readable/exportable only through permitted owner paths and purge-on-uninstall state follows policy.

**Proposed commit:** `test(agentic): verify domain-wide durability and removability`

### AGT-7.06 — Documentation reconciliation and final release gate

- [ ] All 20 feature READMEs match runtime `FeatureSpec` and strict config keys.
- [ ] Agentic README feature/FR/workflow/status/state/role tables match implemented truth.
- [ ] `app/contracts/README.md`, `app/services/README.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, supporting Agentic docs, D-IFACE/UI registries, and `docs/CHANGELOG.md` agree.
- [ ] All donor behaviors are closed at source/test level and normalized nonshared bundles are deleted with restore provenance.
- [ ] Every primary-module usage harness passes.
- [ ] Targeted Agentic tests are warning-free and deterministic.
- [ ] Run the complete repository gate once, after implementation and review fixes:

```powershell
uv run python scripts/ci_check.py
```

- [ ] Confirm project branch coverage remains at or above the configured 80% floor.
- [ ] Mark the Agentic domain `Completed` only after every feature, workflow, NFR, companion boundary, and removal gate is executable evidence.

**Proposed commit:** `docs(agentic): complete rebuild evidence and status`

---

## 10. Verification Strategy

### Fast task iteration

```powershell
git diff --name-only
git diff --cached --name-only
git status --short
uv run pytest --no-cov tests/contracts/agentic/test_<capability>.py tests/services/agentic/<feature>/
uv run pytest --no-cov --lf tests/services/agentic/<feature>/
uv run pytest --no-cov -n auto tests/contracts/agentic/test_<capability>.py tests/services/agentic/<feature>/
```

Do not use bare `pytest`, an unfiltered `uv run pytest`, coverage, or `scripts/ci_check.py` during implementation iteration.

### Individual pre-review checks

```powershell
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run lint-imports
uv run python scripts/architecture_check.py
uv run python scripts/validate_feature_docs.py
uv run pytest --no-cov <affected tests>
uv run python scripts/verify_feature_removal.py --feature FEAT-AGT-<ACTION>
```

### Final gate

```powershell
uv run python scripts/ci_check.py
```

Coverage is only final integration evidence. It does not replace lifecycle, dependency, failure, persistence, security, replacement, readiness, or physical-removal assertions.

---

## 11. Git, Review, and Rollback Policy

### Branch and review

- One branch/Task per feature, e.g. `feature/feat-agt-enforce-mandate`.
- Planner writes a complete path-bounded implementation handoff.
- Executor changes only approved paths and may not resolve specification gaps by invention.
- Reviewer verifies architecture, behavior, authority, tests, usage, cleanup, state, donor reconciliation, and deletion evidence before acceptance.
- Merge in dependency order. Parallel branches rebase onto the latest accepted provider commit before review.

### Commit policy

- One atomic accepted commit per focused feature where practicable.
- Separate owner-domain specification/companion changes when their semantic owner differs.
- Never combine unrelated cleanup, refactoring, dependency upgrades, or formatting sweeps with a feature Task.
- Commit messages listed in each Task are the default and may be refined without changing scope.

### Rollback policy

- Pre-publication activation failures close the new scope and leave no provider published.
- Pre-commit replacement failures retain the old provider generation.
- Post-commit consumer-remount/cleanup failure is reported as degraded; do not falsely claim rollback.
- Feature rollback disables/unregisters the feature and reverts code/config while preserving retained evidence.
- Additive migrations are not destructively reversed; use tombstones, compatibility readers, or a later approved migration.
- Revoke exact leases, contributions, subscriptions, model clients, tasks, and sandbox resources on rollback.
- Receiver-owned requests/results remain with the receiver and are not deleted by Agentic rollback.

---

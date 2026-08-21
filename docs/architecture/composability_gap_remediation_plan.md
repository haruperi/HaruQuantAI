# HaruQuantAI Spatiotemporal Composability Gap Remediation Plan

## Document status

- **Type:** Dry-run implementation plan only
- **Baseline branch:** `main`
- **Audited baseline commit:** `c1584cb572fee29e119ec0daebb689b247aafe40`
- **Target implementation branch:** Create a new implementation branch from the latest passing `main` after this plan is approved
- **Primary goal:** Correct the remaining spatial, temporal, runtime-safety, readiness, and removability gaps without adding unrelated trading-domain functionality

This plan intentionally does **not** implement the fixes. It defines the exact order, files, tests, acceptance criteria, quality gates, documentation updates, and proposed commits for a later coding pass.

---

## 1. Objective

Complete the foundational spatiotemporal-composability architecture so that HaruQuantAI can guarantee all of the following:

1. Removing or disabling a feature removes its capability rather than breaking the application shell.
2. Required consumers stop before a provider stops and restart only after a compatible provider is active.
3. Reconfiguring or replacing a provider never leaves consumers holding stale provider objects.
4. Transactional replacement preserves the replacement feature's tasks, listeners, context-managed resources, callbacks, and service bindings.
5. Runtime task failures transition the owning feature to `FAILED_RUNTIME` and reconcile its dependents.
6. Capability provider selection is explicit and deterministic when multiple providers exist.
7. Event dispatch modes and subscription ownership are enforced exactly.
8. Live readiness can never report `READY` while a required trading-safety capability is absent.
9. Physical feature removal is exercised by CI rather than documented only.
10. The real application entry point boots the composition engine and exposes liveness, readiness, capability, and feature diagnostics.

---

## 2. Protected baseline and implementation constraints

### 2.1 Protected baseline

Before implementation begins:

- [X] Confirm the latest `main` commit and record it in the implementation PR.
- [ ] Create the implementation branch from that exact commit.
- [X] Run the existing quality gates without modifications.
- [X] Save the complete baseline output in the PR description or an attached artifact.
- [X] Do not begin corrective code changes if the baseline already fails.

Baseline command:

```bash
uv sync --frozen --dev
uv run --frozen python scripts/ci_check.py
```

### 2.2 Constraints

- [ ] Preserve Python `>=3.14` unless a separate approved migration changes it.
- [ ] Preserve the current four-level structure: Domain → Feature → Responsibility → Functional Requirement.
- [ ] Do not introduce direct cross-feature implementation imports.
- [ ] Do not add real live-trading execution or broker credentials during this remediation.
- [ ] Use the Mock Broker feature and test doubles for replacement, failure, and readiness tests.
- [ ] Treat every external or irreversible action as out of scope for automatic rollback.
- [ ] Keep each phase reviewable and independently revertible.
- [ ] Add failing characterization tests before correcting the behavior they describe.

### 2.3 Global implementation rules

For every phase:

- [ ] Implement only the files listed for that phase unless an unavoidable dependency is documented in the commit.
- [ ] Add or update unit tests.
- [ ] Add at least one executable usage or integration example where the phase changes public behavior.
- [ ] Run Ruff formatting.
- [ ] Run Ruff linting.
- [ ] Run mypy.
- [ ] Run Import Linter.
- [ ] Run the AST architecture checker.
- [ ] Run the focused tests for the phase.
- [ ] Run the complete test suite before committing.
- [ ] Update relevant architecture and feature documentation.
- [ ] Create one focused Git commit using the proposed commit message.

Standard verification commands:

```bash
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy
uv run --frozen lint-imports
uv run --frozen python scripts/architecture_check.py
uv run --frozen pytest
```

---

## 3. Gap matrix and implementation order

| Priority | Gap                                                               | Required result                                                                    | Phase |
| -------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ----: |
| P0       | Profile configuration grammar is inconsistent                     | One validated grammar; invalid and unknown profiles fail explicitly                |     1 |
| P0       | Live readiness omits safety-critical capabilities                 | Live readiness requires all documented safety capabilities                         |     1 |
| P1       | Multiple providers are selected nondeterministically              | Explicit or unambiguous deterministic provider selection                           |     2 |
| P0       | Provider remount leaves consumers with stale objects              | Provider changes remount the complete transitive consumer closure                  |     3 |
| P0       | Transactional replacement closes the replacement's staged effects | Staged scope becomes the active scope and survives commit                          |     4 |
| P0       | Transactional replacement has incomplete rollback semantics       | Pre-commit rollback is exact; post-commit cleanup errors are reported consistently |     4 |
| P1       | Event modes are stored but ignored                                | Dispatch invokes handlers registered for the requested mode only                   |     5 |
| P1       | One disposer can remove duplicate subscriptions                   | Exact subscription-token disposal                                                  |     5 |
| P1       | Background task failures do not alter feature state               | Unexpected task failure produces`FAILED_RUNTIME` and dependency reconciliation   |     6 |
| P1       | `FeatureContext` does not expose all scope-managed resources    | Sync/async context-manager entry and closed-scope protection                       |     7 |
| P1       | Physical-removal CI workflow currently skips                      | Active deletion matrix that fails on missing verifier or failed scenario           |     8 |
| P1       | Removal verifier weakens evidence by deleting core tests          | Ownership-aware removal that preserves absence and API tests                       |     8 |
| P1       | `app/main.py` is not wired to the runtime                       | Real composition bootstrap and control plane                                       |     9 |
| P1       | Capability and feature docs drift from manifests                  | Validated or generated documentation aligned with runtime declarations             |    10 |
| P2       | Tests are excluded from strict mypy checking                      | Gradual removal of the blanket`tests.* ignore_errors` override                   |    11 |

---

# Phase 0 — Characterization tests and protected-baseline evidence

## Purpose

Lock the current behavior in tests, then add tests that expose each known defect before production code changes begin. The new tests are expected to fail initially.

## Task 0.1 — Record the baseline

- [X] Create `docs/architecture/audit/composability_remediation_baseline.md`.
- [X] Record the baseline commit SHA.
- [X] Record Python and `uv` versions.
- [X] Record the existing test count and coverage generated locally.
- [X] Record results for Ruff, mypy, Import Linter, AST checks, and pytest.
- [X] State clearly that GitHub Actions results, not commit-message claims, are the authoritative remote evidence.

## Task 0.2 — Add failing characterization tests

Create or update:

```text
tests/composition/test_config.py
tests/composition/test_readiness.py
tests/kernel/test_graph.py
tests/kernel/test_reconciler.py
tests/kernel/test_events.py
tests/kernel/test_scope.py
tests/composition/test_hot_reconfiguration.py
tests/services/test_lifecycle_leak.py
```

Add tests for:

- [X] `[profile] name = "live"` is rejected rather than silently becoming Research.
- [X] Unknown profiles are rejected.
- [X] Live readiness is false when any one required safety capability is missing.
- [X] Two enabled providers for one capability without selection are rejected.
- [X] Reconfiguring a provider remounts a consumer and replaces its captured provider object.
- [X] Replacing a provider remounts all transitive consumers.
- [X] A transactional replacement containing a task, listener, callback, and async context manager retains all replacement effects after commit.
- [X] A pre-commit replacement failure preserves the exact old provider instance.
- [X] A cleanup failure after commit is reported as a post-commit cleanup error, not a successful rollback.
- [X] Mixed event modes on one event type invoke only matching handlers.
- [X] Disposing one duplicate handler registration leaves the other registration active.
- [X] Unexpected background-task failure changes feature state to `FAILED_RUNTIME`.
- [X] Registering a new effect on a closed scope raises a lifecycle error.

## Task 0.3 — Quality and documentation

- [X] Confirm the new tests fail for the expected reasons only.
- [X] Do not weaken assertions to make the current implementation pass.
- [X] Add a short failure-to-phase mapping to the baseline document.

## Proposed commit

```text
test(architecture): characterize remaining composability gaps
```

## Exit criteria

- [X] Existing tests still pass.
- [X] New characterization tests fail and identify the audited defects precisely.
- [X] No production behavior has changed.

---

# Phase 1 — Standardize configuration grammar and enforce Live readiness

## Purpose

Remove silent profile fallback and make readiness a reliable safety boundary.

## Files to modify

```text
app/composition/config.py
app/composition/readiness.py
app/composition/engine.py
app/api/system.py
tests/composition/test_config.py
tests/composition/test_readiness.py
tests/composition/test_engine.py
docs/architecture/capability-model.md
docs/dev/setup.md
```

## Task 1.1 — Adopt one configuration grammar

Use this canonical form:

```toml
[application]
profile = "research"

[features.FEAT-BROKER-FEED_MOCK]
enabled = true
```

Implementation steps:

- [x] Parse the active profile only from `[application].profile`.
- [x] Reject the legacy `[profile]` section with a typed `ConfigurationError` explaining the supported form.
- [x] Reject unknown top-level keys where practical, or at minimum reject unknown profile-related sections.
- [x] Reject missing, blank, or non-string profile values.
- [x] Normalize profile names once, using lowercase internal identifiers.
- [x] Preserve feature-specific dictionaries under each feature section.
- [x] Add a typed error hierarchy for parsing and validation rather than relying on generic `ValueError` where the caller needs diagnostics.

## Task 1.2 — Make profile definitions explicit

- [x] Introduce an immutable `DeploymentProfile` model.
- [x] Keep the built-in profiles in one authoritative mapping.
- [x] Reject unknown profiles instead of treating them as having zero requirements.
- [x] Add an explicit noncritical profile such as `offline` if a zero-capability shell is required.
- [x] Ensure profile criticality remains configuration/runtime policy rather than feature-owned policy.

## Task 1.3 — Correct Live readiness

The Live profile must require at least:

```text
system.clock@1
broker.market-data@1
broker.execution@1
data.realtime-ticks@1
portfolio.positions@1
risk.approval@1
trading.execution@1
```

Implementation steps:

- [x] Remove `data.historical-bars@1` from Live requirements unless live startup genuinely depends on it.
- [x] Add all documented Live safety capabilities.
- [x] Confirm Research and Backtest requirements separately.
- [x] Return machine-readable missing capability identifiers.
- [x] Ensure `SystemAPI` reports the selected profile and all missing requirements.

## Task 1.4 — Tests and examples

- [x] Test the canonical grammar.
- [x] Test rejection of legacy grammar.
- [x] Test rejection of an unknown profile.
- [x] Parameterize Live readiness by removing each required capability one at a time.
- [x] Add `config/examples/research.toml`, `config/examples/backtest.toml`, and `config/examples/live.toml` with no credentials.
- [x] Add a usage example that loads each example and prints readiness diagnostics.

## Proposed commit

```text
fix(composition): enforce profile grammar and live readiness safety
```

## Exit criteria

- [x] No configuration can silently select a different profile.
- [x] Live is never ready without all required safety capabilities.
- [x] Documentation, examples, parser, and tests use the same grammar.


---

# Phase 2 — Deterministic capability-provider selection

## Purpose

Prevent the graph and registry from silently choosing different providers when several features provide the same capability.

## Files to modify or create

```text
app/composition/config.py
app/kernel/graph.py
app/kernel/registry.py
app/kernel/feature.py
app/composition/engine.py
tests/kernel/test_graph.py
tests/kernel/test_registry.py
tests/composition/test_config.py
tests/composition/test_engine.py
docs/architecture/capability-model.md
```

A small focused file may be added if provider selection makes `graph.py` too broad:

```text
app/kernel/selection.py
```

## Task 2.1 — Add provider-selection configuration

Canonical syntax:

```toml
[providers]
"broker.market-data@1" = "FEAT-BROKER-FEED_MOCK"
```

Implementation steps:

- [x] Add `provider_selections: dict[str, str]` to `AppConfig`.
- [x] Validate capability identifier format.
- [x] Validate selected feature ID format.
- [x] Reject a selection that names a disabled or undiscovered feature.
- [x] Reject a selection where the chosen feature does not provide the capability.

## Task 2.2 — Define provider-selection rules

- [x] Zero providers: capability is unavailable; consumers are blocked.
- [x] Exactly one enabled provider: select it automatically.
- [x] More than one enabled provider: require explicit configuration.
- [x] A selected provider must be enabled and compatible with the requested major capability version.
- [x] Preserve the selected provider in `GraphResolution.provider_map`.
- [x] Include ambiguity and invalid-selection reasons in diagnostics.

## Task 2.3 — Harden the registry

- [x] Change normal registration so it rejects overwriting an active capability binding.
- [x] Permit replacement only through an explicit replacement/transaction API.
- [x] Preserve generation counters across replacement.
- [x] Add a lock around short multi-binding registry mutations.
- [x] Add `register_many` or equivalent all-or-nothing validation for features providing multiple capabilities.

## Task 2.4 — Tests and examples

- [x] Test automatic selection with one provider.
- [x] Test ambiguity with two providers.
- [x] Test explicit selection with two providers.
- [x] Test invalid feature selection.
- [x] Test selection of a feature that does not provide the capability.
- [x] Test that ordinary `register()` cannot silently replace an active binding.
- [x] Add a configuration example selecting Mock Broker over a second test provider.

## Proposed commit

```text
feat(kernel): add deterministic capability provider selection
```

## Exit criteria

- [x] Graph edges and runtime bindings always refer to the same selected provider.
- [x] Ambiguous providers cannot start accidentally.
- [x] Provider replacement is possible only through the transactional path.


---

# Phase 3 — Reconcile provider generations and transitive consumers

## Purpose

Ensure that disabling, reconfiguring, or replacing a provider never leaves an active consumer holding the old implementation object.

## Files to modify

```text
app/kernel/graph.py
app/kernel/reconciler.py
app/kernel/registry.py
app/composition/engine.py
tests/kernel/test_graph.py
tests/kernel/test_reconciler.py
tests/composition/test_hot_reconfiguration.py
tests/services/test_vertical_feature_pair.py
```

## Task 3.1 — Expose dependency and dependent maps

Extend `GraphResolution` to include:

- [x] Required provider edges.
- [x] Optional provider edges that currently resolve to an active provider.
- [x] Direct dependents by feature ID.
- [x] Transitive dependent-closure calculation.
- [x] Deterministic start and stop order.

## Task 3.2 — Correct cycle semantics

- [x] Detect required dependency cycles before fixed-point eligibility filtering.
- [x] Raise `DependencyCycleError` for required cycles.
- [x] Do not let optional-only cycles prevent activation.
- [x] Use optional edges only for best-effort ordering when the optional provider is selected and active.
- [x] Correct misleading test names and assertions.

## Task 3.3 — Plan remount closures

For any feature whose implementation generation changes:

- [x] Include the feature in the remount set.
- [x] Include all transitive required consumers.
- [x] Include consumers of optional capabilities under the initial simple policy.
- [x] Include downstream consumers of those consumers.
- [x] Stop the closure in reverse topological order.
- [x] Start the closure in topological order.

Generation-changing events include:

- [x] Provider configuration changed.
- [x] Selected provider changed.
- [x] Provider was removed and returned.
- [x] Provider was transactionally replaced.
- [x] Consumer's own configuration changed and it provides a capability used downstream.

## Task 3.4 — Use graph order rather than dictionary insertion order

- [x] Replace reverse `_active_features` iteration with explicit stop order from the current active graph.
- [x] Persist the last successfully committed active graph.
- [x] Ensure partially failed starts do not corrupt the committed active graph.

## Task 3.5 — Tests and usage example

- [x] Build a provider → consumer → downstream-consumer chain.
- [x] Capture each consumer's provider object identity.
- [x] Reconfigure the provider.
- [x] Assert every transitive consumer remounted.
- [x] Assert every consumer points to the new provider object.
- [x] Assert stop order is downstream-first.
- [x] Assert start order is provider-first.
- [x] Add a runnable example printing generations and mount counts before and after a provider change.

## Proposed commit

```text
fix(kernel): remount transitive consumers on provider changes
```

## Exit criteria

- [x] No active feature retains a provider object from an obsolete generation.
- [x] Required and optional dependency changes have deterministic remount behavior.
- [x] Required cycles are rejected explicitly.

---

# Phase 4 — Redesign transactional replacement and HMR lifecycle safety

## Purpose

Make transactional replacement preserve all replacement effects, define exact commit boundaries, and report cleanup outcomes truthfully.

## Files to modify or create

```text
app/kernel/scope.py
app/kernel/registry.py
app/kernel/reconciler.py
app/kernel/feature.py
app/composition/engine.py
app/contracts/events/system.py
tests/composition/test_hot_reconfiguration.py
tests/kernel/test_registry.py
tests/kernel/test_reconciler.py
tests/kernel/test_scope.py
tests/services/test_lifecycle_leak.py
```

A focused result model may be added:

```text
app/kernel/replacement.py
```

## Task 4.1 — Define replacement semantics

Create a typed `ReplacementReport` containing at least:

```text
feature_id
old_generation
new_generation
committed
rolled_back
cleanup_errors
status
```

Define three outcome classes:

1. **Pre-commit failure:** staged scope closes; old provider remains unchanged.
2. **Committed replacement:** staged scope becomes active; old scope closes successfully.
3. **Committed with cleanup error:** new provider remains active; cleanup failure is reported and retried or surfaced as degraded state. It must not be described as a rollback.

## Task 4.2 — Preserve the staged scope

- [x] Mount the new feature into one staged `FeatureScope`.
- [x] Collect staged capability bindings without exposing them globally.
- [x] Run feature-spec validation and optional health checks.
- [x] Atomically publish all staged bindings.
- [x] Attach exact binding-token cleanup callbacks to the same staged scope.
- [x] Set the staged scope as the feature's active scope.
- [x] Never create an empty replacement scope that owns only provider tokens.
- [x] Never close the staged scope after successful commit.

## Task 4.3 — Add optional lifecycle protocols

Define typed optional protocols, for example:

```text
HealthCheckableFeature
QuiesceableFeature
DrainableFeature
```

Rules:

- [x] Health check occurs before commit.
- [x] Quiesce occurs before old-provider retirement.
- [x] Drain is required for a feature to claim zero-downtime replacement.
- [x] Features without drain support use safe stop/remount semantics and must not be labeled zero-downtime.
- [x] Timeouts are configurable and produce typed errors.

## Task 4.4 — Coordinate consumer remounts

- [x] Calculate the provider's transitive dependent closure.
- [x] Quiesce or stop consumers before retiring the old provider unless a safe generation-aware reference exists.
- [x] Commit the new provider.
- [x] Restart consumers against the new generation.
- [x] Preserve the old provider if any pre-commit step fails.

## Task 4.5 — Cleanup-failure handling

- [x] Aggregate cleanup errors without losing records for remaining cleanup operations.
- [x] Store orphaned cleanup scopes for retry when needed.
- [x] Expose cleanup errors through runtime status.
- [x] Emit a typed system event for replacement completion and another for cleanup degradation.

## Task 4.6 — Tests

Create a replacement test feature that registers:

- [x] One capability provider.
- [x] One long-running task.
- [x] One event listener.
- [x] One synchronous callback.
- [x] One asynchronous callback.
- [x] One synchronous context manager.
- [x] One asynchronous context manager.

Test:

- [x] All staged effects remain active after commit.
- [x] All old effects are cleaned after successful replacement.
- [x] Old binding disposers cannot remove new bindings.
- [x] Pre-commit failure preserves the exact old provider and effects.
- [x] Health-check failure rolls back.
- [x] Post-commit old-scope cleanup failure returns `committed=True` plus cleanup errors.
- [x] A dependent consumer uses the new provider generation.
- [x] Repeated replacement does not leak effects.

## Task 4.7 — Usage example

Add a non-production example that:

1. Mounts Mock Broker generation 1.
2. Retrieves a bar.
3. Replaces it with generation 2.
4. Prints the generation change.
5. Confirms the Historical Bars consumer was remounted.
6. Shuts down and confirms no effects remain.

## Proposed commit

```text
fix(kernel): make transactional replacement lifecycle safe
```

## Exit criteria

- [x] Replacement effects survive successful commit.
- [x] Pre-commit failure is exactly reversible.
- [x] Post-commit cleanup failure is represented honestly.
- [x] Consumers never continue using the retired provider generation.

---

# Phase 5 — Enforce event modes and exact subscription ownership

## Purpose

Make event behavior match the public contract and prevent one disposer from removing another registration.

## Files to modify

```text
app/kernel/events.py
app/kernel/context.py
app/kernel/scope.py
tests/kernel/test_events.py
tests/kernel/test_context_events.py
tests/services/test_lifecycle_leak.py
docs/architecture/capability-model.md
```

## Task 5.1 — Introduce subscription tokens

- [x] Add immutable `SubscriptionToken` with a monotonically increasing or UUID identifier.
- [x] Record event type, dispatch mode, and optionally owner feature ID.
- [x] Make `subscribe()` return the exact token or a disposer bound to that token.
- [x] Make disposal idempotent.
- [x] Remove only the exact registration identified by the token.

## Task 5.2 — Filter dispatch by mode

- [x] `publish()` invokes only `PUBLISH` subscriptions.
- [x] `dispatch_serial()` invokes only `SERIAL` subscriptions.
- [x] `dispatch_parallel()` invokes only `PARALLEL` subscriptions.
- [x] `dispatch_pipeline()` invokes only `PIPELINE` subscriptions.
- [x] Preserve registration order for serial and pipeline modes.
- [x] Define and document exception behavior for every mode.

## Task 5.3 — Concurrency and snapshots

- [x] Protect subscription mutation with an appropriate short-lived lock.
- [x] Dispatch from an immutable snapshot.
- [x] Permit a handler to unsubscribe safely during dispatch without corrupting iteration.
- [x] Remove the unused lock if a different implementation is selected.

## Task 5.4 — Tests and example

- [x] Register all four modes for the same event type and verify strict separation.
- [x] Register the same handler twice and dispose one token only.
- [x] Test disposal during dispatch.
- [x] Test pipeline short-circuiting.
- [x] Test publish error isolation.
- [x] Add an example showing an observational event and a policy pipeline using the same payload type only when explicitly intended.

## Proposed commit

```text
fix(kernel): enforce event modes and exact subscription disposal
```

## Exit criteria

- [x] Dispatch mode is part of actual runtime behavior, not metadata only.
- [x] Subscription ownership is exact and idempotent.

---

# Phase 6 — Supervise runtime tasks and reconcile failures

## Purpose

Turn unexpected worker failure into a visible runtime state transition and capability loss rather than leaving a dead feature marked `ACTIVE`.

## Files to modify or create

```text
app/kernel/scope.py
app/kernel/reconciler.py
app/composition/engine.py
app/kernel/feature.py
app/contracts/events/system.py
app/api/system.py
tests/kernel/test_scope.py
tests/kernel/test_reconciler.py
tests/composition/test_engine.py
tests/services/test_lifecycle_leak.py
```

A focused supervision helper may be created:

```text
app/kernel/supervision.py
```

## Task 6.1 — Detect task outcomes

- [x] Attach a completion observer to every task created by `FeatureScope.spawn()`.
- [x] Distinguish normal completion, intentional cancellation, and unexpected exception.
- [x] Capture exception type, message, traceback summary, owner feature ID, and task name.
- [x] Do not classify cancellation during scope shutdown as failure.

## Task 6.2 — Notify the reconciler

- [x] Give the scope a runtime-failure callback supplied by the reconciler.
- [x] Serialize failure handling through the engine/reconciler lock.
- [x] Transition the owner to `FAILED_RUNTIME`.
- [x] Close the owner's scope.
- [x] Remove its capability bindings.
- [x] Stop or block transitive dependents.
- [x] Emit a typed `FeatureRuntimeFailedEvent`.

## Task 6.3 — Recovery policy

- [x] Default to no automatic restart loop.
- [x] Permit a bounded restart policy only when explicitly configured later.
- [x] Record last failure and failure count in runtime diagnostics.
- [x] Keep the application shell live.
- [x] Recalculate readiness immediately.

## Task 6.4 — Tests and example

- [x] Spawn a worker that raises unexpectedly.
- [x] Assert the feature reaches `FAILED_RUNTIME`.
- [x] Assert its capability disappears.
- [x] Assert required consumers become `BLOCKED`.
- [x] Assert unrelated features remain `ACTIVE`.
- [x] Assert shutdown cancellation does not create a failure event.
- [x] Add a runnable failure-injection example that prints the state transition.

## Proposed commit

```text
feat(kernel): supervise runtime task failures
```

## Exit criteria

- [x] No crashed feature remains reported as active.
- [x] Task failure propagates through capability and readiness status safely.

---

# Phase 7 — Complete lifecycle-scoped resource APIs

## Purpose

Expose all supported reversible resource operations through `FeatureContext` and prevent effects from being registered after closure.

## Files to modify

```text
app/kernel/context.py
app/kernel/scope.py
app/kernel/registry.py
app/kernel/events.py
tests/kernel/test_context.py
tests/kernel/test_scope.py
tests/kernel/test_registry.py
```

## Task 7.1 — Add closed-scope protection

- [x] Add a typed `ScopeClosedError`.
- [x] Check scope state before every effect registration operation.
- [x] Reject callbacks, tasks, context managers, listeners, and bindings registered after closure.
- [x] Keep `close()` idempotent.

## Task 7.2 — Expose context-manager operations

Add to `FeatureContext` and `DefaultFeatureContext`:

- [x] `enter_context()`.
- [x] `enter_async_context()`.
- [x] Typed return values.
- [x] Optional resource names for diagnostics.

## Task 7.3 — Improve effect classification

- [x] Record service bindings as `SERVICE_BINDING`.
- [x] Record event subscriptions as `EVENT_LISTENER`.
- [x] Record background tasks as `BACKGROUND_TASK`.
- [x] Preserve resource names and cleanup outcomes.
- [x] Expose active and cleaned effect counts through diagnostics.

## Task 7.4 — Tests

- [x] Test all registrations fail after scope closure.
- [x] Test context-manager entry through `FeatureContext`.
- [x] Test service and listener effect types.
- [x] Test cleanup continues across multiple registered effects even when one cleanup fails, with all failures reported.

## Proposed commit

```text
fix(kernel): complete scoped resource lifecycle APIs
```

## Exit criteria

- [x] Feature authors never need to bypass `FeatureContext` for supported reversible resources.
- [x] A closed scope cannot acquire new unmanaged effects.

---

# Phase 8 — Activate physical-removal verification in CI

## Purpose

Turn physical removability into automated evidence for every registered feature.

## Files to modify or create

```text
scripts/verify_feature_removal.py
scripts/ci_check.py
.github/workflows/ci.yml
.github/workflows/provider-removability.yml
pyproject.toml
tests/architecture/test_architectural_rules.py
tests/composition/test_discovery.py
tests/api/test_facade.py
```

Optional report schema:

```text
scripts/removability_report.py
```

## Task 8.1 — Make feature targets discoverable

- [ ] Add `--all`, `--feature`, and `--report` CLI options.
- [ ] Discover registered feature entry points from `pyproject.toml` or installed metadata.
- [ ] Resolve each entry point before deletion to record feature ID, provided capabilities, package path, and owned test paths.
- [ ] Fail on duplicate feature IDs or unmappable package paths.
- [ ] Avoid a permanently hardcoded target dictionary as the only source of truth.

## Task 8.2 — Define test ownership

- [ ] Feature-local tests may be removed with the feature.
- [ ] Integration tests involving a deleted feature must be declared explicitly as owned feature-set tests.
- [ ] Core API absence tests, discovery tests, architecture tests, and unrelated feature tests must remain.
- [ ] Stop deleting `tests/api/test_facade.py` merely to make removal pass.
- [ ] Add or retain tests proving the facade returns capability-unavailable behavior after deletion.

## Task 8.3 — Strengthen runtime assertions

For each removed feature, assert:

- [ ] The stale configuration still parses.
- [ ] The feature state is `MISSING`.
- [ ] Every capability it provided is unavailable.
- [ ] Required consumers are `BLOCKED`.
- [ ] Unrelated features remain active.
- [ ] Profile readiness reflects the missing capability.
- [ ] The actual application bootstrap starts.
- [ ] Shutdown completes without leaked tasks or listeners.

## Task 8.4 — Correct the workflows

- [ ] Change the removability workflow to execute the real verifier.
- [ ] Remove the silent "script not implemented — skipping" behavior.
- [ ] Fail the workflow if the verifier is missing.
- [ ] Run at least a critical-feature removal check on pull requests.
- [ ] Run the complete matrix nightly, manually, and on releases.
- [ ] Upload a JSON report artifact even when one scenario fails.
- [ ] Include removed feature, provided capabilities, blocked consumers, active unrelated features, command results, and elapsed time in the report.

## Task 8.5 — Tests and usage

- [ ] Unit-test target discovery and report generation.
- [ ] Test deletion of Mock Broker.
- [ ] Test deletion of Historical Bars.
- [ ] Test deletion of Persistent Storage.
- [ ] Run the complete matrix locally.

Commands:

```bash
uv run --frozen python scripts/verify_feature_removal.py --all --report removability-report.json
```

## Proposed commit

```text
feat(architecture): enforce physical feature removability in CI
```

## Exit criteria

- [ ] The CI workflow cannot silently skip removability verification.
- [ ] Every registered built-in feature has a deletion result.
- [ ] Core absence behavior is tested rather than deleted from the temporary workspace.

---

# Phase 9 — Wire the real application bootstrap and system control plane

## Purpose

Replace the print-only entry point with an executable composition runtime and machine-readable diagnostics.

## Files to modify or create

```text
app/main.py
app/api/system.py
app/api/http.py
app/api/facade.py
app/composition/engine.py
config/examples/research.toml
config/examples/backtest.toml
config/examples/live.toml
tests/test_main.py
tests/api/test_system_http.py
tests/api/test_facade.py
README.md
pyproject.toml
```

## Task 9.1 — Implement application bootstrap

- [ ] Add `async_main()`.
- [ ] Parse a configuration-file argument.
- [ ] Construct `CompositionEngine`.
- [ ] Load and reconcile configuration.
- [ ] Construct the `HaruQuantAPI` facade.
- [ ] Install graceful shutdown handling.
- [ ] Always call `engine.shutdown()` in a `finally` block.
- [ ] Return a nonzero exit status only for invalid startup/configuration or control-plane failure, not for ordinary degraded capability status.

## Task 9.2 — Add safe CLI modes

Support at least:

```text
haruquantai --config config/examples/research.toml --status
haruquantai --config config/examples/research.toml --serve
```

- [ ] `--status` prints JSON diagnostics and exits cleanly.
- [ ] `--serve` starts only the system control plane at this stage.
- [ ] No command places orders or connects to real brokers.

## Task 9.3 — Implement system endpoints

Add a minimal FastAPI control plane, or revise the architecture docs if a different framework is deliberately selected.

Required endpoints:

```text
GET /system/liveness
GET /system/readiness
GET /system/capabilities
GET /system/features
```

Behavior:

- [ ] Liveness returns success while kernel and control plane are responsive.
- [ ] Readiness returns `200` only when the selected profile requirements are met.
- [ ] Readiness returns `503` with missing capabilities otherwise.
- [ ] Capability output includes provider feature ID and generation.
- [ ] Feature output includes lifecycle state, package errors, capability errors, runtime failures, and cleanup errors.

## Task 9.4 — Tests and examples

- [ ] Test `--status` with zero features.
- [ ] Test `--status` with Mock Broker and Historical Bars.
- [ ] Test degraded Research readiness.
- [ ] Test Live readiness failure.
- [ ] Test all four system endpoints.
- [ ] Test graceful shutdown leaves no active capabilities or tasks.
- [ ] Add README commands for local non-production startup.

## Proposed commit

```text
feat(app): wire composition runtime and system control plane
```

## Exit criteria

- [ ] The installed application command exercises the real composition engine.
- [ ] Liveness and readiness are observable independently.
- [ ] The physical-removal verifier can launch the real entry point.

---

# Phase 10 — Eliminate manifest, implementation, and documentation drift

## Purpose

Ensure feature documentation describes runtime truth rather than planned behavior that the manifest or implementation does not provide.

## Files to modify or create

```text
app/services/data/historical_bars/manifest.py
app/services/data/historical_bars/config.py
app/services/data/historical_bars/feature.py
app/services/data/historical_bars/README.md
app/services/broker/mock_feed/config.py
app/services/broker/mock_feed/feed.py
app/services/broker/mock_feed/README.md
app/services/system/storage/config.py
app/services/system/storage/README.md
docs/architecture/capability-model.md
docs/architecture/feature_implementation_pipeline.md
README.md
scripts/validate_feature_docs.py
tests/architecture/test_feature_documentation.py
```

## Task 10.1 — Resolve Historical Bars drift

Choose one truthful implementation path:

- [ ] Either declare and implement `data.bar-cache@1` and `system.metrics@1` as optional dependencies, or remove them from the README until implemented.
- [ ] Either use `cache_enabled` or remove the unused configuration field.
- [ ] Either declare `StateDeclaration(namespace="data.historical_bars", ...)` and use storage, or remove the persistent-state claim.
- [ ] Ensure failure and removal behavior matches the manifest.

The preferred minimal remediation is to document only implemented behavior, then add caching later as its own feature.

## Task 10.2 — Resolve Mock Broker drift

- [ ] Implement all accepted timeframes or restrict validation to the provider's supported set.
- [ ] Never silently treat unsupported timeframes as `M1`.
- [ ] Either apply `spread` to a contract that exposes bid/ask information or remove the unused setting from this bar-only provider.
- [ ] Update functional requirements and tests.

## Task 10.3 — Resolve Storage drift

- [ ] Standardize on one configuration key: `base_path` or `root_dir`.
- [ ] Update README, examples, parser, and tests together.
- [ ] Document that unmount retains state and purge is explicit.

## Task 10.4 — Add documentation validation

- [ ] Create a script/test that discovers each built-in feature.
- [ ] Verify each feature has a README.
- [ ] Verify feature ID, domain, provided capabilities, required capabilities, optional capabilities, and state namespace appear consistently.
- [ ] Prefer generating the implemented-feature portion of the capability catalog from `FeatureSpec` objects.
- [ ] Separate implemented capabilities from roadmap capabilities in the catalog.

## Task 10.5 — Root README

- [ ] Explain the project purpose.
- [ ] Explain the composition model.
- [ ] Show project setup and quality commands.
- [ ] Show non-production startup.
- [ ] Link to capability model, implementation pipeline, plugin packaging, and this remediation plan.
- [ ] State clearly that the current foundation is not permission to perform live trading.

## Proposed commit

```text
docs(architecture): align feature manifests and runtime documentation
```

## Exit criteria

- [ ] No implemented feature claims capabilities, state, or configuration it does not actually support.
- [ ] Documentation validation runs in CI.

---

# Phase 11 — Tighten typing, quality gates, and final release evidence

## Purpose

Finish the remediation with strict evidence, remove temporary allowances, and produce an auditable PR.

## Files to modify

```text
pyproject.toml
.pre-commit-config.yaml
scripts/ci_check.py
.github/workflows/ci.yml
docs/architecture/audit/composability_remediation_result.md
```

## Task 11.1 — Tighten test typing

- [ ] Remove the blanket `tests.* ignore_errors = true` override.
- [ ] Fix test typing incrementally by directory if one-step removal is too large.
- [ ] Keep explicit, narrow overrides only for third-party libraries that truly lack typing.
- [ ] Require mypy to check all new remediation tests.

## Task 11.2 — Final quality gate

Run:

```bash
uv sync --frozen --dev
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy
uv run --frozen lint-imports
uv run --frozen python scripts/architecture_check.py
uv run --frozen pytest
uv run --frozen python scripts/verify_feature_removal.py --all --report removability-report.json
```

- [ ] Keep overall coverage at or above 80%.
- [ ] Require new kernel and composition code to have direct tests for all branches involving failure or rollback.
- [ ] Confirm no ignored failing tests, conditional skips, or workflow-level silent skips were added.
- [ ] Confirm pre-commit and CI invoke compatible locked commands.

## Task 11.3 — Final audit report

Create `docs/architecture/audit/composability_remediation_result.md` with:

- [ ] Baseline and final commit SHAs.
- [ ] Gap-by-gap status.
- [ ] Test count and coverage.
- [ ] Full removal-matrix summary.
- [ ] Live-readiness capability list.
- [ ] Replacement success, rollback, and cleanup-degradation evidence.
- [ ] Known limitations and deferred work.
- [ ] Confirmation that no real broker or live-trading operation was executed.

## Proposed commit

```text
chore(quality): finalize composability remediation evidence
```

## Exit criteria

- [ ] All quality gates pass locally and in GitHub Actions.
- [ ] The full removal matrix passes.
- [ ] The remediation result document contains reproducible evidence.

---

## 4. Required acceptance scenarios

The implementation PR must not be approved until every scenario passes.

### Scenario A — Disable a consumer

```text
Mock Broker: ACTIVE
Historical Bars: DISABLED
broker.market-data@1: AVAILABLE
data.historical-bars@1: UNAVAILABLE
application liveness: HEALTHY
```

### Scenario B — Remove a required provider

```text
Mock Broker: MISSING or DISABLED
Historical Bars: BLOCKED
broker.market-data@1: UNAVAILABLE
data.historical-bars@1: UNAVAILABLE
application liveness: HEALTHY
Research readiness: NOT READY
```

### Scenario C — Reconfigure a provider

```text
provider generation 1: retired
provider generation 2: ACTIVE
consumer: remounted
consumer captured provider: generation 2
old provider effects: cleaned
new provider effects: active
```

### Scenario D — Transactional pre-commit failure

```text
replacement committed: false
rollback completed: true
old provider object identity: unchanged
old provider effects: still active
new staged effects: fully cleaned
```

### Scenario E — Transactional commit with cleanup failure

```text
replacement committed: true
new provider: ACTIVE
old cleanup error: reported
result is not labeled rollback
runtime diagnostics: DEGRADED until cleanup succeeds or is acknowledged
```

### Scenario F — Runtime task failure

```text
owner feature: FAILED_RUNTIME
owner capability: UNAVAILABLE
required consumers: BLOCKED
unrelated features: ACTIVE
application liveness: HEALTHY
readiness: recalculated
```

### Scenario G — Event-mode isolation

```text
PUBLISH dispatch: PUBLISH handlers only
SERIAL dispatch: SERIAL handlers only
PARALLEL dispatch: PARALLEL handlers only
PIPELINE dispatch: PIPELINE handlers only
exact token disposal: one registration removed only
```

### Scenario H — Live safety

For every required Live capability:

```text
remove one capability
→ Live readiness must become false
→ missing capability must be reported explicitly
```

### Scenario I — Physical removal matrix

For every registered built-in feature:

```text
physically delete package
remove owned feature-local tests and entry point
keep core absence/API tests
run all quality gates
start actual application
verify MISSING/BLOCKED/unrelated ACTIVE state
produce JSON evidence
```

---

## 5. Proposed commit stack

The coding agent should produce this reviewable sequence:

1. `test(architecture): characterize remaining composability gaps`
2. `fix(composition): enforce profile grammar and live readiness safety`
3. `feat(kernel): add deterministic capability provider selection`
4. `fix(kernel): remount transitive consumers on provider changes`
5. `fix(kernel): make transactional replacement lifecycle safe`
6. `fix(kernel): enforce event modes and exact subscription disposal`
7. `feat(kernel): supervise runtime task failures`
8. `fix(kernel): complete scoped resource lifecycle APIs`
9. `feat(architecture): enforce physical feature removability in CI`
10. `feat(app): wire composition runtime and system control plane`
11. `docs(architecture): align feature manifests and runtime documentation`
12. `chore(quality): finalize composability remediation evidence`

Each commit must pass its focused tests. The final commit must pass the complete gate and removal matrix.

---

## 6. Pull-request structure

### PR title

```text
fix(architecture): complete spatiotemporal composability guarantees
```

### PR description sections

- [ ] Problem statement.
- [ ] Baseline commit.
- [ ] Gap matrix.
- [ ] Phase-by-phase implementation summary.
- [ ] Breaking configuration changes.
- [ ] Provider-selection syntax.
- [ ] Replacement transaction semantics.
- [ ] Live-readiness safety requirements.
- [ ] Runtime-failure behavior.
- [ ] Physical-removal matrix results.
- [ ] Quality-gate output.
- [ ] Coverage result.
- [ ] Known limitations.
- [ ] Explicit statement that no live trading was performed.

### Reviewer focus areas

- [ ] Safety of registry replacement and stale-token handling.
- [ ] Correct transitive consumer closure.
- [ ] Truthful rollback versus committed-cleanup-error reporting.
- [ ] Event-mode isolation.
- [ ] `FAILED_RUNTIME` propagation.
- [ ] Live readiness completeness.
- [ ] Removal verifier independence from deleted feature implementations.
- [ ] Absence of direct cross-feature imports.

---

## 7. Deferred work outside this remediation

The following must not expand this PR:

- Real MT5, cTrader, Binance, or other broker adapters.
- Real order execution.
- Risk-engine business rules.
- Portfolio tracking implementations.
- Strategy, indicator, research, simulator, or optimizer domain features.
- Process-isolated untrusted plugins.
- Native-extension hot reload.
- Full distributed or multi-process orchestration.
- Automatic compensation of irreversible external actions.
- Persistent schema migrations beyond the existing storage foundation.

Those features should be built only after this foundation passes all acceptance scenarios.

---

## 8. Definition of complete remediation

The remediation is complete only when:

- [ ] Spatial boundaries are enforced statically.
- [ ] Feature enable, disable, absence, failure, and replacement are represented at runtime.
- [ ] Every provider change produces a fresh consumer dependency graph.
- [ ] Replacement scopes preserve all committed effects.
- [ ] Pre-commit rollback is exact.
- [ ] Post-commit cleanup errors are visible and not misrepresented.
- [ ] Runtime task failures invalidate capabilities and reconcile dependents.
- [ ] Event dispatch modes are enforced.
- [ ] Provider selection is deterministic.
- [ ] Live readiness is fail-closed.
- [ ] The real application shell is executable.
- [ ] Physical deletion is verified automatically for every built-in feature.
- [ ] Documentation describes implemented runtime truth.
- [ ] Ruff, mypy, Import Linter, AST checks, pytest, coverage, and removal verification pass locally and in GitHub Actions.

At that point, the foundational claim can be upgraded from:

> Spatial composability with basic temporal cleanup

To:

> Verified spatiotemporal composability for built-in Python features, with deterministic dependency reconciliation, lifecycle-safe replacement, fail-closed readiness, runtime supervision, and automated physical-removal evidence.

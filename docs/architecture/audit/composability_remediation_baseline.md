# Spatiotemporal Composability Remediation — Baseline Audit Record

## 1. Audit Metadata

- **Date:** 2026-08-21
- **Baseline Commit SHA:** `c1584cb572fee29e119ec0daebb689b247aafe40`
- **Baseline Branch:** `main`
- **Target Branch:** Implementation branch for gap remediation
- **Python Version:** `3.14.3`
- **uv Version:** `0.12.3`
- **Platform:** Windows (win32)

> [!IMPORTANT]
> GitHub Actions CI results on pull requests and target branches, rather than local developer claims or commit message texts, are the authoritative remote evidence for architectural verification.

---

## 2. Baseline Quality Gate Results

All commands executed at the audited baseline commit:

| Quality Gate | Command | Status | Details |
|---|---|---|---|
| Ruff Formatting | `ruff format --check .` | **PASSED** | 0.24s |
| Ruff Linting | `ruff check .` | **PASSED** | 0.12s |
| Mypy Strict Typing | `mypy` | **PASSED** | 0.80s (with tests override) |
| Import Linter | `lint-imports` | **PASSED** | 0.36s (3 contracts passed) |
| AST Architecture Check | `python scripts/architecture_check.py` | **PASSED** | 0.27s (0 violations) |
| Pytest & Coverage | `pytest --cov=app --cov-fail-under=80` | **PASSED** | 151 passed in 3.46s, Coverage: 95.52% |

---

## 3. Characterization Failure-to-Phase Mapping

Phase 0 introduces characterization tests that deliberately fail on the existing baseline implementation to lock in the target behaviors before code remediation begins:

| Test Identifier | Test File | Target Phase | Description of Audited Defect |
|---|---|---|---|
| `test_legacy_profile_section_rejected` | `tests/composition/test_config.py` | **Phase 1** | Legacy `[profile]` section currently silently falls back to default profile instead of raising a typed configuration error. |
| `test_unknown_profile_rejected` | `tests/composition/test_config.py` | **Phase 1** | Unknown profile string in config is not validated/rejected. |
| `test_live_readiness_requires_all_safety_capabilities` | `tests/composition/test_readiness.py` | **Phase 1** | `check_profile_readiness` for `"live"` omitted `trading.execution@1`, `portfolio.positions@1`, `data.realtime-ticks@1`. |
| `test_unknown_profile_fails_readiness` | `tests/composition/test_readiness.py` | **Phase 1** | Unknown profile currently returns `is_ready=True` with empty requirements. |
| `test_ambiguous_providers_rejected_without_selection` | `tests/kernel/test_graph.py` | **Phase 2** | Two enabled providers for the same capability without selection silently pick arbitrary provider rather than failing. |
| `test_required_dependency_cycle_raises_explicit_error` | `tests/kernel/test_graph.py` | **Phase 3** | Cycle detection was caught by fixed-point eligibility rather than raising `DependencyCycleError`. |
| `test_provider_reconfiguration_remounts_transitive_consumers` | `tests/kernel/test_reconciler.py` | **Phase 3** | Reconfiguring provider does not update provider instances captured by downstream consumers. |
| `test_transactional_replacement_preserves_staged_effects_after_commit` | `tests/composition/test_hot_reconfiguration.py` | **Phase 4** | Staged `shadow_scope` is closed on commit, cancelling tasks/listeners spawned during mount of replacement. |
| `test_transactional_replacement_post_commit_cleanup_failure_reporting` | `tests/composition/test_hot_reconfiguration.py` | **Phase 4** | Old scope cleanup failure should report committed with cleanup errors rather than claiming rollback or silencing. |
| `test_event_mode_strict_isolation` | `tests/kernel/test_events.py` | **Phase 5** | `publish()` currently invokes handlers regardless of whether they registered with `SERIAL`, `PARALLEL`, or `PIPELINE`. |
| `test_duplicate_subscription_exact_token_disposal` | `tests/kernel/test_events.py` | **Phase 5** | Disposing one duplicate subscription removes all subscriptions for that handler. |
| `test_unexpected_task_failure_transitions_to_failed_runtime` | `tests/services/test_lifecycle_leak.py` | **Phase 6** | Spawned task crashing in background leaves feature in `ACTIVE` state. |
| `test_scope_registration_on_closed_scope_raises_error` | `tests/kernel/test_scope.py` | **Phase 7** | Closed `FeatureScope` allows adding new callbacks/tasks without raising `ScopeClosedError`. |

---

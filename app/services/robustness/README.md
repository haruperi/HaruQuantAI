# Robustness

> **Package:** `app/services/robustness/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-ROBUSTNESS`

This README is the domain's single source of truth for its boundary, feature and FR registry,
domain-local workflows, semantic contract ownership, persisted-state model, acceptance evidence,
and deletion behavior. Reference-product evidence is a requirement source, never implementation
evidence.

`PROJECT.md` owns system scope and cross-domain behavior. `ARCHITECTURE.md` owns universal
structure and runtime constraints. `AGENTS.md` owns contributor workflow. The
[Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md) owns the
complete single-file feature delivery checklist.

## Code-aligned implementation convention

Backend features use the simplified modular-monolith layout:

```text
app/services/robustness/
|-- README.md
|-- __init__.py
|-- funnel.py
|-- retests.py
|-- monte_carlo.py
|-- walk_forward_matrix.py
`-- verdicts.py

app/contracts/robustness.py
app/services/persistence/robustness.py
tests/services/robustness/<feature>/
tests/examples/12_robustness.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/robustness.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/robustness.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/12_robustness.py`.

---

## 1. Purpose and boundary

### Purpose

Own ordered cross-check funnels, higher-precision/additional-market retests, Monte Carlo perturbations, walk-forward matrix evaluation, acceptance gates, and verdicts.

### Owns

- Versioned check definitions, ordered execution, early dismissal, and cost estimates.
- Trade/execution/history/parameter perturbations with named seed streams and distributions.
- Walk-forward/matrix cells, cluster rules, per-check evidence, and aggregate verdicts.

### Does not own

- Base simulation, optimization trial scheduling, metric formulas, or portfolio construction.
- Inventing acceptance thresholds from vendor examples.

### Shared contracts


The public boundary is `app/contracts/robustness.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `robustness.funnel@1` | `CrossCheckFunnel` | `1` | Ordered gated cross-check execution |
| Missing | `robustness.retests@1` | `RobustnessRetester` | `1` | Precision, market, and timeframe retests |
| Missing | `robustness.monte_carlo@1` | `MonteCarloService` | `1` | Seeded perturbation scenario distributions |
| Missing | `robustness.walk_forward_matrix@1` | `WalkForwardMatrixService` | `1` | Walk-forward matrix cells and clusters |
| Missing | `robustness.verdicts@1` | `RobustnessVerdictService` | `1` | Explainable pass/fail/inconclusive verdicts |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `robustness.v1` | `FEAT-ROBUSTNESS-FUNNEL` and registry peers | `sqlite` | Explicit reference-safe policy | `robustness.funnel@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-ROBUSTNESS-FUNNEL` | Ordered gated cross-check execution | `app/services/robustness/funnel.py` | `robustness.funnel@1` | `workspace.jobs@1` | Missing |
| `FEAT-ROBUSTNESS-RETEST` | Precision, market, and timeframe retests | `app/services/robustness/retests.py` | `robustness.retests@1` | `simulator.backtest@1` | Missing |
| `FEAT-ROBUSTNESS-MONTECARLO` | Seeded perturbation scenario distributions | `app/services/robustness/monte_carlo.py` | `robustness.monte_carlo@1` | `simulator.backtest@1` | Missing |
| `FEAT-ROBUSTNESS-WALKFORWARD` | Walk-forward matrix cells and clusters | `app/services/robustness/walk_forward_matrix.py` | `robustness.walk_forward_matrix@1` | `optimization.walk_forward@1` | Missing |
| `FEAT-ROBUSTNESS-VERDICTS` | Explainable pass/fail/inconclusive verdicts | `app/services/robustness/verdicts.py` | `robustness.verdicts@1` | `analytics.metrics@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-ROBUSTNESS-FUNNEL` — Execute an ordered robustness funnel

- **Lead owner:** `FEAT-ROBUSTNESS-FUNNEL`
- **Participants:** Configured checks, simulator, optimizer, metrics, jobs, and artifact store.
- **Input boundary:** Immutable strategy/base result, ordered checks, scenario counts/seeds, thresholds, and stop policy.
- **Output boundary:** Per-check results/distributions/reasons plus pass/fail/inconclusive/cancelled aggregate verdict.
- **Failure boundary:** A mandatory failure skips later expensive checks with reason; cancellation/error never becomes pass.
- **Acceptance:** `ATW-ROBUSTNESS-FUNNEL-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `funnel.py` — `FEAT-ROBUSTNESS-FUNNEL`

> **Feature ID:** `FEAT-ROBUSTNESS-FUNNEL`
> **Status:** `Missing`
> **Owner module:** `app/services/robustness/funnel.py`

#### Purpose

Provide ordered gated cross-check execution without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `robustness.funnel@1`
- **Requires:** `workspace.jobs@1`
- **Optional / operation-gated:** absence is explicit; no silent substitution.

#### Configuration and limits

Configuration is immutable, typed, versioned, and bounded. Reference sample values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatible versions |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability/contribution | Managed feature scope | Withdraw with scope |
| Task/subscription/resource | Managed lifecycle API | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence/API protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/robustness.py`
- **Namespace:** `robustness.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `funnel.py` | Ordered gated cross-check execution; configuration, service, lifecycle, immutable specification, factory/contribution | `CrossCheckFunnel` |
| Missing | `retests.py` | Precision, market, and timeframe retests; configuration, service, lifecycle, immutable specification, factory/contribution | `RobustnessRetester` |
| Missing | `monte_carlo.py` | Seeded perturbation scenario distributions; configuration, service, lifecycle, immutable specification, factory/contribution | `MonteCarloService` |
| Missing | `walk_forward_matrix.py` | Walk-forward matrix cells and clusters; configuration, service, lifecycle, immutable specification, factory/contribution | `WalkForwardMatrixService` |
| Missing | `verdicts.py` | Explainable pass/fail/inconclusive verdicts; configuration, service, lifecycle, immutable specification, factory/contribution | `RobustnessVerdictService` |
| Missing | `tests/examples/12_robustness.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-ROBUSTNESS-001` | Checks run in configured order and early dismissal is recorded. | Funnel integration |
| Missing | `FR-ROBUSTNESS-002` | Scenario generation is reproducible and each seed/config is retained. | Monte Carlo golden |
| Missing | `FR-ROBUSTNESS-003` | Acceptance uses named metric versions, quantiles, comparators, and sample scope. | Boundary tests |
| Missing | `FR-ROBUSTNESS-004` | WFM cluster evaluation is deterministic and example thresholds are not defaults. | Matrix fixtures |

#### Removal behavior

Withdraw the capability and managed effects while retaining schema-readable artifacts. Dependent
operations return attributed unavailable; reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/robustness.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/robustness.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-ROBUSTNESS-001` | Verdicts distinguish fail, inconclusive, cancelled, and error. | Truthfulness | E-O04 |
| Open | `DEC-ROBUSTNESS-002` | Exact random distributions, clipping, and cell-boundary rules are unverified. | Parity | Statistical/reference fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/robustness/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/12_robustness.py
```

Editing uses explicit affected paths with `--no-cov`; the full candidate gate remains
`uv run python scripts/ci_check.py`.

- [ ] Stable feature and requirement IDs have one owner.
- [ ] Public contracts and exact `FeatureSpec` dependencies exist.
- [ ] Registration is explicit; imports have no runtime effects.
- [ ] Happy, invalid, boundary, unavailable, lifecycle, persistence, and removal tests pass.
- [ ] Numerical or stateful behavior has deterministic golden/fault fixtures.
- [ ] One offline usage example exists per completed feature.
- [ ] Domain status reflects repository evidence, not reference-product evidence.
- [ ] Architecture and full qualification gates pass.

---

## 8. Change process

1. Update this README and identify the exact feature/requirement scope.
2. Update `app/contracts/robustness.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/robustness.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Official cross-checks form an ordered cost funnel with early dismissal: higher precision, Monte Carlo trade manipulation, additional markets, and Monte Carlo retests are documented categories (E-O04). Local snippets add trade reorder/resample/skip/execution degradation and randomized history/OHLC/minimum distance/slippage/spread/start/parameters (E-L04). Each method defines distribution, bounds, correlation, clipping, seed derivation, scenario count, metric profile and acceptance statistic. WFM spans run/window and OOS-percent cells; cluster examples such as 7 of 9 passing in a 3x3 neighborhood are illustrative, not universal defaults (E-O05). A verdict records all skipped/failed cells and source identities.

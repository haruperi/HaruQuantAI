# Portfolio

> **Package:** `app/services/portfolio/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-PORTFOLIO`

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
app/services/portfolio/
|-- README.md
|-- __init__.py
|-- definitions.py
|-- correlation.py
|-- composer.py
|-- search.py
`-- simulation.py

app/contracts/portfolio.py
app/services/persistence/portfolio.py
tests/services/portfolio/<feature>/
tests/examples/13_portfolio.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/portfolio.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/portfolio.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/13_portfolio.py`.

---

## 1. Purpose and boundary

### Purpose

Own portfolio definitions, immutable strategy-result membership, weights, correlation/overlap analysis, constrained combination search, and shared-capital simulation.

### Owns

- Member/result identities, enabled state, weights, groups/sectors, capital/leverage, and constraints.
- Aligned return/equity inputs, overlap-aware correlation, and diversification diagnostics.
- Manual composition and searched-portfolio artifacts with shared-capital results.

### Does not own

- Individual strategy backtests, metric definitions, or live order routing.
- Databank membership mechanics or account/broker truth.

### Shared contracts


The public boundary is `app/contracts/portfolio.py`; private implementation imports are forbidden.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `portfolio.definitions@1` | `PortfolioRepository` | `1` | Versioned members, weights, capital, and constraints |
| Missing | `portfolio.correlation@1` | `CorrelationService` | `1` | Aligned overlap-aware dependence analysis |
| Missing | `portfolio.composer@1` | `PortfolioComposer` | `1` | Manual weighting and result recomputation |
| Missing | `portfolio.search@1` | `PortfolioSearch` | `1` | Constrained brute-force/genetic combinations |
| Missing | `portfolio.simulation@1` | `PortfolioSimulator` | `1` | Shared-capital account replay |

### Persisted-state ownership


Semantic state remains feature-owned although storage mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `portfolio.v1` | `FEAT-PORTFOLIO-DEFINITIONS` and registry peers | `sqlite` | Explicit reference-safe policy | `portfolio.definitions@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-PORTFOLIO-DEFINITIONS` | Versioned members, weights, capital, and constraints | `app/services/portfolio/definitions.py` | `portfolio.definitions@1` | `persistence.artifacts@1` | Missing |
| `FEAT-PORTFOLIO-CORRELATION` | Aligned overlap-aware dependence analysis | `app/services/portfolio/correlation.py` | `portfolio.correlation@1` | `analytics.equity@1` | Missing |
| `FEAT-PORTFOLIO-COMPOSER` | Manual weighting and result recomputation | `app/services/portfolio/composer.py` | `portfolio.composer@1` | `simulator.backtest@1` | Missing |
| `FEAT-PORTFOLIO-SEARCH` | Constrained brute-force/genetic combinations | `app/services/portfolio/search.py` | `portfolio.search@1` | `portfolio.correlation@1` | Missing |
| `FEAT-PORTFOLIO-SIMULATION` | Shared-capital account replay | `app/services/portfolio/simulation.py` | `portfolio.simulation@1` | `simulator.account@1` | Missing |

Dependencies use versioned public contracts. Removing a contribution withdraws only its capability;
required consumers become attributed `BLOCKED`, optional operations return unavailable, and
retained state is not purged.

---

## 3. Domain workflows


### `WF-PORTFOLIO-COMPOSE` — Compose and evaluate a shared-capital portfolio

- **Lead owner:** `FEAT-PORTFOLIO-COMPOSER`
- **Participants:** Member results, analytics, correlation, constraints, simulation, and artifact store.
- **Input boundary:** Immutable member result IDs, weights/enabled state, capital, leverage, alignment, and limits.
- **Output boundary:** Versioned definition/result, correlation evidence, account/equity series, metrics, and constraint diagnostics.
- **Failure boundary:** Missing/incompatible member scope or invalid weights fail before replay; margin breach is an explicit result.
- **Acceptance:** `ATW-PORTFOLIO-COMPOSE-001`

---

## 4. Feature specifications


This representative card applies to every registry entry; exact algorithms and states are in Section 9.

### `definitions.py` — `FEAT-PORTFOLIO-DEFINITIONS`

> **Feature ID:** `FEAT-PORTFOLIO-DEFINITIONS`
> **Status:** `Missing`
> **Owner module:** `app/services/portfolio/definitions.py`

#### Purpose

Provide versioned members, weights, capital, and constraints without absorbing another feature's responsibility.

#### Capability declarations

- **Provides:** `portfolio.definitions@1`
- **Requires:** `persistence.artifacts@1`
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

- **Domain persistence module:** `app/services/persistence/portfolio.py`
- **Namespace:** `portfolio.v1`
- **Schema version:** `1` initially; forward migration only
- **Retention and purge:** explicit and reference-safe; removal never implicitly purges.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `definitions.py` | Versioned members, weights, capital, and constraints; configuration, service, lifecycle, immutable specification, factory/contribution | `PortfolioRepository` |
| Missing | `correlation.py` | Aligned overlap-aware dependence analysis; configuration, service, lifecycle, immutable specification, factory/contribution | `CorrelationService` |
| Missing | `composer.py` | Manual weighting and result recomputation; configuration, service, lifecycle, immutable specification, factory/contribution | `PortfolioComposer` |
| Missing | `search.py` | Constrained brute-force/genetic combinations; configuration, service, lifecycle, immutable specification, factory/contribution | `PortfolioSearch` |
| Missing | `simulation.py` | Shared-capital account replay; configuration, service, lifecycle, immutable specification, factory/contribution | `PortfolioSimulator` |
| Missing | `tests/examples/13_portfolio.py` | Offline primary-purpose evidence | one named scenario per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-PORTFOLIO-001` | Member identity binds result/data/config, not display name. | Identity test |
| Missing | `FR-PORTFOLIO-002` | Correlation declares return transform, alignment, overlap, missing policy, and minimum samples. | Golden matrix |
| Missing | `FR-PORTFOLIO-003` | Weight edits create a new result without rewriting member backtests. | Lineage test |
| Missing | `FR-PORTFOLIO-004` | Search enforces member/group/correlation/capital constraints deterministically. | Search fixtures |

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
| Missing | `ARCH-004` | Public contracts live in `app/contracts/portfolio.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/portfolio.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-PORTFOLIO-001` | Manual composition and portfolio search are distinct artifact types. | Semantics | E-O09 |
| Open | `DEC-PORTFOLIO-002` | Reference shared-margin/netting and search tie rules are unverified. | Parity | Hand/reference scenarios |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; installed names and
sample values are not runtime proof.

---

## 7. Tests and definition of done

```text
tests/services/portfolio/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/13_portfolio.py
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
2. Update `app/contracts/portfolio.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/portfolio.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

A member binds strategy and immutable result identities, enabled state, weight, group/sector and optional limits. Correlation inputs declare equity/return transform, resampling timezone/calendar, overlap interval, missing-value policy, minimum samples, and method; insufficient overlap is not zero correlation. Shared-capital replay orders simultaneous member events deterministically and applies explicit currency conversion, leverage, margin, netting/hedging, costs, and liquidation. Official Portfolio Composer changes weights and recomputes position sizing, distinct from Portfolio Master search (E-O09). Bundled automatic-portfolio settings demonstrate member, sector, correlation and metric constraints but their numeric values are examples (E-L03).

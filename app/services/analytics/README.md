# Analytics

> **Package:** `app/services/analytics/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-ANALYTICS`

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
app/services/analytics/
|-- README.md
|-- __init__.py
|-- metrics.py
|-- equity.py
|-- trades.py
|-- periods.py
`-- reports.py

app/contracts/analytics.py
app/services/persistence/analytics.py
tests/services/analytics/<feature>/
tests/examples/08_analytics.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/analytics.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/analytics.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/08_analytics.py`.

---

## 1. Purpose and boundary

### Purpose

Own the canonical metric registry, trade/equity/drawdown projections, time/side/exit analysis, and provenance-rich reports/exports.

### Owns

- Versioned metric definitions with scope, units, denominator, invalid behavior, precision, and direction.
- Reconciled equity, drawdown, trade, MAE/MFE, and period projections.
- Reports/exports bound to filters, registry version, source hashes, and warnings.

### Does not own

- Trade/fill mutation, strategy generation, or ranking policy.
- Portfolio membership or simulation event ordering.

### Shared contracts


The public boundary is `app/contracts/analytics.py`; counterparty status never authorizes a private import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `analytics.metrics@1` | `MetricRegistry` | `1` | Canonical versioned metric calculation |
| Missing | `analytics.equity@1` | `EquityAnalysis` | `1` | Equity and drawdown projections |
| Missing | `analytics.trades@1` | `TradeAnalysis` | `1` | Trade, MAE/MFE, direction, and exit analysis |
| Missing | `analytics.periods@1` | `PeriodAnalysis` | `1` | Timezone-explicit period aggregation |
| Missing | `analytics.reports@1` | `ReportService` | `1` | Versioned reports and machine exports |

### Persisted-state ownership


Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `analytics.v1` | `FEAT-ANALYTICS-METRICS` and registry peers | `sqlite` | Explicit reference-safe policy | `analytics.metrics@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-ANALYTICS-METRICS` | Canonical versioned metric calculation | `app/services/analytics/metrics.py` | `analytics.metrics@1` | `persistence.artifacts@1` | Missing |
| `FEAT-ANALYTICS-EQUITY` | Equity and drawdown projections | `app/services/analytics/equity.py` | `analytics.equity@1` | `analytics.metrics@1` | Missing |
| `FEAT-ANALYTICS-TRADES` | Trade, MAE/MFE, direction, and exit analysis | `app/services/analytics/trades.py` | `analytics.trades@1` | `persistence.artifacts@1` | Missing |
| `FEAT-ANALYTICS-PERIODS` | Timezone-explicit period aggregation | `app/services/analytics/periods.py` | `analytics.periods@1` | `analytics.metrics@1` | Missing |
| `FEAT-ANALYTICS-REPORTS` | Versioned reports and machine exports | `app/services/analytics/reports.py` | `analytics.reports@1` | `analytics.metrics@1` | Missing |

Dependencies point to public contracts, never implementations. Removal withdraws only the named
capability; required consumers become attributed `BLOCKED`, optional operations return
unavailable, and retained state is not purged.

---

## 3. Domain workflows


### `WF-ANALYTICS-PROJECT` — Project one result across synchronized views

- **Lead owner:** `FEAT-ANALYTICS-METRICS`
- **Participants:** Immutable trade/equity artifacts, registry, filters, and report service.
- **Input boundary:** Result identity, metric profile/version, sample, direction, currency, timezone, filters.
- **Output boundary:** Metric set and linked projections with common source identity and provenance.
- **Failure boundary:** Schema mismatch or undefined metric is typed invalid/not-applicable, never substituted zero.
- **Acceptance:** `ATW-ANALYTICS-PROJECT-001`

---

## 4. Feature specifications


This representative module card applies to every registry entry; algorithms and state semantics
are in Section 9.

### `metrics.py` — `FEAT-ANALYTICS-METRICS`

> **Feature ID:** `FEAT-ANALYTICS-METRICS`
> **Status:** `Missing`
> **Owner module:** `app/services/analytics/metrics.py`

#### Purpose

Provide canonical versioned metric calculation without absorbing another registry entry's responsibility.

#### Capability declarations

- **Provides:** `analytics.metrics@1`
- **Requires:** `persistence.artifacts@1`
- **Optional / operation-gated:** absence returns typed unavailable; no silent substitution.

#### Configuration and limits

Each owner has a slotted immutable `<Feature>Config`; sample reference values are not defaults.

| Status | Setting | Type / unit | Default | Validation and failure |
| --- | --- | --- | --- | --- |
| Missing | `schema_version` | positive integer | `1` | Reject incompatibility |
| Missing | `operation_timeout_s` | finite seconds | operation-specific | Positive and bounded |
| Missing | `resource_limit` | positive integer | deployment-specific | Reject unbounded/nonpositive |

#### Runtime effects and cleanup

| Effect | Acquisition | Cleanup / failure behavior |
| --- | --- | --- |
| Capability | `FeatureContext.provide(...)` | Withdraw with scope |
| Managed effects | `FeatureContext` resource/task/subscription APIs | Reverse-order close; failed start unwinds |
| Durable mutation | Focused persistence protocol | Roll back; partial output remains unpublished |

#### Persistent state

- **Domain persistence module:** `app/services/persistence/analytics.py`
- **Namespace:** `analytics.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** explicit and reference-safe; feature removal never purges state.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `metrics.py` | Canonical versioned metric calculation; config, service, lifecycle, immutable `SPEC`, factory | `MetricRegistry` |
| Missing | `equity.py` | Equity and drawdown projections; config, service, lifecycle, immutable `SPEC`, factory | `EquityAnalysis` |
| Missing | `trades.py` | Trade, MAE/MFE, direction, and exit analysis; config, service, lifecycle, immutable `SPEC`, factory | `TradeAnalysis` |
| Missing | `periods.py` | Timezone-explicit period aggregation; config, service, lifecycle, immutable `SPEC`, factory | `PeriodAnalysis` |
| Missing | `reports.py` | Versioned reports and machine exports; config, service, lifecycle, immutable `SPEC`, factory | `ReportService` |
| Missing | `tests/examples/08_analytics.py` | Offline evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-ANALYTICS-001` | One metric ID/version agrees in API, UI, filter, rank, and report. | Cross-surface golden |
| Missing | `FR-ANALYTICS-002` | Empty, invalid, undefined, not-applicable, and zero remain distinct. | Edge table |
| Missing | `FR-ANALYTICS-003` | Equity/drawdown reconcile to the source ledger. | Accounting invariants |
| Missing | `FR-ANALYTICS-004` | Rounding happens only at registered output unless explicitly profiled. | Neighbor test |

#### Removal behavior

Withdraw capability and managed effects; retain schema-readable artifacts. Dependent operations
return attributed unavailable. Reinstall requires schema/version compatibility.

---

## 5. Domain-wide requirements and invariants

| Status | Requirement ID | Rule | Verification |
| --- | --- | --- | --- |
| Missing | `ARCH-001` | `__init__.py` is docstring-only. | `scripts/architecture_check.py` |
| Missing | `ARCH-002` | Tasks and resources are managed through `FeatureContext`. | Lifecycle tests |
| Missing | `ARCH-003` | Logging uses `app.kernel.logging`; no service configures handlers. | Architecture/logging tests |
| Missing | `ARCH-004` | Public contracts live in `app/contracts/analytics.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/analytics.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-ANALYTICS-001` | Reference-compatible and standard profiles are separately named/versioned. | Metrics | Avoid ambiguity |
| Open | `DEC-ANALYTICS-002` | Sharpe deviation, exposure endpoints, and stability wording require fixtures. | Parity | Hand/reference fixtures |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; filenames and bundled
sample values are not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/analytics/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/08_analytics.py
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
2. Update `app/contracts/analytics.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/analytics.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Observed E-L04 profiles: expectancy is net profit/trades rounded 2; average trade same ratio rounded 4; profit factor is 0 for no trades and, with zero loss, 0 for zero profit or cap 5; drawdown follows realized equity/peaks; CAGR compounds capital plus realized P/L when valid; Calmar is CAGR/max DD%; return/DD uses 0 for 0/0 and cap 10 for positive profit at zero DD. Stability squares correlation of daily money equity to a first-final line and is negative with negative profit. SQN uses R-multiples and observed formulas split at 100 trades. Exposure counts occupied day buckets. Observed Sharpe seeds weekdays with -0.05/252 and annualizes by sqrt(252); this is a named reference profile. Full precision feeds calculations; presentation rounding does not.

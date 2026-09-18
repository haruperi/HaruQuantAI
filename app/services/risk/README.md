# Risk

> **Package:** `app/services/risk/`
> **Status:** `Missing`
> **Last updated:** `2026-09-18`
> **Domain ID:** `D-RISK`

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
app/services/risk/
|-- README.md
|-- __init__.py
|-- position_sizing.py
|-- protective_levels.py
|-- trailing_stop.py
|-- break_even.py
|-- scale_out.py
`-- limits.py

app/contracts/risk.py
app/services/persistence/risk.py
tests/services/risk/<feature>/
tests/examples/07_risk.py
```

Each feature module is one cohesive physical removal unit. It contains typed configuration,
service behavior, lifecycle wiring, immutable `SPEC`, and a zero-argument factory. Registration
is explicit in `app/registry.py`; import-time discovery and ambient singletons are forbidden.
Cross-boundary DTOs, protocols, events, errors, and capability keys live in
`app/contracts/risk.py`. Features resolve dependencies through `FeatureContext` and
never import sibling implementations.

All schema, parameterized SQL, and transactions for this domain live in
`app/services/persistence/risk.py`. A feature may be stateless, but it never accepts an
unrestricted database connection. Every completed feature contributes a deterministic, offline,
secret-safe example to `tests/examples/07_risk.py`.

---

## 1. Purpose and boundary

### Purpose

Own deterministic position sizing, protective levels, trailing, break-even, scale-out, and pre-trade exposure policies.

### Owns

- Unit-safe sizing with raw/normalized quantity and binding constraints.
- Stop/target/trailing/break-even/scale-out calculation and state.
- Pre-trade account/strategy/portfolio exposure checks.

### Does not own

- Order submission, broker reconciliation, or fill simulation.
- Strategy signals, market-data normalization, or account truth.

### Shared contracts


The public boundary is `app/contracts/risk.py`; counterparty status never authorizes a private import.

| Status | Capability or event | Protocol / DTO symbol | Version | Purpose |
| --- | --- | --- | --- | --- |
| Missing | `risk.position_sizing@1` | `PositionSizer` | `1` | Fixed, monetary, percent, and ATR sizing |
| Missing | `risk.protective_levels@1` | `ProtectiveLevelService` | `1` | Stop-loss and profit-target levels |
| Missing | `risk.trailing_stop@1` | `TrailingStopPolicy` | `1` | Monotonic trailing protection |
| Missing | `risk.break_even@1` | `BreakEvenPolicy` | `1` | Trigger-based break-even moves |
| Missing | `risk.scale_out@1` | `ScaleOutPolicy` | `1` | Quantity-step-safe partial exits |
| Missing | `risk.pretrade_limits@1` | `PretradeLimits` | `1` | Exposure and loss constraints |

### Persisted-state ownership


Semantic state remains feature-owned although database mechanics are centralized.

| Status | Namespace | Owning feature | Driver | Retention | Public read boundary |
| --- | --- | --- | --- | --- | --- |
| Missing | `risk.v1` | `FEAT-RISK-SIZING` and registry peers | `sqlite` | Explicit reference-safe policy | `risk.position_sizing@1` |

---

## 2. Feature registry and dependency direction


| Feature | Delivered value | Owner module | Provides | Required capabilities | Status |
| --- | --- | --- | --- | --- | --- |
| `FEAT-RISK-SIZING` | Fixed, monetary, percent, and ATR sizing | `app/services/risk/position_sizing.py` | `risk.position_sizing@1` | `data.instruments@1` | Missing |
| `FEAT-RISK-PROTECTION` | Stop-loss and profit-target levels | `app/services/risk/protective_levels.py` | `risk.protective_levels@1` | `data.instruments@1` | Missing |
| `FEAT-RISK-TRAILING` | Monotonic trailing protection | `app/services/risk/trailing_stop.py` | `risk.trailing_stop@1` | `risk.protective_levels@1` | Missing |
| `FEAT-RISK-BREAKEVEN` | Trigger-based break-even moves | `app/services/risk/break_even.py` | `risk.break_even@1` | `risk.protective_levels@1` | Missing |
| `FEAT-RISK-SCALEOUT` | Quantity-step-safe partial exits | `app/services/risk/scale_out.py` | `risk.scale_out@1` | `data.instruments@1` | Missing |
| `FEAT-RISK-LIMITS` | Exposure and loss constraints | `app/services/risk/limits.py` | `risk.pretrade_limits@1` | `risk.position_sizing@1` | Missing |

Dependencies point to public contracts, never implementations. Removal withdraws only the named
capability; required consumers become attributed `BLOCKED`, optional operations return
unavailable, and retained state is not purged.

---

## 3. Domain workflows


### `WF-RISK-SIZE` — Size and protect an intended position

- **Lead owner:** `FEAT-RISK-SIZING`
- **Participants:** Instrument metadata, account snapshot, conversions, protection and limit policies.
- **Input boundary:** Policy/version, equity/currency, entry/stop/direction, rules, exposure, weight, conversion time.
- **Output boundary:** Raw/normalized quantity, risk amount/percent, protection, constraints, warnings.
- **Failure boundary:** Nonfinite/stale/zero inputs fail closed; fallback only when explicitly configured.
- **Acceptance:** `ATW-RISK-SIZE-001`

---

## 4. Feature specifications


This representative module card applies to every registry entry; algorithms and state semantics
are in Section 9.

### `position_sizing.py` — `FEAT-RISK-SIZING`

> **Feature ID:** `FEAT-RISK-SIZING`
> **Status:** `Missing`
> **Owner module:** `app/services/risk/position_sizing.py`

#### Purpose

Provide fixed, monetary, percent, and atr sizing without absorbing another registry entry's responsibility.

#### Capability declarations

- **Provides:** `risk.position_sizing@1`
- **Requires:** `data.instruments@1`
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

- **Domain persistence module:** `app/services/persistence/risk.py`
- **Namespace:** `risk.v1`
- **Schema version:** `1` initially; forward migrations only
- **Retention and purge:** explicit and reference-safe; feature removal never purges state.

#### Single-file structure and symbols

| Status | Owner | Responsibility | Symbols |
| --- | --- | --- | --- |
| Missing | `position_sizing.py` | Fixed, monetary, percent, and ATR sizing; config, service, lifecycle, immutable `SPEC`, factory | `PositionSizer` |
| Missing | `protective_levels.py` | Stop-loss and profit-target levels; config, service, lifecycle, immutable `SPEC`, factory | `ProtectiveLevelService` |
| Missing | `trailing_stop.py` | Monotonic trailing protection; config, service, lifecycle, immutable `SPEC`, factory | `TrailingStopPolicy` |
| Missing | `break_even.py` | Trigger-based break-even moves; config, service, lifecycle, immutable `SPEC`, factory | `BreakEvenPolicy` |
| Missing | `scale_out.py` | Quantity-step-safe partial exits; config, service, lifecycle, immutable `SPEC`, factory | `ScaleOutPolicy` |
| Missing | `limits.py` | Exposure and loss constraints; config, service, lifecycle, immutable `SPEC`, factory | `PretradeLimits` |
| Missing | `tests/examples/07_risk.py` | Offline evidence | one `example_<NN>_<feature_slug>()` per completed feature |

#### Functional requirements

| Status | Requirement ID | Observable behavior | Evidence |
| --- | --- | --- | --- |
| Missing | `FR-RISK-001` | Sizing is finite, unit-safe, deterministic, and step compliant. | Golden table |
| Missing | `FR-RISK-002` | Invalid or stale monetary inputs fail closed. | Boundary tests |
| Missing | `FR-RISK-003` | Protective rounding never increases risk beyond policy. | Tick-neighbor test |
| Missing | `FR-RISK-004` | Trailing and break-even changes are side-correct and monotonic. | Long/short tables |

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
| Missing | `ARCH-004` | Public contracts live in `app/contracts/risk.py`. | Import/contract checks |
| Missing | `ARCH-005` | Feature modules never import sibling implementations. | Import checks |
| Missing | `ARCH-006` | SQL/schema operations live in `app/services/persistence/risk.py`. | Architecture/schema checks |

---

## 6. Decisions and open evidence


| Status | Decision ID | Decision or missing evidence | Scope | Required closure |
| --- | --- | --- | --- | --- |
| Accepted | `DEC-RISK-001` | Financial values retain units and explicit rounding. | Policies | Architecture numeric rules |
| Open | `DEC-RISK-002` | Trailing activation/order and broker freeze distance are unverified. | Parity/adapters | Fixtures and vendor docs |

Evidence IDs resolve through `docs/PROJECT.md`. Unknowns remain explicit; filenames and bundled
sample values are not proof of runtime semantics.

---

## 7. Tests and definition of done

```text
tests/services/risk/<feature>/
|-- test_config.py
|-- test_<feature>.py
|-- test_lifecycle.py
|-- test_removal.py
`-- test_persistence.py       # when applicable

tests/examples/07_risk.py
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
2. Update `app/contracts/risk.py` first when the public boundary changes.
3. Implement one cohesive owner module and immutable `SPEC`.
4. Change `app/services/persistence/risk.py` only for database mechanics.
5. Update explicit registry, consolidated examples, and focused tests.
6. Verify feature removal and affected consumers.
7. Run the repository-prescribed candidate gate and record actual results.

---

## 9. Normative domain specification

Observed fixed-risk behavior derives stop ticks from entry-to-stop or configured fallback, computes loss per lot from tick count/size/value, caps weighted risk at 100%, divides equity risk by loss per lot, normalizes to volume step/decimals, uses an explicitly selected fallback when nonpositive, and caps maximum lots. ATR sizing uses prior-bar ATR times a multiplier (E-L04). Break-even is observed on bar-open: long uses bid, short ask; the stop must improve protection, honor minimum distance, and normalize to ticks. Exact trailing activation remains unverified. Scale-out children plus remainder reconcile exactly at volume-step precision.

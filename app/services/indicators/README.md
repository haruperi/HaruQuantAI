# Indicators

> **Package:** `app/services/indicators/`
> **Status:** `Partial` — documentary target; runtime acceptance is **NOT_REVALIDATED**.
> **Last updated:** `2026-09-06`
> **Domain ID:** `D-IND`

> This README is the domain target registry for boundaries, composable feature capabilities, requirements, ownership, workflows, acceptance, and removal. Update it before changing the affected implementation. It does not certify that a target package, contract, test, usage demonstration or provider is already implemented.

**Selected scope:** 7 features · 21 owned functional requirements · 14 feature-local non-functional requirements. All original feature and requirement IDs are retained. These selected workbench obligations do **not** delete unrelated existing domain behavior. This document must be merged with current evidence and any out-of-scope entries before replacing an existing domain registry.

**Sources:** [Unified Specification](../../../docs/dev/SQX/HaruQuantAI_Unified_Specification.md) · [Feature–Requirement Traceability Register](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md) · [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md) · [README template](../../../docs/templates/README.md). Source fingerprints and unresolved bindings are recorded in §6 and §9. The feature cards below reproduce owned requirements and acceptance oracles; their scoped shared-NFR, catalogue, original-ID and operation-gate tables remain binding through the linked source card.

---

## Code-Aligned Implementation Convention

This domain README defines target behavior; `PROJECT.md` retains system scope, cross-domain policy, system NFRs and release gates, and `ARCHITECTURE.md` retains universal package/runtime constraints. Feature-local READMEs, manifests, contracts, migrations and evidence mirror rather than silently redefine this target. For focused work, load §1, the affected §4 card, applicable §5 and §9 rules, and §7. Follow the [Feature Implementation Pipeline](../../../docs/dev/feature_implementation_pipeline.md).

Implement one feature directly in its selected owner folder and discover it through the `haruquantai.features` Python entry-point group. Declare one immutable `SPEC = FeatureSpec(...)` in `manifest.py`; do not introduce a domain registry or YAML manifest. The feature contains pure `__init__.py`, a runtime-validated `README.md`, strict `config.py` with `.from_dict()`, lifecycle `feature.py`, focused logic modules and required `_usage.py`. Add `_persistence.py` only when the feature performs database operations. Effects and dependencies flow through `FeatureContext` and `FeatureScope`; durable state is declared by `FeatureSpec.state`. Existing compatible public contracts and owners are reused, not copied into a parallel implementation.

Each core logic module documents its public API. Every service feature has one required `_usage.py` containing its bounded offline `if __name__ == "__main__":` scenarios; production logic modules do not contain demonstrations. Optional `_persistence.py` owns all feature-local database operations when durable state is required. The paths below are documentary targets pending current-code reconciliation, not claims of executable files. Tests verify the scenarios independently.

FR and acceptance IDs are trace identities, not runtime registrations. Required-provider keys below reproduce the register’s required graph. Optional providers are operation-gated: they must be declared and tested without making an absent future extension a universal startup dependency. The plan’s P1–P16 execution phases are distinct from specification U0–U13 release milestones; a U label is not proof of readiness or a new feature task.

## 1. Purpose and Boundary

### Purpose

Supply deterministic numerical series and predicates with explicit types, units, warm-up, missingness and causal availability. Strategy, Research and Analytics consume the same mathematical definitions rather than reproduce calculations in their own layers.

### Owns

Trend and moving-average series; momentum/oscillator series; volatility and channel series; source-aware volume/flow series; candle predicates; rolling and fitted series transforms; Volume Profile and TPO calculations.

### Does not own

Market-data acquisition, repair and clock definitions; strategy entry/exit policy; order execution; chart rendering; arbitrary model training. Indicator availability does not imply support in every exporter or execution target.

### Shared Contracts

**Owned by this domain.** Status is an evidence state. Contract modules are selected public boundaries; an unbound symbol/DTO must be reconciled before implementing its production consumer. Do not infer a callable signature from the English title.

| Evidence | Capability | Protocol / DTO / contract target | Major | Purpose |
| --- | --- | --- | --- | --- |
| NOT_REVALIDATED | `indicators.calculate-trend@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/calculate_trend.py`](../../contracts/indicators/calculate_trend.py) | 1 | Calculate causal trend and moving-average series |
| NOT_REVALIDATED | `indicators.calculate-momentum@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/calculate_momentum.py`](../../contracts/indicators/calculate_momentum.py) | 1 | Calculate causal oscillators and momentum series |
| NOT_REVALIDATED | `indicators.calculate-volatility@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/calculate_volatility.py`](../../contracts/indicators/calculate_volatility.py) | 1 | Calculate causal volatility and channel series |
| NOT_REVALIDATED | `indicators.calculate-volume-flow@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/calculate_volume_flow.py`](../../contracts/indicators/calculate_volume_flow.py) | 1 | Calculate source-aware volume and flow series |
| NOT_REVALIDATED | `indicators.detect-candle-patterns@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/detect_candle_patterns.py`](../../contracts/indicators/detect_candle_patterns.py) | 1 | Recognize declared candle-pattern predicates |
| NOT_REVALIDATED | `indicators.transform-series@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/transform_series.py`](../../contracts/indicators/transform_series.py) | 1 | Calculate typed rolling and fitted series transforms |
| NOT_REVALIDATED | `indicators.calculate-market-profiles@1` | Public operation/DTO symbols in the selected contract; literal binding remains open.<br>[`app/contracts/indicators/calculate_market_profiles.py`](../../contracts/indicators/calculate_market_profiles.py) | 1 | Calculate Volume Profile and TPO |

**Consumed from other domains — required providers.** Runtime resolution is through the exact key; the provider’s implementation folder is not an import target. Same-domain edges are listed in the owning feature card.

There are no cross-domain required-provider edges in this selected register slice.

**Operation-gated providers.** For each §4 feature, its linked source card’s complete “Operation-gated providers” table defines applicability, exact provider identity and absence behavior. This is scoped incorporation, not permission to treat all 233 register-wide operation edges as optional for every feature. Resolve those provider IDs to their primary capability keys in the corresponding domain README; bind actual operations in the acceptance record. An omitted local duplicate table does not waive a source dependency.

### Persisted State Ownership

Bounded per-evaluation rolling/kernel state and explicitly pinned fit artifacts where applicable. No implicit shared mutable indicator history. Durable artifacts use the declared owner and Workspace custody.

| Evidence | Owning feature | Partition / ownership class | Driver binding | Retention / read boundary |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | [`FEAT-IND-CALCULATE_TREND`](#feat-ind-calculate-trend) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-CALCULATE_MOMENTUM`](#feat-ind-calculate-momentum) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-CALCULATE_VOLATILITY`](#feat-ind-calculate-volatility) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-CALCULATE_VOLUME_FLOW`](#feat-ind-calculate-volume-flow) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-DETECT_CANDLE_PATTERNS`](#feat-ind-detect-candle-patterns) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-TRANSFORM_SERIES`](#feat-ind-transform-series) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |
| BINDING_PENDING | [`FEAT-IND-CALCULATE_MARKET_PROFILES`](#feat-ind-calculate-market-profiles) | No new durable business partition selected here | No new business driver. | Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy. |

A feature’s exact durable namespace, schema version and migrations are taken from its reconciled manifest and contract, not guessed from its folder name. External consumers access semantic state only through the owner capability. Workspace persistence/artifact custody never acquires that semantic ownership.

### Four-Level Structural Hierarchy

| Code level | Represents | Domain example |
| --- | --- | --- |
| Package | Domain boundary | `app/services/indicators/` |
| Module folder | Composable feature owner | `app/services/indicators/calculate_trend/` — [`FEAT-IND-CALCULATE_TREND`](#feat-ind-calculate-trend) |
| File | Manifest, strict configuration, lifecycle or focused use case | `manifest.py`, `config.py`, `feature.py`, focused logic module |
| Class / function / method | One or more traced requirement behaviors | `FR-TRC-IND-CALCULATE_TREND-001` and its acceptance oracle |

### Domain Capability Map

The table in §2 is the complete domain capability map. Edges below illustrate dependency direction, not a new orchestrator or private import relationship.

```mermaid
flowchart LR
    Caller["Caller / consuming feature"] --> Contract["Versioned public contract"]
    Provider["Removable domain feature"] -->|provides| Contract
    Provider --> Scope["Scoped effects and disposal"]
    Provider --> State["Own records only, when declared"]
```

## 2. Final Package Structure and Feature Independence

Feature owners are independent and physically removable. The selected package is a target binding: reconcile known current aliases and preserve compatible existing identities before creating a folder. Folder absence does not prove behavior absence. Removing a feature withdraws its contributions; it does not delete another feature’s source or retained evidence.

| Feature | Delivered value | Selected owner package | First U gate | FRs | Local NFRs | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [`FEAT-IND-CALCULATE_TREND`](#feat-ind-calculate-trend) | Calculate causal trend and moving-average series | `app/services/indicators/calculate_trend/` | U2 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-CALCULATE_MOMENTUM`](#feat-ind-calculate-momentum) | Calculate causal oscillators and momentum series | `app/services/indicators/calculate_momentum/` | U2 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-CALCULATE_VOLATILITY`](#feat-ind-calculate-volatility) | Calculate causal volatility and channel series | `app/services/indicators/calculate_volatility/` | U2 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-CALCULATE_VOLUME_FLOW`](#feat-ind-calculate-volume-flow) | Calculate source-aware volume and flow series | `app/services/indicators/calculate_volume_flow/` | U5 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-DETECT_CANDLE_PATTERNS`](#feat-ind-detect-candle-patterns) | Recognize declared candle-pattern predicates | `app/services/indicators/detect_candle_patterns/` | U5 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-TRANSFORM_SERIES`](#feat-ind-transform-series) | Calculate typed rolling and fitted series transforms | `app/services/indicators/transform_series/` | U2 | 3 | 2 | NOT_REVALIDATED |
| [`FEAT-IND-CALCULATE_MARKET_PROFILES`](#feat-ind-calculate-market-profiles) | Calculate Volume Profile and TPO | `app/services/indicators/calculate_market_profiles/` | U10 | 3 | 2 | NOT_REVALIDATED |

```text
app/services/indicators/
├── README.md  # this domain target registry
├── __init__.py  # docstring only
├── calculate_trend/  # FEAT-IND-CALCULATE_TREND
├── calculate_momentum/  # FEAT-IND-CALCULATE_MOMENTUM
├── calculate_volatility/  # FEAT-IND-CALCULATE_VOLATILITY
├── calculate_volume_flow/  # FEAT-IND-CALCULATE_VOLUME_FLOW
├── detect_candle_patterns/  # FEAT-IND-DETECT_CANDLE_PATTERNS
├── transform_series/  # FEAT-IND-TRANSFORM_SERIES
└── calculate_market_profiles/  # FEAT-IND-CALCULATE_MARKET_PROFILES
```

Every feature folder contains `README.md`, docstring-only `__init__.py`, `manifest.py`, `config.py`, `feature.py` and its focused logic modules. Shared contract definitions live outside those removable packages. The primary logic-module designation in §4 is a target for usage ownership; adapt a compatible existing module rather than duplicate its service.

### Feature Capability Dependency Direction

A required edge means “consumer requires the provider’s public capability.” It never means “import the provider package.” Optional operation closure is resolved by the composition/runtime boundary and rechecked at invocation. Physical removal must cause the declared unavailable or blocked state while unrelated capabilities remain usable.

## 3. Workflows

Workflows connect existing features; they do not create additional feature owners. “Internal” means all participating behavior is domain-local. “Cross-Domain” means collaboration through public contracts. Participant lists below are **not** a substitute for the plan’s execution schedule or the workflow’s validated operation graph.

### Domain-local reading sequence — Calculate a causal series

**Input boundary:** Validated typed buffers, parameters, clock, validity mask and source identity.

**Output boundary:** Versioned numerical outputs with valid/warm-up/undefined states and available-time semantics.

**Capabilities to inspect:** [`FEAT-IND-CALCULATE_TREND`](#feat-ind-calculate-trend) → [`FEAT-IND-CALCULATE_MOMENTUM`](#feat-ind-calculate-momentum).

This is a domain-oriented explanation, not an additional canonical `WF-*` identity. Apply every FR of the participating operation, not only its first validation step. Validate scope and immutable references, resolve admitted providers, perform owner work, verify the owner receipt, and then expose the result. Invalid input, provider absence, stale revision and cancellation retain separate typed outcomes.

No separate named workflow in the register’s 20-workflow set assigns this domain a participant here. The feature capabilities still participate in their actual caller/provider integration tests and release gates; the local reading sequence is not counted as a 21st workflow.

## 4. Composable Feature Specifications

Each card is one permanent feature/task slot. Its owned FRs, local NFRs and expected acceptance outcomes are reproduced below. All acceptance states are PENDING / NOT_REVALIDATED. Contract targets and intended tests do not prove runtime support. `Binding pending` prohibits executor invention: resolve the exact compatible contract, configuration, state and fixture before production use. The plan’s one-feature task rule includes all registered variants; future-provider qualification is not permission to leave owned adapter behavior unimplemented.

<a id="feat-ind-calculate-trend"></a>
### 4.1 `calculate_trend/` — `FEAT-IND-CALCULATE_TREND`

> **Feature ID:** `FEAT-IND-CALCULATE_TREND`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/calculate_trend/`
> **First release milestone:** `U2`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate causal trend and moving-average series. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.calculate-trend@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-trend) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/calculate_trend.py`](../../contracts/indicators/calculate_trend.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-CALCULATE_TREND-001`, `FR-TRC-IND-CALCULATE_TREND-002`, `NFR-TRC-IND-CALCULATE_TREND-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.calculate-trend@1` | FEAT-IND-CALCULATE_TREND | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-CALCULATE_TREND | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| calculate_trend.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-CALCULATE_TREND-001` | Use declared price/source inputs, periods, seed, warm-up, session and availability policy; preserve multi-output component identity. | `AT-IND-CALCULATE_TREND-001` | EMA uses the simple mean of the first N valid closed values, then alpha=2/(N+1); no pre-seed output is usable. Future-value perturbations cannot alter already available outputs. |
| PENDING | `FR-TRC-IND-CALCULATE_TREND-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-CALCULATE_TREND-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-CALCULATE_TREND-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-CALCULATE_TREND-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-CALCULATE_TREND-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-CALCULATE_TREND-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-CALCULATE_TREND-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-CALCULATE_TREND-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-trend): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/calculate_trend/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/calculate_trend/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-CALCULATE_TREND/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.calculate_trend._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-CALCULATE_TREND`. Withdraw `indicators.calculate-trend@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-calculate-momentum"></a>
### 4.2 `calculate_momentum/` — `FEAT-IND-CALCULATE_MOMENTUM`

> **Feature ID:** `FEAT-IND-CALCULATE_MOMENTUM`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/calculate_momentum/`
> **First release milestone:** `U2`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate causal oscillators and momentum series. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.calculate-momentum@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-momentum) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/calculate_momentum.py`](../../contracts/indicators/calculate_momentum.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-CALCULATE_MOMENTUM-001`, `FR-TRC-IND-CALCULATE_MOMENTUM-002`, `NFR-TRC-IND-CALCULATE_MOMENTUM-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.calculate-momentum@1` | FEAT-IND-CALCULATE_MOMENTUM | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-CALCULATE_MOMENTUM | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| calculate_momentum.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-CALCULATE_MOMENTUM-001` | Version oscillator units, bounds where applicable, smoothing, missingness and symmetry metadata; CCI is not declared bounded merely because it has a midpoint. | `AT-IND-CALCULATE_MOMENTUM-001` | Wilder RSI returns 50 for zero gain and zero loss, 100 for zero loss only and 0 for zero gain only; comparison/equality-boundary fixtures agree with the reference. |
| PENDING | `FR-TRC-IND-CALCULATE_MOMENTUM-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-CALCULATE_MOMENTUM-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-CALCULATE_MOMENTUM-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-CALCULATE_MOMENTUM-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-CALCULATE_MOMENTUM-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-CALCULATE_MOMENTUM-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-CALCULATE_MOMENTUM-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-CALCULATE_MOMENTUM-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-momentum): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/calculate_momentum/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/calculate_momentum/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-CALCULATE_MOMENTUM/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.calculate_momentum._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-CALCULATE_MOMENTUM`. Withdraw `indicators.calculate-momentum@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-calculate-volatility"></a>
### 4.3 `calculate_volatility/` — `FEAT-IND-CALCULATE_VOLATILITY`

> **Feature ID:** `FEAT-IND-CALCULATE_VOLATILITY`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/calculate_volatility/`
> **First release milestone:** `U2`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate causal volatility and channel series. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.calculate-volatility@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-volatility) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/calculate_volatility.py`](../../contracts/indicators/calculate_volatility.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-CALCULATE_VOLATILITY-001`, `FR-TRC-IND-CALCULATE_VOLATILITY-002`, `NFR-TRC-IND-CALCULATE_VOLATILITY-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.calculate-volatility@1` | FEAT-IND-CALCULATE_VOLATILITY | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-CALCULATE_VOLATILITY | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| calculate_volatility.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-CALCULATE_VOLATILITY-001` | Bind estimator definition, window, annualization/session/OHLC assumptions, seed and unavailable conditions rather than treating all volatility measures as interchangeable. | `AT-IND-CALCULATE_VOLATILITY-001` | ATR seeds the mean of N valid true ranges using the prior available close and then Wilder smoothing; zero/invalid denominators and inadequate history are unavailable. |
| PENDING | `FR-TRC-IND-CALCULATE_VOLATILITY-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-CALCULATE_VOLATILITY-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-CALCULATE_VOLATILITY-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-CALCULATE_VOLATILITY-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-CALCULATE_VOLATILITY-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-CALCULATE_VOLATILITY-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-CALCULATE_VOLATILITY-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-CALCULATE_VOLATILITY-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-volatility): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/calculate_volatility/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/calculate_volatility/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-CALCULATE_VOLATILITY/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.calculate_volatility._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-CALCULATE_VOLATILITY`. Withdraw `indicators.calculate-volatility@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-calculate-volume-flow"></a>
### 4.4 `calculate_volume_flow/` — `FEAT-IND-CALCULATE_VOLUME_FLOW`

> **Feature ID:** `FEAT-IND-CALCULATE_VOLUME_FLOW`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/calculate_volume_flow/`
> **First release milestone:** `U5`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate source-aware volume and flow series. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.calculate-volume-flow@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-volume-flow) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/calculate_volume_flow.py`](../../contracts/indicators/calculate_volume_flow.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-CALCULATE_VOLUME_FLOW-002`, `NFR-TRC-IND-CALCULATE_VOLUME_FLOW-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.calculate-volume-flow@1` | FEAT-IND-CALCULATE_VOLUME_FLOW | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-CALCULATE_VOLUME_FLOW | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| calculate_volume_flow.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-CALCULATE_VOLUME_FLOW-001` | Require declared feed volume meaning, price/volume alignment and missingness; bind adjusted-data and session assumptions. | `AT-IND-CALCULATE_VOLUME_FLOW-001` | Exchange-volume and tick-count inputs retain different provenance; a missing quantity cannot be silently interpreted as zero traded volume. |
| PENDING | `FR-TRC-IND-CALCULATE_VOLUME_FLOW-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-CALCULATE_VOLUME_FLOW-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-CALCULATE_VOLUME_FLOW-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-CALCULATE_VOLUME_FLOW-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-CALCULATE_VOLUME_FLOW-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-CALCULATE_VOLUME_FLOW-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-CALCULATE_VOLUME_FLOW-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-CALCULATE_VOLUME_FLOW-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-volume-flow): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/calculate_volume_flow/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/calculate_volume_flow/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-CALCULATE_VOLUME_FLOW/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.calculate_volume_flow._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-CALCULATE_VOLUME_FLOW`. Withdraw `indicators.calculate-volume-flow@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-detect-candle-patterns"></a>
### 4.5 `detect_candle_patterns/` — `FEAT-IND-DETECT_CANDLE_PATTERNS`

> **Feature ID:** `FEAT-IND-DETECT_CANDLE_PATTERNS`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/detect_candle_patterns/`
> **First release milestone:** `U5`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Recognize declared candle-pattern predicates. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.detect-candle-patterns@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-detect-candle-patterns) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/detect_candle_patterns.py`](../../contracts/indicators/detect_candle_patterns.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-DETECT_CANDLE_PATTERNS-002`, `NFR-TRC-IND-DETECT_CANDLE_PATTERNS-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.detect-candle-patterns@1` | FEAT-IND-DETECT_CANDLE_PATTERNS | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-DETECT_CANDLE_PATTERNS | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| detect_candle_patterns.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-DETECT_CANDLE_PATTERNS-001` | Define each pattern with explicit body/shadow ratios, comparison policy, lookback and closed-bar availability before registration. | `AT-IND-DETECT_CANDLE_PATTERNS-001` | Boundary and gap fixtures return true/false/unknown according to the registered definition; a forming or missing bar cannot produce a confirmed pattern. |
| PENDING | `FR-TRC-IND-DETECT_CANDLE_PATTERNS-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-DETECT_CANDLE_PATTERNS-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-DETECT_CANDLE_PATTERNS-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-DETECT_CANDLE_PATTERNS-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-DETECT_CANDLE_PATTERNS-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-DETECT_CANDLE_PATTERNS-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-DETECT_CANDLE_PATTERNS-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-DETECT_CANDLE_PATTERNS-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-detect-candle-patterns): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/detect_candle_patterns/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/detect_candle_patterns/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-DETECT_CANDLE_PATTERNS/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.detect_candle_patterns._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-DETECT_CANDLE_PATTERNS`. Withdraw `indicators.detect-candle-patterns@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-transform-series"></a>
### 4.6 `transform_series/` — `FEAT-IND-TRANSFORM_SERIES`

> **Feature ID:** `FEAT-IND-TRANSFORM_SERIES`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/transform_series/`
> **First release milestone:** `U2`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate typed rolling and fitted series transforms. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.transform-series@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-transform-series) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/transform_series.py`](../../contracts/indicators/transform_series.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-TRANSFORM_SERIES-001`, `FR-TRC-IND-TRANSFORM_SERIES-002`, `NFR-TRC-IND-TRANSFORM_SERIES-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.transform-series@1` | FEAT-IND-TRANSFORM_SERIES | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-TRANSFORM_SERIES | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| transform_series.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-TRANSFORM_SERIES-001` | Apply typed units, finite numerical domains, rolling state, fit-window metadata and explicit zero-variance/invalid arithmetic policies. | `AT-IND-TRANSFORM_SERIES-001` | Divide-by-zero and invalid log/root inputs are unavailable; fitted transforms reject evaluation timestamps and reuse training-fitted state on validation/test. |
| PENDING | `FR-TRC-IND-TRANSFORM_SERIES-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-TRANSFORM_SERIES-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-TRANSFORM_SERIES-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-TRANSFORM_SERIES-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-TRANSFORM_SERIES-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-TRANSFORM_SERIES-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-TRANSFORM_SERIES-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-TRANSFORM_SERIES-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-transform-series): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/transform_series/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/transform_series/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-TRANSFORM_SERIES/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.transform_series._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-TRANSFORM_SERIES`. Withdraw `indicators.transform-series@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

<a id="feat-ind-calculate-market-profiles"></a>
### 4.7 `calculate_market_profiles/` — `FEAT-IND-CALCULATE_MARKET_PROFILES`

> **Feature ID:** `FEAT-IND-CALCULATE_MARKET_PROFILES`
> **Domain:** `indicators`
> **Status:** `Partial` — target documented; full-scope implementation evidence **NOT_REVALIDATED**.
> **Selected owner:** `app/services/indicators/calculate_market_profiles/`
> **First release milestone:** `U10`; execution order remains in the [Phased Feature Implementation Plan](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md).

#### Purpose

Calculate Volume Profile and TPO. Deliver the bounded behaviors in the FR table through this feature’s declared public capability; retain the domain boundary in §1.

#### Capability Declarations

**Provides:** `indicators.calculate-market-profiles@1`.

**Required capabilities:**

None (root with respect to the register’s required-provider graph)..

**Optional / operation-gated capabilities:** the complete scoped provider table in the [source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-market-profiles) is normative. Declare each applicable key separately from required startup dependencies. Absence must affect only the operations requiring it, with the exact recorded denial/unavailable behavior.

**Public contract target:** [`app/contracts/indicators/calculate_market_profiles.py`](../../contracts/indicators/calculate_market_profiles.py). **Literal protocol/DTO/operation symbols:** bind to the compatible selected contract before implementation; no alternate signature is invented here.

**Input boundary:** validated typed operation data, current authenticated scope where applicable, and immutable owner references; numerical operations accept validated bounded buffers. **Output boundary:** the owned FRs and acceptance oracles below. Preserve typed invalid, denied, unavailable, stale/conflict, partial, cancelled and failed outcomes wherever the selected contract defines them; do not create a second generic error vocabulary.

#### Feature Configuration & Limits Manifest

| Binding state | Setting / limit source | Type / default | Required | Validation / ownership |
| --- | --- | --- | --- | --- |
| BINDING_PENDING | Exact accepted feature config keys in reconciled config.py / manifest.py / feature README | Owner-declared types and defaults only; none fabricated by this README. | As declared by the owner. | Unknown keys and invalid values fail validation; manifest/config/README key parity is mandatory. |
| NORMATIVE | Operation parameters, immutable profile references and policy limits in the FRs below | Use the selected request/profile schema; no implicit coercion or default substitution. | All prerequisites of the selected operation. | Do not confuse a request parameter, historical profile value or user-visible setting with a new feature config key. |
| NORMATIVE | Resource, security, retention and version requirements in local/shared NFRs | Finite admitted values; stricter applicable owner policy wins. | Before the affected operation. | Pin effective values/revisions in evidence; never alter a historical run by editing current settings. |

**Feature-specific parameter/limit obligations:** `FR-TRC-IND-CALCULATE_MARKET_PROFILES-002`, `NFR-TRC-IND-CALCULATE_MARKET_PROFILES-001`. Their full text and test oracles below are binding; this list is an index, not a reduced schema.

#### Runtime Effects & Scope Disposal

| Effect | Owner | Disposal mechanism |
| --- | --- | --- |
| Capability binding `indicators.calculate-market-profiles@1` | FEAT-IND-CALCULATE_MARKET_PROFILES | Unregister when the reconciler closes the feature scope. |
| Tasks, listeners, requests, workers, leases or buffers actually created by this feature | FEAT-IND-CALCULATE_MARKET_PROFILES | Register exact disposers; cancel/await/release on failure or removal. A pure provider must not create unnecessary effects. |
| Accepted owner work and committed records | Their declared semantic owner | Observation cleanup does not secretly cancel accepted work or purge committed evidence; use explicit owner commands. |

Teardown is idempotent. Failed mount unwinds partial effects. Dependency replacement/removal must not leave stale registrations, jobs, subscriptions, source buffers or credential references usable by the removed scope.

#### Persistent State Ownership

**Ownership class:** No new durable business partition selected here.

**Records:** Validated inputs and bounded computation/runtime state; immutable source references are owned elsewhere.

**Retention and deletion:** Release local buffers/caches on teardown. Retaining an artifact requires the declared custody capability and an explicit owner policy.

**Namespace / schema / driver binding:** Do not infer persistence merely because the template contains a state section. A durable cache, if selected, needs a separate explicit state declaration within this feature. A missing literal binding is an explicit §6 precondition, not permission to choose a schema version or table name during execution.

#### Feature Package Structure & Files

| Target file within owner package | Responsibility | Exports / dependency boundary |
| --- | --- | --- |
| __init__.py | Pure package description | Docstring only. |
| README.md | Runtime-validated mirror of this feature scope | Document exact keys, paths and evidence. |
| manifest.py | Immutable identity, capabilities, config keys and optional state declaration | SPEC : FeatureSpec; metadata only. |
| config.py | Strict typed configuration with unknown-key validation | Compatible FeatureConfig.from_dict() binding; no invented accepted keys. |
| feature.py | Scoped mount adapter and zero-argument factory | create_feature(); mount through FeatureContext/FeatureScope. |
| calculate_market_profiles.py | Focused production domain-logic module | Compatible contract operation binding. |
| _persistence.py | Optional owner of all feature-local database operations when durable state is required | Declared storage operations through public Workspace persistence contracts; no raw connection, policy, authorization or orchestration. |
| _usage.py | Required bounded offline usage scenarios and executable __main__ harness | _run_usage_example(); scenarios map to every applicable FR without owning business logic. |

These are documentary ownership targets, not a claim that files or symbols already exist. Reconcile a compatible existing filename/symbol once in the feature’s path-binding receipt rather than creating duplicate logic. Public contract files remain outside the removable backend owner.

#### Functional Requirements (FR)

| Status | Requirement ID | Responsibility / required behavior | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `FR-TRC-IND-CALCULATE_MARKET_PROFILES-001` | Compute profiles from eligible Data-prepared source slices with pinned volume meaning, bin size, session and tie/expansion policies. | `AT-IND-CALCULATE_MARKET_PROFILES-001` | Empty sessions, equal-volume POC ties, gaps and exact bin boundaries match goldens; bin totals conserve the eligible input volume/TPO counts. |
| PENDING | `FR-TRC-IND-CALCULATE_MARKET_PROFILES-002` | Expose a versioned native-operation descriptor containing typed inputs/outputs, units, state layout, warm-up, supported clocks/methods, numeric policy and provider generation. | `AT-IND-CALCULATE_MARKET_PROFILES-002` | An unsupported clock, generated-data evidence class or dtype fails preflight; no silent Python/object-mode fallback is advertised. |
| PENDING | `FR-TRC-IND-CALCULATE_MARKET_PROFILES-003` | Carry incremental state across input chunks and invalidate caches on any semantic input/provider change. | `AT-IND-CALCULATE_MARKET_PROFILES-003` | Chunk sizes 1, 17 and 65,536 produce the same exact fields and tolerance-bound floats; changing a period or source version invalidates the appropriate output cache. |

**Implementing-symbol and side-effect binding:** bind each requirement to the actual operation in the selected public contract and its focused implementation module before acceptance. For each FR, the acceptance receipt records actual symbol, side effects, typed error/exception branch, usage scenario and test location. Do not replace a specified typed failure with a guessed `ValueError`, or treat its absence from this summary as success.

#### Non-Functional Requirements (Local)

| Status | Requirement ID | Quality / removal constraint | Acceptance ID | Expected result |
| --- | --- | --- | --- | --- |
| PENDING | `NFR-TRC-IND-CALCULATE_MARKET_PROFILES-001` | Execute hot numerical loops with fastmath=False under the approved exact/Float64 policy and finite per-operation memory estimates. | `ATN-IND-CALCULATE_MARKET_PROFILES-001` | Native/reference goldens pass on normal, constant, missing, nonfinite and boundary inputs; measured state memory is bounded by the declared lookback. |
| PENDING | `NFR-TRC-IND-CALCULATE_MARKET_PROFILES-002` | Removal drains users of the pinned kernel generation before releasing native handles, buffers and cached state. | `ATN-IND-CALCULATE_MARKET_PROFILES-002` | A provider replacement cannot change a running stream; new admission sees the new generation only after a compatible plan is rebound. |

#### Applicable Shared NFRs, Catalogue and Source Bindings

[source feature card](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md#feat-ind-calculate-market-profiles): the exact “Applicable shared NFRs,” “Detailed catalogue families,” “Catalogue entries, algorithms and controls delivered,” “Source scope / Original source IDs,” and operation-gated provider sections are incorporated for **this feature only**. These sections remain normative; an acceptance manifest must enumerate the actual linked IDs/entries and evidence, not just cite this paragraph. No source algorithm, control, permission or release condition is weakened by this domain projection.

#### Acceptance Tests and Evidence

| Acceptance family | Intended test owner | Required evidence state |
| --- | --- | --- |
| Every AT ID in this card | `tests/services/indicators/calculate_market_profiles/test_traceability.py` | PENDING: bind an actual named test and assertion to each oracle. |
| Every ATN ID in this card | `tests/services/indicators/calculate_market_profiles/test_lifecycle.py` | PENDING: lifecycle/resource/numerical evidence as applicable. |
| Contract → provider → composition → Interfaces → UI → end-to-end | `docs/dev/SQX/evidence/features/FEAT-IND-CALCULATE_MARKET_PROFILES/acceptance.json` | All six stages NOT_REVALIDATED; justify each genuinely inapplicable stage. |

Intended test paths may be mapped to a compatible current test owner; they are not assertions of existing files. Full oracle coverage, shared requirements, catalogue entries, original source mappings and actual-provider operation qualification must be included in the final acceptance record. A contract fixture cannot certify actual provider integration.

#### Feature Usage Examples

**Required `_usage.py` command - planned, not executed:**

```powershell
uv run --frozen python -m app.services.indicators.calculate_market_profiles._usage
```

`_usage.py` uses bounded deterministic offline inputs and composes production behavior through public contracts or this feature's focused modules. It demonstrates a useful accepted operation, the appropriate invalid/unavailable/refusal case, and exact cleanup without owning business logic. Map each FR above to a named scenario; the expected observations are its acceptance oracles, not invented console output. Do not import sibling implementations, require live credentials/network by default, or put the public example under tests. Before marking it runnable, bind concrete fixture values and record its actual command, output and exit code.

#### Removal Behaviour

Disable and physically remove the actual reconciled owner of `FEAT-IND-CALCULATE_MARKET_PROFILES`. Withdraw `indicators.calculate-market-profiles@1` and all its scoped contributions. Required dependents become BLOCKED/unavailable through their declared contract; operation-gated consumers disable only affected operations. Retain committed source objects and evidence; no cross-provider substitute or implicit purge is permitted. Exercise the local ATN oracles and §7 gates before restoring the feature.

---

## 5. Package-Wide Requirements, Configuration, and Architecture Invariants

| ID | Category | Rule / architectural constraint | Verification |
| --- | --- | --- | --- |
| ARCH-001 | Init purity | All backend __init__.py files contain only docstrings; no imports, registration or I/O. | Architecture check and AST review. |
| ARCH-002 | Managed tasks | Spawn asynchronous service work through FeatureContext.spawn(); own all effects in FeatureScope. | Architecture check; lifecycle, failure and cancellation tests. |
| ARCH-003 | Logging hygiene | No root logging.basicConfig() in service packages; preserve scoped structured redaction. | Static checks and secret/redaction fixtures. |
| ARCH-004 | Contract purity | Public backend contracts live in app/contracts/ and depend on no removable service implementation. | Import Linter and AST checks. |
| ARCH-005 | Interfaces purity | Gateways use contracts and declared capabilities; no service imports, business computations or business persistence. | Import/architecture checks and real-owner parity tests. |
| ARCH-006 | Feature independence | A feature never imports another feature’s implementation, including siblings in the same domain. | Import Linter, physical removal and startup tests. |

| Policy | Binding requirement | Verification |
| --- | --- | --- |
| Focused responsibility | Each file has one focused responsibility; feature identity is not split by algorithm variant, workflow, role or test. | Review and module/ownership checks. |
| Type safety | Follow the template’s Python 3.14 strict-typing target and reconcile the actual repository/lockfile runtime in Phase 0; no type-ignore bypasses. UI follows the existing strict TypeScript build. | mypy / TypeScript checks against the ratified environment. |
| Coverage | At least 80% line and branch coverage, retaining any stronger applicable repository or owner floor. | Actual coverage reports at the approved quality boundary. |
| Configuration parity | Exact accepted keys agree between strict config, manifest and feature-local README; request/profile controls do not become implicit feature settings. | Positive/negative parsing and parity fixtures. |
| Numerical / resource truth | Use the domain-specific §9 rules, exact source algorithms, finite admission and explicit measurement fixtures. Targets are not measurements. | Golden, causal, overflow, bounded-memory and native/reference evidence where applicable. |
| Scope and authority | Identity, environment, account, dataset, approval and receiver boundaries are rechecked by their actual owners. | Wrong-scope, stale, refusal, idempotency and removal tests. |
| Shared NFR applicability | Apply only the exact shared-NFR bindings of each source feature card; all applicable requirements remain mandatory. | Expanded per-feature acceptance mapping, not a blanket global pass. |

## 6. Open Decisions

The following are explicit documentary/implementation-entry gaps, not deferred permission to invent a design. Resolve the affected binding before production use. This documentation delivery does not close Preparation 0.03 or certify Phase 1 entry.

| State | Decision / evidence label | Required resolution | Constraints | Impact |
| --- | --- | --- | --- | --- |
| OPEN | SOURCE-RECONCILIATION | Reconcile clause-level differences among the register’s source specification, the plan’s inspected specification and the current fetched specification. | Retain the supplied 205-feature identity set unless explicitly changed; differing hashes are not a semantic diff. | All source-dependent behavior. |
| OPEN | EVD-CONTRACT-01 | Bind exact current protocol/DTO symbols, callable signatures, error branches, accepted config keys/defaults and literal state namespace/schema/driver. | Reuse compatible existing public contracts; no duplicate owner or invented field. Source-selected capability keys and target modules are retained here. | Each affected feature before its production consumer. |
| OPEN | CURRENT-OWNER-BINDING | Reconcile selected target paths, compatible existing aliases, unrelated domain scope and actual implementation progress. | No automatic rename, overwrite of unrelated README entries or assumption that a missing target folder means missing behavior. | All target owners; especially legacy semantic folders and permanent UI IDs. |
| OPEN | FIXTURE-AND-USAGE-BINDING | Pin concrete deterministic request/response fixtures, intended test symbols and runnable `_usage.py` or UI examples. | Use every existing acceptance oracle; a planned command or path is not a passing example. | Every feature acceptance bundle. |
| OPEN | NUMERICAL-AND-EXTERNAL-EVIDENCE | Ratify exact algorithm/version, golden fixture, supported format/provider/target and runtime/toolchain evidence for the affected operation. | Do not invent production generated-tick paths, donor binary formats, licenses, toolchain results or numerical pass measurements. | Only the affected numerical/external operation; retain release gates. |
| OPEN | OPERATION-QUALIFICATION | Expand applicable shared-NFR/catalogue/source/operation tables into the actual per-feature evidence manifest and qualify real providers. | Complete registered adapter behavior once; an absent later provider gates only affected operations. Contract stubs are not real-provider evidence. | Applicable later-operation and release claims. |
| CLOSED — documentary scope | IDENTITY-AND-BOUNDARY | Use the register feature/FR/local-NFR identities and exact primary-capability / required-provider bindings. | No additional feature for roles, algorithms, workflows, tests, performance or later UI integration. | The selected features in §2. |

## 7. Tests and Definition of Done

### Test Suite Structure

Focused feature tests live at the intended owners named in §4. Add config, manifest, lifecycle, failure, boundary, numerical and replay coverage where applicable. Cross-feature contract, composition, Interfaces, browser, accessibility, physical-removal and leak evidence remains independent of feature unit tests. Do not mislabel an offline fixture as production integration.

### Commands

The following are target verification recipes. Bind actual paths and runner scripts before use; none is reported as executed by this documentation delivery.

```powershell
uv run --frozen pytest --no-cov tests/services/indicators/calculate_trend
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy
uv run --frozen lint-imports
uv run --frozen python scripts/architecture_check.py
uv run --frozen python scripts/validate_feature_docs.py
uv run --frozen python scripts/verify_feature_removal.py --feature FEAT-IND-CALCULATE_TREND --report removal-report.json
```

The first test/removal command illustrates this domain’s first feature; use the affected feature’s exact owner path and ID for other cards. The full `scripts/ci_check.py` and coverage gate run at the approved pre-commit/CI/release boundary, not as a substitute for focused iterative checks.

### Acceptance evidence model

For each feature, retain `docs/dev/SQX/evidence/features/<FEAT-ID>/acceptance.json` with source/README hashes, actual tested tree/commit, paths and symbols, FR/local/shared-NFR/catalogue/source/acceptance mappings, fixture hashes, environment, exact commands and exit codes, reports, usage transcript or browser trace, operation-qualification state, lifecycle/removal results and independent review. No credentials or private raw data enter this evidence. The final accepted commit is recorded after creation to avoid a self-referential hash.

| Stage | Current README evidence state | What closes it |
| --- | --- | --- |
| Contract | NOT_REVALIDATED | Exact compatible schema, operation, config and error bindings plus contract tests. |
| Provider | NOT_REVALIDATED | Actual implementation satisfies every owned FR/local NFR and applicable numerical/resource rule. |
| Composition | NOT_REVALIDATED | Real registration, dependency closure, mount rollback and physical removal. |
| Interfaces | NOT_REVALIDATED | Typed authenticated owner routing and parity; justify genuine nonapplicability. |
| UI | NOT_REVALIDATED | Reachable truthful interaction, accessibility, cleanup and owner outcome. |
| End-to-end | NOT_REVALIDATED | Real-provider workflow with canonical receipts and complete acceptance oracles. |

### Feature Definition of Done Checklist

- [ ] 1. Stable feature ID: retain the registered identity, including permanent numeric UI IDs.
- [ ] 2. Single domain ownership: each feature has exactly one semantic owner and one implementation task.
- [ ] 3. Cohesive capability: implement the complete registered behavior, not merely an adapter-shaped stub.
- [ ] 4. External contracts: reuse compatible public contracts outside removable implementation packages; UI contribution contracts consume the generated wire boundary.
- [ ] 5. Declared dependencies: manifest provides/requires/optional keys agree with the resolved public contracts and operation gates.
- [ ] 6. Zero private feature imports: use public contracts and context-resolved capabilities only.
- [ ] 7. Zero import-time I/O or registration: initialization remains pure.
- [ ] 8. Scoped runtime effects: bindings, tasks, listeners, requests, workers and buffers have exact owners and disposers.
- [ ] 9. Mount rollback: injected mount failure releases every partial contribution.
- [ ] 10. Idempotent teardown: repeated scope closure is safe and leaves no orphan runtime effect.
- [ ] 11. Required-dependency loss: absent/removed required providers block only dependent behavior and yield the declared failure state.
- [ ] 12. Optional-dependency loss: affected operations fail explicitly; no substitute provider, fabricated data or silently reduced semantics.
- [ ] 13. Persistent state: literal namespace/schema/driver/retention/purge and migrations are bound where state is owned; otherwise explicitly none.
- [ ] 14. Irreversible-action safety: exact scope, idempotency, receiver reconciliation and retained audit are tested.
- [ ] 15. Starts feature-absent: deleting the feature physically does not break unrelated startup and capabilities.
- [ ] 16. Interfaces/UI degradation: typed unavailable/denied/partial states remain usable and truthful.
- [ ] 17. README parity: feature-local documentation, this domain entry, manifests, configuration and contracts agree.
- [ ] 18. Module usage: focused capability modules document public Python/API or interactive UI use and failure cases.
- [ ] 19. Usage evidence: every backend feature has one required `_usage.py` with the bounded offline `__main__` scenarios; UI has real interaction evidence instead.
- [ ] 20. Quality and acceptance: mapped FR/local/shared NFR, catalogue, source, workflow, removal and actual-provider evidence passes all applicable gates; no target is reported as a measurement.

The ordinary ≥80% coverage floor is not proof of semantic completeness. Repeated enable/disable, failed mount, dependency loss/replacement and physical removal must demonstrate exact cleanup; use 100-cycle tests where specified. Stronger owner-specific limits and evaluation thresholds take precedence. Missing mandatory evidence prevents acceptance; a future optional provider must remain explicitly OPERATION_NOT_QUALIFIED.

## 8. Change Process

Update this domain card first, then reconcile the contract and source scope. A breaking public change bumps the capability major rather than shadowing an existing contract. Keep manifest declarations, strict configuration, feature-local README and state migrations aligned. Implement only the selected feature’s cohesive behavior, update its required `_usage.py` scenarios or UI workflow, and add the exact acceptance and failure assertions. Verify dependency/removal behavior and actual provider integration, then run the approved quality gates and independent review.

Maintain one feature task and its accepted implementation commit in the existing Planner → Executor → Reviewer workflow. A verified existing feature keeps its slot and evidence; do not force a rewrite or empty commit. The phase’s last feature owns its cross-feature checkpoint, not a new feature. Later providers add real integration evidence to the already complete consumer adapter; they do not authorize unnoticed extra implementation scope. Record progress in the tracker and receipts, never by declaring all targets Implemented in this README. Preserve unrelated current domain entries when merging this selected scope.

## 9. Normative Domain Specification

The following domain-specific rules explain the source requirements and ownership boundaries. Stable labels here are navigation labels, **not newly counted FR/NFR or feature IDs**. The feature FR/local-NFR tables and exact linked source semantics remain binding; these explanations never replace an algorithm definition, contract schema, catalogue entry or release qualification gate.

<a id="ind-native"></a>
### 9.1 IND-NATIVE

Each numerical provider declares typed input/output buffers, parameters, warm-up, state layout and native operation identity. Python validates and orchestrates; admitted native kernels perform the numerical work. Do not enable fastmath when it violates the required numerical contract.

<a id="ind-parity"></a>
### 9.2 IND-PARITY

Whole-array and chunked processing, including chunks of 1, 17 and 65,536 observations, must reproduce the same declared state transitions and output validity. Compare against pinned small golden fixtures before throughput qualification. Tolerance is an explicit numerical policy, not a substitute for incompatible formulas.

<a id="ind-seeds"></a>
### 9.3 IND-SEEDS

Retain the registered initialization rules, including EMA seeding from the first N-value arithmetic mean followed by alpha = 2/(N+1), and Wilder-style recurrences where specified. Constant-series and zero-denominator cases must return the exact declared values or typed undefined reasons.

<a id="ind-edge-cases"></a>
### 9.4 IND-EDGE-CASES

Wilder RSI treats a flat eligible series as 50, positive gain with no loss as 100, and loss with no gain as 0 under its registered definition. ATR uses its declared true-range seed and recurrence. CCI is not clamped into an invented bounded oscillator range.

<a id="ind-fitting"></a>
### 9.5 IND-FITTING

A fitted transform can use only its declared training window. Preserve fit-window and parameter identity in the output artifact; test holdout and future observations cannot affect fitted statistics. Rolling windows honor causal availability and warm-up.

<a id="ind-profiles"></a>
### 9.6 IND-PROFILES

Volume Profile and TPO consume explicitly eligible source volume, bins and pinned sessions from Data/Catalogue. Conserve the applicable volume or time-at-price measure. Do not substitute tick count for exchange volume, and do not let the chart engine compute the authoritative profile.

### Normative source and acceptance binding

Each §4 source-card link incorporates only that feature’s shared NFR applicability, operation-gated dependencies, detailed catalogue entries, original source-ID relationships and source clauses. Open the linked entry, not a similarly named legacy feature. The register-wide inventories contain 66 shared NFRs, 646 catalogue entries, 389 original requirement-ID mappings and 233 operation-time dependency edges. Those inventories are **retained by scoped reference**, not reproduced or independently expanded in this delivery. The actual acceptance manifest must enumerate their applicable members before scope can be signed off.

### Source fingerprint record

| Source | Git blob identity | Role |
| --- | --- | --- |
| [`docs/dev/SQX/HaruQuantAI_Unified_Specification.md`](../../../docs/dev/SQX/HaruQuantAI_Unified_Specification.md) | `f805dff20c0f7bb00ed897f112a73e853ccf91a3` | Product and domain semantics; current fetched identity; differences from the register baseline remain unresolved. |
| [`docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md`](../../../docs/dev/HaruQuantAI_Feature_Requirement_Traceability_Register.md) | `32d7ff8ea18784c66b479beae822f17744462044` | Selected feature identities, owned FRs/local NFRs, capability and dependency targets, catalogues, source mappings, and workflow scope. |
| [`docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md`](../../../docs/dev/HaruQuantAI_Phased_Feature_Implementation_Plan.md) | `ffe9b7d3a3a29b32f7a6559122f32d73258709f8` | One task per feature; execution phases, evidence states, readiness and acceptance procedure. |
| [`docs/templates/README.md`](../../../docs/templates/README.md) | `8d6fb9075784113e95857555c17f7182996f7cc3` | README structure and code-aligned conventions. |

The register records specification blob `7b592a2c25276ceae7cf7011f0a4f98eabe9c7fd` at commit `c06456fe2c03bc89f52edad1a0a8428118287377`. The phased plan records inspected specification blob `d69bef59cb981350cd6f2ebdccc31b231a4e0950` at commit `a3c81dff4e5b903e749259ff463b8d9280d6fc26`. The fetched specification identity above differs from both. This delivery records the mismatch but does not claim a clause-level reconciliation or authorize a silent change to the 205-feature scope.

### Delivery evidence boundary

This is a documentation projection and proposed domain-registry update. Generated-document checks may establish identity/count/graph/anchor consistency; they do not establish current code parity, external-provider licensing/support, native throughput, model eligibility, browser behavior, successful live connectivity or Phase 0 completion. No application suite or live operation was executed as part of authoring this README.

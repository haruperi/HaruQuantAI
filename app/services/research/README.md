# Research

> **Package:** `app/services/research`
> **Status:** `Completed` — all thirteen registered features, including
> `FEAT-RES-13` fundamental and sentiment source evidence, are implemented and
> verified.
> **Last updated:** `2026-07-30`

> This README is the package's **single source of truth** for requirements, final structure, implementation sequence, progress, usage examples, and tests.
> Update this file before changing the code.

---

## 1. Purpose and Boundary

### Purpose

Research provides a sandboxed, leakage-gated environment for exploring research-ready market data and evaluating hypotheses. It produces reproducible, versioned, advisory-only evidence—including prepared datasets, edge studies, market-structure profiles, unsupervised insights, scorecards, snapshots, and `ResearchReport v1` artifacts—without authorizing or mutating live trading, strategy, or risk state.

Research consumes trusted `MarketDataset v1` inputs from Data, pure indicator
evidence through the Indicators package root, and public `PerformanceReport v1`
evidence from Analytics. Data/provider acquisition, cross-domain scheduling,
database infrastructure, and strategy registration remain outside this package.

### Owns

- Research configurations and immutable result contracts.
- Deterministic research-only cleaning, validation, enrichment, and quality evidence.
- Research-specific returns, Hurst, forward outcomes, excursions, feature-frame assembly, and all deterministic historical labeling; Research owns this capability.
- Chronological splitting, leakage evidence, and recursive artifact masking.
- Core research metric profiles and their bounded calculator registry.
- Seeded bootstrap, permutation, null-model, threshold, and multiple-testing computations.
- Mean-reversion, trend-persistence, and session edge studies with one confirmation policy.
- Timezone-aware session tagging and seasonality opportunity analysis.
- Market-structure profiles, opt-in stability/robustness, forward validation, consolidated calibration, and advisory strategy fit.
- Deterministic PCA/K-Means evidence and unsupervised insight generation.
- Deterministic scorecards, profile snapshots, report rendering, and comparisons.
- Research artifact schemas, migration definitions, and safe masked artifact persistence.
- Bounded fundamental and deterministic sentiment evidence projected from eligible,
  point-in-time Data source records, with explicit applicability and missingness.
- `ResearchReport v1` and the explicit classified Research public API.

### Does not own

- Market-data or external-feed acquisition, provider connections, caching, or provider retries; Data owns production provider contracts.
- Generic indicator formulas or Analytics ratios; Research imports SMA, EMA, ATR,
  Bollinger Bands, RSI, and ADR only from the Indicators package root and consumes
  Analytics only through `PerformanceReport v1`. Research does not re-export or
  deep-import either owning domain.
- Backtest or optimization orchestration.
- Strategy registration, promotion, runtime state, or production signal execution.
- Risk policy, position sizing, exposure limits, approval, or kill-switch state.
- Broker reads or mutations, order execution, reconciliation, or live controls.
- API routes, authentication, scheduling, cross-domain workflow coordination, or database connection/migration execution infrastructure.
- Guarantees of profitability, compliance, or production-grade performance before resource targets are approved and verified.

### Glossary

| Term | Meaning |
|---|---|
| **Edge Lab** | The progressive, externally orchestrated sequence of approved Research stages that produces an advisory profile and `ResearchReport`. |
| **Null baseline** | A seeded reference distribution matched to the observed study's side, sample, horizon, and declared null method. |
| **Profile snapshot** | A versioned, normalized record of approved stage outputs, provenance, warnings, readiness reasons, and advisory status. |
| **Advisory evidence** | Research output that may inform review but never authorizes strategy registration, risk approval, or execution. |
| **Leakage report** | Structured evidence about suspected lookahead fields, declared forward columns, severity, and required action. |
| **Research artifact** | A masked, versioned JSON or Markdown representation persisted by Research under an approved storage policy. |

### Shared contracts

Contract definitions match `docs/PROJECT.md`. Commands and requests are owned by their receiver; results are owned by their producer.

**Owned by this domain**—defined authoritatively here:

| Status | Contract | Version | Counterparty | Purpose |
|---|---|---|---|---|
| Completed | `ResearchReport` | `v1` | `UI/API` | Return advisory research evidence and hypothesis results; leakage-gate failure blocks publication. |

### StandardResponse v1 boundary

The package-root `run_edge_lab_profile` operation returns the Utils-owned
`StandardResponse[ResearchReport]` envelope. The complete report is placed
directly in `data`; failures use the immutable Research-owned error catalogue
and return `data=None`. The response metadata identifies
`research.run_edge_lab_profile` as low-risk, read-only, non-networked, and free
of file, database, and trade side effects. Feature-module stage functions remain
raw internal composition APIs and are wrapped only once at this root boundary.

`ResearchReport` is the only registered cross-domain Research result in the initial
build. Prepared datasets, stage profiles/results, scorecards, snapshots, warnings, and
artifact references are Research-internal assembly types or are nested inside the
report; another domain must not consume them directly until separately registered.

#### `ResearchReport v1` schema

`ResearchReport` is an immutable, JSON-serializable result. Unknown fields are rejected at construction; breaking field or semantic changes require a new contract version.

| Field | Type | Required | Contract |
|---|---|---|---|
| `contract_version` | `Literal["v1"]` | Yes | Compatibility version; always `v1`. |
| `schema_id` | `Literal["research.report.v1"]` | Yes | Stable namespaced schema identity; never parsed for compatibility. |
| `report_id` | `str` | Yes | Non-empty Research-owned identifier. |
| `hypothesis` | `str` | Yes | The tested question or declared research objective. |
| `evidence` | `Mapping[str, JSONValue]` | Yes | Versioned stage evidence; observations and assumptions remain distinguishable. |
| `seeds` | `Mapping[str, int]` | Yes | Effective seed for every stochastic stage; empty only when no stochastic stage ran. |
| `configuration_hash` | `str` | Yes | Lowercase SHA-256 of canonical effective configuration. |
| `dataset_hash` | `str` | Yes | Lowercase SHA-256 of the canonical input identity/snapshot. |
| `source_references` | `tuple[str, ...]` | Yes | Data/report identifiers used as evidence; never provider SDK objects. |
| `warnings` | `tuple[ResearchWarning, ...]` | Yes | Structured caveats, insufficiency, masking, and partial-stage evidence. |
| `generated_at` | `datetime` | Yes | Timezone-aware UTC timestamp serialized with `Z`. |
| `dependency_versions` | `Mapping[str, str]` | Yes | Versions required to reproduce the result. |
| `duration_ms` | `float` | Yes | Non-negative monotonic execution duration. |
| `advisory_only` | `Literal[True]` | Yes | Always true; any other value is invalid. |

**Consumed from other domains—referenced only, never redefined:**

| Contract | Version | Owner | Used for |
|---|---|---|---|
| `MarketDataset` | `v1` | `Data` | Canonical research-ready OHLCV/OHLCVS records, availability metadata, provenance, and dataset identity. |
| `PerformanceReport` | `v1` | `Analytics` | Read-only metric evidence used by scorecards/reports without reimplementing Analytics ratios. |
| `AuthContext` | `v1` | `Utils` | Principal and trace context for governed artifact publication. |
| `AuditEvent` | `v1` | `Utils` | Redacted audit envelope emitted for governed artifact writes; Data persists it. |

### Persisted state

Data owns the shared database connection, locking, and migration execution framework. Research alone owns and writes its artifact schemas and migration definitions; other domains read through `ResearchReport v1`.

| Status | State / Store | Read access (via contract) | Migration definitions |
|---|---|---|---|
| Completed | Research artifact metadata and versioned JSON/Markdown artifacts | `UI/API` via `ResearchReport v1` | `{DATA_DIR}/artifacts/research/` plus `research_artifacts` metadata table; migrations at `app/services/research/artifacts/migrations.py`. |

### Four-level structure

| Code level | Represents |
|---|---|
| **Package** | Research domain |
| **Module folder** | Feature / capability |
| **File** | Use case or focused responsibility |
| **Class / function / method** | Functional requirement behaviour |

```text
Package
└── Module folder
    └── File
        └── Class / Function / Method
```

### Package capability map

```mermaid
flowchart TD
    RES[[Research Package]]
    RES --> CON[[contracts]]
    RES --> DAT[[data]]
    RES --> FEA[[features]]
    RES --> LEA[[leakage]]
    RES --> MET[[metrics]]
    RES --> STA[[statistics]]
    RES --> STU[[studies]]
    RES --> SEA[[seasonality]]
    RES --> MKS[[market_structure]]
    RES --> MOD[[modeling]]
    RES --> PRO[[profiles]]
    RES --> ART[[artifacts]]

    CON --> CON1[configurations.py]
    CON --> CON2[results.py]
    CON --> CON3[api.py]
    DAT --> DAT1[validation.py]
    DAT --> DAT2[preparation.py]
    FEA --> FEA1[calculations.py]
    FEA --> FEA2[frame.py]
    LEA --> LEA1[validation.py]
    LEA --> LEA2[splitting.py]
    LEA --> LEA3[masking.py]
    MET --> MET1[registry.py]
    MET --> MET2[profile.py]
    STA --> STA1[resampling.py]
    STA --> STA2[null_models.py]
    STA --> STA3[corrections.py]
    STU --> STU1[null_baseline.py]
    STU --> STU2[edge_studies.py]
    STU --> STU3[classification.py]
    SEA --> SEA1[sessions.py]
    SEA --> SEA2[analysis.py]
    MKS --> MKS1[profile.py]
    MKS --> MKS2[quality.py]
    MKS --> MKS3[validation.py]
    MKS --> MKS4[calibration.py]
    MKS --> MKS5[fit.py]
    MOD --> MOD1[decomposition.py]
    MOD --> MOD2[clustering.py]
    MOD --> MOD3[insights.py]
    MOD --> MOD4[workflow.py]
    PRO --> PRO1[scorecard.py]
    PRO --> PRO2[snapshot.py]
    PRO --> PRO3[rendering.py]
    PRO --> PRO4[workflow.py]
    ART --> ART1[migrations.py]
    ART --> ART2[persistence.py]
```

---

## 2. Final Package Structure

Folders and files are ordered from lowest dependency to highest dependency; this is the implementation sequence.

### Feature Registry

All thirteen registered features are `Completed` with focused unit and integration
tests, one standalone usage program per feature, repository-wide type checking,
and at least 80% domain coverage. `run_edge_lab_profile` composes all ten
configured in-memory stages in canonical dependency order while provider reads,
scheduling, database orchestration, artifact writes, and Strategy submission
remain external.

| Status | Feature | Owning module | Public API and contracts | Requirements | Usage evidence |
|---|---|---|---|---|---|
| Completed | `FEAT-RES-01` Versioned Contracts and Configuration | `contracts/` | Implemented package-root contracts include `ResearchReport v1` and `EdgeLabConfig`; exact declarations: Section 4.1 | Section 4.1 functional requirements | `tests/research/usage/features/01_contracts.py` |
| Completed | `FEAT-RES-02` Deterministic Dataset Preparation | `data/` | Implemented declarations: Section 4.2 | Section 4.2 functional requirements | `tests/research/usage/features/02_data.py` |
| Completed | `FEAT-RES-03` Research-Specific Features | `features/` | Implemented declarations: Section 4.3 | Section 4.3 functional requirements | `tests/research/usage/features/03_features.py` |
| Completed | `FEAT-RES-04` Leakage Evidence, Splits, and Masking | `leakage/` | Implemented declarations: Section 4.4 | Section 4.4 functional requirements | `tests/research/usage/features/04_leakage.py` |
| Completed | `FEAT-RES-05` Core Metric Profile | `metrics/` | Implemented declarations: Section 4.5 | Section 4.5 functional requirements | `tests/research/usage/features/05_metrics.py` |
| Completed | `FEAT-RES-06` Seeded Statistical Validation | `statistics/` | Implemented declarations: Section 4.6 | Section 4.6 functional requirements | `tests/research/usage/features/06_statistics.py` |
| Completed | `FEAT-RES-07` Edge Discovery and Confirmation | `studies/` | Implemented declarations: Section 4.7 | Section 4.7 functional requirements | `tests/research/usage/features/07_studies.py` |
| Completed | `FEAT-RES-08` Sessions and Seasonality | `seasonality/` | Implemented declarations: Section 4.8 | Section 4.8 functional requirements | `tests/research/usage/features/08_seasonality.py` |
| Completed | `FEAT-RES-09` Market Structure Analysis | `market_structure/` | Implemented declarations: Section 4.9 | Section 4.9 functional requirements | `tests/research/usage/features/09_market_structure.py` |
| Completed | `FEAT-RES-10` Deterministic Unsupervised Insights | `modeling/` | Implemented declarations: Section 4.10 | Section 4.10 functional requirements | `tests/research/usage/features/10_modeling.py` |
| Completed | `FEAT-RES-11` Scorecards, Snapshots, and Edge Lab Profiles | `profiles/` | Implemented declarations: Section 4.11 | `FR-RES-089`–`096` | `tests/research/usage/features/11_profiles.py` |
| Completed | `FEAT-RES-12` Safe Research Artifact Persistence | `artifacts/` | Implemented declarations: Section 4.12 | Section 4.12 functional requirements | `tests/research/usage/features/12_artifacts.py` |
| Completed | `FEAT-RES-13` Fundamental and Sentiment Source Evidence | `intelligence/` | `assess_intelligence_applicability`, `build_fundamental_source_evidence`, `build_sentiment_source_evidence`, `project_intelligence_evidence`; internal evidence values remain opaque | `FR-RES-099`–`104` | `tests/research/usage/features/13_intelligence.py` |

```text
research/
├── __init__.py                         # Explicit function-only domain API
├── README.md
├── contracts/                          # Versioned configurations and result contracts
│   ├── __init__.py
│   ├── configurations.py
│   ├── results.py
│   └── api.py
├── data/                               # Deterministic preparation and quality evidence
│   ├── __init__.py
│   ├── validation.py
│   └── preparation.py
├── features/                           # Research-specific calculations and feature frames
│   ├── __init__.py
│   ├── calculations.py
│   └── frame.py
├── leakage/                            # Leakage evidence, splits, and masking
│   ├── __init__.py
│   ├── validation.py
│   ├── splitting.py
│   └── masking.py
├── metrics/                            # Core metric registry and profile
│   ├── __init__.py
│   ├── registry.py
│   └── profile.py
├── statistics/                         # Seeded resampling and statistical controls
│   ├── __init__.py
│   ├── resampling.py
│   ├── null_models.py
│   └── corrections.py
├── studies/                            # Edge studies and confirmation
│   ├── __init__.py
│   ├── null_baseline.py
│   ├── edge_studies.py
│   └── classification.py
├── seasonality/                        # Unified sessions and seasonality analysis
│   ├── __init__.py
│   ├── sessions.py
│   └── analysis.py
├── market_structure/                   # Profiles, quality, validation, calibration, fit
│   ├── __init__.py
│   ├── profile.py
│   ├── quality.py
│   ├── validation.py
│   ├── calibration.py
│   └── fit.py
├── modeling/                           # Stateless PCA/K-Means insight workflow
│   ├── __init__.py
│   ├── decomposition.py
│   ├── clustering.py
│   ├── insights.py
│   └── workflow.py
├── profiles/                           # Scorecard, snapshot, rendering, Edge Lab stages
│   ├── __init__.py
│   ├── scorecard.py
│   ├── snapshot.py
│   ├── rendering.py
│   └── workflow.py
├── artifacts/                          # Safe masked artifact persistence
│   ├── __init__.py
│   └── persistence.py
└── intelligence/                       # FEAT-RES-13 fundamental/sentiment evidence
    ├── __init__.py
    ├── contracts.py
    └── evidence.py
```

Usage examples are outside production:

```text
tests/research/usage/
├── 01_contracts.py
├── 02_data.py
├── 03_features.py
├── 04_leakage.py
├── 05_metrics.py
├── 06_statistics.py
├── 07_studies.py
├── 08_seasonality.py
├── 09_market_structure.py
├── 10_modeling.py
├── 11_profiles.py
├── 12_artifacts.py
└── 13_intelligence.py
```

### Module dependency diagram

Arrows point from required module to consuming module.

```mermaid
flowchart LR
    CON[[contracts]]
    DAT[[data]]
    FEA[[features]]
    LEA[[leakage]]
    MET[[metrics]]
    STA[[statistics]]
    STU[[studies]]
    SEA[[seasonality]]
    MKS[[market_structure]]
    MOD[[modeling]]
    PRO[[profiles]]
    ART[[artifacts]]
    INTEL[[intelligence]]

    CON --> DAT
    CON --> FEA
    CON --> LEA
    CON --> MET
    CON --> STA
    CON --> STU
    CON --> SEA
    CON --> MKS
    CON --> MOD
    CON --> PRO
    CON --> ART
    CON --> INTEL
    DAT --> INTEL
    DAT --> FEA
    DAT --> LEA
    DAT --> MET
    FEA --> LEA
    FEA --> STU
    FEA --> SEA
    FEA --> MKS
    FEA --> MOD
    LEA --> STU
    LEA --> MKS
    LEA --> MOD
    MET --> MKS
    MET --> PRO
    STA --> STU
    STU --> MKS
    SEA --> MKS
    MKS --> PRO
    MOD --> PRO
    STU --> PRO
    SEA --> PRO
    PRO --> ART
    LEA --> ART
```

### Structure rules

- The package root contains no business implementation.
- Each module folder owns one approved capability.
- Files contain one focused responsibility and expose only symbols listed in Section 4.
- Common Indicators and Analytics calculations are imported through documented owning-domain APIs; no compatibility re-exports exist.
- Incremental feature computation, provider adapters, cluster signal adaptation, console printing, generic helpers/services/managers, and database orchestration are absent.
- Module `__init__.py` files expose only their approved feature APIs; package `__init__.py` exposes only stable domain APIs and `get_public_api_classifications()`.
- No module imports `profiles` or `artifacts` from a lower layer; circular imports are prohibited.

---

## 3. Workflows

> **Workflow Usage Evidence**: Each active workflow has one standalone program in
> `tests/research/usage/workflows/`; `run_all.py` executes them in registry order.

### Workflow rank values

| Rank | Identifier | Meaning |
|---|---|---|
| **Primary** | `WF-RES-PRI` | The workflow this domain exists to serve. |
| **Secondary** | `WF-RES-SEC` | The next most load-bearing workflow. |
| **Tertiary** | `WF-RES-TER` | The third-ranked workflow. |
| **Supporting** | `WF-RES-0NN` | Every remaining registered workflow. |

### Retired identifiers

`WF-RES-011`, `WF-RES-001`, and `WF-RES-005` were absorbed into `WF-RES-PRI`,
`WF-RES-SEC`, and `WF-RES-TER` respectively. Absorbed numbers are retired and are
never reused. New workflows continue from `WF-RES-012`.

### Step annotation convention

Research exposes standalone functions only from `app.services.research`; `__all__`
is the complete public boundary. Public consumers never import Research classes,
constants, or feature submodules. Internal immutable values are created, inspected,
projected, or operated on through package-root factory and accessor functions.
Cross-domain steps name the owning domain's public export.

Evidence programs:

- `WF-RES-PRI`: `tests/research/usage/workflows/wf_res_pri_run_complete_edge_lab_profile.py`
- `WF-RES-SEC`: `tests/research/usage/workflows/wf_res_sec_prepare_research_dataset.py`
- `WF-RES-TER`: `tests/research/usage/workflows/wf_res_ter_run_edge_study_null_evidence.py`
- `WF-RES-002`: `tests/research/usage/workflows/wf_res_002_build_core_metric_profile.py`
- `WF-RES-003`: `tests/research/usage/workflows/wf_res_003_build_leakage_safe_feature_frame_time_splits.py`
- `WF-RES-004`: `tests/research/usage/workflows/wf_res_004_analyze_session_seasonality_opportunity.py`
- `WF-RES-006`: `tests/research/usage/workflows/wf_res_006_build_market_structure_profile.py`
- `WF-RES-007`: `tests/research/usage/workflows/wf_res_007_forward_validate_calibrate_market_structure.py`
- `WF-RES-008`: `tests/research/usage/workflows/wf_res_008_run_unsupervised_market_structure_research.py`
- `WF-RES-009`: `tests/research/usage/workflows/wf_res_009_build_research_scorecard_profile_snapshot.py`
- `WF-RES-010`: `tests/research/usage/workflows/wf_res_010_render_persist_research_artifact.py`
- `WF-RES-012`: `tests/research/usage/workflows/wf_res_012_compare_research_profiles_across_periods.py`

### Status values

| Status | Meaning |
|---|---|
| **Missing** | Not implemented, conflicting with the final contract, or not verified. |
| **Partial** | Valuable V1 behavior exists, but relocation, contracts, validation, errors, or tests remain. |
| **Completed** | Final behavior, structure, runtime use, and tests are verified. |

### Workflow scope values

| Scope | Meaning |
|---|---|
| **Internal** | The complete workflow occurs within Research. |
| **Cross-domain** | Research receives input from or produces output for another domain. |

| Status | Rank | Workflow ID | Scope | Workflow | Trigger / Input boundary | Final outcome / Output boundary | Requirement sequence |
|---|---|---|---|---|---|---|---|
| Completed | Primary | `WF-RES-PRI` | Cross-domain | Run Complete Edge Lab Profile | Explicit hypothesis, `EdgeLabConfig`, and `MarketDataset v1` from external orchestrator | Advisory `ResearchReport v1` to UI/API; selected stages execute in canonical dependency order | `FR-RES-096` plus selected stage requirements |
| Completed | Secondary | `WF-RES-SEC` | Cross-domain | Prepare Research Dataset | `MarketDataset v1` from Data | Research-internal `PreparedDataset`; never returned across the boundary | `FR-RES-027 → 030` |
| Completed | Tertiary | `WF-RES-TER` | Internal | Run Edge Study Against Null Evidence | Split data + study/statistical config | Advisory `EdgeResult` | `FR-RES-050 → 068` |
| Completed | Supporting | `WF-RES-002` | Internal | Build Core Metric Profile | `PreparedDataset` | `CoreMetricProfile` | `FR-RES-042 → 049` |
| Completed | Supporting | `WF-RES-003` | Internal | Build Leakage-Safe Feature Frame and Time Splits | Prepared data + feature config | Feature frame + `LeakageReport` + `TimeSplitResult` | `FR-RES-031 → 041` |
| Completed | Supporting | `WF-RES-004` | Internal | Analyze Session and Seasonality Opportunity | Prepared OHLCVS + approved session policy | Advisory seasonality summaries | `FR-RES-069 → 074` |
| Completed | Supporting | `WF-RES-006` | Internal | Build Market-Structure Profile | Prepared data + market-structure config | `MarketStructureProfile` + advisory fit | `FR-RES-075 → 076, 080` |
| Completed | Supporting | `WF-RES-007` | Internal | Forward Validate and Calibrate Market Structure | Persisted prediction + later approved dataset already supplied to the run | Research-internal validation/calibration evidence nested only in `ResearchReport v1` | `FR-RES-077 → 079` |
| Completed | Supporting | `WF-RES-008` | Internal | Run Unsupervised Market-Structure Research | Leakage-safe feature frame + seed | `UnsupervisedResearchResult` | `FR-RES-081 → 088` |
| Completed | Supporting | `WF-RES-009` | Internal | Build Research Scorecard and Profile Snapshot | Approved stage outputs | `ResearchScorecard` + `ResearchProfileSnapshot` | `FR-RES-089 → 092` |
| Completed | Supporting | `WF-RES-010` | Internal | Render and Persist Research Artifact | Masked result + approved Research-owned output location | Research-internal `ArtifactReference` or typed failure; UI/API receives only `ResearchReport v1` | `FR-RES-093 → 095, 097` |
| Completed | Supporting | `WF-RES-012` | Internal | Compare Research Profiles Across Periods | Two or more opaque Research profile snapshots over comparable schema and configuration | Period-over-period score deltas, readiness stability, and explicit caveats; advisory only | `FR-RES-089`–`092` comparison projection |

### `WF-RES-SEC` — Prepare Research Dataset

**Scope:** `Cross-domain`
**System workflow:** `SYS-WF-004`

**Input boundary:** Data supplies `MarketDataset v1` and provenance; Research performs no provider read.
**Output boundary:** Research retains `PreparedDataset` as internal stage evidence;
only the final `ResearchReport v1` may expose its bounded lineage/result projection.

1. Data supplies the dataset and provenance; Research performs no provider read —
   `data.get_market_data()`.
2. Produce fatal and warning quality evidence —
   `research.validate_dataset()` *(internal)*.
3. Apply only explicit approved actions to a copy —
   `research.clean_dataset()` *(internal)*.
4. Add research-owned price, return-label, and calendar fields —
   `research.enrich_dataset()` *(internal)*.
5. Return the versioned dataset, hashes, and report —
   `research.prepare_research_dataset()` *(internal)*, `utils.canonical_digest()`.

**Failure behaviour:**

- Fatal schema/OHLC/time issue → typed validation failure; no prepared dataset.
- Unapproved or absent data-changing default → configuration failure; no implicit fill/drop.
- Row/duration limit exceeded → typed resource-limit failure.

**Integration test:** `tests/research/integration/test_prepare_dataset.py::test_prepare_dataset_from_market_dataset()`

### `WF-RES-002` — Build Core Metric Profile

**Scope:** `Internal`
**System workflow:** None.

`PreparedDataset → immutable MetricRegistry → seven metric families → CoreMetricProfile`

1. Resolve the immutable metric registry —
   `research.get_metric_registry()` *(internal)*.
2. Calculate the seven metric families over the prepared dataset —
   `research.build_core_metric_profile()` *(internal)*.
3. Keep undefined metrics explicit with warnings and units rather than coercing them
   silently — `research.build_core_metric_profile()` *(internal)*.

**Integration test:** `tests/research/integration/test_core_metric_profile.py::test_build_core_metric_profile_with_provenance()`

### `WF-RES-003` — Build Leakage-Safe Feature Frame and Time Splits

**Scope:** `Internal`
**System workflow:** None.

1. Build the research feature frame from prepared data and feature config —
   `research.build_research_feature_frame()` *(internal)*.
2. Validate that no feature reads forward information —
   `research.validate_no_lookahead_features()` *(internal)*.
3. Enforce the declared time split —
   `research.enforce_time_split()` *(internal)*.

High/critical leakage evidence blocks downstream claims. Forward columns remain explicitly declared and excluded from feature inputs.

**Integration test:** `tests/research/integration/test_feature_leakage.py::test_feature_frame_is_split_without_lookahead()`

### `WF-RES-004` — Analyze Session and Seasonality Opportunity

**Scope:** `Internal`
**System workflow:** None.

1. Tag each bar with its canonical session —
   `research.tag_sessions()` *(internal)*, `data.get_active_market_sessions()`.
2. Run the seasonality analysis over the tagged buckets —
   `research.run_seasonality()` *(internal)*.
3. Return advisory opportunity summaries with structured warnings —
   `research.run_seasonality()` *(internal)*.

Sparse buckets, overlaps, DST transitions, and unmatched hours produce structured warnings. UTC is authoritative, with Sydney 21:00–06:00, Tokyo 00:00–09:00, London 07:00–16:00, New York 12:00–21:00, and overlap precedence `london > new_york > tokyo > sydney`; DST is not modeled in v1.

**Integration test:** `tests/research/integration/test_seasonality.py::test_seasonality_uses_canonical_sessions()`

### `WF-RES-TER` — Run Edge Study Against Null Evidence

**Scope:** `Internal`
**System workflow:** None.

1. Build the matching seeded null baseline for the split data —
   `research.build_null_baseline()` *(internal)*.
2. Run the selected study against the same split —
   `research.run_edge_study()` *(internal)*.
3. Compare the study against its null and classify the result —
   `research.classify_edge_result()` *(internal)*.
4. Preserve statistical caveats rather than asserting significance —
   `analytics.run_statistical_validation()`.

Isolated study failures may be reported and other independent studies continued only when `StudyConfig.continue_on_study_error` is explicitly true. Mixed/BUY/SELL samples use matching null direction; one confirmation policy drives results, profiles, and reports.

**Integration test:** `tests/research/integration/test_edge_study.py::test_edge_study_uses_matching_seeded_null()`

### `WF-RES-006` — Build Market-Structure Profile

**Scope:** `Internal`
**System workflow:** None.

1. Build the market-structure profile from prepared data and config —
   `research.build_market_structure_profile()` *(internal)*.
2. Run the opt-in bounded quality evaluation —
   `research.evaluate_structure_quality()` *(internal)*.
3. Score the profile and derive advisory strategy fit —
   `research.score_market_structure()` *(internal)*.

Quality layers are opt-in and bounded. The canonical profile scorer is also used by calibration.

**Integration test:** `tests/research/integration/test_market_structure_profile.py::test_profile_and_fit_share_canonical_score()`

### `WF-RES-007` — Forward Validate and Calibrate Market Structure

**Scope:** `Internal`
**System workflow:** Internal contribution to `SYS-WF-004`.

**Input boundary:** The Research run receives an approved persisted prediction and a
later research-ready dataset through its existing Data input boundary.
**Output boundary:** Labeling, validation, stability, and calibration evidence remains
Research-internal and may cross only as bounded fields in `ResearchReport v1`.

1. Label the realized forward outcome at the declared horizon —
   `research.label_forward_outcome()` *(internal)*.
2. Validate the persisted prediction against that realized outcome —
   `research.forward_validate_structure()` *(internal)*.
3. Calibrate using the canonical profile scorer —
   `research.score_market_structure()` *(internal)*.
4. Rank evidence by calibration error and then sample size —
   `research.forward_validate_structure()` *(internal)*.

The validation horizon is expressed in bars of the study timeframe; realized forward outcome at that horizon is calibration truth.

**Integration test:** `tests/research/integration/test_market_structure_validation.py::test_forward_validation_returns_ranked_evidence()`

### `WF-RES-008` — Run Unsupervised Market-Structure Research

**Scope:** `Internal`
**System workflow:** None.

1. Preprocess and scale the leakage-safe feature frame under the effective seed —
   `research.preprocess_features()` *(internal)*.
2. Reduce dimensionality and derive factor evidence —
   `research.run_factor_analysis()` *(internal)*.
3. Cluster the reduced space and derive cluster evidence —
   `research.run_clustering()` *(internal)*.
4. Record selected and dropped columns, scaler behavior, seed, model parameters, and
   diagnostics — `research.run_unsupervised_research()` *(internal)*.

Preprocessing, selected/dropped columns, scaler behavior, effective seed, model parameters, and diagnostics are recorded. Signal adaptation is absent.

**Integration test:** `tests/research/integration/test_unsupervised_research.py::test_unsupervised_workflow_is_seeded_and_advisory()`

### `WF-RES-009` — Build Research Scorecard and Profile Snapshot

**Scope:** `Internal`
**System workflow:** None.

1. Build the scorecard from approved stage outputs under one confirmation policy —
   `research.build_research_scorecard()` *(internal)*.
2. Freeze the scorecard and stage lineage into an immutable snapshot —
   `research.build_research_profile_snapshot()` *(internal)*.
3. Bind versions and hashes so the snapshot is reproducible —
   `utils.canonical_json()`, `utils.canonical_digest()`.

The scorecard and snapshot use one confirmation/fit policy and preserve uncertainty, readiness reasons, versions, hashes, warnings, and advisory status.

**Integration test:** `tests/research/integration/test_profile_snapshot.py::test_scorecard_snapshot_is_deterministic()`

### `WF-RES-010` — Render and Persist Research Artifact

**Scope:** `Internal`
**System workflow:** Internal governed persistence contribution to `SYS-WF-004`.

**Input boundary:** A caller supplies a versioned result/snapshot, `AuthContext v1`, and approved destination.
**Output boundary:** `ArtifactReference` remains Research-internal. Research emits the
registered redacted `AuditEvent v1`; UI/API receives only `ResearchReport v1`.

1. Mask the result before any serialization —
   `research.mask_research_result()` *(internal)*, `utils.redact_mapping_value()`.
2. Serialize the masked result canonically —
   `utils.canonical_json()`.
3. Write atomically to the approved Research-owned destination —
   `research.persist_research_artifact()` *(internal)*, `data.save_dataset()`.
4. Emit the registered redacted audit event —
   `utils.create_audit_event()`, `data.persist_audit_event()`.

Masking precedes serialization; traversal, disallowed root, overwrite conflict, permission failure, non-serializable input, and unsupported atomic replacement fail explicitly.

**Integration test:** `tests/research/integration/test_artifact_persistence.py::test_persist_masked_artifact_atomically()`

### `WF-RES-PRI` — Run Complete Edge Lab Profile

**Scope:** `Cross-domain`
**System workflow:** `SYS-WF-004`

**Input boundary:** External UI/API orchestration supplies an explicit hypothesis,
`EdgeLabConfig`, `MarketDataset v1`, and optional `PerformanceReport v1`.
**Output boundary:** Research returns `ResearchReport v1`. UI/API owns human approval and any `StrategyRegistrationRequest` submission.

1. The external orchestrator supplies the dataset and config; Research reads no
   provider — `data.get_market_data()`,
   `analytics.build_performance_report()`.
2. Enter the single public boundary, which runs the selected stages in canonical
   dependency order — `research.run_edge_lab_profile()`.
3. Prepare the dataset (`WF-RES-SEC`) —
   `research.prepare_research_dataset()` *(internal)*.
4. Run the selected evidence stages — metrics, features and splits, seasonality,
   edge studies, market structure, unsupervised research —
   `research.run_edge_study()` *(internal)*,
   `research.build_market_structure_profile()` *(internal)*.
5. Build the scorecard and profile snapshot —
   `research.build_research_scorecard()` *(internal)*.
6. Return the advisory report; UI/API owns human approval —
   `research.run_edge_lab_profile()`.
7. Only after explicit human approval may Strategy register the candidate —
   `strategy.register_strategy_version()`.

Research executes only selected deterministic stages. External code owns triggering, scheduling, provider reads, caching, and database orchestration.

**Integration tests:** `tests/research/unit/test_workflow.py`;
`tests/system/integration/test_research_to_strategy.py`.

### `WF-RES-012` — Compare Research Profiles Across Periods

**Scope:** `Internal`
**System workflow:** Internal contribution to `SYS-WF-004`.

**Input boundary:** two or more `ResearchProfileSnapshot` records covering
comparable symbol, timeframe, and configuration over different periods.
**Output boundary:** period-over-period profile deltas and stability caveats. The
comparison is advisory and confers no readiness or registration authority.

1. Confirm snapshots share a schema and configuration and carry distinct dataset
   hashes in chronological order — `research.compare_research_profiles()`.
2. Compare each adjacent period's scorecard rows and total —
   `research.compare_research_profiles()`.
3. Report readiness stability and changed conclusions without averaging periods —
   `research.render_profile_comparison()`.
4. Preserve explicit multiple-period and advisory-only caveats —
   `research.render_profile_comparison()`.

**Failure behaviour:** snapshots with incompatible symbol, timeframe, or config are
refused rather than compared. A conclusion that holds in one period only is reported
as unstable rather than averaged into an apparent edge.

**Integration test:** `tests/research/integration/test_profile_comparison.py`

#### End-to-end workflow diagram

```mermaid
sequenceDiagram
    participant O as External Orchestrator
    participant D as Research Data
    participant E as Research Evidence Stages
    participant P as Research Profiles
    participant A as Research Artifacts
    participant U as UI/API

    O->>D: MarketDataset v1 + EdgeLabConfig
    D-->>O: PreparedDataset or typed failure
    O->>E: Selected deterministic stage inputs
    E-->>O: Metrics, studies, structure, modeling evidence
    O->>P: Approved stage outputs
    P-->>O: ResearchReport v1
    opt Approved artifact write
        O->>A: Masked report + AuthContext + destination
        A-->>O: ArtifactReference or typed failure
    end
    O->>U: Advisory ResearchReport v1
```

---

## 4. Module and Requirement Specifications

This section is the implementation plan. Statuses reflect V1 audit evidence, not intention. `Partial` means reusable V1 behavior exists but the final structure/contracts/tests are not complete.

### Owner-resolved implementation policy

The following policy is authoritative for every Section 4 requirement. Public
boundaries map dependency failures to Research-owned errors with redacted symbolic
details:

| Error class | Approved Research codes |
|---|---|
| `ConfigurationError` | `RES_CONFIGURATION_INVALID`, `RES_STAGE_DEPENDENCY_INVALID`, `RES_STAGE_UNAVAILABLE` |
| `ValidationError` | `RES_INPUT_INVALID`, `RES_INSUFFICIENT_DATA`, `RES_NONFINITE_DATA`, `RES_RESOURCE_LIMIT_EXCEEDED`, `RES_VERSION_INCOMPATIBLE`, `RES_MODEL_FIT_FAILED` |
| `SecurityError` | `RES_PERMISSION_DENIED`, `RES_LEAKAGE_DETECTED`, `RES_ARTIFACT_PATH_REJECTED`, `RES_SENSITIVE_OUTPUT_REJECTED` |
| `ResearchError` | `RES_ARTIFACT_CONFLICT`, `RES_ARTIFACT_TOO_LARGE`, `RES_ARTIFACT_ATOMICITY_UNAVAILABLE`, `RES_ARTIFACT_WRITE_FAILED`, `RES_AUDIT_PERSISTENCE_FAILED` |

Exact hard bounds are 500,000 rows, 600 seconds per heavy operation, 50 MiB per
serialized artifact, 1–10,000 resampling/null iterations, 1–128 calibration
candidates, at most 32 distinct quality windows, and at most 100 reports in one
multi-symbol rendering. ADR uses 14 bars. Hurst requires at least 20 finite
observations. K-Means uses 2–64 clusters; PCA components may not exceed
`min(feature_count, usable_rows - 1)`; modeling requires at least
`max(20, 10 * clusters, 2 * pca_components)` usable rows. A supplied memory budget
is enforced against measured frame memory before heavy work.

Study mappings are closed schemas and reject unknown keys. Mean reversion uses a
rolling close-price z-score with explicit lookback, entry threshold, side, and hold
horizon. Trend persistence compares an explicit lookback log-return direction with
an explicit forward horizon/minimum move. Session studies group forward returns
under `SessionConfig`. Benjamini–Hochberg covers every successfully evaluated
hypothesis. `confirmed` requires the minimum sample, a directionally correct 95%
confidence interval excluding zero, adjusted p-value at or below `q`, and observed
evidence beyond the matched directional null quantile. A directionally opposite
interval excluding zero is `contradicted`; all other evidence is `inconclusive`.

Market-structure validation horizons are positive integer bars. Confirmed pivots
become available only after their confirmation window. The canonical score is
`100 * (0.60 * Kaufman efficiency ratio + 0.40 * directional persistence)`;
scores at least 65 are `trending`, scores at most 35 are `ranging`, and others are
`mixed`. Calibration receives an explicit candidate grid and ranks ascending Brier
error, descending validation sample, then canonical configuration hash.

The scorecard measures evidence quality, never trading merit. Input quality,
leakage safety, statistical confirmation, out-of-sample validation, and
reproducibility each contribute 0, 10, or 20 points. Readiness is `BLOCKED` for a
fatal data issue, high-severity leakage, or incompatible version; `REVIEW_READY`
requires at least 80 points and nonzero evidence in every row; otherwise it is
`INSUFFICIENT_EVIDENCE`. Trading-readiness language is prohibited.

### 4.1 `contracts/` — Versioned Contracts and Configuration

**Purpose:** Define immutable configuration, result, warning, resource, and API-classification contracts shared by Research modules.

**Module flow:** `validated configuration + stage evidence → immutable versioned contracts`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `configurations.py` | Define immutable, validated Research configuration contracts without hidden data-changing defaults. | `ResearchResourceLimits`, `CleaningConfig`, `EnrichmentConfig`, `FeatureConfig`, `StatisticalConfig`, `StudyConfig`, `SessionConfig`, `MarketStructureConfig`, `UnsupervisedResearchConfig`, `ArtifactWriteConfig`, `EdgeLabConfig` | **Standard library:** dataclasses, datetime, pathlib, typing<br>**Required third-party:** None<br>**Local:** approved shared Utils errors in the owner-resolved policy above |
| Completed | `results.py` | Define versioned immutable Research results and the owned `ResearchReport v1` contract. | `PreparedDataset`, `DataQualityReport`, `LeakageReport`, `TimeSplitResult`, `CoreMetricProfile`, `EdgeResult`, `MarketStructureProfile`, `MarketStructureQualityReport`, `UnsupervisedResearchResult`, `ResearchScorecard`, `ResearchProfileSnapshot`, `ResearchWarning`, `ResearchReport`, `ArtifactReference` | **Standard library:** dataclasses, datetime, pathlib, typing<br>**Required third-party:** pandas<br>**Local:** configurations.py → configuration types; app.services.data public API → `MarketDataset` reference |
| Completed | `api.py` | Define the explicit unique classification map used by the package lazy facade. | `PUBLIC_API_CLASSIFICATIONS` | **Standard library:** types, typing<br>**Required third-party:** None<br>**Local:** None |
| Completed | `__init__.py` | Expose the approved public contract API. | All key exports above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** configurations.py, results.py, api.py → listed exports |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `max_rows` | `int` | Explicit per run | Yes | All frame-consuming public functions | Hard row ceiling; excess raises `RES_RESOURCE_LIMIT_EXCEEDED` before heavy work. |
| Completed | `max_duration_seconds` | `float` | Explicit per run | Yes | Heavy studies, quality, modeling, Edge Lab workflow | Bounded duration policy carried by `ResearchResourceLimits`. |
| Completed | `max_artifact_bytes` | `int` | Explicit per run | Yes | `write_research_artifact` | Maximum serialized artifact size; excess is rejected, never silently truncated. |
| Excluded | `memory_budget_mb` | `int \| None` | None | No | Heavy workflows | Portable hard memory enforcement is not claimed in V1; row/iteration/duration/artifact bounds are authoritative. |
| Completed | internal result `schema_version` | `Literal["v1"]` | `"v1"` | Yes | Research-internal stage/result types only | Structural version for internal/nested evidence; the registered `ResearchReport` uses separate `contract_version` and `schema_id`. |

#### `configurations.py` — Immutable Configuration Contracts

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-001` | The system shall define bounded row, duration, artifact-size, and advisory memory budgets without claiming unverified production performance. | `ResearchResourceLimits(max_rows: int, max_duration_seconds: float, max_artifact_bytes: int, memory_budget_mb: int \| None = None)` | None | invalid/non-positive limit; invalid or non-positive approved limits | **Usage:** `01_contracts.py::fr_res_001`<br>**Unit:** `test_contract_configurations.py::test_resource_limits_reject_non_positive` |
| Completed | `FR-RES-002` | The system shall require explicit timestamp, duplicate, missing-bar, non-trading-period, and spread-cleaning policies and shall never silently fill or drop data. | `CleaningConfig(timezone: str, duplicate_strategy: str, missing_bar_strategy: str, non_trading_period_strategy: str, spread_strategy: str)` | None | unsupported or absent policy | **Usage:** `01_contracts.py::fr_res_002`<br>**Unit:** `test_contract_configurations.py::test_cleaning_requires_explicit_data_actions` |
| Completed | `FR-RES-003` | The system shall define explicit pip, geometry, return-label, and calendar enrichment selections; canonical session tagging remains owned by `seasonality/`. | `EnrichmentConfig(symbol: str, include_geometry: bool, include_returns: bool, include_forward_labels: bool, include_calendar: bool)` | None | malformed symbol or incompatible selection | **Usage:** `01_contracts.py::fr_res_003`<br>**Unit:** `test_contract_configurations.py::test_enrichment_rejects_incompatible_fields` |
| Completed | `FR-RES-004` | The system shall define feature windows, declared forward columns, warm-up/NaN policy, and non-mutation behavior. | `FeatureConfig(windows: Mapping[str, int], forward_horizons: tuple[int,...], allowed_forward_columns: tuple[str,...], nan_policy: str)` | None | invalid window/horizon/policy | **Usage:** `01_contracts.py::fr_res_004`<br>**Unit:** `test_contract_configurations.py::test_feature_config_rejects_invalid_window` |
| Completed | `FR-RES-005` | The system shall define bootstrap, permutation, null, correction, effective-seed, and bounded-iteration settings in one statistical contract. | `StatisticalConfig(seed: int, bootstrap_samples: int, permutation_samples: int, block_size: int, null_samples: int, correction: str \| None)` | None | invalid seed, count, block, correction, or resource request | **Usage:** `01_contracts.py::fr_res_005`<br>**Unit:** `test_contract_configurations.py::test_statistics_rejects_invalid_block_size` |
| Completed | `FR-RES-006` | The system shall define mean-reversion, trend-persistence, session-study, confirmation, and explicit isolated-failure policy. | `StudyConfig(mean_reversion: Mapping[str, JSONValue], trend_persistence: Mapping[str, JSONValue], session: Mapping[str, JSONValue], continue_on_study_error: bool = False)` | None | unsupported study/confirmation setting | **Usage:** `01_contracts.py::fr_res_006`<br>**Unit:** `test_contract_configurations.py::test_study_config_fails_closed_by_default` |
| Completed | `FR-RES-007` | The system shall define one timezone-aware set of named windows and deterministic overlap precedence for all session consumers. | `SessionConfig(timezone: str, windows: Mapping[str, tuple[time, time]], overlap_precedence: tuple[str,...])` | None | session policy unresolved or invalid | **Usage:** `01_contracts.py::fr_res_007`<br>**Unit:** `test_contract_configurations.py::test_session_config_requires_overlap_precedence` |
| Completed | `FR-RES-008` | The system shall define bounded structure detection, canonical scoring, quality, validation, and calibration settings. | `MarketStructureConfig(profile: Mapping[str, JSONValue], enable_quality: bool, quality_windows: tuple[int,...], calibration_candidates: int, validation_horizon: int)` | None | invalid validation or calibration policy | **Usage:** `01_contracts.py::fr_res_008`<br>**Unit:** `test_contract_configurations.py::test_market_structure_bounds_candidates` |
| Completed | `FR-RES-009` | The system shall define selected features, preprocessing, PCA components, cluster count, minimum sample, and effective seed. | `UnsupervisedResearchConfig(feature_columns: tuple[str,...], scale: bool, pca_components: int, clusters: int, minimum_samples: int, seed: int)` | None | invalid dimension/sample/seed | **Usage:** `01_contracts.py::fr_res_009`<br>**Unit:** `test_contract_configurations.py::test_unsupervised_config_rejects_excess_clusters` |
| Completed | `FR-RES-010` | The system shall define an allowed root, format, encoding, overwrite, masking, and atomic-write policy for artifacts. | `ArtifactWriteConfig(allowed_root: Path, format: Literal["json", "markdown"], overwrite: bool = False, encoding: str = "utf-8", require_atomic: bool = True)` | None | root or ownership invalid | **Usage:** `01_contracts.py::fr_res_010`<br>**Unit:** `test_contract_configurations.py::test_artifact_config_rejects_relative_root` |
| Completed | `FR-RES-011` | The system shall aggregate explicit stage configs, selected stages, and resource limits without supplying hidden trading/data policies. | `EdgeLabConfig(cleaning: CleaningConfig, enrichment: EnrichmentConfig, features: FeatureConfig, statistics: StatisticalConfig, studies: StudyConfig, sessions: SessionConfig, market_structure: MarketStructureConfig, modeling: UnsupervisedResearchConfig, artifacts: ArtifactWriteConfig, limits: ResearchResourceLimits, selected_stages: tuple[str,...])` | None | absent/incompatible configuration | **Usage:** `01_contracts.py::fr_res_011`<br>**Unit:** `test_contract_configurations.py::test_edge_lab_config_requires_stage_dependencies` |

#### `results.py` — Versioned Result Contracts

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-012` | The system shall carry prepared records, canonical schema metadata, quality evidence, dataset/config hashes, and provenance without provider objects. | `PreparedDataset(data: DataFrame, schema_version: str, quality: DataQualityReport, dataset_hash: str, configuration_hash: str, source_references: tuple[str,...])` | None | invalid schema/hash/frame | **Usage:** `01_contracts.py::fr_res_012`<br>**Unit:** `test_contract_results.py::test_prepared_dataset_rejects_provider_object` |
| Completed | `FR-RES-013` | The system shall distinguish fatal issues, warnings, checks, and explicit cleaning actions with machine-readable codes. | `DataQualityReport(fatal_issues: tuple[Mapping[str, JSONValue],...], warnings: tuple[ResearchWarning,...], checks: tuple[str,...], cleaning_actions: tuple[Mapping[str, JSONValue],...])` | None | invalid severity/code/details | **Usage:** `01_contracts.py::fr_res_013`<br>**Unit:** `test_contract_results.py::test_quality_report_distinguishes_fatal_warning` |
| Completed | `FR-RES-014` | The system shall identify suspected lookahead columns, severity, evidence, recommendation, allowed forward columns, target, and source metadata. | `LeakageReport(suspected_columns: tuple[str,...], severity: str, evidence: Mapping[str, JSONValue], recommendation: str, allowed_forward_columns: tuple[str,...], target_column: str \| None, source_references: tuple[str,...])` | None | invalid severity/evidence | **Usage:** `01_contracts.py::fr_res_014`<br>**Unit:** `test_contract_results.py::test_leakage_report_requires_evidence` |
| Completed | `FR-RES-015` | The system shall represent deterministic chronological train/validation/test partitions and boundary identities. | `TimeSplitResult(train: DataFrame, validation: DataFrame, test: DataFrame, boundaries: Mapping[str, datetime], split_hash: str)` | None | overlapping/invalid partitions | **Usage:** `01_contracts.py::fr_res_015`<br>**Unit:** `test_contract_results.py::test_time_split_rejects_overlap` |
| Completed | `FR-RES-016` | The system shall represent seven-family metric values with units, sample size, undefined-value reason, warnings, and reproducibility metadata. | `CoreMetricProfile(schema_version: str, metrics: Mapping[str, JSONValue], quality: DataQualityReport, dataset_hash: str, configuration_hash: str, warnings: tuple[ResearchWarning,...])` | None | invalid metric/metadata schema | **Usage:** `01_contracts.py::fr_res_016`<br>**Unit:** `test_contract_results.py::test_metric_profile_requires_units` |
| Completed | `FR-RES-017` | The system shall represent one advisory edge study with sample, rule/config, split identity, null evidence, uncertainty, confirmation, seed, warnings, and provenance. | `EdgeResult(schema_version: str, study: str, statistics: Mapping[str, JSONValue], null_evidence: Mapping[str, JSONValue], classification: str, seed: int, warnings: tuple[ResearchWarning,...], advisory_only: Literal[True])` | None | invalid or contradictory result | **Usage:** `01_contracts.py::fr_res_017`<br>**Unit:** `test_contract_results.py::test_edge_result_is_advisory` |
| Completed | `FR-RES-018` | The system shall represent reproducible swings, legs, distributions, regimes, canonical score, verdict, and advisory fit evidence. | `MarketStructureProfile(schema_version: str, structure: Mapping[str, JSONValue], score: float, verdict: str, strategy_fit: Mapping[str, JSONValue], warnings: tuple[ResearchWarning,...])` | None | invalid score/profile | **Usage:** `01_contracts.py::fr_res_018`<br>**Unit:** `test_contract_results.py::test_market_structure_uses_canonical_score` |
| Completed | `FR-RES-019` | The system shall represent opt-in stability, robustness, validation, calibration candidates, ranking criteria, windows, duration, and warnings. | `MarketStructureQualityReport(schema_version: str, stability: Mapping[str, JSONValue], robustness: Mapping[str, JSONValue], calibration: Mapping[str, JSONValue], duration_ms: float, warnings: tuple[ResearchWarning,...])` | None | invalid validation truth | **Usage:** `01_contracts.py::fr_res_019`<br>**Unit:** `test_contract_results.py::test_quality_report_records_windows` |
| Completed | `FR-RES-020` | The system shall represent preprocessing, features, dropped columns, scaler, PCA, clusters, factor/cluster evidence, seed, parameters, diagnostics, and advisory status. | `UnsupervisedResearchResult(schema_version: str, preprocessing: Mapping[str, JSONValue], pca: Mapping[str, JSONValue], clusters: Mapping[str, JSONValue], insights: Mapping[str, JSONValue], seed: int, warnings: tuple[ResearchWarning,...], advisory_only: Literal[True])` | None | invalid model metadata | **Usage:** `01_contracts.py::fr_res_020`<br>**Unit:** `test_contract_results.py::test_unsupervised_result_records_seed` |
| Completed | `FR-RES-021` | The system shall represent deterministic score rows, uncertainty, final score, readiness reasons, versions, and advisory status. | `ResearchScorecard(schema_version: str, score_rows: tuple[Mapping[str, JSONValue],...], final_score: float, readiness: str, reasons: tuple[str,...], warnings: tuple[ResearchWarning,...], advisory_only: Literal[True])` | None | invalid score/readiness schema | **Usage:** `01_contracts.py::fr_res_021`<br>**Unit:** `test_contract_results.py::test_scorecard_readiness_has_reasons` |
| Completed | `FR-RES-022` | The system shall normalize approved stage outputs into one versioned snapshot with hashes, versions, warnings, and advisory status. | `ResearchProfileSnapshot(schema_version: str, stages: Mapping[str, JSONValue], scorecard: ResearchScorecard, dataset_hash: str, configuration_hash: str, generated_at: datetime, warnings: tuple[ResearchWarning,...], advisory_only: Literal[True])` | None | missing required stage/version/hash | **Usage:** `01_contracts.py::fr_res_022`<br>**Unit:** `test_contract_results.py::test_snapshot_rejects_unversioned_stage` |
| Completed | `FR-RES-023` | The system shall expose bounded structured warnings with code, message, severity, optional field path, and bounded details. | `ResearchWarning(code: str, message: str, severity: str, field_path: str \| None = None, details: Mapping[str, JSONValue] \| None = None)` | None | invalid warning vocabulary | **Usage:** `01_contracts.py::fr_res_023`<br>**Unit:** `test_contract_results.py::test_warning_details_are_bounded` |
| Completed | `FR-RES-024` | The system shall produce the fully defined `ResearchReport v1` contract in Section 1 with `advisory_only=True` and complete reproducibility metadata. | `ResearchReport(...)` | None | contract validation; pending leakage gate: unsafe evidence blocks construction/publication | **Usage:** `01_contracts.py::fr_res_024`<br>**Unit:** `test_contract_results.py::test_research_report_v1_contract` |
| Completed | `FR-RES-025` | The system shall return a safe artifact reference containing relative location, format, byte size, content hash, atomicity, schema version, and audit identity. | `ArtifactReference(relative_path: Path, format: str, size_bytes: int, sha256: str, atomic: bool, schema_version: str, audit_event_id: str)` | None | invalid/out-of-root reference | **Usage:** `01_contracts.py::fr_res_025`<br>**Unit:** `test_contract_results.py::test_artifact_reference_is_relative` |

#### `api.py` — Classified Public API

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-026` | The system shall expose a unique immutable mapping for every `__all__` name with `stable` classification and lazy import target, without recursive scanning or callable wrapping. | `PUBLIC_API_CLASSIFICATIONS: Mapping[str, Literal["stable"]]` | None | None | **Usage:** `01_contracts.py::fr_res_026()`<br>**Unit:** `test_contract_api.py::test_public_api_is_unique_resolvable_and_side_effect_free()` |

**Rules:**

- Contracts are immutable, reject unknown fields, and serialize deterministically.
- Research exceptions extend the Utils-owned shared base hierarchy, use Research-specific codes, and map failures at the Research public boundary.
- Internal-support models may be imported only by their module path and are excluded from package `__all__`.
- No class is added merely to wrap stateless functions.

**Implementation notes:**

- Refactor useful V1 dataclass fields, but do not preserve accidental public surface or mixed errors.
- Use Utils-owned UTC, canonical JSON, hashing, redaction, and shared base-error contracts; Research defines and maps its own focused errors.

### Feature usage examples

`tests/research/usage/01_contracts.py` contains one `fr_res_*` function named in each row above.

---

### 4.2 `data/` — Deterministic Dataset Preparation

**Purpose:** Convert `MarketDataset v1` into a validated, explicitly cleaned and enriched `PreparedDataset` with machine-readable quality evidence.

**Module flow:** `MarketDataset → validate_dataset() → clean_dataset() → enrich_dataset() → prepare_research_dataset()`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `validation.py` | Validate canonical schema, timestamps, continuity, OHLC, spread, and volume. | `validate_dataset` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts.results → `DataQualityReport`; Data public API → `MarketDataset` |
| Completed | `preparation.py` | Apply explicit cleaning/enrichment and assemble the prepared contract. | `clean_dataset`, `enrich_dataset`, `prepare_research_dataset` | **Standard library:** time, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts.configurations → configs/limits; contracts.results → prepared/quality contracts; validation.py → `validate_dataset` |
| Completed | `__init__.py` | Expose the supported data-preparation API. | Four functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** validation.py, preparation.py → listed exports |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `missing_bar_strategy` | `str` | Explicit | Yes | `clean_dataset` | Controls missing bars; no fill/drop occurs without an explicit approved value and recorded action. |
| Completed | `non_trading_period_strategy` | `str` | Explicit | Yes | `clean_dataset` | Controls weekends, holidays, synthetic bars, and provider gaps; unresolved cases block cleaning. |
| Completed | `timezone` | `str` | `UTC` | Yes | All data functions | Canonical timezone basis; invalid/naive/mixed timestamps fail or warn exactly as the approved policy defines. |
| Completed | `max_rows` | `int` | Explicit per run | Yes | All data functions | Enforced before copying/processing; excess raises resource-limit failure. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-027` | The system shall validate required columns, UTC/time ordering, duplicates, gaps, OHLC consistency, spread quality, volume, finite values, and source metadata without mutating input. | `validate_dataset(dataset: MarketDataset, *, limits: ResearchResourceLimits) -> DataQualityReport` | Read-only | invalid input/schema/resource limit | **Usage:** `02_data.py::fr_res_027`<br>**Unit:** `test_data_validation.py::test_validate_dataset_reports_fatal_ohlc_issue` |
| Completed | `FR-RES-028` | The system shall clean a copy using only explicit approved strategies and record every action and unresolved warning. | `clean_dataset(dataset: MarketDataset, *, config: CleaningConfig, report: DataQualityReport, limits: ResearchResourceLimits) -> tuple[DataFrame, DataQualityReport]` | Local state mutation | unsupported/absent policy or invalid data | **Usage:** `02_data.py::fr_res_028`<br>**Unit:** `test_data_preparation.py::test_clean_dataset_never_fills_implicitly` |
| Completed | `FR-RES-029` | The system shall enrich a copy with selected pip/geometry/return-label/calendar fields, label forward fields as research-only, and preserve row alignment; session tagging is a later `seasonality/` operation. | `enrich_dataset(data: DataFrame, *, config: EnrichmentConfig, report: DataQualityReport) -> tuple[DataFrame, DataQualityReport]` | Local state mutation | missing structural inputs or incompatible enrichment | **Usage:** `02_data.py::fr_res_029`<br>**Unit:** `test_data_preparation.py::test_enrich_dataset_labels_forward_columns` |
| Completed | `FR-RES-030` | The system shall execute validate → clean → revalidate → enrich deterministically and return hashes, provenance, and quality evidence, never fetching provider data. | `prepare_research_dataset(dataset: MarketDataset, *, cleaning: CleaningConfig, enrichment: EnrichmentConfig, limits: ResearchResourceLimits) -> PreparedDataset` | Read-only | fatal validation/config/resource failure | **Usage:** `02_data.py::fr_res_030`<br>**Unit:** `test_data_preparation.py::test_prepare_dataset_is_deterministic_and_provider_free` |

**Rules:**

- Fatal issues block output; warnings remain machine-readable.
- Raw provider objects, hidden fallback sources, and implicit fill/drop are prohibited.
- V1 preparation logic is reusable only after provider fetching and propagated SDK errors are removed.

### Feature usage examples

`tests/research/usage/02_data.py` contains the four mapped examples.

---

### 4.3 `features/` — Research-Specific Features

**Purpose:** Compute research-owned returns, Hurst, forward outcomes, excursions, and one timestamp-aligned feature frame while consuming—not duplicating—shared Indicator/Analytics formulas.

**Module flow:** `PreparedDataset + FeatureConfig → calculations → build_research_feature_frame()`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `calculations.py` | Provide pure research-specific scalar/series calculations. | `log_returns`, `simple_returns`, `hurst_exponent`, `rolling_hurst`, `forward_returns`, `forward_max_favorable_excursion`, `forward_max_adverse_excursion` | **Standard library:** math, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts.configurations → `FeatureConfig` |
| Completed | `frame.py` | Assemble one canonical feature frame and metadata using shared formulas. | `build_research_feature_frame` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts → configs/results; calculations.py → research functions; Indicators/Analytics public APIs → documented Indicators and Analytics public contracts |
| Completed | `__init__.py` | Expose only the approved feature API. | Eight functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** calculations.py, frame.py → listed exports |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `forward_horizons` | `tuple[int, ...]` | Explicit | Yes when forward outcomes requested | Forward functions/frame builder | Positive bounded horizons; unavailable trailing rows are explicit NaN research labels, never feature inputs. |
| Completed | `nan_policy` | `str` | Explicit | Yes | `build_research_feature_frame()` | Defines warm-up and missing behavior; hidden filling is forbidden. |
| Completed | `shared_formula_contracts` | documented imports | direct documented contracts only | Yes | `build_research_feature_frame` | Public Indicator result contracts are injected; Research does not deep-import domain internals. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-031` | Compute one-period log returns without mutating input and preserve index alignment. | `log_returns(close: Series) -> Series` | Read-only | non-finite/non-positive/insufficient input | **Usage:** `03_features.py::fr_res_031`<br>**Unit:** `test_feature_calculations.py::test_log_returns_preserves_alignment` |
| Completed | `FR-RES-032` | Compute arithmetic returns without mutating input and preserve index alignment. | `simple_returns(close: Series) -> Series` | Read-only | invalid/insufficient input | **Usage:** `03_features.py::fr_res_032`<br>**Unit:** `test_feature_calculations.py::test_simple_returns_constant_series` |
| Completed | `FR-RES-033` | Estimate Hurst exponent with explicit minimum sample and finite-value validation. | `hurst_exponent(values: Series, *, minimum_samples: int) -> float` | Read-only | insufficient/non-finite/constant sample | **Usage:** `03_features.py::fr_res_033`<br>**Unit:** `test_feature_calculations.py::test_hurst_rejects_insufficient_sample` |
| Completed | `FR-RES-034` | Compute rolling Hurst values with documented warm-up NaNs and stable alignment. | `rolling_hurst(values: Series, *, window: int, minimum_samples: int) -> Series` | Read-only | invalid window/sample | **Usage:** `03_features.py::fr_res_034`<br>**Unit:** `test_feature_calculations.py::test_rolling_hurst_has_declared_warmup` |
| Completed | `FR-RES-035` | Compute one canonical horizon-aligned forward return in log or simple mode and mark it research-only. | `forward_returns(close: Series, *, horizon: int, mode: Literal["log", "simple"], output_label: str) -> Series` | Read-only | invalid horizon/mode/label | **Usage:** `03_features.py::fr_res_035`<br>**Unit:** `test_feature_calculations.py::test_forward_returns_never_used_as_feature` |
| Completed | `FR-RES-036` | Compute forward maximum favorable excursion for declared side/horizon with trailing unavailability explicit. | `forward_max_favorable_excursion(data: DataFrame, *, horizon: int, side: Literal["buy", "sell"]) -> Series` | Read-only | invalid side/horizon/OHLC | **Usage:** `03_features.py::fr_res_036`<br>**Unit:** `test_feature_calculations.py::test_forward_mfe_buy_sell_direction` |
| Completed | `FR-RES-037` | Compute forward maximum adverse excursion for declared side/horizon with trailing unavailability explicit. | `forward_max_adverse_excursion(data: DataFrame, *, horizon: int, side: Literal["buy", "sell"]) -> Series` | Read-only | invalid side/horizon/OHLC | **Usage:** `03_features.py::fr_res_037`<br>**Unit:** `test_feature_calculations.py::test_forward_mae_buy_sell_direction` |
| Completed | `FR-RES-038` | Build a new feature frame with declared lineage, warm-up/NaN behavior, caller-supplied public `IndicatorResult v1` inputs, research-only forward columns, and no input mutation. | `build_research_feature_frame(prepared: PreparedDataset, *, indicator_results: Mapping[str, IndicatorResult], config: FeatureConfig, limits: ResearchResourceLimits) -> tuple[DataFrame, Mapping[str, JSONValue]]` | Read-only | invalid feature/shared dependency/resource | **Usage:** `03_features.py::fr_res_038`<br>**Unit:** `test_feature_frame.py::test_feature_frame_records_lineage_and_forward_columns` |

**Implementation notes:**

- Reuse V1 return/Hurst/forward logic after validating parity.
- Shared SMA, EMA, ATR, Bollinger, RSI, and equivalent generic formulas are
  caller-supplied `IndicatorResult v1` values created through the Indicators package
  root. This preserves the original `MarketDataset` checksum and prevents Research
  from reconstructing or duplicating indicator formulas.
- Incremental feature computation is excluded.

### Feature usage examples

`tests/research/usage/03_features.py` contains the eight mapped examples.

---

### 4.4 `leakage/` — Leakage Evidence, Splits, and Masking

**Purpose:** Detect declared/structural lookahead risk, enforce deterministic chronological partitions, and recursively mask sensitive/research-only fields.

**Module flow:** `feature frame → leakage report → chronological split; artifact → masked artifact`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `validation.py` | Produce structured leakage evidence without false certification. | `validate_no_lookahead_features` | **Standard library:** typing<br>**Required third-party:** pandas<br>**Local:** contracts → `FeatureConfig`, `LeakageReport` |
| Completed | `splitting.py` | Produce deterministic chronological train/validation/test partitions. | `enforce_time_split` | **Standard library:** datetime, typing<br>**Required third-party:** pandas<br>**Local:** contracts.results → `TimeSplitResult` |
| Completed | `masking.py` | Recursively redact sensitive and forbidden research fields in memory. | `mask_research_artifact` | **Standard library:** collections.abc, typing<br>**Required third-party:** None<br>**Local:** app.utils.security → redaction primitives |
| Completed | `__init__.py` | Expose the supported leakage API. | Three functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** validation.py, splitting.py, masking.py |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `train_fraction / validation_fraction` | `float` | Explicit | Yes | `enforce_time_split()` | Positive fractions with non-empty remainder; invalid/insufficient splits fail. |
| Completed | `allowed_forward_columns` | `tuple[str, ...]` | `()` | Yes | `validate_no_lookahead_features()` | Explicit exceptions remain reported and cannot enter training features. |
| Completed | `mask_keys` | `frozenset[str]` | Utils security policy | Yes | `mask_research_artifact()` | Recursive denylist is tested against nested sensitive and forward fields. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-039` | Inspect feature metadata, names, targets, horizons, and declarations and return evidence/severity/recommendation without claiming proof of no leakage. | `validate_no_lookahead_features(data: DataFrame, *, feature_metadata: Mapping[str, JSONValue], target_column: str \| None, allowed_forward_columns: tuple[str,...] = ()) -> LeakageReport` | Read-only | `ValidationError(RES_INPUT_INVALID)` | **Usage:** `04_leakage.py::fr_res_039`<br>**Unit:** `test_leakage_validation.py::test_leakage_report_detects_forward_target` |
| Completed | `FR-RES-040` | Split chronologically into non-overlapping train/validation/test frames with deterministic boundaries and split hash. | `enforce_time_split(data: DataFrame, *, train_fraction: float, validation_fraction: float, gap_rows: int = 0) -> TimeSplitResult` | Read-only | invalid fractions/gap/insufficient rows | **Usage:** `04_leakage.py::fr_res_040`<br>**Unit:** `test_leakage_splitting.py::test_time_split_is_chronological_and_gapped` |
| Completed | `FR-RES-041` | Recursively mask sensitive, broker/account, and forbidden forward fields before sharing or serialization without mutating input. | `mask_research_artifact(artifact: JSONValue, *, extra_sensitive_keys: frozenset[str] = frozenset()) -> JSONValue` | Read-only | `SecurityError(RES_SENSITIVE_OUTPUT_REJECTED)` | **Usage:** `04_leakage.py::fr_res_041`<br>**Unit:** `test_leakage_masking.py::test_masking_covers_nested_sensitive_fields` |

### Feature usage examples

`tests/research/usage/04_leakage.py` contains the three mapped examples.

---

### 4.5 `metrics/` — Core Metric Profile

**Purpose:** Build a schema-aware seven-family metric profile through a bounded registry with explicit units, undefined values, warnings, and provenance.

**Module flow:** `PreparedDataset → MetricRegistry → calculators → build_core_metric_profile()`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `registry.py` | Define the calculator protocol and immutable calculator membership. | `MetricCalculator`, `MetricRegistry`, `build_default_registry` | **Standard library:** collections.abc, typing<br>**Required third-party:** None<br>**Local:** contracts.results → internal metric context/value contracts |
| Completed | `profile.py` | Execute calculators and assemble the versioned profile. | `build_core_metric_profile` | **Standard library:** math, time, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts → prepared/profile/limits; registry.py → registry/protocol; Analytics public API → documented Indicators and Analytics public contracts |
| Completed | `__init__.py` | Expose the supported metric API. | Four exports above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** registry.py, profile.py |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `metric_families` | `tuple[str, ...]` | `returns, roc, candles, ranges, volatility, spread, activity` | Yes | `build_default_registry()` | Exact seven retained V1 families; duplicate family names fail. |
| Completed | `undefined_value_policy` | `str` | `explicit` | Yes | `build_core_metric_profile()` | Non-computable metrics carry reason/warning; Infinity is invalid and no silent zero is used. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-042` | Define the read-only contract implemented by one named metric-family calculator. | `class MetricCalculator(Protocol)` | None | None | **Usage:** `05_metrics.py::fr_res_042()`<br>**Unit:** `test_metric_registry.py::test_calculator_protocol_contract()` |
| Completed | `FR-RES-043` | Compute normalized values for one family from an immutable metric context. | `MetricCalculator.compute(context: MetricContext) -> tuple[MetricValue,...]` | Read-only | invalid/missing metric input | **Usage:** `05_metrics.py::fr_res_043`<br>**Unit:** `test_metric_registry.py::test_calculator_returns_normalized_values` |
| Completed | `FR-RES-044` | Own unique bounded calculator membership without global mutable defaults. | `MetricRegistry` | Local state mutation | duplicate/invalid calculator | **Usage:** `05_metrics.py::fr_res_044`<br>**Unit:** `test_metric_registry.py::test_registry_rejects_duplicate_family` |
| Completed | `FR-RES-045` | Construct an isolated registry from a bounded calculator iterable. | `MetricRegistry.from_calculators(calculators: Iterable[MetricCalculator]) -> MetricRegistry` | Local state mutation | duplicate/empty/invalid calculators | **Usage:** `05_metrics.py::fr_res_045`<br>**Unit:** `test_metric_registry.py::test_from_calculators_is_isolated` |
| Completed | `FR-RES-046` | Resolve a calculator by exact family name. | `MetricRegistry.resolve(family: str) -> MetricCalculator` | Read-only | family not found | **Usage:** `05_metrics.py::fr_res_046`<br>**Unit:** `test_metric_registry.py::test_resolve_missing_family` |
| Completed | `FR-RES-047` | Return calculators in deterministic registration order without exposing mutable storage. | `MetricRegistry.all() -> tuple[MetricCalculator, ...]` | Read-only | None | **Usage:** `05_metrics.py::fr_res_047()`<br>**Unit:** `test_metric_registry.py::test_all_is_immutable_and_ordered()` |
| Completed | `FR-RES-048` | Build a new default registry containing the seven retained metric families. | `build_default_registry() -> MetricRegistry` | Local state mutation | `ValidationError(RES_INPUT_INVALID)` | **Usage:** `05_metrics.py::fr_res_048`<br>**Unit:** `test_metric_registry.py::test_default_registry_has_seven_families` |
| Completed | `FR-RES-049` | Build a deterministic profile with units, samples, undefined reasons, hashes, warnings, and duration from a prepared dataset. | `build_core_metric_profile(prepared: PreparedDataset, *, registry: MetricRegistry \| None = None, limits: ResearchResourceLimits) -> CoreMetricProfile` | Read-only | invalid data/dependency/resource | **Usage:** `05_metrics.py::fr_res_049`<br>**Unit:** `test_metric_profile.py::test_profile_contains_units_hashes_and_warnings` |

**Implementation notes:**

- Refactor V1 registry and seven calculator families; remove mutable `DEFAULT_CALCULATORS`.
- Research does not re-export Analytics ratios.

### Feature usage examples

`tests/research/usage/05_metrics.py` contains the eight mapped examples.

---

### 4.6 `statistics/` — Seeded Statistical Validation

**Purpose:** Provide deterministic, bounded resampling, matched null distributions, percentiles/thresholds, and multiple-testing corrections.

**Module flow:** `observed sample + StatisticalConfig → resampling/null/correction evidence`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `resampling.py` | Bootstrap and permutation computations. | `block_bootstrap_distribution`, `block_bootstrap_ci`, `permutation_test` | **Standard library:** collections.abc, typing<br>**Required third-party:** numpy<br>**Local:** contracts.configurations → `StatisticalConfig` |
| Completed | `null_models.py` | Generate matched nulls and summarize/compare them. | `random_entry_null`, `r_space_null`, `session_randomized_null`, `shuffle_returns_null`, `compute_null_percentile`, `null_distribution_stats`, `exceeds_null_threshold` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts.configurations → `StatisticalConfig` |
| Completed | `corrections.py` | Apply multiple-comparison corrections. | `benjamini_hochberg`, `holm_bonferroni` | **Standard library:** typing<br>**Required third-party:** numpy<br>**Local:** None |
| Completed | `__init__.py` | Expose the supported statistical API. | Twelve functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** three files above |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `seed` | `int` | Required explicit master seed | Yes | All stochastic functions | Effective seeds are deterministic and recorded in results and `ResearchReport.seeds`. |
| Completed | `bootstrap_samples / permutation_samples / null_samples` | `int` | Explicit per run | Yes | Resampling/null functions | Positive bounded iteration counts; excess fails before allocation. |
| Completed | `block_size` | `int` | Explicit | Conditional | Bootstrap/shuffle null | Must not exceed sample length; invalid sizes fail. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-050` | Generate a seeded block-bootstrap statistic distribution and record the effective parameters. | `block_bootstrap_distribution(values: NDArray, *, statistic: Callable[[NDArray], float], config: StatisticalConfig) -> NDArray` | Read-only | invalid/insufficient/non-finite sample or limit | **Usage:** `06_statistics.py::fr_res_050`<br>**Unit:** `test_statistics_resampling.py::test_distribution_is_seed_reproducible` |
| Completed | `FR-RES-051` | Compute a block-bootstrap confidence interval from the seeded distribution. | `block_bootstrap_ci(values: NDArray, *, statistic: Callable[[NDArray], float], confidence: float, config: StatisticalConfig) -> tuple[float, float]` | Read-only | Pending taxonomy: invalid confidence/sample/statistic | **Usage:** `06_statistics.py::fr_res_051()`<br>**Unit:** `test_statistics_resampling.py::test_ci_rejects_non_finite_statistic()` |
| Completed | `FR-RES-052` | Compute an empirical permutation p-value with declared alternative and seed. | `permutation_test(observed: float, samples: NDArray, *, alternative: str, config: StatisticalConfig) -> float` | Read-only | Pending taxonomy: invalid observed/empty sample/alternative | **Usage:** `06_statistics.py::fr_res_052()`<br>**Unit:** `test_statistics_resampling.py::test_permutation_rejects_empty_sample()` |
| Completed | `FR-RES-053` | Generate a side- and horizon-matched random-entry null in log-return space. | `random_entry_null(data: DataFrame, *, side: Literal["buy", "sell", "mixed"], hold_bars: int, config: StatisticalConfig) -> NDArray` | Read-only | Pending taxonomy: invalid side/horizon/OHLC/sample | **Usage:** `06_statistics.py::fr_res_053()`<br>**Unit:** `test_statistics_null_models.py::test_random_entry_null_matches_side()` |
| Completed | `FR-RES-054` | Generate a seeded null distribution in R-multiple space from declared trade assumptions. | `r_space_null(samples: NDArray, *, config: StatisticalConfig) -> NDArray` | Read-only | Pending taxonomy: empty/non-finite/invalid config | **Usage:** `06_statistics.py::fr_res_054()`<br>**Unit:** `test_statistics_null_models.py::test_r_space_null_rejects_non_finite()` |
| Completed | `FR-RES-055` | Generate a seeded null by shuffling entries only within the same configured session. | `session_randomized_null(data: DataFrame, *, session_column: str, config: StatisticalConfig) -> NDArray` | Read-only | invalid session/sample/config | **Usage:** `06_statistics.py::fr_res_055`<br>**Unit:** `test_statistics_null_models.py::test_session_null_preserves_session_groups` |
| Completed | `FR-RES-056` | Generate a seeded null by shuffling return blocks while preserving declared block length. | `shuffle_returns_null(returns: Series, *, config: StatisticalConfig) -> NDArray` | Read-only | Pending taxonomy: invalid block/sample/non-finite values | **Usage:** `06_statistics.py::fr_res_056()`<br>**Unit:** `test_statistics_null_models.py::test_shuffle_null_rejects_large_block()` |
| Completed | `FR-RES-057` | Compute the observed percentile within a finite non-empty null distribution. | `compute_null_percentile(observed: float, distribution: NDArray) -> float` | Read-only | Pending taxonomy: non-finite observed/empty/non-finite distribution | **Usage:** `06_statistics.py::fr_res_057()`<br>**Unit:** `test_statistics_null_models.py::test_percentile_outside_sample_range()` |
| Completed | `FR-RES-058` | Return finite count, location, dispersion, and declared quantiles for a null distribution. | `null_distribution_stats(distribution: NDArray) -> Mapping[str, float]` | Read-only | Pending taxonomy: empty/non-finite distribution | **Usage:** `06_statistics.py::fr_res_058()`<br>**Unit:** `test_statistics_null_models.py::test_null_stats_reject_empty()` |
| Completed | `FR-RES-059` | Determine threshold exceedance under an explicit upper/lower/two-sided rule. | `exceeds_null_threshold(observed: float, distribution: NDArray, *, quantile: float, alternative: str) -> bool` | Read-only | Pending taxonomy: invalid quantile/alternative/distribution | **Usage:** `06_statistics.py::fr_res_059()`<br>**Unit:** `test_statistics_null_models.py::test_threshold_direction_is_explicit()` |
| Completed | `FR-RES-060` | Apply Benjamini-Hochberg FDR correction to finite p-values in original order. | `benjamini_hochberg(p_values: Sequence[float], *, q: float) -> NDArray` | Read-only | Pending taxonomy: empty/invalid p-values/q | **Usage:** `06_statistics.py::fr_res_060()`<br>**Unit:** `test_statistics_corrections.py::test_bh_preserves_original_order()` |
| Completed | `FR-RES-061` | Apply Holm-Bonferroni family-wise correction to finite p-values in original order. | `holm_bonferroni(p_values: Sequence[float], *, alpha: float) -> NDArray` | Read-only | Pending taxonomy: empty/invalid p-values/alpha | **Usage:** `06_statistics.py::fr_res_061()`<br>**Unit:** `test_statistics_corrections.py::test_holm_rejects_invalid_p_value()` |

### Feature usage examples

`tests/research/usage/06_statistics.py` contains the twelve mapped examples.

---

### 4.7 `studies/` — Edge Discovery and Confirmation

**Purpose:** Run null, mean-reversion, trend-persistence, and session studies against declared splits and apply one confirmation/classification policy.

**Module flow:** `split data + configs → null baseline → study → comparison → classification → EdgeResult`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `null_baseline.py` | Build and compare matched null evidence. | `run_eds_null_baseline`, `compare_to_null`, `get_acceptance_criteria` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; statistics public API |
| Completed | `edge_studies.py` | Execute three approved edge-study families; session studies consume an already tagged frame and do not define/tag sessions. | `run_eds_mean_reversion`, `run_eds_trend_persistence`, `run_eds_session` | **Standard library:** time, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; features; leakage; statistics |
| Completed | `classification.py` | Apply the single versioned confirmation/classification policy. | `classify_symbol` | **Standard library:** typing<br>**Required third-party:** None<br>**Local:** contracts.results → `EdgeResult` |
| Completed | `__init__.py` | Expose the supported study API. | Seven functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** three files above |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `confirmation_policy_version` | `str` | `v1` | Yes | All study/classification/report consumers | One truth table for status, classification, profiles, scorecards, and reports. |
| Completed | `minimum_samples` | `Mapping[str, int]` | Explicit per study | Yes | Study functions | Per-study evidence threshold; insufficiency never becomes a confirmed edge. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-062` | Build seeded random-entry, R-space, and shuffled-return baselines with recorded data/split/config identity. | `run_eds_null_baseline(data: DataFrame, *, split: TimeSplitResult, statistics: StatisticalConfig, study: StudyConfig) -> EdgeResult` | Read-only | `ValidationError`: invalid/insufficient data/config | **Usage:** `07_studies.py::fr_res_062()`<br>**Unit:** `test_studies_null_baseline.py::test_baseline_records_seed_and_split()` |
| Completed | `FR-RES-063` | Compare observed evidence to the correctly matched null and return percentile, threshold, p-value, and warnings. | `compare_to_null(observed: EdgeResult, baseline: EdgeResult) -> Mapping[str, JSONValue]` | Read-only | `ValidationError`: incompatible/malformed results | **Usage:** `07_studies.py::fr_res_063()`<br>**Unit:** `test_studies_null_baseline.py::test_compare_rejects_mismatched_side()` |
| Completed | `FR-RES-064` | Extract versioned acceptance criteria from baseline evidence without hard-coded direction drift. | `get_acceptance_criteria(baseline: EdgeResult) -> Mapping[str, JSONValue]` | Read-only | `ValidationError`: absent/incompatible baseline | **Usage:** `07_studies.py::fr_res_064()`<br>**Unit:** `test_studies_null_baseline.py::test_criteria_follow_confirmation_policy()` |
| Completed | `FR-RES-065` | Evaluate compression/z-score fade mean reversion on declared split data and return advisory uncertainty evidence. | `run_eds_mean_reversion(data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult` | Read-only | Pending taxonomy: invalid/insufficient/resource/statistical failure | **Usage:** `07_studies.py::fr_res_065()`<br>**Unit:** `test_edge_studies.py::test_mean_reversion_uses_matched_null()` |
| Completed | `FR-RES-066` | Evaluate high-volatility breakout follow-through on declared split data and return advisory uncertainty evidence. | `run_eds_trend_persistence(data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult` | Read-only | Pending taxonomy: invalid/insufficient/resource/statistical failure | **Usage:** `07_studies.py::fr_res_066()`<br>**Unit:** `test_edge_studies.py::test_trend_study_records_rule_config()` |
| Completed | `FR-RES-067` | Evaluate breakout/fade hypotheses on a frame already tagged by `seasonality.tag_sessions` and apply multiple-testing correction without redefining session windows. | `run_eds_session(tagged_data: DataFrame, *, split: TimeSplitResult, study: StudyConfig, statistics: StatisticalConfig, limits: ResearchResourceLimits) -> EdgeResult` | Read-only | missing/invalid canonical session tags, validation, or resource failure | **Usage:** `07_studies.py::fr_res_067`<br>**Unit:** `test_edge_studies.py::test_session_study_applies_fdr` |
| Completed | `FR-RES-068` | Classify mean-reversion and trend evidence using one versioned confirmation policy and preserve uncertainty/advisory status. | `classify_symbol(mean_reversion: EdgeResult, trend_persistence: EdgeResult, *, policy_version: str) -> Mapping[str, JSONValue]` | Read-only | `ValidationError`: incompatible result/policy | **Usage:** `07_studies.py::fr_res_068()`<br>**Unit:** `test_studies_classification.py::test_classification_matches_report_policy()` |

**Implementation notes:**

- Keep session statistics and breakout/fade simulation as private helpers.
- Reuse V1 study mechanics only after correcting BUY-side null assumptions and confirmation drift.

### Feature usage examples

`tests/research/usage/07_studies.py` contains the seven mapped examples.

---

### 4.8 `seasonality/` — Sessions and Seasonality

**Purpose:** Provide one timezone-aware session authority and calendar/session/hour opportunity analysis.

**Module flow:** `timestamp/session config → session tags → run_seasonality()`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `sessions.py` | Resolve, describe, and tag canonical sessions. | `active_sessions_for_hour`, `session_label_for_hour`, `session_hours_payload`, `tag_sessions` | **Standard library:** datetime, typing<br>**Required third-party:** pandas<br>**Local:** contracts.configurations → `SessionConfig` |
| Completed | `analysis.py` | Compute seasonality summaries under the canonical session policy. | `SeasonalityFilters`, `run_seasonality` | **Standard library:** dataclasses, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; sessions.py |
| Completed | `__init__.py` | Expose the supported session/seasonality API. | Six exports above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** sessions.py, analysis.py |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `session timezone/windows/precedence` | `SessionConfig` | Explicit per run | Yes | All module symbols | One authority across enrichment, session studies, heatmaps, and summaries. |
| Completed | `adr_period` | `int` | `14` | Yes | `run_seasonality()` | Positive window; too-short data produces documented insufficiency. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-069` | Return every configured session active for a timezone-aware hour using canonical overlap precedence. | `active_sessions_for_hour(hour: int, *, config: SessionConfig) -> tuple[str,...]` | Read-only | invalid hour/session policy | **Usage:** `08_seasonality.py::fr_res_069`<br>**Unit:** `test_sessions.py::test_active_sessions_handles_overlap` |
| Completed | `FR-RES-070` | Return the deterministic primary session label for an hour while preserving overlap evidence. | `session_label_for_hour(hour: int, *, config: SessionConfig) -> str` | Read-only | unmatched/invalid hour | **Usage:** `08_seasonality.py::fr_res_070`<br>**Unit:** `test_sessions.py::test_session_label_uses_precedence` |
| Completed | `FR-RES-071` | Return a machine-readable payload of timezone, windows, order, overlaps, and schema version. | `session_hours_payload(*, config: SessionConfig) -> Mapping[str, JSONValue]` | Read-only | invalid policy | **Usage:** `08_seasonality.py::fr_res_071`<br>**Unit:** `test_sessions.py::test_session_payload_is_versioned` |
| Completed | `FR-RES-072` | Add session labels to a copied timezone-aware frame and record DST/unmatched warnings without changing row order. | `tag_sessions(data: DataFrame, *, config: SessionConfig) -> tuple[DataFrame, tuple[ResearchWarning,...]]` | Read-only | invalid index/timezone/policy | **Usage:** `08_seasonality.py::fr_res_072`<br>**Unit:** `test_sessions.py::test_tag_sessions_handles_cross_midnight` |
| Completed | `FR-RES-073` | Define immutable optional calendar, session, symbol, and hour filters without embedding session definitions. | `SeasonalityFilters(years: tuple[int, ...] = (), months: tuple[int, ...] = (), weekdays: tuple[int, ...] = (), hours: tuple[int, ...] = (), sessions: tuple[str, ...] = ())` | None | Pending taxonomy: invalid range/filter | **Usage:** `08_seasonality.py::fr_res_073()`<br>**Unit:** `test_analysis.py::test_filters_reject_invalid_month()` |
| Completed | `FR-RES-074` | Compute calendar/session/hour summaries, sparse-bucket warnings, opportunity windows, and extremes from supplied data and filters. | `run_seasonality(prepared: PreparedDataset, *, sessions: SessionConfig, filters: SeasonalityFilters, limits: ResearchResourceLimits) -> Mapping[str, JSONValue]` | Read-only | invalid session/data/resource | **Usage:** `08_seasonality.py::fr_res_074`<br>**Unit:** `test_analysis.py::test_seasonality_warns_sparse_bucket` |

### Feature usage examples

`tests/research/usage/08_seasonality.py` contains the six mapped examples.

---

### 4.9 `market_structure/` — Structure, Quality, Validation, Calibration, and Fit

**Purpose:** Produce one reproducible directional profile and optionally evaluate bounded quality, later outcomes, consolidated calibration, and advisory fit.

**Module flow:** `PreparedDataset → profile → optional quality/validation/calibration → advisory fit`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `profile.py` | Detect swings/legs/ranges/distributions/regimes and apply canonical scoring. | `build_market_structure_profile` | **Standard library:** time, typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; features; metrics; studies; seasonality |
| Completed | `quality.py` | Run bounded opt-in stability and robustness evaluation using the canonical builder. | `evaluate_market_structure_quality` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; profile.py |
| Completed | `validation.py` | Label later behavior and summarize prediction evidence. | `label_realized_market_behavior`, `build_validation_summary` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts |
| Completed | `calibration.py` | Rank bounded candidates using the same canonical score and explicit validation truth. | `calibrate_market_structure` | **Standard library:** itertools, typing<br>**Required third-party:** numpy<br>**Local:** contracts; profile.py; validation.py |
| Completed | `fit.py` | Convert research evidence into advisory strategy-archetype fit only. | `build_strategy_fit` | **Standard library:** typing<br>**Required third-party:** None<br>**Local:** contracts.results → `MarketStructureProfile` |
| Completed | `__init__.py` | Expose the supported market-structure API. | Six functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** five files above |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `validation_horizon` | `int` | Explicit positive bars | Yes | Validation/calibration | Defines realized truth; no heuristic default is allowed. |
| Completed | `max_calibration_candidates` | `int` | `128` hard maximum | Yes | `calibrate_market_structure` | Candidate grids are caller-supplied; excess is rejected before evaluation. |
| Completed | `enable_quality` | `bool` | `False` | No | `evaluate_market_structure_quality()` | Stability/robustness are explicitly opt-in due cost. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-075` | Build swings, directional legs, range/distribution/excursion/regime evidence, canonical score/verdict, warnings, hashes, and advisory fit. | `build_market_structure_profile(prepared: PreparedDataset, *, config: MarketStructureConfig, limits: ResearchResourceLimits) -> MarketStructureProfile` | Read-only | Pending taxonomy/resource: invalid/insufficient data or limit | **Usage:** `09_market_structure.py::fr_res_075()`<br>**Unit:** `test_metric_profile.py::test_profile_reuses_canonical_score()` |
| Completed | `FR-RES-076` | Run bounded temporal stability and parameter robustness only when enabled and record windows, variants, duration, and warnings. | `evaluate_market_structure_quality(prepared: PreparedDataset, *, config: MarketStructureConfig, limits: ResearchResourceLimits) -> MarketStructureQualityReport` | Read-only | Pending taxonomy/resource: disabled/invalid/budget exceeded | **Usage:** `09_market_structure.py::fr_res_076()`<br>**Unit:** `test_quality.py::test_quality_is_opt_in_and_bounded()` |
| Completed | `FR-RES-077` | Label later bars as trend/reversion/mixed under one approved horizon/truth policy and return insufficiency as structured evidence. | `label_realized_market_behavior(data: DataFrame, *, symbol: str, timeframe: str, config: MarketStructureConfig) -> Mapping[str, JSONValue]` | Read-only | invalid truth policy or data | **Usage:** `09_market_structure.py::fr_res_077`<br>**Unit:** `test_data_validation.py::test_label_behavior_uses_approved_horizon` |
| Completed | `FR-RES-078` | Aggregate prediction evidence by confidence, verdict, symbol, and timeframe with sample counts and warnings. | `build_validation_summary(rows: Sequence[Mapping[str, JSONValue]]) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: malformed/insufficient rows | **Usage:** `09_market_structure.py::fr_res_078()`<br>**Unit:** `test_data_validation.py::test_summary_preserves_sample_counts()` |
| Completed | `FR-RES-079` | Build and rank a bounded candidate grid against approved validation truth using the same canonical score, recording parameters, criteria, window, stability, and warnings. | `calibrate_market_structure(run_rows: Sequence[Mapping[str, JSONValue]], validation_rows: Sequence[Mapping[str, JSONValue]], *, config: MarketStructureConfig, limits: ResearchResourceLimits) -> Mapping[str, JSONValue]` | Read-only | invalid truth/candidate/resource | **Usage:** `09_market_structure.py::fr_res_079`<br>**Unit:** `test_calibration.py::test_calibration_uses_profile_score` |
| Completed | `FR-RES-080` | Rank advisory strategy archetypes from profile evidence without mutating or approving Strategy, Risk, or Trading state. | `build_strategy_fit(profile: MarketStructureProfile) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: malformed/insufficient profile | **Usage:** `09_market_structure.py::fr_res_080()`<br>**Unit:** `test_fit.py::test_strategy_fit_is_advisory_only()` |

**Implementation notes:**

- Split the V1 large market-structure file; keep focused private swing/leg/range helpers.
- Replace three calibration implementations with `calibrate_market_structure()`.
- `build_market_structure_research_profile()` and mutable profile override tables do not survive as public APIs.

### Feature usage examples

`tests/research/usage/09_market_structure.py` contains the six mapped examples.

---

### 4.10 `modeling/` — Deterministic Unsupervised Insights

**Purpose:** Produce seeded PCA/K-Means evidence and descriptive cluster insights through stateless functions.

**Module flow:** `leakage-safe frame + config → PCA → K-Means → insights → UnsupervisedResearchResult`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `decomposition.py` | Scale selected numeric features and compute PCA evidence. | `run_pca` | **Standard library:** typing<br>**Required third-party:** numpy, pandas, scikit-learn<br>**Local:** contracts |
| Completed | `clustering.py` | Compute deterministic K-Means labels and attach them to a copy. | `cluster_feature_space`, `attach_cluster_labels` | **Standard library:** typing<br>**Required third-party:** numpy, pandas, scikit-learn<br>**Local:** contracts |
| Completed | `insights.py` | Summarize investment data, factors, cluster forward evidence, and the complete insight payload. | `summarize_investment_data`, `identify_pca_risk_factors`, `analyze_cluster_outperformance`, `build_unsupervised_insight_report` | **Standard library:** typing<br>**Required third-party:** numpy, pandas<br>**Local:** contracts; features → `forward_returns`; decomposition/clustering |
| Completed | `workflow.py` | Validate prerequisites and execute the complete stateless workflow. | `run_unsupervised_research` | **Standard library:** time, typing<br>**Required third-party:** pandas<br>**Local:** contracts; three files above |
| Completed | `__init__.py` | Expose the supported modeling API. | Eight functions above | **Standard library:** None<br>**Required third-party:** None<br>**Local:** four files above |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `seed` | `int` | Required explicit master seed | Yes | Clustering/workflow | Effective seed recorded; fixed inputs/config/dependencies reproduce labels. |
| Completed | `minimum_samples` | `int` | Explicit | Yes | All modeling functions | Too-few rows produce typed insufficiency, not ambiguous `SKIPPED`. |
| Completed | `pca_components / clusters` | `int` | Explicit | Yes | PCA/K-Means | Must be positive and supported by usable rows/features. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-081` | Scale selected finite numeric features and return PCA scores, loadings, variance, preprocessing, and diagnostics without mutation. | `run_pca(features: DataFrame, *, config: UnsupervisedResearchConfig) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: invalid/constant/missing/insufficient dimensions | **Usage:** `10_modeling.py::fr_res_081()`<br>**Unit:** `test_decomposition.py::test_pca_records_preprocessing()` |
| Completed | `FR-RES-082` | Cluster finite feature rows with deterministic K-Means under the effective seed and return labels/centers/diagnostics. | `cluster_feature_space(features: DataFrame, *, config: UnsupervisedResearchConfig) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: invalid cluster/sample/seed/data | **Usage:** `10_modeling.py::fr_res_082()`<br>**Unit:** `test_clustering.py::test_clusters_reproduce_with_seed()` |
| Completed | `FR-RES-083` | Attach aligned labels to a copied feature frame without mutating input or changing row order. | `attach_cluster_labels(features: DataFrame, labels: Series, *, column: str = "cluster") -> DataFrame` | Read-only | Pending taxonomy: misaligned labels/duplicate column | **Usage:** `10_modeling.py::fr_res_083()`<br>**Unit:** `test_clustering.py::test_attach_labels_does_not_mutate()` |
| Completed | `FR-RES-084` | Return descriptive finite-value, missingness, duplicate, return, and correlation evidence for investment data. | `summarize_investment_data(data: DataFrame) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: empty/invalid data | **Usage:** `10_modeling.py::fr_res_084()`<br>**Unit:** `test_insights.py::test_summary_handles_constant_columns()` |
| Completed | `FR-RES-085` | Extract the largest absolute PCA loadings as interpretable factors with component/feature/sign/magnitude evidence. | `identify_pca_risk_factors(pca: Mapping[str, JSONValue], *, top_count: int) -> tuple[Mapping[str, JSONValue], ...]` | Read-only | Pending taxonomy: malformed PCA/non-positive count | **Usage:** `10_modeling.py::fr_res_085()`<br>**Unit:** `test_insights.py::test_factors_rank_absolute_loadings()` |
| Completed | `FR-RES-086` | Compare clusters using canonical forward returns, sample counts, uncertainty, and semantic advisory names without adapting signals. | `analyze_cluster_outperformance(data: DataFrame, labels: Series, *, horizon: int) -> tuple[Mapping[str, JSONValue], ...]` | Read-only | Pending taxonomy: invalid/misaligned/insufficient data | **Usage:** `10_modeling.py::fr_res_086()`<br>**Unit:** `test_insights.py::test_cluster_outperformance_records_sample_size()` |
| Completed | `FR-RES-087` | Combine descriptive, PCA, cluster, factor, and forward evidence with warnings and diagnostics; omit all signal-adaptation behavior. | `build_unsupervised_insight_report(features: DataFrame, *, config: UnsupervisedResearchConfig) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: nested model/validation failure | **Usage:** `10_modeling.py::fr_res_087()`<br>**Unit:** `test_insights.py::test_insight_report_has_no_signal_control()` |
| Completed | `FR-RES-088` | Execute the stateless bounded modeling workflow and return complete reproducibility metadata and advisory status. | `run_unsupervised_research(features: DataFrame, *, config: UnsupervisedResearchConfig, limits: ResearchResourceLimits) -> UnsupervisedResearchResult` | Read-only | invalid/insufficient/resource/model failure | **Usage:** `10_modeling.py::fr_res_088`<br>**Unit:** `test_workflow.py::test_workflow_is_stateless_seeded_and_advisory` |

**Implementation notes:**

- Replace V1 `UnsupervisedResearchService` with `run_unsupervised_research()`.
- Merge V1 `compute_forward_returns` into `features.forward_returns`.
- Exclude `SignalAdaptationResult` and `adapt_signals_by_cluster`.

### Feature usage examples

`tests/research/usage/10_modeling.py` contains the eight mapped examples.

---

### 4.11 `profiles/` — Scorecards, Snapshots, Rendering, and Edge Lab Stages

**Purpose:** Build the canonical deterministic evidence view, render it without I/O, and expose pure stage sequencing for external orchestration.

**Module flow:** `stage outputs → scorecard → snapshot → render/report → ResearchReport v1`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `scorecard.py` | Build one deterministic advisory scorecard. | `build_research_scorecard` | **Standard library:** typing<br>**Required third-party:** None<br>**Local:** contracts; metrics; studies; seasonality; market_structure; Analytics `PerformanceReport` |
| Completed | `snapshot.py` | Normalize approved versioned stage outputs. | `build_research_profile_snapshot`, `build_profile_summary`, `build_dashboard_summary` | **Standard library:** datetime, typing<br>**Required third-party:** None<br>**Local:** contracts; scorecard.py |
| Completed | `rendering.py` | Render JSON-compatible, Markdown, comparison, and multi-symbol reports without writing. | `render_research_report`, `render_profile_comparison`, `generate_multi_symbol_report` | **Standard library:** json, typing<br>**Required third-party:** None<br>**Local:** contracts; snapshot.py |
| Completed | `workflow.py` | Execute all selected deterministic Research stages in canonical dependency order and construct `ResearchReport v1` inside one standard response; invalid dependencies fail closed. | `run_edge_lab_profile` | **Standard library:** collections, dataclasses, time, typing<br>**Required third-party:** pandas/numpy through selected stages<br>**Local:** Research feature APIs and error catalogue; Data `MarketDataset`; Analytics `PerformanceReport`; Utils validation/hash/logging/response contracts |
| Completed | `__init__.py` | Expose the completed profiles API. | Profile builders, renderers, `run_edge_lab_profile` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** focused profile files |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `scorecard_schema_version` | `str` | `v1` | Yes | Scorecard/snapshot/report | Versioned confirmation/readiness semantics. |
| Completed | `selected_stages` | `tuple[str, ...]` | None | Yes | `run_edge_lab_profile()` | Explicit stages only; dependencies validated and external orchestration retained. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-089` | Build deterministic score rows, final score, uncertainty, readiness/reasons, versions, warnings, and advisory status from approved evidence. | `build_research_scorecard(*, metric_profile: CoreMetricProfile, seasonality: Mapping[str, JSONValue] \| None, edges: Sequence[EdgeResult], market_structure: MarketStructureProfile \| None, modeling: UnsupervisedResearchResult \| None, performance: PerformanceReport \| None = None) -> ResearchScorecard` | Read-only | Pending taxonomy/dependency: absent prerequisite or incompatible versions | **Usage:** `11_profiles.py::fr_res_089()`<br>**Unit:** `test_scorecard.py::test_scorecard_is_deterministic_and_advisory()` |
| Completed | `FR-RES-090` | Build one canonical versioned snapshot from approved stage outputs and reject route-specific/unversioned payloads. | `build_research_profile_snapshot(*, stages: Mapping[str, JSONValue], scorecard: ResearchScorecard, dataset_hash: str, configuration_hash: str) -> ResearchProfileSnapshot` | Read-only | Pending taxonomy: missing/incompatible stage/hash | **Usage:** `11_profiles.py::fr_res_090()`<br>**Unit:** `test_snapshot.py::test_snapshot_rejects_unversioned_stage()` |
| Completed | `FR-RES-091` | Return a concise observation/uncertainty/readiness summary from a canonical snapshot. | `build_profile_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy: invalid snapshot | **Usage:** `11_profiles.py::fr_res_091()`<br>**Unit:** `test_snapshot.py::test_profile_summary_preserves_warnings()` |
| Completed | `FR-RES-092` | Return a bounded UI-ready block from a canonical snapshot without presentation-side calculation. | `build_dashboard_summary(snapshot: ResearchProfileSnapshot) -> Mapping[str, JSONValue]` | Read-only | Pending taxonomy/resource: invalid/oversized snapshot | **Usage:** `11_profiles.py::fr_res_092()`<br>**Unit:** `test_snapshot.py::test_dashboard_summary_is_bounded()` |
| Completed | `FR-RES-093` | Render a canonical report as JSON-compatible data or Markdown with UTC metadata and no persistence side effect. | `render_research_report(report: ResearchReport, *, format: Literal["json", "markdown"]) -> JSONValue \| str` | Read-only | Pending taxonomy: unsupported format/non-serializable report | **Usage:** `11_profiles.py::fr_res_093()`<br>**Unit:** `test_rendering.py::test_render_report_uses_utc_and_no_io()` |
| Completed | `FR-RES-094` | Render a Markdown comparison of two compatible snapshots while exposing schema/config/dataset differences. | `render_profile_comparison(left: ResearchProfileSnapshot, right: ResearchProfileSnapshot) -> str` | Read-only | Pending taxonomy: incompatible schema/snapshot | **Usage:** `11_profiles.py::fr_res_094()`<br>**Unit:** `test_rendering.py::test_comparison_rejects_incompatible_schema()` |
| Completed | `FR-RES-095` | Render per-symbol and combined advisory summaries in memory while preserving individual failures/warnings; it shall not write files. | `generate_multi_symbol_report(reports: Mapping[str, ResearchReport], *, format: Literal["json", "markdown"]) -> JSONValue \| str` | Read-only | Pending taxonomy/resource: empty/invalid/oversized report set | **Usage:** `11_profiles.py::fr_res_095()`<br>**Unit:** `test_rendering.py::test_multi_symbol_preserves_partial_warnings()` |
| Completed | `FR-RES-096` | Execute selected `data`, `features`, `leakage`, `metrics`, `statistics`, `studies`, `seasonality`, `market_structure`, `modeling`, and `profiles` APIs in canonical dependency order and return advisory `ResearchReport v1` directly in `StandardResponse.data` while leaving provider reads, cache, scheduling, database/artifact writes, and strategy submission external. | `run_edge_lab_profile(dataset: MarketDataset, *, hypothesis: str, config: EdgeLabConfig, performance: PerformanceReport \| None = None) -> StandardResponse[ResearchReport]` | Read-only | `StandardResponse.error` with approved Research code, including `RES_INPUT_INVALID`, `RES_STAGE_DEPENDENCY_INVALID`, or `RES_STAGE_UNAVAILABLE`; unexpected failures map safely to `INTERNAL_ERROR` | **Usage:** `tests/research/usage/11_profiles.py::fr_res_096()`<br>**Unit:** `tests/research/unit/test_workflow.py`<br>**System:** `tests/system/integration/test_research_to_strategy.py` |

**Implementation notes:**

- Merge V1 scorecard/snapshot/reporting behavior around one schema.
- `print_result_summary` and separate save functions are removed.
- `run_edge_lab_profile()` is stage orchestration only; UI/API remains the cross-domain coordinator.

### Feature usage examples

`tests/research/usage/11_profiles.py` contains the eight mapped examples.

---

### 4.12 `artifacts/` — Safe Research Artifact Persistence

**Purpose:** Mask, serialize, validate, and atomically persist approved Research artifacts under an approved root.

**Module flow:** `ResearchReport/snapshot → mask → render → path/size/overwrite checks → atomic replace → ArtifactReference + AuditEvent`

### Files

| Status | File | Responsibility | Key exports | Dependencies |
|---|---|---|---|---|
| Completed | `persistence.py` | Perform the single approved Research persistence side effect. | `write_research_artifact` | **Standard library:** hashlib, os, pathlib, tempfile, typing<br>**Required third-party:** None<br>**Local:** contracts; leakage.masking; profiles.rendering; Utils `AuthContext`/`AuditEvent`/security; Data migration/connection public API through Data's documented migration and connection API |
| Completed | `migrations.py` | Define the immutable Research-owned artifact metadata migration for Data's shared executor. | `build_research_migration_request` | **Standard library:** hashlib<br>**Required third-party:** None<br>**Local:** Data `MigrationRequest`/`MigrationStep` contracts |
| Completed | `__init__.py` | Expose the supported artifact API. | `write_research_artifact` | **Standard library:** None<br>**Required third-party:** None<br>**Local:** persistence.py → `write_research_artifact` |

### Configuration and Limits Manifest

| Status | Setting / Limit | Type | Default | Required | Used by | Description |
|---|---|---|---|---|---|---|
| Completed | `allowed_root` | `Path` | Explicit absolute root | Yes | `write_research_artifact` | Resolved destination must remain under this root; traversal fails. |
| Completed | `overwrite` | `bool` | `False` | Yes | `write_research_artifact()` | Existing destination fails unless explicitly true. |
| Completed | `require_atomic` | `bool` | `True` | Yes | `write_research_artifact()` | Temporary write plus atomic replace is enforced when required. |
| Completed | `max_artifact_bytes` | `int` | Explicit per run | Yes | `write_research_artifact` | Oversized artifact rejected before final write; no silent truncation. |

#### Functional requirements

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-097` | Mask and render an approved artifact, enforce allowed root/overwrite/encoding/size/atomic policy, write via temporary replacement, emit a redacted audit event, and return `ArtifactReference`. | `write_research_artifact(artifact: ResearchReport \| ResearchProfileSnapshot, destination: Path, *, config: ArtifactWriteConfig, auth: AuthContext, limits: ResearchResourceLimits) -> ArtifactReference` | Persistence write; event publication | invalid path, traversal, conflict, permission, serialization, size, atomicity, audit failure | **Usage:** `12_artifacts.py::fr_res_097`<br>**Unit:** `test_persistence.py::test_write_artifact_masks_and_replaces_atomically` |
| Completed | `FR-RES-098` | Return the deterministic Research-owned `001_research_artifacts_v1` metadata migration for execution through Data's migration framework. | `build_research_migration_request(request_id: str) -> MigrationRequest` | None | `ConfigurationError(RES_CONFIGURATION_INVALID)` | **Usage:** `12_artifacts.py::fr_res_098`<br>**Unit:** `test_artifact_migrations.py::test_research_migration_is_stable_and_owned` |

**Rules:**

- Database snapshots are not written directly by Research stage functions.
- Masking occurs before bytes are generated; warnings/audit metadata are also redacted.
- Same-path concurrent writes obey Data's shared path-lock contract and surface conflicts.

### Feature usage examples

`tests/research/usage/12_artifacts.py` contains `fr_res_097()`.

---

### 4.13 `intelligence/` — Fundamental and Sentiment Source Evidence

**Status:** `Completed`

This deterministic feature converts eligible Data-owned point-in-time research
documents into bounded evidence suitable for Agentic analysis. It performs
selection, normalization, coverage, and deterministic measurement; it does not use
an LLM, express a market opinion, approve a strategy, or trade.

| Status | Requirement ID | Responsibility | Class / Function / Method | Side Effects | Raises | Usage / Test |
|---|---|---|---|---|---|---|
| Completed | `FR-RES-099` | Represent fundamental source evidence with issuer/asset scope, filing/statement/transcript/macro references, coverage, revisions, currency/unit lineage, quality, and canonical hash. | Internal opaque evidence created by `build_fundamental_source_evidence(...)` and inspected/projected through root functions | None | `ValidationError[RES_INPUT_INVALID]` | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |
| Completed | `FR-RES-100` | Build fundamental source evidence only from eligible Data source records available by the supplied decision time and refuse missing required coverage. | `build_fundamental_source_evidence(...)` | Data package-root query and projection reads | `ValidationError[RES_INSUFFICIENT_DATA\|RES_INPUT_INVALID]` | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |
| Completed | `FR-RES-101` | Represent sentiment source evidence with bounded document references, source coverage, deterministic polarity measurements where available, revision/trust/manipulation/injection evidence, and canonical hash. | Internal opaque evidence created by `build_sentiment_source_evidence(...)` and inspected/projected through root functions | None | `ValidationError[RES_INPUT_INVALID]` | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |
| Completed | `FR-RES-102` | Build sentiment source evidence from eligible point-in-time documents using the declared deterministic lexicon version and preserve disagreement and missingness. | `build_sentiment_source_evidence(...)` | Data package-root query and projection reads | `ValidationError[RES_INSUFFICIENT_DATA\|RES_INPUT_INVALID]` | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |
| Completed | `FR-RES-103` | Enforce asset-class applicability so issuer-specific evidence is not fabricated for instruments without an applicable issuer/fundamental model. | `assess_intelligence_applicability(...)` | None | None; returns typed applicability/refusal reasons | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |
| Completed | `FR-RES-104` | Return detached, bounded, non-binding evidence with no unrestricted source payload, model instruction, strategy recommendation, or execution field. | `project_intelligence_evidence(...)` | None | `ValidationError[RES_INPUT_INVALID]` | **Usage:** `tests/research/usage/13_intelligence.py`<br>**Integration:** `tests/research/integration/test_intelligence.py` |

FEAT-RES-13 remains provider-agnostic and network-free. Network retrieval,
provider parsing, licensing metadata, structured observations, immutable
revisions, and point-in-time eligibility are owned by Data `FEAT-DATA-16`.
Research consumes only bounded Data package-root queries and projections.
Transcript evidence currently establishes official document existence and scope;
sentiment remains deterministic title analysis and does not claim transcript-body
language coverage.

## 5. Package-Wide Requirements and Shared Configuration

Shared settings are consumed from `docs/PROJECT.md` and not redefined: `ENVIRONMENT`, `RUNTIME_PROFILE=research`, `DATABASE_URL/DATA_DIR`, UTC time policy, trace identifiers, secret redaction, and `LOG_LEVEL`. Research accepts only `RUNTIME_PROFILE=research` and performs no live mutation regardless of global toggles.

| Status | Requirement ID | Type | Responsibility | Verification |
|---|---|---|---|---|
| Completed | `NFR-RES-001` | Safety | Research shall remain advisory and shall never place, modify, cancel, route, approve, or block live orders or mutate Strategy/Risk/Trading state. | `tests/system/integration/test_research_to_strategy.py` |
| Completed | `NFR-RES-002` | Reliability | Any attempted live-state mutation or governance bypass shall fail closed before side effects. | `tests/research/unit/test_workflow.py`, `tests/system/integration/test_research_to_strategy.py` |
| Completed | `NFR-RES-003` | Reproducibility | Fixed data, effective config, seed, dependency versions, and schema version shall produce equivalent outputs; hashes and effective seeds are recorded. | `tests/research/unit/test_statistics_resampling.py`, `tests/research/integration/test_unsupervised_research.py` |
| Completed | `NFR-RES-004` | Leakage | Forward-looking fields shall be declared, detectable, excluded from feature inputs, and gated before publication. | `tests/research/unit/test_leakage_validation.py`, `tests/research/unit/test_feature_frame.py` |
| Completed | `NFR-RES-005` | Statistical quality | Results shall expose relevant uncertainty and multiple-comparison controls, sample sizes, null assumptions, and warnings. | `tests/research/unit/test_statistics_corrections.py`, `tests/research/unit/test_studies_null_baseline.py` |
| Completed | `NFR-RES-006` | API boundary | Other domains shall use only documented package exports; `__all__` and classifications are unique, resolvable, and stable. | `tests/research/unit/test_contract_api.py` |
| Completed | `NFR-RES-007` | Import safety | Importing Research shall perform no network, disk write, provider/credential initialization, live-state read, or heavy computation. | `tests/research/unit/test_contract_api.py` |
| Completed | `NFR-RES-008` | Security | Secrets, credentials, broker/account identifiers, private fields, and forbidden forward fields shall not appear in artifacts, warnings, logs, errors, or audit metadata. | `tests/research/unit/test_leakage_masking.py`, `tests/research/unit/test_persistence.py` |
| Completed | `NFR-RES-009` | Persistence safety | Artifact writes shall prevent traversal and accidental overwrite, enforce size/encoding/root policy, and use atomic replacement where approved. | `tests/research/unit/test_persistence.py`, `tests/research/integration/test_artifact_persistence.py` |
| Completed | `NFR-RES-010` | Resource safety | Heavy operations shall enforce approved row/iteration/duration/artifact bounds and fail explicitly rather than attempt unbounded work. | `tests/research/unit/test_contract_configurations.py`, selected-stage resource tests |
| Completed | `NFR-RES-011` | Observability | Validation failures, cleaning actions, masking, insufficiency, selected stages, and duration shall emit structured redacted warnings/logs with trace identifiers. | Research unit/integration tests plus logger-boundary inspection |
| Completed | `NFR-RES-012` | Platform | Deterministic library behavior and safe persistence shall work on the project's supported Python 3.14 Windows baseline; platform atomicity differences are explicit. | Targeted tests and usage programs executed on the Windows baseline |
| Completed | `NFR-RES-013` | Maintainability | No recursive facade scan, duplicate formula wrapper, generic helper/service/manager, mutable global registry, or cross-domain internal import shall exist. | Package structure and import/API audit |
| Completed | `NFR-RES-014` | Testing | Every `FR-RES-*` shall have its mapped usage and unit test; every active workflow shall have one standalone README-aligned usage program; every collaborative workflow shall have its mapped integration test; coverage shall be at least 80%. | `tests/research/unit/test_workflow_usage_parity.py`, direct workflow runner, `tests/research/integration/test_usage_scripts.py`, coverage gate |
| Completed | `NFR-RES-015` | Documentation | Every module, class, function, and method shall use Google-style docstrings and every public DataFrame contract shall document columns, index, timezone, alignment, NaNs, and mutation. | Ruff docstring checks and package README contract tables |

---

## 6. Open Decisions

No open decisions. The error taxonomy, dependency boundaries, statistical policy,
market-structure score, scorecard readiness, resource ceilings, artifact migration,
and persistence policy are resolved in the owner-resolved implementation policy.

## Explicit Exclusions

- ForexFactory/news/calendar/sentiment acquisition, provider caching/retry/rate-limit/envelopes.
- Cluster-based signal adaptation.
- Incremental feature computation.
- Production performance claims beyond the advisory budgets specified in Section 4.

---

## 7. Tests and Definition of Done

### Test and usage locations

```text
tests/research/
├── unit/                         # Every public symbol and failure path
├── integration/                  # Module and workflow collaboration
└── usage/                        # One runnable example per FR
```

### Commands

```bash
uv run ruff check app/services/research tests/research
uv run ruff format --check app/services/research tests/research
uv run mypy app/services/research

uv run pytest tests/research/unit
uv run pytest tests/research/integration

uv run python tests/research/usage/01_contracts.py
uv run python tests/research/usage/02_data.py
uv run python tests/research/usage/03_features.py
uv run python tests/research/usage/04_leakage.py
uv run python tests/research/usage/05_metrics.py
uv run python tests/research/usage/06_statistics.py
uv run python tests/research/usage/07_studies.py
uv run python tests/research/usage/08_seasonality.py
uv run python tests/research/usage/09_market_structure.py
uv run python tests/research/usage/10_modeling.py
uv run python tests/research/usage/11_profiles.py
uv run python tests/research/usage/12_artifacts.py

uv run pytest tests/research --cov=app.services.research --cov-branch --cov-fail-under=80
```

Only targeted Research tests are run during iterative development. The full repository suite is reserved for final integration verification.

### Required test levels

- **Unit:** Every `FR-RES-*` success path, validation, documented error, side effect, edge case, and retained V1 parity behavior.
- **Integration:** Every `WF-RES-*` collaboration, `SYS-WF-004` Research boundary, no-live-side-effect boundary, contract compatibility, and artifact safety.
- **Usage:** Every mapped `fr_res_*` example imports only documented public feature APIs, executes directly, and is repeated by the integration usage harness.
- **Security/concurrency:** Nested masking, import safety, same-path writes, immutable registry reads, and parallel seeded reproducibility.
- **Resource:** Approved maximum rows/iterations/duration/artifact size against the explicit resource limits.

### Package completion checklist

- [X] The actual package tree matches Section 2 — evidence: `app/services/research/__init__.py:33`.
- [X] Module sections and files remain in dependency order with no circular imports — evidence: `tests/research/unit/test_contract_api.py:7`.
- [X] Every approved reconciliation capability has its final destination — evidence: `tests/research/integration/test_usage_scripts.py:26`.
- [X] Removed, rejected, and excluded behavior is absent from the package/API — evidence: `tests/research/unit/test_contract_api.py:7`.
- [X] Every module folder represents one coherent capability and every file one focused responsibility — evidence: `app/services/research/__init__.py:33`.
- [X] Every requirement and workflow has status `Completed` — evidence: `tests/research/unit/test_workflow.py:113`.
- [X] `ResearchReport v1` matches `docs/PROJECT.md` and producer/consumer compatibility tests pass — evidence: `tests/system/integration/test_research_to_strategy.py:62`.
- [X] Research artifact ownership/migrations match the top-level data ownership table — evidence: `app/services/research/artifacts/migrations.py:56`.
- [X] Every public export is listed once, classified `stable`, and mapped to exactly one `FR-RES-*` row — evidence: `tests/research/unit/test_contract_api.py:7`.
- [X] Every `FR-RES-*` has its typed signature, side effect, exact resolved error, usage example, and unit test — evidence: `tests/research/integration/test_usage_scripts.py:26`.
- [X] Every collaborative workflow has its integration test — evidence: `tests/system/integration/test_research_to_strategy.py:62`.
- [X] DataFrame contracts document columns, index, timezone, alignment, NaNs, and mutation — evidence: `app/services/research/contracts/results.py:195`.
- [X] V1 parity tests cover preparation, seven metric families, studies, seasonality, structure, quality/calibration, modeling, scorecard, and Edge Lab sequence — evidence: `tests/research/unit/test_workflow.py:113`.
- [X] No provider SDK object, DataFrame, database session, or mutable cross-domain object leaks through `ResearchReport v1` — evidence: `app/services/research/contracts/results.py:512`.
- [X] No live/broker/risk/strategy side effect is reachable from Research — evidence: `tests/system/integration/test_research_to_strategy.py:62`.
- [X] No secret or sensitive nested field appears in output, warning, error, log, or audit metadata — evidence: `app/services/research/leakage/masking.py:66`.
- [X] No open decision remains; no affected implementation was guessed — evidence: `app/services/research/profiles/workflow.py:598`.
- [X] Ruff, formatting, mypy, targeted tests, usage tests, integration tests, and ≥80% coverage pass — evidence: `tests/research/unit/test_analysis.py:93`.

Current completion evidence:

- [X] Final requirements, boundaries, structure, workflows, dependencies, side effects, tests, and open decisions are documented.
- [X] Approved V1 behaviors have final destinations and rejected/excluded behavior is absent.
- [X] Final package implementation and tests match this README — evidence: `tests/research/integration/test_usage_scripts.py:26`.

---

## 8. Change Process

For every future change:

```text
1. Update this README first.
2. Add or change the workflow when system behaviour changes.
3. Resolve or record any decision that would otherwise require guessing.
4. Add or change the functional requirement row, including Side Effects and exact errors.
5. Update the file's key exports and dependencies.
6. Reorder modules or files if dependency order changes.
7. Implement the smallest code change.
8. Add or update the usage example.
9. Add or update targeted unit/integration tests.
10. Change Status to Completed only after runtime use and verification pass.
```

This keeps requirements, dependency order, implementation, examples, tests, and documentation aligned in one authoritative domain specification.


---

## Appendix P — Provisional Component Requirements (roadmap-promoted)

These IDs were minted by the agile delivery roadmap (`docs/dev/AGILE_ROADMAP.md`) and are promoted here to authoritative status. Each `P-RES-NNN` authorizes establishment of the named package seam under `app/services/research/` — its public port, package `__init__`, and error/DTO surface — as a stable component that hosts the same-named module and its `FR-RES-*` behavior defined in §4 (Module and Requirement Specifications). Acceptance = the named package exists with its public seam fixed, typed, logged, tested, and passing the domain quality gates. "First phase" is the delivery phase in the roadmap; the seam is defined no later than that phase and deepened behind it.

| Requirement ID | Component / package | First phase | Hosts |
|---|---|---|---|
| `P-RES-001` | `app/services/research/contracts/` | 1 | `contracts` module + its `FR-RES-*` behavior (§4) |
| `P-RES-002` | `app/services/research/data/` | 1 | `data` module + its `FR-RES-*` behavior (§4) |
| `P-RES-005` | `app/services/research/metrics/` | 1 | `metrics` module + its `FR-RES-*` behavior (§4) |
| `P-RES-011` | `app/services/research/profiles/` | 1 | `profiles` module + its `FR-RES-*` behavior (§4) |
| `P-RES-003` | `app/services/research/features/` | 10 | `features` module + its `FR-RES-*` behavior (§4) |
| `P-RES-004` | `app/services/research/leakage/` | 10 | `leakage` module + its `FR-RES-*` behavior (§4) |
| `P-RES-006` | `app/services/research/statistics/` | 10 | `statistics` module + its `FR-RES-*` behavior (§4) |
| `P-RES-007` | `app/services/research/studies/` | 10 | `studies` module + its `FR-RES-*` behavior (§4) |
| `P-RES-008` | `app/services/research/seasonality/` | 10 | `seasonality` module + its `FR-RES-*` behavior (§4) |
| `P-RES-009` | `app/services/research/market_structure/` | 10 | `market_structure` module + its `FR-RES-*` behavior (§4) |
| `P-RES-010` | `app/services/research/modeling/` | 10 | `modeling` module + its `FR-RES-*` behavior (§4) |
| `P-RES-012` | `app/services/research/artifacts/` | 10 | `artifacts` module + its `FR-RES-*` behavior (§4) |

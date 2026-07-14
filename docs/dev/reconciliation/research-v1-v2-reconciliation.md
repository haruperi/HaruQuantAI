# Research — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** `research` (`res`)
* **V1 audit report:** `docs/dev/audits/research-v1-audit.md` (SHA-256 `924d5bb416ba0a50dec9fd147babcc535689ec75e9ef8aa6994d1b4deab8288d`)
* **V2 requirements:** `12_research.md` (SHA-256 `685d872a3c172ece27729a8a124553bf8cd690a37dbe226893da8a72f1c67237`)
* **V1 package evidenced by the audit:** `app/services/research`
* **V2 package proposal:** `tools/research` in the V2 architecture section; package-location decision remains open for pipeline step 05.
* **Method:** behavior-to-behavior reconciliation only. No code, repository, tests, or runtime were re-inspected.
* **Traceability convention:** V2 did not provide stable requirement IDs. This document assigns reconciliation-local IDs (`V2-FR-RES-*`, `V2-NFR-RES-*`, `V2-BND-RES-*`, `V2-API-RES-*`, `V2-EDGE-RES-*`, and `V2-TEST-RES-*`) in source order.
* **Comparison limitations:**
  * V1 evidence is limited to the audit report and inherits its caller-search, test-enumeration, and dynamic-resolution uncertainties.
  * V2 contains unresolved defaults, placeholder performance targets, and proposed architecture that is not automatically accepted.
  * Test execution, dependency compatibility, performance, and deletion safety are not revalidated in this step.
  * Cross-domain ownership recommendations are provisional until pipeline step 05.

## 2. Executive Summary

Version 1 already contains a substantial, integrated Edge Lab. The proven value is the progressive path from prepared market data through core metrics, seasonality, statistical edge studies, market structure, unsupervised modeling, scorecard generation, validation/calibration, and profile persistence. Those behaviors should not be rebuilt from scratch.

The final direction is a **controlled refactor**, not a wholesale replacement:

* Preserve and correct the operational data-preparation, core-metric, seasonality, EDS, market-structure, unsupervised-modeling, scorecard, and validation workflows.
* Remove provider acquisition, scheduler, cache, database, live-control, and cross-domain compatibility behavior from Research ownership.
* Replace the 207-symbol recursive facade with a small explicit classified export map.
* Consolidate duplicated indicator, analytics, regime, session, report, snapshot, and calibration behavior.
* Add missing contract discipline: typed errors, structured warnings, schema versions, deterministic seeds, data/config hashes, UTC timestamps, dependency metadata, resource bounds, safe artifact writes, and stronger leakage evidence.
* Defer unproven ForexFactory/network helpers, broad agent hypothesis tooling, and cluster-based signal adaptation.
* Reject analytics/validator compatibility re-exports, duplicate standard calculation wrappers, a public module-returning helper, console-printing as a domain API, and a stateless `UnsupervisedResearchService` class.
* Keep the complete Edge Lab workflow, but split ownership: Research owns deterministic computations and advisory artifacts; external API/scheduler/data/database components own triggering, provider reads, caching, scheduling, and persistence orchestration.

The largest unresolved decisions are cleaning defaults, session/timezone authority, package location, seed propagation, error/envelope vocabulary, resource targets, artifact-storage ownership, calibration validation windows, and whether deferred external-provider or signal-adaptation workflows will ever enter scope.

## 3. Decision Principles

1. Preserve behavior demonstrated by `V1-WF-RESEARCH-*` runtime workflows.
2. Treat V1 structure as evidence, not a template.
3. Treat V2 requirements as proposals, not automatic approvals.
4. Keep Research advisory and sandboxed; no output authorizes trading or risk changes.
5. Accept research-ready data at the boundary; do not own production provider lifecycle.
6. Prefer stateless functions. Keep classes only for immutable models, owned registry state, or real lifecycle.
7. Keep one canonical calculation/contract; consume Analytics and Indicators instead of re-exporting or duplicating them.
8. Use one session policy, one edge-confirmation policy, one snapshot schema, one scorecard, and one calibration scoring implementation.
9. Make expensive stability, robustness, calibration, and modeling behavior explicit, seeded, bounded, and opt-in.
10. Add public surface area only for confirmed workflows.
11. Defer network-backed and agent-facing capabilities until their caller, provider, envelope, and failure contracts are approved.
12. Keep the final structure compatible with Package → Feature module → Focused file → Public behavior.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `CAP-RES-001` | Versioned research contracts and configuration | `V1-CAP-RESEARCH-001`, `010`–`014`, `016`, `021`–`023`; `V1-ISSUE-RESEARCH-015`, `020` | `V2-FR-RES-CFG-001`–`014`, `016`–`020`; model-contract requirements | V1 models/configs work but schemas, failure contracts, defaults, and metadata are inconsistent. | **Modify** | Expose a small versioned set of immutable configuration and result contracts with one documented failure pattern per public callable. | Refactor | Preserves operational contracts while removing ambiguous defaults and mixed errors. |
| `CAP-RES-002` | Research dataset preparation and quality evidence | `V1-CAP-RESEARCH-002`–`005`; `V1-WF-RESEARCH-001` | `V2-FR-RES-DATA-001`–`014` | V1 preparation is operational, but provider fetching, cleaning defaults, schema handling, and fatal/warning semantics need correction. | **Modify** | Accept canonical in-memory OHLCV/OHLCVS plus source metadata; validate, clean, and enrich deterministically into `PreparedDataset` with machine-readable quality evidence. | Refactor | Retains proven value while restoring the Data/Research boundary. |
| `CAP-RES-003` | Research feature computation | `V1-CAP-RESEARCH-006`, `007`, `021`; `V1-ISSUE-RESEARCH-005`, `012` | `V2-FR-RES-FEAT-001`–`029` | V1 contains useful features but duplicates Indicators/Analytics and uses inconsistent casing/contracts. | **Merge** | Keep research-specific returns, Hurst, forward outcomes, excursions, and regime-frame assembly; consume shared indicator formulas for common indicators. | Refactor/reuse shared dependencies | Smallest design avoids a second indicator library. |
| `CAP-RES-004` | Leakage controls and chronological validation | `V1-CAP-RESEARCH-008`; `V1-ISSUE-RESEARCH-009` | `V2-FR-RES-LEAK-001`–`006`; `V2-NFR-RES-007` | V1 split/masking exists, but lookahead detection is heuristic and can overstate assurance. | **Modify** | Provide deterministic chronological splits, structured leakage evidence, forward-column declarations, and recursive artifact masking. | Refactor | Preserves useful safety behavior while removing false-certification risk. |
| `CAP-RES-005` | Core metric profile | `V1-CAP-RESEARCH-009`; `V1-WF-RESEARCH-002`; `V1-ISSUE-RESEARCH-011` | `V2-FR-RES-METRIC-001`–`015` | V1 is operational but hard-codes columns and omits complete units/reproducibility metadata. | **Modify** | Build a schema-aware normalized metric profile through a bounded, immutable calculator registry. | Refactor | Confirmed runtime value justifies retention. |
| `CAP-RES-006` | Resampling, null models, and multiple-testing controls | `V1-CAP-RESEARCH-010`; `V1-WF-RESEARCH-004`; `V1-ISSUE-RESEARCH-008`, `015` | `V2-FR-RES-STAT-001`–`015` | V1 functions exist, but direction, seed, invalid-input, and unused-config behavior are inconsistent. | **Modify** | Expose deterministic seeded bootstrap/permutation/null operations with typed failures and recorded effective parameters. | Refactor | Statistical validity is core research behavior. |
| `CAP-RES-007` | Edge discovery studies | `V1-CAP-RESEARCH-011`–`013`; `V1-WF-RESEARCH-004` | `V2-FR-RES-EDS-001`–`009`, `014` | V1 studies run in production integration but need consistent evidence contracts and matched null comparisons. | **Modify** | Run mean-reversion, trend-persistence, and session studies against declared data splits and matching nulls, returning advisory `EdgeResult` evidence. | Refactor | Preserves working Edge Lab value with corrected statistics. |
| `CAP-RES-008` | Edge classification and confirmation semantics | `V1-CAP-RESEARCH-014`; `V1-ISSUE-RESEARCH-007` | `V2-FR-RES-EDS-010`–`014` | Classifier, schema, and reporting apply different confirmation rules. | **Modify** | Use one versioned confirmation policy for result status, classification, scorecards, and reports. | Refactor | Prevents contradictory user-facing decisions. |
| `CAP-RES-009` | Session definitions and seasonality analysis | `V1-CAP-RESEARCH-013`, `015`; `V1-WF-RESEARCH-003`; `V1-ISSUE-RESEARCH-006` | `V2-FR-RES-SEAS-001`–`006` | Operational analytics use conflicting session windows. | **Modify** | Use one timezone-aware session configuration for tagging, EDS session studies, heatmaps, and opportunity summaries. | Refactor | Unifies a proven workflow and removes semantic drift. |
| `CAP-RES-010` | Market-structure profiling | `V1-CAP-RESEARCH-016`; `V1-WF-RESEARCH-005`; `V1-ISSUE-RESEARCH-004` | `V2-FR-RES-STRUCT-001`–`006` | V1 works but one large file combines detection, distributions, regimes, scoring, and quality adjustment. | **Split** | Produce a reproducible profile from focused swing/leg, range/regime, distribution/excursion, and scoring capabilities. | Refactor | Preserves value while reducing change coupling. |
| `CAP-RES-011` | Market-structure validation, stability, robustness, and calibration | `V1-CAP-RESEARCH-018`–`020`; `V1-WF-RESEARCH-008`; `V1-ISSUE-RESEARCH-014` | `V2-FR-RES-STRUCT-007`–`023`, `025` | V1 is integrated, but calibration duplicates production scoring and quality runs can be expensive. | **Merge** | Use one scoring function and one bounded calibration/validation capability with explicit windows, candidate metadata, stability, and warnings. | Refactor | Retains demonstrated workflow while removing divergent implementations. |
| `CAP-RES-012` | Advisory strategy-fit evidence | `V1-CAP-RESEARCH-017`; `V1-WF-RESEARCH-005` | `V2-FR-RES-STRUCT-024`; advisory NFRs | V1 provides rankings, but scorecard and structure paths can duplicate recommendations. | **Modify** | Generate one advisory strategy-fit section from research evidence; never mutate Strategy, Risk, or Execution state. | Refactor | Useful interpretation is retained without crossing ownership boundaries. |
| `CAP-RES-013` | Unsupervised feature modeling | `V1-CAP-RESEARCH-021`, `022`; `V1-WF-RESEARCH-006` | `V2-FR-RES-UNSUP-001`–`015`, `017`–`021`, `023`–`024` | V1 PCA/K-Means path is operational but needs explicit seed, preprocessing, diagnostics, and canonical columns. | **Modify** | Run deterministic feature-frame preparation, PCA, clustering, labels, factor extraction, and cluster evidence through stateless functions and versioned result models. | Refactor | The current stateless service class is unnecessary. |
| `CAP-RES-014` | Cluster-based signal adaptation recommendations | `V1-CAP-RESEARCH-024`; `V1-ISSUE-RESEARCH-018` | `V2-FR-RES-UNSUP-016`, `022` | No active signal-frame caller is confirmed; V1 evaluates and adapts on the same sample. | **Defer** | Exclude from the initial rebuild. Reconsider only as an out-of-sample advisory recommendation with explicit Strategy/Risk boundaries. | Do not migrate initially | Prevents overfit research output from becoming implicit live control. |
| `CAP-RES-015` | Deterministic research scorecard and readiness | `V1-CAP-RESEARCH-025`; `V1-WF-RESEARCH-007` | `V2-FR-RES-REPORT-015`; reproducibility NFRs | V1 is used, but duplicates strategy-fit logic and lacks complete versioned provenance. | **Modify** | Build one deterministic scorecard from approved stage outputs, showing uncertainty, readiness reasons, versions, and advisory status. | Refactor | Strong operational value with manageable corrections. |
| `CAP-RES-016` | Canonical profile snapshots and report rendering | `V1-CAP-RESEARCH-027`–`029`; `V1-ISSUE-RESEARCH-016`, `017` | `V2-FR-RES-REPORT-001`–`002`, `005`, `007`–`012` | V1 has fragmented EDS/profile/snapshot renderers and route-side snapshot assembly. | **Merge** | Use one versioned snapshot schema and shared JSON/Markdown/dashboard/comparison renderers. | Refactor | Eliminates schema and timestamp drift. |
| `CAP-RES-017` | Safe research artifact persistence | `V1-CAP-RESEARCH-008`, `027`, `028`; reporting side effects | `V2-FR-RES-REPORT-003`–`004`, `013`–`014`, `016`–`017`; serialization NFRs | V1 writes directly without a unified path, overwrite, atomicity, or permission contract. | **Modify** | Persist only masked, versioned artifacts through one bounded writer with allowed roots, overwrite policy, atomic replacement where supported, and typed failures. | Refactor | Disk I/O is justified but must be explicit and safe. |
| `CAP-RES-018` | Explicit public API registry | `V1-CAP-RESEARCH-034`; `V1-ISSUE-RESEARCH-001`–`003` | V2 public API classification and lazy-export requirements | V1 recursive resolution exposes 207 mixed symbols and changes callables at import time. | **Modify** | Maintain an explicit, unique, classified export map; lazy-load only listed symbols without scanning or wrapping business callables. | Replace facade internals | Preserves import ergonomics while making the boundary auditable. |
| `CAP-RES-019` | Canonical errors, warnings, and reproducibility metadata | `V1-ISSUE-RESEARCH-017`, `020`; mixed failure behavior across V1 | `V2-FR-RES-CFG-016`–`028`; `V2-NFR-RES-003`–`005`, `017`, `022`–`027` | V1 mixes exceptions, NaNs, `None`, `SKIPPED`, and envelopes. | **Add** | Define typed research errors, structured warnings, schema/config/data hashes, seeds, UTC timestamps, dependency versions, duration, and bounded resource behavior. | New shared contracts | Required for reliable integration and reproducibility. |
| `CAP-RES-020` | Cross-domain Edge Lab orchestration contract | `V1-CAP-RESEARCH-026`; `V1-WF-RESEARCH-007` | V2 aggregate `EdgeLabConfig`, snapshots, scorecard, and workflows | The working workflow is orchestrated in API code and includes cache, scheduler, broker, and database ownership outside Research. | **Split** | Research exposes deterministic stage inputs/outputs; an external orchestrator sequences stages, caching, scheduling, provider reads, and persistence. | Reuse stage functions; move orchestration | Preserves the real workflow without importing infrastructure ownership. |
| `CAP-RES-021` | External research-feed helpers | `V1-CAP-RESEARCH-030`, `031`; `V1-WF-RESEARCH-009`; `V1-ISSUE-RESEARCH-013` | `V2-FR-RES-TOOL-001`–`012`; network NFRs | Direct ForexFactory coupling is unverified and brittle; provider ownership and contracts are unresolved. | **Defer** | Exclude providers and news/calendar parsing from the initial rebuild; later add optional adapters only after a confirmed research-evidence workflow. | Do not migrate initially | Avoids significant unproven network complexity. |
| `CAP-RES-022` | Research hypothesis and evidence guardrails | `V1-CAP-RESEARCH-033`; `V1-WF-RESEARCH-009` | `V2-FR-RES-TOOL-026`–`033` | V1 functions are dynamically exposed but no caller is confirmed; several checks overlap validation/leakage/snapshots. | **Defer** | Keep sample-size and lookahead checks inside validation; postpone autonomous hypothesis/evidence tooling until an agent workflow and contract exist. | Partial merge; remainder deferred | Prevents a disconnected agent-facing layer. |
| `CAP-RES-023` | Shared Analytics and Indicator consumption | `V1-CAP-RESEARCH-006`, `032`, `035`; `V1-ISSUE-RESEARCH-005` | `V2-FR-RES-COMPAT-001`–`008`; duplicated helper requirements | V1 re-exports and reimplements cross-domain calculations. | **Remove** | Research may call documented Analytics/Indicator contracts but shall not re-export or duplicate their public APIs. | Replace imports; remove compatibility facade | Restores ownership and reduces formula drift. |


## 5. V1 Disposition Register

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
| --- | --- | --- | --- | --- | --- | --- |
| `V1-CAP-RESEARCH-001` | Canonical research dataset contracts | `data/models.py` | Essential; usage: Used | **Modify** | contracts + data | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-002` | Data quality validation | `validate_dataset` | Essential; usage: Used | **Modify** | data quality | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-003` | Configurable data cleaning | `clean_dataset` | Essential; usage: Used | **Modify** | data preparation | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-004` | Research data enrichment | `enrich_dataset` | Essential; usage: Used | **Modify** | data preparation | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-005` | Provider-to-prepared-data orchestration | `prepare_research_dataset` | Essential; usage: Used | **Split** | data boundary + data preparation | Verify all callers can pass an in-memory canonical frame plus source metadata before removing provider-fetch logic from Research. |
| `V1-CAP-RESEARCH-006` | Flat numerical feature library | `features/calculations.py` | Supporting; usage: Used internally | **Merge** | features | Verify formula compatibility and migrate callers before deleting duplicate functions. |
| `V1-CAP-RESEARCH-007` | Versioned feature pipeline | `FeaturePipeline` | Essential; usage: Used | **Split** | features + modeling | Verify no dynamic caller depends on `compute_incremental` before exclusion. |
| `V1-CAP-RESEARCH-008` | Leakage/time-split/masking helpers | `features/leakage.py` | Useful/Questionable; usage: Possibly used | **Modify** | leakage + artifacts | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-009` | Core market metric profile | `core_metrics/*` | Essential; usage: Used | **Modify** | metrics | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-010` | Statistical null baselines | `null_models.py`, `eds_null_models.py` | Essential; usage: Used | **Modify** | statistics + studies | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-011` | Mean-reversion edge detector | `run_eds_mean_reversion` | Essential; usage: Used | **Modify** | studies | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-012` | Trend-persistence edge detector | `run_eds_trend_persistence` | Essential; usage: Used | **Modify** | studies | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-013` | Session breakout/fade edge detector | `run_eds_session` | Essential; usage: Used | **Modify** | studies + seasonality | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-014` | Edge classification | `classify_symbol` | Useful; usage: Used | **Modify** | studies classification | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-015` | Seasonality and opportunity analysis | `run_seasonality` | Essential; usage: Used | **Modify** | seasonality | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-016` | Market-structure profile | `build_market_structure_profile` | Essential; usage: Used | **Split** | market_structure | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-017` | Market-structure strategy fit | `build_strategy_fit` | Useful; usage: Used internally | **Modify** | market_structure strategy fit | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-018` | Stability and parameter robustness | stability/robustness builders | Useful; usage: Used | **Modify** | market_structure quality | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-019` | Forward-outcome validation | validation module | Useful; usage: Used | **Modify** | market_structure validation | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-020` | Verdict and metric calibration | three calibration modules | Useful; usage: Used | **Merge** | market_structure calibration | Verify route callers and persisted payload compatibility before removing separate modules. |
| `V1-CAP-RESEARCH-021` | Unsupervised feature construction | `build_market_regime_feature_frame` | Essential; usage: Used | **Modify** | modeling features | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-022` | PCA and K-Means modeling | `run_pca`, `cluster_feature_space` | Essential; usage: Used | **Modify** | modeling | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-023` | Unsupervised insight report | modeling insights/service | Essential; usage: Used | **Modify** | modeling insights | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-024` | Advisory cluster-based signal suppression | `adapt_signals_by_cluster` | Questionable; usage: Possibly used | **Defer** | none in initial rebuild | Verify no dynamic caller and define an out-of-sample advisory workflow before reintroduction. |
| `V1-CAP-RESEARCH-025` | Deterministic Edge Lab scorecard | `build_edge_lab_scorecard_report` | Essential; usage: Used | **Modify** | profiles/scorecard | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-026` | Full profile automation/caching/scheduling | research outputs orchestrated by `app/api/routes/edge.py` | Essential; usage: Used | **Split** | research stages + external orchestration | Cross-domain alignment must confirm the owner of cache/scheduler/database operations before moving code. |
| `V1-CAP-RESEARCH-027` | EDS Markdown/JSON reports | `reporting.py` | Useful; usage: Possibly used | **Merge** | profiles/reporting | Verify manual/dynamic consumers before deleting legacy entry points. |
| `V1-CAP-RESEARCH-028` | Profile/dashboard/comparison reports | `profile_reporting.py` | Useful; usage: Possibly used | **Merge** | profiles/reporting | Verify any UI imports and preserve output schema during migration. |
| `V1-CAP-RESEARCH-029` | Profile snapshot normalization | `build_edge_profile_snapshot` | Questionable; usage: Possibly used | **Merge** | profiles/snapshot | Confirm database schema and API payload migration before deleting the bypassed helper or route assembly. |
| `V1-CAP-RESEARCH-030` | Standardized web research fetch tools | four ForexFactory functions | Questionable; usage: Possibly used | **Defer** | future optional providers | Verify no dynamic agent caller; require an approved provider contract before reintroduction. |
| `V1-CAP-RESEARCH-031` | Standardized news/event interpretation tools | six standard tools | Useful if connected; usage: Possibly used | **Defer** | future external-evidence capability | Verify caller and approve external-evidence workflow/provider schema. |
| `V1-CAP-RESEARCH-032` | Standardized market calculation/detection tools | 13 standard tools | Questionable; usage: Possibly used | **Remove** | existing final capabilities | Complete dynamic-caller search and provide compatibility redirects before deletion. |
| `V1-CAP-RESEARCH-033` | Hypothesis and evidence guardrails | nine standard tools | Useful if connected; usage: Possibly used | **Defer** | future hypothesis/evidence workflow | Confirm agent workflow and approve a versioned evidence contract before implementation. |
| `V1-CAP-RESEARCH-034` | Dynamic package/service symbol resolution | package facade and `_common.py` | Supporting; usage: Used | **Modify** | package API registry | Not applicable; behavior is retained or refactored. |
| `V1-CAP-RESEARCH-035` | Analytics and validator convenience re-exports | root package facade | Questionable; usage: Possibly used | **Remove** | cross-domain direct dependencies | Search external imports and provide a deprecation window before deleting convenience exports. |


## 6. V2 Requirement Disposition Register

Every explicit V2 functional and non-functional checkbox, ownership/API statement, listed edge case, required test/clarification, and acceptance note is dispositioned below. Implementation-heavy proposals are accepted only to the extent stated in **Final requirement direction**.

### 6.1 4.1 Configuration and contracts

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-CFG-001` | `create_config` shall create an Edge Lab configuration object with common defaults for research workflows. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-002` | `DataConfig` shall describe source, symbol, timeframe, and date-range data inputs for research workflows. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-003` | `SessionConfig` shall describe trading-session windows and related session settings. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-004` | `BootstrapConfig` shall describe bootstrap resampling settings. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-005` | `PermutationConfig` shall describe permutation-test settings. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-006` | `NullModelsConfig` shall describe null-model settings and acceptance criteria. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-007` | `MeanReversionConfig` shall describe mean-reversion edge-discovery settings. | **Keep** | Retain this behavior in the versioned contracts/configuration capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-CFG-008` | `TrendPersistenceConfig` shall describe trend-persistence edge-discovery settings. | **Keep** | Retain this behavior in the versioned contracts/configuration capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-CFG-009` | `MarketStructureConfig` shall describe market-structure research settings. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-010` | `SessionEdgeConfig` shall describe session-edge research settings. | **Keep** | Retain this behavior in the versioned contracts/configuration capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-CFG-011` | `EdgeLabConfig` shall aggregate the module's research configuration sections into one workflow-level configuration. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-012` | `TradeSample` shall represent a normalized trade sample for edge-result reporting. | **Keep** | Retain this behavior in the versioned contracts/configuration capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-CFG-013` | `EdgeStats` shall represent summary statistics for an edge result. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-014` | `EdgeResult` shall represent a complete edge-study result suitable for summaries and reports. | **Modify** | Retain the behavioral intent in the versioned contracts/configuration capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-CFG-015` | `research_modeling_module` shall return the research modeling service module through the shared lazy-resolution utility. | **Reject** | Do not expose a public module-returning helper; use the explicit lazy registry internally. | No workflow needs a function that returns a Python module, and it expands the public surface without business value. |
| `V2-FR-RES-CFG-016` | Each public export in `app.services.research.__all__` shall have a documented contract specifying API status, input types, required fields, output type, error behavior, side effects, determinism guarantees, network/heavy dependency status, and stability level. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-017` | Core model contracts shall define required fields, optional fields, schema versions, validation behavior, serialization behavior, and example payloads for `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, `UnsupervisedInsightReport`, and report payloads. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-018` | The module shall define a canonical research error taxonomy covering validation errors, configuration errors, insufficient-data errors, statistical-invalidity errors, external-provider errors, serialization errors, resource-limit errors, and permission errors. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-019` | Public library functions shall either raise typed research exceptions or return structured result objects with warnings according to their documented contract; standard research tools shall return errors through the standard HaruQuant envelope. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-020` | Each public callable contract shall explicitly choose one failure pattern: typed exception, structured result with warnings/errors, or standard research envelope. Mixed behavior is not allowed unless every branch is documented. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-021` | The standard research envelope shall define at least `status`, `data`, `errors`, `warnings`, `audit`, `side_effect`, `approval_required`, `dry_run`, `environment`, `risk_level`, and `timing`. | **Defer** | Define the envelope only when the deferred agent/network helper slice is approved. | The deterministic library slice should use typed exceptions and structured result models; a universal envelope would add premature complexity. |
| `V2-FR-RES-CFG-022` | Standard research envelope `errors` and `warnings` shall use machine-readable codes, human-readable messages, optional field paths, severity, retryability, and bounded details. | **Defer** | Defer detailed envelope error/warning entries with the envelope-backed helper slice. | Useful only after an envelope-returning public capability is approved. |
| `V2-FR-RES-CFG-023` | Standard research envelope `audit` shall include request ID, correlation ID where available, tool/capability name, schema version, source references where applicable, created-at timestamp, and redaction/provenance metadata. | **Defer** | Defer envelope audit fields with the envelope-backed helper slice. | Core reproducibility metadata remains required in result/artifact contracts. |
| `V2-FR-RES-CFG-024` | Standard research envelope schema must be frozen for the approved first implementation slice before any network-backed, standard helper, evidence-pack, or agent-facing research helper is implemented. | **Modify** | Freeze the envelope before implementing any future network-backed or agent-facing helper, not before the deterministic first slice. | The dependency gate is valid but is attached to the wrong initial slice. |
| `V2-FR-RES-CFG-025` | Each public callable in the approved implementation slice shall have a behavior/error table that maps invalid input, insufficient data, unsupported config, provider unavailable, rate limit, serialization failure, resource limit, and permission failure to one exact typed exception, structured result warning/error, or standard envelope error. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-026` | Provisional insufficient-sample behavior: research calculations should fail with a typed validation error or standard-envelope error code such as `ERR_INSUFFICIENT_SAMPLES` when the approved minimum sample size is not met; final code names and thresholds remain pending owner/architect approval. | **Open Decision** | Owner must approve error code names and per-capability minimum samples; use one typed insufficient-data family meanwhile in design only. | Thresholds are statistical policy and cannot be inferred safely. |
| `V2-FR-RES-CFG-027` | The first implementation slice shall be explicitly approved before Builder handoff; proposed initial slice is data preparation plus core metrics unless the owner approves a different slice. | **Open Decision** | Approve the first slice before Builder handoff; recommended slice is contracts/errors + data preparation + leakage foundations + core metrics. | The V2 proposal names data/core only, but leakage and error foundations are prerequisites. |
| `V2-FR-RES-CFG-028` | A contract-first checklist shall block coding until every public callable in the approved slice has input/output types, error model, determinism guarantee, side-effect classification, envelope/result shape, examples, and mapped tests. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-CFG-029` | The module glossary shall define `Edge Lab`, `null baseline`, `profile snapshot`, `research envelope`, `advisory evidence`, `leakage report`, and `research artifact`. | **Add** | Add this behavior to the versioned contracts/configuration capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.2 4.2 Data preparation, cleaning, validation, and enrichment

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-DATA-001` | `CanonicalOHLCVSSchema` shall define the canonical research dataset schema for OHLCV data with spread support. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-002` | `DatasetIssue` shall represent a detected dataset quality issue. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-003` | `CleaningAction` shall represent a cleaning action applied to research data. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-004` | `DataQualityReportModel` shall summarize validation issues and cleaning actions for a dataset. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-005` | `PreparedDataset` shall carry cleaned, validated, enriched data with its quality report and metadata. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-006` | `CleaningConfig` shall describe data-cleaning behavior for timezone normalization, missing bars, non-trading periods, and spread anomalies. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-007` | `CleaningConfig` shall define `missing_bar_strategy` with approved values such as `drop`, `forward_fill`, `interpolate`, and `none`, with deterministic behavior documented for each value. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-008` | `CleaningConfig.missing_bar_strategy` default must be owner-approved before implementation. No Builder may infer a default or silently fill/drop bars without an approved default and explicit quality-report action. | **Open Decision** | Owner must select the default missing-bar strategy; no silent fill/drop is allowed. | Different instruments and providers require an explicit policy decision. |
| `V2-FR-RES-DATA-009` | `CleaningConfig` shall define `non_trading_period_strategy` with approved values and shall document weekend, holiday, synthetic-bar, and provider-gap behavior. | **Open Decision** | Approve allowed non-trading-period strategies and the default in coordination with Data/session policy. | Weekend, holiday, and synthetic-bar treatment affects multiple domains. |
| `V2-FR-RES-DATA-010` | `clean_dataset` shall normalize timestamps to the configured timezone, resolve duplicate or non-monotonic timestamps according to `CleaningConfig`, apply configured missing-bar and non-trading-period handling, detect spread anomalies, and return both cleaned data and a `DataQualityReportModel` containing machine-readable cleaning actions and unresolved warnings. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-011` | `EnrichmentConfig` shall describe enrichment settings for pip metadata, bar geometry, returns, labels, calendar fields, and sessions. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-012` | `enrich_dataset` shall add research features such as pip metadata, bar geometry, return labels, calendar fields, and session fields. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-013` | `validate_dataset` shall validate schema, continuity, OHLC consistency, duplicate timestamps, spread quality, and volume fields while distinguishing fatal validation errors from warnings through machine-readable issue codes. | **Modify** | Retain the behavioral intent in the deterministic dataset-preparation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-DATA-014` | `prepare_research_dataset` shall accept either in-memory raw OHLCV/OHLCVS data or a configured research data source, apply cleaning, validation, and enrichment in deterministic order, and return a `PreparedDataset` containing prepared data, metadata, and a quality report. It shall fail with a typed validation or configuration error when fatal issues prevent safe research use. | **Modify** | Accept in-memory canonical data plus source metadata. Provider acquisition remains outside Research. | This preserves preparation behavior while preventing Research from owning broker/provider lifecycle. |
| `V2-FR-RES-DATA-015` | `DataSource` shall represent the shared data-source descriptor used by research dataset validation. | **Reject** | Use the shared Data-domain descriptor at the boundary; do not re-export it from Research. | Compatibility re-exports obscure ownership. |
| `V2-FR-RES-DATA-016` | `OHLCVSchema` shall represent the shared OHLCV schema descriptor used by research dataset validation. | **Reject** | Use the shared schema contract at the boundary; do not re-export it from Research. | Research owns its canonical prepared schema, not the Data-domain public API. |


### 6.3 4.3 Feature calculations and market features

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-FEAT-001` | `log_returns` shall compute log returns from close prices. | **Keep** | Retain this behavior in the research feature capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-FEAT-002` | `simple_returns` shall compute arithmetic returns from close prices. | **Keep** | Retain this behavior in the research feature capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-FEAT-003` | `sma` shall compute simple moving averages over a configured window. | **Merge** | Consume the shared SMA implementation; no duplicate stable Research `sma` API. | Common indicator behavior belongs to Indicators. |
| `V2-FR-RES-FEAT-004` | `ema` shall compute exponential moving averages over a configured span. | **Merge** | Consume the shared EMA implementation; no duplicate stable Research `ema` API. | Common indicator behavior belongs to Indicators. |
| `V2-FR-RES-FEAT-005` | `std` shall compute rolling standard deviation over a configured window. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-006` | `zscore` shall compute a close-price z-score relative to a moving average and standard deviation. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-007` | `percent_rank` shall compute rolling percentile rank values. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-008` | `atr` shall compute Average True Range. | **Merge** | Consume shared ATR and expose only research-specific derived evidence where required. | Avoid duplicate formula stacks. |
| `V2-FR-RES-FEAT-009` | `atr_percent` shall compute ATR as a percentage of close price. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-010` | `bollinger_bands` shall compute Bollinger-style upper, middle, and lower bands. | **Merge** | Consume shared Bollinger-band calculations. | Avoid duplicate formula stacks. |
| `V2-FR-RES-FEAT-011` | `bb_width` shall compute Bollinger Band width. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-012` | `bb_percent_b` shall compute Bollinger Band percent-B. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-013` | `rolling_percentile_rank` shall compute rolling percentile rank for a supplied series. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-014` | `rsi` shall compute Relative Strength Index. | **Merge** | Consume shared RSI. | Avoid duplicate formula stacks. |
| `V2-FR-RES-FEAT-015` | `rate_of_change` shall compute rate of change as a momentum measure. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-016` | `momentum` shall compute simple price-difference momentum. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-017` | `donchian_channel` shall compute Donchian breakout levels. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-018` | `hurst_exponent` shall estimate Hurst exponent for mean-reversion versus trend detection. | **Keep** | Retain this behavior in the research feature capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-FEAT-019` | `rolling_hurst` shall compute Hurst exponent over rolling windows. | **Keep** | Retain this behavior in the research feature capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-FEAT-020` | `pivot_points` shall compute pivot, support, and resistance levels. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-021` | `adr` shall compute Average Daily Range. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-022` | `forward_returns` shall compute horizon-aligned forward log returns. | **Modify** | Keep one canonical research forward-return function with explicit horizon, log/simple mode, output label, and leakage metadata. | Resolves overlap with modeling `compute_forward_returns`. |
| `V2-FR-RES-FEAT-023` | `forward_max_favorable_excursion` shall compute maximum favorable price excursion over a forward horizon. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-024` | `forward_max_adverse_excursion` shall compute maximum adverse price excursion over a forward horizon. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-025` | `detect_volatility_regime` shall classify volatility regime using ATR percentile or equivalent volatility evidence. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-026` | `detect_trend_regime` shall classify trend regime from moving-average relationships. | **Merge** | Preserve the useful behavior by merging it into the research feature capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-FEAT-027` | `build_market_regime_feature_frame` shall build timestamp-aligned feature rows for PCA and clustering regime research. | **Modify** | Retain the behavioral intent in the research feature capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-FEAT-028` | Feature functions shall define warm-up-period behavior, NaN handling, minimum window behavior, numeric precision expectations, and input mutation behavior. | **Add** | Add this behavior to the research feature capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-FEAT-029` | Forward-looking feature functions shall clearly label forward columns as research-only and shall be detectable by leakage checks. | **Add** | Add this behavior to the research feature capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.4 4.4 Leakage controls and artifact masking

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-LEAK-001` | `TimeSplitResult` shall represent deterministic chronological train, validation, and test partitions. | **Keep** | Retain this behavior in the leakage and artifact-safety capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-LEAK-002` | `LeakageReport` shall define `suspected_columns`, `severity`, `evidence`, `recommendation`, `allowed_forward_columns`, `target_column`, and request/source metadata. | **Add** | Add this behavior to the leakage and artifact-safety capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-LEAK-003` | `validate_no_lookahead_features` shall inspect declared feature metadata, column naming conventions, target/horizon columns, and configured allowed-forward columns, then return a structured leakage report identifying suspected lookahead fields, severity, evidence, and recommended action without mutating the input frame. | **Modify** | Retain the behavioral intent in the leakage and artifact-safety capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-LEAK-004` | `enforce_time_split` shall enforce deterministic chronological train, validation, and test splits. | **Keep** | Retain this behavior in the leakage and artifact-safety capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-LEAK-005` | `mask_research_artifact` shall remove or redact sensitive fields from research artifacts before persistence or sharing. | **Modify** | Retain the behavioral intent in the leakage and artifact-safety capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-LEAK-006` | `dump_masked_research_json` shall serialize a masked research artifact to JSON. | **Modify** | Retain the behavioral intent in the leakage and artifact-safety capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |


### 6.5 4.5 Core metrics

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-METRIC-001` | `MetricValue` shall represent one normalized metric value with metadata. | **Modify** | Retain the behavioral intent in the core-metric profile capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-METRIC-002` | `MetricContext` shall provide the dataset and metadata needed by metric calculators. | **Modify** | Retain the behavioral intent in the core-metric profile capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-METRIC-003` | `MetricCalculator` shall define the calculator interface for research core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-004` | `MetricRegistry` shall register and resolve named metric calculators. | **Modify** | Keep a small registry class because it owns calculator membership; reject global mutable defaults. | State ownership justifies the class, but module-level mutation does not. |
| `V2-FR-RES-METRIC-005` | `CoreMetricProfile` shall represent a normalized profile of core dataset metrics. | **Modify** | Retain the behavioral intent in the core-metric profile capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-METRIC-006` | `ReturnsCalculator` shall calculate return-related core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-007` | `RocCalculator` shall calculate rate-of-change core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-008` | `CandlesCalculator` shall calculate candle-geometry core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-009` | `RangesCalculator` shall calculate range-related core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-010` | `VolatilityCalculator` shall calculate volatility core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-011` | `SpreadCalculator` shall calculate spread-quality core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-012` | `VolumeActivityCalculator` shall calculate volume or activity core metrics. | **Keep** | Retain this behavior in the core-metric profile capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-METRIC-013` | `build_default_registry` shall build the default registry of research metric calculators. | **Modify** | Retain the behavioral intent in the core-metric profile capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-METRIC-014` | `build_core_metric_profile` shall build a normalized core metric profile from a prepared dataset. | **Modify** | Retain the behavioral intent in the core-metric profile capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-METRIC-015` | Metric profile output shall define units, sample size, source dataset identity, warnings, undefined-value behavior, and reproducibility metadata. | **Add** | Add this behavior to the core-metric profile capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.6 4.6 Edge discovery studies

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-EDS-001` | `run_eds_null_baseline` shall establish null-model baselines for edge-discovery studies. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-002` | `compare_to_null` shall compare observed expectancy or performance against a null distribution. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-003` | `get_acceptance_criteria` shall extract acceptance criteria from a null baseline. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-004` | `run_eds_mean_reversion` shall evaluate a mean-reversion detector based on compression and z-score fade behavior. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-005` | `run_eds_trend_persistence` shall evaluate a trend-persistence detector based on high-ATR breakout follow-through behavior. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-006` | `compute_session_statistics` shall calculate detailed statistics for a configured trading session. | **Merge** | Keep session-statistics behavior as an internal part of the session study, not a separate stable public capability. | It is a helper within the EDS session workflow. |
| `V2-FR-RES-EDS-007` | `run_session_breakout_strategy` shall evaluate an opening-range breakout strategy for a session. | **Merge** | Keep breakout evaluation inside the focused session-study capability. | No separate public strategy runtime is needed. |
| `V2-FR-RES-EDS-008` | `run_session_fade_strategy` shall evaluate a mean-reversion fade strategy within a session. | **Merge** | Keep fade evaluation inside the focused session-study capability. | No separate public strategy runtime is needed. |
| `V2-FR-RES-EDS-009` | `run_eds_session` shall run session-edge discovery across configured session studies. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-010` | `EdgeClass` shall represent the classification category assigned to an edge. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-011` | `EdgeSummary` shall summarize mean-reversion and trend-persistence evidence for a symbol. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-012` | `ClassificationResult` shall represent the result of classifying a symbol's edge profile. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-013` | `classify_symbol` shall classify a symbol based on mean-reversion and trend-persistence evidence. | **Modify** | Retain the behavioral intent in the edge-study capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-EDS-014` | Edge-discovery results shall include sample size, evaluated rule/config, source dataset identity, split identifiers, uncertainty metadata, warnings, and an advisory-only disclaimer. | **Add** | Add this behavior to the edge-study capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.7 4.7 Null models and statistical validation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-STAT-001` | `block_bootstrap_ci` shall compute a confidence interval using block bootstrap resampling. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-002` | `block_bootstrap_distribution` shall generate a bootstrap distribution for a statistic. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-003` | `permutation_test` shall compute a permutation-test p-value. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-004` | `random_entry_null` shall generate a null distribution from random entries in log-return space. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-005` | `r_space_null` shall generate a null distribution in R-multiple space. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-006` | `session_randomized_null` shall generate a null distribution by shuffling entries within the same session. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-007` | `shuffle_returns_null` shall generate a null distribution by shuffling return blocks. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-008` | `benjamini_hochberg` shall apply Benjamini-Hochberg false-discovery-rate correction. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-009` | `holm_bonferroni` shall apply Holm-Bonferroni multiple-comparison correction. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-010` | `compute_null_percentile` shall compute the percentile of an observed value within a null distribution. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-011` | `null_distribution_stats` shall compute summary statistics for a null distribution. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-012` | `exceeds_null_threshold` shall determine whether an observed value exceeds a configured null-distribution threshold. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STAT-013` | Null-model functions shall define behavior for invalid sample sizes, non-finite statistics, empty distributions, random seeds, replacement/block settings, and multiple-comparison correction applicability. | **Add** | Add this behavior to the statistical validation capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-STAT-014` | Null-model behavior/error tables shall dictate exact outcomes for invalid sample sizes, non-finite statistics, empty distributions, invalid random seeds, invalid replacement/block settings, and inapplicable multiple-comparison corrections; these cases may not be left to Builder interpretation. | **Add** | Add this behavior to the statistical validation capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-STAT-015` | Bootstrap, permutation, and null-generation functions shall accept an explicit `seed` parameter or source one from a documented configuration object; returned results shall record the effective seed. | **Modify** | Retain the behavioral intent in the statistical validation capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |


### 6.8 4.8 Market structure profiles, calibration, validation, and fit

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-STRUCT-001` | `TrendSwingPoint` shall represent a detected swing point used in market-structure analysis. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-002` | `TrendLeg` shall represent a directional leg between swing points. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-003` | `TrendScoreRow` shall represent one market-structure score row. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-004` | `MarketStructureProfile` shall represent a reproducible directional structure profile. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-005` | `build_market_structure_profile` shall build a directional market-structure profile from a prepared dataset. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-006` | `build_market_structure_research_profile` shall build a `MarketStructureProfile` plus configured research-only validation layers, including calibration evidence, stability summary, robustness summary, warnings, runtime metadata, and quality-adjusted confidence fields. | **Merge** | Use one profile builder plus an explicit opt-in quality evaluation; do not maintain a second overlapping builder. | The V1 research builder has no confirmed caller and duplicates the base path. |
| `V2-FR-RES-STRUCT-007` | `MarketStructureCalibrationCandidate` shall represent one calibration candidate for market-structure classification. | **Merge** | Preserve the useful behavior by merging it into the market-structure capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-STRUCT-008` | `classify_with_candidate` shall classify market structure using one calibration candidate. | **Merge** | Preserve the useful behavior by merging it into the market-structure capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-STRUCT-009` | `build_calibration_grid` shall build candidate parameter grids for market-structure calibration. | **Merge** | Preserve the useful behavior by merging it into the market-structure capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-STRUCT-010` | `evaluate_calibration_candidates` shall evaluate market-structure calibration candidates against realized evidence. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-011` | `MarketStructureMetricCalibrationCandidate` shall represent one metric-calibration candidate. | **Merge** | Preserve the useful behavior by merging it into the market-structure capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-STRUCT-012` | `build_metric_calibration_grid` shall build candidate grids for market-structure metric calibration. | **Merge** | Preserve the useful behavior by merging it into the market-structure capability; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-STRUCT-013` | `evaluate_metric_calibration_candidates` shall evaluate metric-calibration candidates against target behavior. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-014` | `evaluate_profile_calibration` shall evaluate profile-level calibration behavior. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-015` | `timeframe_bucket` shall map a timeframe into a market-structure profile bucket. | **Merge** | Treat timeframe bucketing as private profile-policy logic. | It is implementation support, not a standalone public capability. |
| `V2-FR-RES-STRUCT-016` | `symbol_class` shall map a symbol into a market-structure symbol class. | **Merge** | Treat symbol classification as private profile-policy logic. | It is implementation support, not a standalone public capability. |
| `V2-FR-RES-STRUCT-017` | `resolve_market_structure_profile` shall resolve the applicable market-structure profile for a symbol and timeframe. | **Merge** | Resolve profile policy through one configuration capability; keep the helper internal. | Reduces public surface and hard-coded policy exposure. |
| `V2-FR-RES-STRUCT-018` | `resolve_market_structure_profile_overrides` shall resolve profile overrides for a symbol, timeframe, or profile class. | **Merge** | Resolve overrides from versioned configuration rather than mutable module tables. | Hard-coded mutable overrides are difficult to reproduce. |
| `V2-FR-RES-STRUCT-019` | `confidence_bucket` shall convert validation evidence into a confidence bucket. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-020` | `label_realized_market_behavior` shall classify realized future behavior as trend, reversion, or mixed. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-021` | `build_validation_summary` shall summarize market-structure validation evidence. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-022` | `build_market_structure_stability_report` shall report stability of market-structure behavior across samples or windows. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-023` | `build_market_structure_robustness_report` shall report robustness of market-structure behavior across parameter or data variations. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-024` | `build_strategy_fit` shall assess advisory strategy-fit evidence from market-structure research and shall not approve strategy promotion, mutate strategy runtime state, or authorize execution changes. | **Modify** | Retain the behavioral intent in the market-structure capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-STRUCT-025` | Market-structure calibration outputs shall include candidate parameters, ranking criteria, validation window, stability evidence, and warnings for unstable rankings. | **Add** | Add this behavior to the market-structure capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.9 4.9 Unsupervised modeling and insight generation

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-UNSUP-001` | `UnsupervisedResearchConfig` shall describe unsupervised research settings. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-002` | `UnsupervisedResearchConfig` shall include a `seed` field used by non-deterministic algorithms. | **Add** | Add this behavior to the unsupervised modeling capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-UNSUP-003` | `UnsupervisedResearchRequest` shall represent one unsupervised research request. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-004` | `UnsupervisedResearchResult` shall represent a complete unsupervised research result. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-005` | `UnsupervisedResearchService` shall orchestrate unsupervised research workflows. | **Reject** | Replace the stateless `UnsupervisedResearchService` class with a public workflow function. | The class owns no state, dependency lifecycle, or resource that justifies a service layer. |
| `V2-FR-RES-UNSUP-006` | `FeatureSetFrame` shall represent the feature frame used by unsupervised modeling. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-007` | `PcaModelResult` shall represent PCA scores, loadings, and explained variance. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-008` | `ClusterModelResult` shall represent clustering labels and cluster metadata. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-009` | `run_pca` shall run PCA on numeric feature columns and return component scores and loadings. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-010` | `cluster_feature_space` shall cluster numeric feature rows using deterministic K-Means labels. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-011` | `cluster_feature_space` shall consume `UnsupervisedResearchConfig.seed` or an explicit seed parameter so K-Means output is reproducible for fixed inputs and dependency versions. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-012` | `attach_cluster_labels` shall attach cluster labels to a feature frame without mutating the input. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-013` | `InvestmentDataSummary` shall represent descriptive statistics for investment data. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-014` | `PcaRiskFactor` shall represent an interpreted PCA loading or risk factor. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-015` | `ClusterOutperformance` shall represent forward-return evidence by cluster. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-016` | `SignalAdaptationResult` shall represent signal-suppression or signal-adaptation recommendations by cluster. | **Defer** | Exclude signal-adaptation result contracts from the initial rebuild. | No confirmed caller and current evidence is in-sample. |
| `V2-FR-RES-UNSUP-017` | `UnsupervisedInsightReport` shall represent a complete unsupervised insight report for trading workflows. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-018` | `summarize_investment_data` shall return key descriptive statistics for investment data. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-019` | `identify_pca_risk_factors` shall extract the largest PCA loadings as interpretable risk factors. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-020` | `compute_forward_returns` shall compute horizon-aligned forward returns from a price column. | **Merge** | Merge with the canonical research `forward_returns` implementation. | Two public functions for the same behavior are unnecessary. |
| `V2-FR-RES-UNSUP-021` | `analyze_cluster_outperformance` shall score clusters by future returns and assign semantic regime names. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-022` | `adapt_signals_by_cluster` shall produce advisory signal-adaptation recommendations identifying clusters where forward-return evidence is weak; it shall not mutate strategy runtime state, block live entries, or authorize execution changes. | **Defer** | Defer until out-of-sample validation and Strategy/Risk advisory contracts are approved. | Prevents research output from becoming implicit execution control. |
| `V2-FR-RES-UNSUP-023` | `build_unsupervised_insight_report` shall build a complete unsupervised insight report for trading workflows. | **Modify** | Retain the behavioral intent in the unsupervised modeling capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-UNSUP-024` | Unsupervised modeling outputs shall include preprocessing metadata, selected feature columns, dropped columns, scaler behavior, seed, model parameters, and cluster/component diagnostics. | **Add** | Add this behavior to the unsupervised modeling capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.10 4.10 Session and seasonality

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-SEAS-001` | `active_sessions_for_hour` shall return the active trading sessions for a given hour. | **Modify** | Retain the behavioral intent in the session/seasonality capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-SEAS-002` | `session_label_for_hour` shall return the session label for a given hour. | **Modify** | Retain the behavioral intent in the session/seasonality capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-SEAS-003` | `session_hours_payload` shall return a machine-readable payload describing configured session hours. | **Modify** | Retain the behavioral intent in the session/seasonality capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-SEAS-004` | `tag_sessions` shall tag each market-data row with its trading session. | **Modify** | Retain the behavioral intent in the session/seasonality capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-SEAS-005` | `SeasonalityFilters` shall describe calendar, session, or symbol filters for seasonality analysis. | **Keep** | Retain this behavior in the session/seasonality capability, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-FR-RES-SEAS-006` | `run_seasonality` shall calculate seasonality statistics for the provided dataset and filters. | **Modify** | Retain the behavioral intent in the session/seasonality capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |


### 6.11 4.11 Research standard tools and evidence helpers

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-TOOL-001` | `fetch_forexfactory_news` shall retrieve ForexFactory news data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, and offline-test behavior, then return a standard research envelope containing status, normalized data, provider metadata, source timestamp, warnings, errors, and audit metadata. | **Defer** | Defer the provider capability; do not migrate direct ForexFactory fetching. | No active workflow is confirmed and provider contracts are unresolved. |
| `V2-FR-RES-TOOL-002` | `fetch_forexfactory_calendar` shall retrieve ForexFactory economic calendar data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope. | **Defer** | Defer the provider capability; do not migrate direct ForexFactory fetching. | No active workflow is confirmed and provider contracts are unresolved. |
| `V2-FR-RES-TOOL-003` | `fetch_forexfactory_sentiment` shall retrieve ForexFactory sentiment data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope. | **Defer** | Defer the provider capability; do not migrate direct ForexFactory fetching. | No active workflow is confirmed and provider contracts are unresolved. |
| `V2-FR-RES-TOOL-004` | `fetch_forexfactory_instrument_page` shall retrieve a symbol-specific ForexFactory page through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope. | **Defer** | Defer the provider capability; do not migrate direct ForexFactory fetching. | No active workflow is confirmed and provider contracts are unresolved. |
| `V2-FR-RES-TOOL-005` | ForexFactory and other external-feed helpers shall be optional-provider capabilities. Missing provider adapters shall return a deterministic provider-unavailable envelope or documented typed configuration error without breaking import or unrelated research workflows. | **Defer** | If later approved, providers must be optional and import-safe; no provider export exists in the initial surface. | Valid future constraint, not initial scope. |
| `V2-FR-RES-TOOL-006` | External-feed helpers shall handle HTTP 429 responses, including missing or invalid `Retry-After` headers, through deterministic rate-limit errors or warnings with bounded retry metadata. | **Defer** | Apply deterministic rate-limit handling only in a future approved provider adapter. | There is no current provider slice to implement. |
| `V2-FR-RES-TOOL-007` | `parse_news_items` shall normalize raw news items into structured research records. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-008` | `parse_calendar_events` shall normalize economic calendar events. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-009` | `parse_sentiment_snapshot` shall normalize sentiment-positioning snapshots. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-010` | `filter_events_by_symbol` shall filter calendar events by the currencies or instruments relevant to a symbol. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-011` | `classify_news_impact` shall classify the impact level of economic news. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-012` | `create_news_blackout_windows` shall create advisory research blackout-window recommendations around news events and shall not create live no-trade controls or mutate risk/execution policy. | **Defer** | Defer advisory blackout recommendations; live no-trade windows remain Risk-owned. | No active research-evidence workflow is confirmed. |
| `V2-FR-RES-TOOL-013` | `calculate_returns` shall calculate price returns for standard research tooling. | **Merge** | Use the canonical feature/core return calculation; remove the duplicate standard-tool wrapper. | Duplicate public APIs create formula drift. |
| `V2-FR-RES-TOOL-014` | `calculate_volatility` shall calculate rolling annualized volatility. | **Merge** | Use core metrics/Analytics volatility; remove the duplicate standard-tool wrapper. | Duplicate public APIs create formula drift. |
| `V2-FR-RES-TOOL-015` | `calculate_atr` shall calculate Average True Range. | **Merge** | Use shared ATR through Indicators; remove the duplicate standard-tool wrapper. | Duplicate public APIs create formula drift. |
| `V2-FR-RES-TOOL-016` | `calculate_adr` shall calculate Average Daily Range. | **Merge** | Use the canonical Research seasonality/feature ADR behavior; remove the duplicate wrapper. | Duplicate public APIs create formula drift. |
| `V2-FR-RES-TOOL-017` | `calculate_spread_statistics` shall calculate spread distribution statistics. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-018` | `calculate_session_statistics` shall calculate session return statistics. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-019` | `calculate_seasonality_statistics` shall calculate calendar seasonality statistics. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-020` | `calculate_regime_features` shall calculate regime feature rows. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-021` | `calculate_correlation_matrix` shall calculate a correlation matrix for research inputs. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-022` | `detect_trend_strength` shall detect trend strength from moving-average evidence. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-023` | `detect_market_regime` shall classify market regime from supplied research features. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-024` | `detect_mean_reversion_conditions` shall detect mean-reversion conditions. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-025` | `detect_breakout_conditions` shall detect breakout conditions. | **Merge** | Preserve the useful behavior by merging it into the standard-helper proposal; do not keep a separate overlapping public API. | The proposed behavior overlaps an existing capability and would create duplicate contracts. |
| `V2-FR-RES-TOOL-026` | `generate_research_hypothesis` shall generate a structured research hypothesis from inputs and evidence. | **Defer** | Defer automated hypothesis generation until an agent workflow and evidence contract are approved. | No caller is confirmed. |
| `V2-FR-RES-TOOL-027` | `score_research_hypothesis` shall score research evidence quality. | **Defer** | Defer standalone evidence scoring; the initial scorecard remains the approved scoring output. | Avoid competing scoring systems. |
| `V2-FR-RES-TOOL-028` | `check_sample_size` shall validate whether a sample is large enough for the intended research claim. | **Merge** | Merge sample-size validation into result/study contracts and the canonical insufficient-data policy. | A separate envelope tool is unnecessary. |
| `V2-FR-RES-TOOL-029` | `check_data_snooping_risk` shall assess data-snooping risk. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-030` | `check_lookahead_bias_risk` shall assess lookahead-bias risk. | **Merge** | Merge lookahead-risk assessment into the leakage capability. | Avoid duplicate safety checks. |
| `V2-FR-RES-TOOL-031` | `check_hypothesis_testability` shall assess whether a hypothesis is testable. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-032` | `check_contradictory_evidence` shall assess whether evidence contradicts the proposed hypothesis. | **Defer** | Exclude this behavior from the initial rebuild and document it as a future capability. | No confirmed initial workflow justifies the complexity or dependency. |
| `V2-FR-RES-TOOL-033` | `build_research_evidence_pack` shall build a structured research evidence pack containing source references, assumptions, warnings, and validation notes. | **Merge** | Merge evidence-pack output into the canonical versioned profile snapshot/report. | One evidence artifact is preferable to a parallel disconnected envelope. |


### 6.12 4.12 Reporting, profile snapshots, and scorecards

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-REPORT-001` | `result_to_markdown` shall convert an edge result into a Markdown report. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-002` | `result_to_summary` shall generate a concise summary dictionary from an edge result. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-003` | `save_markdown` shall persist an edge result report as Markdown and shall expose an `overwrite: bool` contract. | **Merge** | Merge into one safe artifact writer with format selection and overwrite policy. | Separate save functions duplicate path and atomicity logic. |
| `V2-FR-RES-REPORT-004` | `save_json` shall persist an edge result report as JSON and shall expose an `overwrite: bool` contract. | **Merge** | Merge into one safe artifact writer with format selection and overwrite policy. | Separate save functions duplicate path and atomicity logic. |
| `V2-FR-RES-REPORT-005` | `generate_multi_symbol_report` shall generate a combined report for multiple symbols. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-006` | `print_result_summary` shall print a concise result summary to console. | **Reject** | Do not include console printing in the stable library API; callers may print rendered summaries. | A print side effect is not a domain capability. |
| `V2-FR-RES-REPORT-007` | `build_edge_profile_snapshot` shall build a normalized snapshot payload from progressive Edge Lab tab results. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-008` | `build_profile_summary` shall build a concise dashboard-ready summary from one profile snapshot. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-009` | `build_dashboard_summary` shall build a UI or dashboard summary block from one profile snapshot. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-010` | `snapshot_report_json` shall build a machine-readable profile snapshot report. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-011` | `snapshot_report_markdown` shall render a human-readable profile snapshot report. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-012` | `comparison_report_markdown` shall render a Markdown comparison report from two profile snapshots. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-013` | `save_json_report` shall save one complete JSON profile report. | **Merge** | Merge JSON profile persistence into the safe artifact writer. | Centralizes path, masking, overwrite, and atomicity rules. |
| `V2-FR-RES-REPORT-014` | `save_markdown_report` shall save one complete Markdown profile report. | **Merge** | Merge Markdown profile persistence into the safe artifact writer. | Centralizes path, masking, overwrite, and atomicity rules. |
| `V2-FR-RES-REPORT-015` | `build_edge_lab_scorecard_report` shall build a deterministic backend scorecard report from progressive Edge Lab outputs. | **Modify** | Retain the behavioral intent in the profile/reporting capability, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-FR-RES-REPORT-016` | Report persistence functions shall define allowed output paths, overwrite behavior, atomic write behavior, encoding, masking behavior, permission-failure behavior, and return value. | **Add** | Add this behavior to the profile/reporting capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-FR-RES-REPORT-017` | Report persistence functions shall write to a temporary file and atomically rename where the platform supports it; unsupported atomic behavior shall be disclosed in the result metadata or typed error. | **Add** | Add this behavior to the profile/reporting capability as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.13 4.13 Analytics compatibility exports

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-FR-RES-COMPAT-001` | `calmar_ratio` shall expose the analytics Calmar ratio for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-002` | `expectancy` shall expose the analytics expectancy calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-003` | `max_drawdown` shall expose the analytics maximum drawdown calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-004` | `median_mae_mfe` shall expose the analytics median MAE/MFE calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-005` | `profit_factor` shall expose the analytics profit-factor calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-006` | `sharpe_ratio` shall expose the analytics Sharpe ratio calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-007` | `sortino_ratio` shall expose the analytics Sortino ratio calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |
| `V2-FR-RES-COMPAT-008` | `win_rate` shall expose the analytics win-rate calculation for research workflows. | **Reject** | Do not include this proposal in the final Research public API. | It adds no distinct domain behavior, duplicates another domain, or prescribes unnecessary structure. |


### 6.14 5. Non-Functional Requirements

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-NFR-RES-001` | The module shall be sandboxed and shall not place, modify, cancel, or route live orders. | **Keep** | Retain this behavior in the domain-wide non-functional contract, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-NFR-RES-002` | The module shall fail closed when a workflow attempts to mutate live trading state or bypass governance. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-003` | Research artifacts shall preserve source references, assumptions, warnings, and enough metadata to reproduce the result. | **Modify** | Retain the behavioral intent in the domain-wide non-functional contract, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-NFR-RES-004` | Persisted research artifacts shall include artifact schema version, module version, config hash, dataset identity or data hash, random seed, generated-at timestamp, timezone, source references, and dependency/version metadata required to reproduce the result. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-005` | Persisted research artifacts shall include SHA-256 hashes of the input dataset identity or canonical data snapshot and the effective configuration used to generate the artifact. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-006` | Research outputs shall clearly distinguish observations, assumptions, warnings, and validation evidence from approved trading decisions. | **Keep** | Retain this behavior in the domain-wide non-functional contract, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-NFR-RES-007` | Data preparation and feature pipelines shall avoid lookahead bias and shall support explicit chronological split validation. | **Modify** | Retain the behavioral intent in the domain-wide non-functional contract, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-NFR-RES-008` | Statistical results shall expose uncertainty where applicable, including p-values, confidence intervals, null percentiles, or comparable validation metadata. | **Keep** | Retain this behavior in the domain-wide non-functional contract, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-NFR-RES-009` | Multiple-comparison checks shall be available when evaluating many hypotheses or candidates. | **Keep** | Retain this behavior in the domain-wide non-functional contract, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-NFR-RES-010` | Public standard tools shall return the standard HaruQuant envelope containing status, tool metadata, request metadata, data, errors, warnings, and audit metadata. | **Defer** | Apply the shared envelope only to future approved envelope-backed helpers. | No standard/network helper is in the initial rebuild. |
| `V2-NFR-RES-011` | Standard tool envelopes shall include side-effect, approval-required, dry-run, environment, risk-level, and timing audit fields. | **Defer** | Defer envelope audit fields with the future helper slice. | Core result/artifact metadata remains mandatory. |
| `V2-NFR-RES-012` | The standard research envelope schema shall be versioned and referenced by every network-backed helper, standard helper, evidence-pack helper, and future agent-facing research tool. | **Defer** | Version the envelope before future agent/network helpers are implemented. | Not an initial deterministic-library requirement. |
| `V2-NFR-RES-013` | Network-backed research helpers shall be isolated from core deterministic calculations and shall be skippable in offline or heavy-environment tests. | **Defer** | Retain as a future provider constraint; no network helper ships initially. | Network isolation is valid but deferred with the capability. |
| `V2-NFR-RES-014` | Network-backed research helpers shall enforce configured timeout, retry, rate-limit, cache, stale-data, and provider-layout-change behavior and shall return partial or failed results only through the standard research envelope with warnings and audit metadata. | **Defer** | Retain as a future provider constraint; no network helper ships initially. | Timeout/retry/cache/layout policy is provider-specific and premature. |
| `V2-NFR-RES-015` | Serialization helpers shall support masked JSON or Markdown output without leaking sensitive source details. | **Modify** | Retain the behavioral intent in the domain-wide non-functional contract, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-NFR-RES-016` | Public exports shall remain unique and resolvable through the lazy namespace. | **Modify** | Use an explicit classified lazy export map with uniqueness tests. | V1 recursive resolution is too broad. |
| `V2-NFR-RES-017` | Seeded research workflows shall produce equivalent outputs for fixed input data, configuration, random seed, dependency versions, and artifact schema version. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-018` | The module shall avoid storing real secrets, credentials, private broker data, or unredacted private artifacts. | **Keep** | Retain this behavior in the domain-wide non-functional contract, with the existing proven semantics unless another approved row narrows them. | V1 already provides useful behavior and no contradictory V2 need requires replacement. |
| `V2-NFR-RES-019` | The module shall remain interoperable with analytics, optimization, risk, and execution modules only through documented public contracts. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-020` | Importing `app.services.research` shall not perform network calls, disk writes, provider initialization, credential reads, live trading state access, or heavy model execution. | **Modify** | Retain the behavioral intent in the domain-wide non-functional contract, but align it with the approved boundary, error, metadata, determinism, and minimal-API rules. | The behavior is valuable, but V1/V2 details require correction or simplification. |
| `V2-NFR-RES-021` | Report and artifact serialization shall prevent path traversal, accidental overwrite unless configured, and leakage of masked fields. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-022` | Long-running workflows shall expose duration metadata and shall support configured resource limits or fail with a typed resource-limit error. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-023` | `ResearchResourceLimits` shall define `max_duration_seconds`, `max_memory_mb`, `max_rows`, and behavior when a limit is exceeded. | **Modify** | Define bounded rows and duration now; treat memory as a platform-dependent measured guard rather than a portable hard guarantee. | Hard memory enforcement is not reliably portable in a pure library. |
| `V2-NFR-RES-024` | Before production Builder handoff, the owner shall approve measurable resource targets for the first implementation slice, including maximum rows, runtime budget, memory budget, and reference hardware. | **Open Decision** | Owner must approve concrete resource budgets and reference hardware before production claims. | The requirement is valid but unresolved. |
| `V2-NFR-RES-025` | Proposed benchmark placeholder: `prepare_research_dataset` should process up to 1,000,000 rows in no more than 30 seconds on approved reference hardware; this remains pending until owner approval. | **Reject** | Do not adopt the 1,000,000 rows/30 seconds target without measurement and owner approval. | It is explicitly a placeholder, not an approved requirement. |
| `V2-NFR-RES-026` | Until resource limits and reference hardware are approved, Research may not claim production-grade performance; oversized or long-running workflows must fail with a typed resource-limit error or standard-envelope resource-limit error instead of attempting unbounded work. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |
| `V2-NFR-RES-027` | The module shall emit structured warnings or logs for validation failures, dropped rows, masking actions, provider failures, statistical insufficiency, and partial report generation. | **Add** | Add this behavior to the domain-wide non-functional contract as a documented contract for the approved implementation slice. | The behavior is needed for safety, reproducibility, or integration and is not adequately present in V1. |


### 6.15 Boundary ownership

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-BND-RES-OWN-001` | Research configuration models for data preparation, bootstrap/permutation/null-model settings, market-structure settings, mean-reversion settings, trend-persistence settings, session-edge settings, and overall Edge Lab configuration. | **Modify** | Research owns research configuration contracts, excluding provider connection lifecycle. | Matches V1 value but needs boundary cleanup. |
| `V2-BND-RES-OWN-002` | Research-only data cleaning, enrichment, validation, preparation, and data-quality report models. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-003` | Research feature calculations for returns, moving averages, volatility, range, momentum, Bollinger-style statistics, Hurst statistics, pivot levels, forward returns, MAE/MFE, and simple regime labels. | **Modify** | Research owns research-specific features and may consume shared Indicator/Analytics formulas; it does not own duplicate generic indicator implementations. | V1 duplication is a confirmed structural problem. |
| `V2-BND-RES-OWN-004` | Leakage controls for chronological splits, lookahead validation, and masking of research artifacts before persistence. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-005` | Core metric calculator contracts, metric registry behavior, and normalized core metric profile creation. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-006` | Edge-discovery studies for mean reversion, trend persistence, session behavior, and null baselines. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-007` | Null-model generation, bootstrap distributions, permutation testing, multiple-comparison corrections, null percentiles, and null-threshold checks. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-008` | Market-structure profiles, calibration candidates, profile overrides, validation summaries, stability reports, robustness reports, and strategy-fit reports. | **Modify** | Research owns profile evidence and bounded validation/calibration, not unbounded automatic tuning. | V1 is useful but expensive and duplicated. |
| `V2-BND-RES-OWN-009` | Unsupervised research contracts, PCA outputs, clustering outputs, cluster labels, cluster outperformance analysis, PCA risk-factor summaries, signal adaptation results, and unsupervised insight reports. | **Modify** | Research owns PCA/clustering evidence; cluster signal adaptation is deferred. | Modeling is used, but adaptation is unverified and in-sample. |
| `V2-BND-RES-OWN-010` | Seasonality analysis filters and seasonality result generation. | **Keep** | Retain this ownership boundary in the final Research domain. | It matches demonstrated Research behavior and domain purpose. |
| `V2-BND-RES-OWN-011` | Research reporting, profile snapshots, dashboard summaries, scorecard reports, Markdown/JSON serialization, and multi-symbol reports. | **Modify** | Research owns snapshot/report construction and safe artifact rendering; external database orchestration remains outside. | V1 reporting/snapshot paths are fragmented. |
| `V2-BND-RES-OWN-012` | Standard research tool envelopes for external research helpers, including news/calendar parsing, research-hypothesis generation, evidence scoring, and evidence-pack construction. | **Defer** | Defer standard envelope-backed helper ownership until an agent/evidence workflow is approved. | No confirmed caller. |
| `V2-BND-RES-OWN-013` | Public lazy-export registry for research capabilities. | **Modify** | Research owns an explicit classified lazy export registry, not recursive discovery. | V1 facade is too broad. |
| `V2-BND-RES-OWN-014` | Optional external-feed helper contracts. External-feed helper exports may be absent or disabled when the corresponding provider adapter is not installed; importing `app.services.research` must not fail because of a missing optional adapter. | **Defer** | Defer optional external-feed contracts; Data retains production provider ownership. | Provider roadmap and caller are unresolved. |


### 6.16 Boundary exclusions

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-BND-RES-NOTOWN-001` | Live trading execution, broker adapters, order placement, order modification, order cancellation, reconciliation, or kill-switch controls. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-002` | Portfolio risk enforcement, position sizing, exposure limits, or final trade approval. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-003` | Strategy runtime orchestration or production signal execution. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-004` | Backtest engine ownership, production optimization orchestration, or analytics module ownership for reused analytics ratios. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-005` | Market-data provider contracts beyond research-ready input preparation and optional external research-feed helpers. | **Keep** | Research accepts research-ready data and source metadata; Data owns production provider contracts and acquisition. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-006` | Broad market-data provider adapter ownership. Research may own optional external-feed helper interfaces for research evidence only, but Data owns production market-data ingestion/provider contracts unless an explicit roadmap decision changes ownership. | **Keep** | Research accepts research-ready data and source metadata; Data owns production provider contracts and acquisition. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-007` | Persistent secrets, broker credentials, API credentials, Telegram/email credentials, or private production artifacts. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-008` | AI provider execution policy, model-provider governance, or unbounded autonomous research actions. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |
| `V2-BND-RES-NOTOWN-009` | Durable product, roadmap, or architecture decisions outside the active documentation set. | **Keep** | Retain this exclusion from Research ownership. | The responsibility belongs to another domain or system-level governance. |


### 6.17 Public API

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-API-RES-001` | Importable service namespace: `app.services.research`. | **Keep** | Keep `app.services.research` as the migration target unless pipeline step 05 approves a package move. | It is the operational V1 package and minimizes migration risk. |
| `V2-API-RES-002` | Lazy public exports declared through `app.services.research.__all__`. | **Modify** | Use explicit `__all__` plus an explicit classified lazy map; no recursive package scan. | V1 `__all__` and lazy surface disagree. |
| `V2-API-RES-003` | Standardized domain export metadata registered for the `research` tool category. | **Defer** | Defer agent tool-category registration until agent-facing helpers are approved. | No current registry/caller was confirmed. |
| `V2-API-RES-004` | Public configuration and model objects for research setup, data quality, core metrics, edge results, market structure, and unsupervised modeling. | **Modify** | Expose only approved stable contracts; keep internal-support models importable by module path but outside the stable facade. | V2 would otherwise preserve an unnecessarily broad surface. |
| `V2-API-RES-005` | Public functional API groups for data preparation, feature engineering, leakage checks, core metric profiling, edge discovery, null-model analysis, market-structure analysis, unsupervised modeling, seasonality, standard research helpers, and reporting. | **Modify** | Expose approved deterministic groups only; standard/network helpers are deferred. | Keeps the initial API small. |
| `V2-API-RES-006` | Re-exported dataset validator types from shared validators: `DataSource`, `OHLCVSchema`. | **Reject** | Do not re-export `DataSource` or `OHLCVSchema`; reference their owning domain contracts. | Compatibility re-export is ownership leakage. |
| `V2-API-RES-007` | Re-exported analytics functions used by research workflows: `calmar_ratio`, `expectancy`, `max_drawdown`, `median_mae_mfe`, `profit_factor`, `sharpe_ratio`, `sortino_ratio`, `win_rate`. | **Reject** | Do not re-export Analytics functions; Research imports Analytics explicitly where needed. | Avoids duplicate ownership and compatibility burden. |
| `V2-API-RES-008` | Each public export must be classified as stable public API, internal-support contract, compatibility re-export, experimental capability, or network-backed helper before Builder implementation. | **Add** | Add explicit API classification metadata and exclude non-stable items from agent catalogs. | Needed to make the public boundary auditable. |
| `V2-API-RES-009` | Each item in `app.services.research.__all__` must carry a documented classification label such as `stable`, `internal-support`, `compatibility-re-export`, `experimental`, `network-backed`, or `optional-provider`. | **Add** | Add explicit API classification metadata and exclude non-stable items from agent catalogs. | Needed to make the public boundary auditable. |
| `V2-API-RES-010` | `internal-support` and `compatibility-re-export` items must be excluded from agent-facing stable tool catalogs by default and must be documented as subject to breaking changes unless explicitly promoted through a versioned contract. | **Add** | Add explicit API classification metadata and exclude non-stable items from agent catalogs. | Needed to make the public boundary auditable. |
| `V2-API-RES-011` | Network-backed exports must be marked as `network-backed` and `optional-provider` in the lazy registry and must define provider-missing behavior. | **Defer** | Apply network/optional-provider labels only when the deferred provider slice is approved. | No network helper ships initially. |
| `V2-API-RES-012` | Each public callable must document input type, required fields, optional fields, output type, error behavior, side effects, determinism behavior, dependency behavior, and whether it may perform disk or network I/O. | **Add** | Document full callable/DataFrame contracts for every approved stable export. | Required to replace V1's implicit dynamic behavior. |
| `V2-API-RES-013` | DataFrame-returning functions must document required input columns, output columns, index behavior, timezone expectations, row alignment, NaN behavior, and whether the input is mutated. | **Add** | Document full callable/DataFrame contracts for every approved stable export. | Required to replace V1's implicit dynamic behavior. |
| `V2-API-RES-014` | Re-exported analytics functions must preserve upstream analytics contracts and must be covered by research compatibility tests. | **Reject** | No compatibility tests are required because analytics re-exports are rejected; test direct dependency contracts instead. | The proposed re-export itself is rejected. |


### 6.18 Edge-case test scope

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-EDGE-RES-001` | Empty datasets, single-row datasets, or datasets too small for requested windows or statistical tests. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-002` | Missing required OHLCV/OHLCVS columns. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-003` | Non-monotonic timestamps, duplicate timestamps, timezone-naive timestamps, mixed timezones, clock drift, out-of-order timestamps from merging distributed data sources, or gaps around daylight-saving transitions. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-004` | Invalid OHLC relationships such as high below low, close outside high/low, or negative prices. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-005` | Missing, zero, negative, or extreme spread and volume values. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-006` | Datasets containing weekends, holidays, synthetic bars, or provider-specific missing-bar patterns. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-007` | Rolling windows larger than available history. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-008` | Forward-return, MAE, or MFE horizons extending beyond the available dataset. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-009` | Constant-price series, all-zero returns, all-winning samples, all-losing samples, or division-by-zero metric denominators. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-010` | Null distributions with too few samples, non-finite values, or observed values outside the sampled range. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-011` | Bootstrap block sizes larger than the available sample. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-012` | Permutation requests with invalid labels, empty groups, or unbalanced samples. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-013` | Multiple-comparison corrections with empty p-value lists or invalid p-values. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-014` | PCA or clustering inputs with non-numeric columns, constant columns, missing values, too few rows, or too many requested components/clusters. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-015` | Session tagging across midnight, overlapping sessions, or instruments whose trading hours do not match configured sessions. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-016` | Market-structure calibration candidates that produce no signals, all signals, contradictory labels, or unstable candidate rankings. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-017` | Hypotheses that are untestable, underspecified, contradicted by evidence, or based on data-snooping. | **Defer** | Defer this case with the associated hypothesis/provider capability. | The underlying capability is excluded from the initial rebuild. |
| `V2-EDGE-RES-018` | Research artifacts containing sensitive fields that must be masked before persistence. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-019` | External research-feed fetch failures, malformed HTML, empty news feeds, HTTP 429 with missing or invalid `Retry-After`, rate limits, or provider layout changes. | **Defer** | Defer this case with the associated hypothesis/provider capability. | The underlying capability is excluded from the initial rebuild. |
| `V2-EDGE-RES-020` | Oversized reports or artifacts that need summarization, truncation, or external storage. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-021` | Attempts to use research outputs as direct execution approval. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-022` | Corrupted or partially missing configuration objects. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-023` | Unknown symbol, unsupported timeframe, malformed date range, or end date before start date. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-024` | DataFrame inputs with duplicate column names, object-typed numeric columns, mixed numeric/string values, NaN/Inf values, or unsorted indexes. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-025` | NaT timestamps, columns that are entirely NaN after cleaning, and all-identical feature values used in PCA or clustering. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-026` | Multi-symbol workflows where one symbol fails and others succeed. | **Modify** | Test this at the cross-domain orchestrator boundary; Research stage functions remain single-run deterministic. | Multi-symbol partial success is orchestration behavior. |
| `V2-EDGE-RES-027` | Report output path is missing, unwritable, already exists, points outside allowed directories, or contains path traversal segments. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-028` | Concurrent calls attempt to write the same report or mutate the same registry. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-029` | Cached external feed exists but is stale, corrupted, or from a prior provider schema version. | **Defer** | Defer this case with the associated hypothesis/provider capability. | The underlying capability is excluded from the initial rebuild. |
| `V2-EDGE-RES-030` | External helper returns partial data with warnings. | **Defer** | Defer this case with the associated hypothesis/provider capability. | The underlying capability is excluded from the initial rebuild. |
| `V2-EDGE-RES-031` | Masking configuration misses a sensitive nested field. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |
| `V2-EDGE-RES-032` | Artifact schema version is unknown or incompatible. | **Keep** | Include this case in the accepted capability's failure/edge-case tests. | It can materially affect correctness, safety, or reproducibility. |


### 6.19 Testing and clarifications

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-TEST-RES-001` | Unit tests proving `app.services.research.__init__` contains only lazy export exposure and no business implementation. | **Modify** | Test that package initialization contains only explicit export metadata/lazy loading and no business logic. | The accepted facade differs from V2's blanket lazy model. |
| `V2-TEST-RES-002` | Unit tests proving `app.services.research.__all__` is unique, complete, and resolvable for public functions. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-003` | Unit tests proving each research file has a module docstring and public member docstrings. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-004` | Unit tests proving standard research tools include the required documentation template fields. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-005` | Unit tests proving standard research tools return the standard envelope keys and audit keys. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-006` | Unit tests proving exported functions have usage-example coverage or are explicitly skipped for external/heavy dependencies. | **Modify** | Require executable examples for every approved stable export; do not keep broad skip-by-default coverage. | V1 example is stale and broken. |
| `V2-TEST-RES-007` | Contract tests proving each public function documents input type, output type, error behavior, side effects, and determinism status. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-008` | Contract tests proving each `app.services.research.__all__` export resolves to the documented callable or model. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-009` | Contract tests for standard envelope shape for every network-backed helper. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-010` | Contract tests for output schema of `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, and report payloads. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-011` | Requirement-to-test traceability proving that each public capability, high-risk edge case, and non-functional safety requirement has at least one verifying test. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-012` | Data validation tests for missing columns, invalid OHLC values, duplicate timestamps, gaps, spreads, volume, and timezone handling. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-013` | Cleaning and enrichment tests for missing bars, weekend/holiday behavior, bar geometry, returns, labels, and session fields. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-014` | Feature calculation tests for returns, moving averages, volatility, ATR/ADR, Bollinger statistics, RSI, momentum, Hurst, pivots, forward returns, MAE, and MFE. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-015` | Leakage tests for lookahead detection, chronological split enforcement, and masked artifact serialization. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-016` | Core metric registry tests for calculator registration, duplicate names, missing calculators, and profile output shape. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-017` | Edge-discovery tests for mean-reversion, trend-persistence, session breakout, session fade, and null-baseline workflows. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-018` | Null-model tests for bootstrap, permutation, random-entry, R-space, session-randomized, shuffled-return, percentile, threshold, and multiple-comparison behavior. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-019` | Market-structure tests for swing points, legs, score rows, profile construction, calibration grids, candidate evaluation, profile overrides, validation summaries, stability reports, robustness reports, and strategy-fit reports. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-020` | Unsupervised modeling tests for feature-frame construction, PCA, clustering, label attachment without mutation, risk-factor extraction, cluster outperformance, signal adaptation, and insight reports. | **Modify** | Test approved unsupervised behavior; exclude signal adaptation until its deferred capability is revived. | Core modeling is accepted, adaptation is not. |
| `V2-TEST-RES-021` | Seasonality and session tests for calendar filters, cross-midnight sessions, overlapping sessions, and sparse calendar buckets. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-022` | Reporting tests for Markdown output, JSON output, multi-symbol reports, snapshot reports, comparison reports, dashboard summaries, profile summaries, and scorecard determinism. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-023` | Standard helper tests for news/calendar/sentiment parsing, symbol filtering, impact classification, blackout-window creation, hypothesis generation, evidence scoring, sample-size checks, snooping-risk checks, lookahead-risk checks, testability checks, contradictory-evidence checks, and evidence-pack construction. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-024` | Integration tests proving research artifacts cannot mutate live trading state and cannot bypass risk, approval, idempotency, reconciliation, audit, or kill-switch controls. | **Keep** | Prove Research outputs are advisory and no Research API imports or calls live execution/risk mutation paths. | Boundary safety is mandatory; idempotency/reconciliation internals remain owned elsewhere. |
| `V2-TEST-RES-025` | Failure-path tests for external provider timeout, rate limit, malformed response, empty response, partial response, and layout-change behavior. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-026` | Failure-path tests for serialization failure due to permission denied, missing directory, overwrite disabled, invalid path, path traversal, and non-serializable values. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-027` | Security tests proving secrets, credentials, broker identifiers, account identifiers, and private artifact fields are masked before JSON or Markdown persistence. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-028` | Import-time safety tests proving `app.services.research` does not read secrets, access live trading state, call providers, write files, or perform heavy model execution at import time. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-029` | Concurrency tests for concurrent metric registry reads, report generation, same-path artifact writes, and deterministic seeded workflows under parallel execution. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-030` | Performance/resource tests for maximum supported dataset size, bootstrap/permutation resource behavior, oversized report behavior, and network-helper timeout budgets. | **Modify** | Test approved row/duration/artifact limits; provider timeout budgets are deferred. | Resource testing must match retained capabilities. |
| `V2-TEST-RES-031` | Observability tests proving validation reports include machine-readable issue codes, masking actions are auditable without exposing masked values, and partial failures include warnings and traceable audit metadata. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-032` | Documentation/example tests proving valid examples execute against minimal fixtures and invalid-input examples produce documented error or warning shapes. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-033` | Tests proving the documented error-handling pattern for each public callable is exercised by usage examples or dedicated failure-path examples. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-034` | Tests proving missing optional provider adapters do not break `app.services.research` import or unrelated deterministic research functions. | **Defer** | Defer with network/standard helper capabilities. | No such helper is in the initial rebuild. |
| `V2-TEST-RES-035` | Property-based rolling-window and feature-calculation tests shall verify timestamp alignment and absence of lookahead behavior where a property-based test dependency is approved; otherwise equivalent deterministic generated-case tests are required. | **Modify** | Use property-based tests only if dependency-approved; deterministic generated cases are acceptable. | The behavior matters more than the test library. |
| `V2-TEST-RES-036` | Masking robustness tests shall verify nested sensitive fields do not leak through `mask_research_artifact`, serialized JSON, Markdown reports, warnings, or audit metadata. Mutation-testing tooling is optional and requires dependency approval. | **Keep** | Retain this verification requirement for the approved capability set. | It validates accepted behavior or safety. |
| `V2-TEST-RES-037` | `forward_returns` and `compute_forward_returns` overlap; before Builder handoff, clarify whether they are separate APIs, aliases, or domain-specific variants. | **Merge** | Resolve to one canonical `forward_returns` API; modeling consumes it. | Removes duplicate contracts. |
| `V2-TEST-RES-038` | `atr` and `calculate_atr` overlap; before Builder handoff, clarify whether one returns a Series and the other returns an envelope-compatible output. | **Merge** | Use shared Indicators ATR; remove `calculate_atr` wrapper. | Removes duplicate contracts. |
| `V2-TEST-RES-039` | `adr` and `calculate_adr` overlap; before Builder handoff, clarify the function-level distinction. | **Merge** | Use one canonical ADR behavior in Research seasonality/features; remove `calculate_adr` wrapper. | Removes duplicate contracts. |
| `V2-TEST-RES-040` | `compute_session_statistics` and `calculate_session_statistics` overlap; before Builder handoff, clarify whether one is edge-discovery specific and the other is a standard helper. | **Merge** | Keep session-statistics logic internal to EDS/seasonality; remove standard wrapper. | Removes duplicate contracts. |
| `V2-TEST-RES-041` | `detect_volatility_regime`, `detect_trend_regime`, `detect_market_regime`, `calculate_regime_features`, and `build_market_regime_feature_frame` must have documented boundaries. | **Merge** | Define one regime-feature pipeline; keep simple labels internal to market-structure/modeling consumers. | Resolves five overlapping APIs. |
| `V2-TEST-RES-042` | The overlap resolutions above must be moved into Functional Requirements before Builder handoff; this section cannot remain the only record of API responsibility. | **Add** | Record overlap resolutions in this reconciliation and carry them into the final README requirements. | The clarification is accepted and resolved here. |
| `V2-TEST-RES-043` | ForexFactory helper ownership must be explicitly scoped as optional external research-feed helper behavior, not broad market-data provider ownership. | **Modify** | Keep Data as provider owner; defer optional Research evidence adapters. | Boundary is accepted but provider capability is deferred. |
| `V2-TEST-RES-044` | Standard research envelope schema, canonical error taxonomy, and audit fields must be frozen before any network-backed or agent-facing research helper is implemented. | **Defer** | Freeze envelope/error/audit contracts before any future agent/network helper slice, not before core deterministic work. | Correct gate, deferred timing. |
| `V2-TEST-RES-045` | `CleaningConfig` strategy enums and exact cleaning actions must be approved before data-preparation implementation. | **Open Decision** | Owner must approve cleaning enums, exact actions, and defaults before Builder handoff. | Cannot infer data-altering defaults. |
| `V2-TEST-RES-046` | `CleaningConfig` defaults, including `missing_bar_strategy`, must be approved before implementation. | **Open Decision** | Owner must approve cleaning enums, exact actions, and defaults before Builder handoff. | Cannot infer data-altering defaults. |
| `V2-TEST-RES-047` | Seed source and propagation rules must be approved for bootstrap, permutation, null-model, clustering, and unsupervised workflows. | **Open Decision** | Owner/architect must approve one seed propagation policy across statistical and modeling workflows. | Reproducibility requires a single rule. |
| `V2-TEST-RES-048` | Measurable resource targets and reference hardware must be approved before claiming production-grade performance. | **Open Decision** | Owner must approve resource budgets and reference hardware before production claims. | No measured targets are available. |


### 6.20 Acceptance notes

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
| --- | --- | --- | --- | --- |
| `V2-NOTE-RES-001` | The public namespace exposes both the active `__all__` contract and additional local research classes that may be used internally; rebuild planning should treat `__all__` as the externally visible minimum and local public classes as important implementation-support contracts. | **Modify** | Treat only explicit `__all__` entries as stable; internal public-looking classes are not preserved automatically. | V1 evidence does not justify every local class as a contract. |
| `V2-NOTE-RES-002` | Future provider adapters may support multiple economic calendar/news providers behind the same standard research envelope. | **Defer** | Defer multi-provider adapters with external-feed capability. | No confirmed workflow. |
| `V2-NOTE-RES-003` | Research outputs should continue to be treated as evidence, not approval to trade. | **Keep** | Retain advisory-only semantics across all outputs. | Core safety boundary. |
| `V2-NOTE-RES-004` | Statistical evidence can be sensitive to sample size, market regime, timeframe, and multiple testing; reports should keep uncertainty and caveats visible. | **Keep** | Keep uncertainty and caveats visible in results and reports. | Required for honest statistical interpretation. |
| `V2-NOTE-RES-005` | Future research promotion workflows may integrate with strategy/risk review, but promotion and approval remain outside this module. | **Keep** | Keep promotion/approval outside Research; expose evidence only. | Preserves Strategy/Risk ownership. |


## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `WF-RES-001` | Prepare Research Dataset | Cross-domain | Working — `V1-WF-RESEARCH-001` | Canonical schema, deterministic cleaning/validation/enrichment, typed fatal errors, configurable strategies. | **Modify** | Data/API supplies canonical OHLCV/OHLCVS + source metadata → Research validates, cleans, enriches, and records quality evidence → `PreparedDataset`. |
| `WF-RES-002` | Build Core Metric Profile | Internal | Working — `V1-WF-RESEARCH-002` | Schema-aware calculators, registry, units, warnings, reproducibility metadata. | **Modify** | `PreparedDataset` → Research metric calculators → versioned `CoreMetricProfile`. |
| `WF-RES-003` | Build Leakage-Safe Feature Frame and Time Splits | Internal | Partial — `V1-CAP-RESEARCH-007`, `008` | Feature contracts, forward labels, structured leakage report, chronological train/validation/test splits. | **Add** | Prepared data + feature specification → Research features/leakage checks → feature frame, split IDs, and leakage report. |
| `WF-RES-004` | Analyze Session and Seasonality Opportunity | Internal | Working — `V1-WF-RESEARCH-003` | Unified session utilities, filters, cross-midnight behavior, seasonality outputs. | **Modify** | Prepared OHLCVS + approved session policy → Research seasonality → calendar/session/hour summaries and advisory opportunity windows. |
| `WF-RES-005` | Run Edge Study Against Null Evidence | Internal | Working with caveats — `V1-WF-RESEARCH-004` | EDS studies, seeded nulls, multiple comparison controls, consistent result metadata. | **Modify** | Prepared/split data + study config + seed → Research study and matching null model → advisory `EdgeResult` and comparison evidence. |
| `WF-RES-006` | Build Market-Structure Profile | Internal | Working — `V1-WF-RESEARCH-005` | Reproducible swings, legs, regimes, distributions, excursions, scores, and advisory fit. | **Modify** | Prepared data + market-structure config → Research structure analysis → versioned profile and advisory strategy fit. |
| `WF-RES-007` | Forward Validate and Calibrate Market Structure | Cross-domain | Working/partially tolerant — `V1-WF-RESEARCH-008` | Realized labels, summaries, bounded calibration grids, stability and robustness evidence. | **Modify** | External orchestrator supplies persisted prediction + later research-ready bars → Research labels outcomes and evaluates candidates → validation/calibration evidence returned for persistence. |
| `WF-RES-008` | Run Unsupervised Market-Structure Research | Internal | Working — `V1-WF-RESEARCH-006` | Feature frame, PCA, K-Means, factor interpretation, cluster forward evidence, diagnostics. | **Modify** | Leakage-safe research feature frame + seed → PCA/K-Means and descriptive analysis → advisory unsupervised insight result. |
| `WF-RES-009` | Build Research Scorecard and Profile Snapshot | Internal | Working but fragmented — `V1-WF-RESEARCH-007`, `V1-CAP-RESEARCH-025`, `029` | Deterministic scorecard, normalized snapshot, readiness, reproducibility metadata. | **Modify** | Approved stage outputs → Research scorecard/snapshot builder → versioned advisory evidence artifact. |
| `WF-RES-010` | Render and Persist Research Artifact | Cross-domain | Partial/disconnected reporting — `V1-CAP-RESEARCH-027`–`029` | Markdown/JSON/dashboard/comparison rendering and safe atomic persistence. | **Modify** | Versioned masked research result/snapshot + approved output location → Research renderer/writer → artifact reference or typed failure. |
| `WF-RES-011` | Run Complete Edge Lab Profile | Cross-domain | Working — `V1-WF-RESEARCH-007` | Aggregated configuration, progressive stages, snapshots, scorecard, resource/reproducibility controls. | **Modify** | External API/scheduler supplies data and run request → Research stage APIs execute deterministic computations → external orchestrator caches, schedules, and persists returned artifacts. |
| `WF-RES-012` | Fetch and Normalize External Research Evidence | Cross-domain | Unverified — `V1-WF-RESEARCH-009`, `V1-CAP-RESEARCH-030`, `031` | Optional provider adapters, retries, cache/stale policy, envelopes, news/calendar/sentiment parsing. | **Defer** | Future approved provider adapter → normalized external evidence → advisory research record. |
| `WF-RES-013` | Generate and Score Research Hypothesis Evidence Pack | Internal/Cross-domain | Unverified — `V1-CAP-RESEARCH-033` | Hypothesis generation, testability, snooping/contradiction checks, evidence pack and envelope. | **Defer** | Future analyst/agent hypothesis + approved evidence → Research validation/scoring → advisory evidence pack. |
| `WF-RES-014` | Recommend Cluster-Based Signal Adaptation | Cross-domain | Implemented but uncalled/in-sample — `V1-CAP-RESEARCH-024` | Advisory signal adaptation without live mutation. | **Defer** | Future out-of-sample cluster evidence → Research recommendation → Strategy/Risk review boundary. |


### `WF-RES-001` — Prepare Research Dataset

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Provider/data source fetch → `prepare_research_dataset()` → validate → clean → enrich → `PreparedDataset`.
```

**V2 proposal:**

```text
Accept raw in-memory data or configured source; apply approved strategies, typed failures, schema/version metadata, and quality actions.
```

**Final decision:**

```text
Modify — Remove provider connection lifecycle from Research. Accept data and source metadata, execute one deterministic prepare sequence, and return a versioned `PreparedDataset` or typed configuration/validation failure.
```

**Reason:**

The workflow is proven, but acquisition belongs to Data/API and silent cleaning defaults are unsafe.

### `WF-RES-002` — Build Core Metric Profile

**Scope:** `Internal`

**V1 behaviour:**

```text
Prepared dataset → mutable default registry → seven calculators → profile.
```

**V2 proposal:**

```text
Normalized metric contracts and metadata-rich profile.
```

**Final decision:**

```text
Modify — Keep the seven families and a small registry, make defaults immutable, honor schema mappings, and record units, sample size, undefined values, dataset/config identity, and warnings.
```

**Reason:**

Operational value is confirmed; changes fix schema and reproducibility defects.

### `WF-RES-003` — Build Leakage-Safe Feature Frame and Time Splits

**Scope:** `Internal`

**V1 behaviour:**

```text
Feature batch pipeline exists; chronological split/masking helpers exist; no strong end-to-end leakage workflow is confirmed.
```

**V2 proposal:**

```text
Compute features with documented warm-up/NaN behavior; declare forward columns; validate lookahead risk and enforce chronological splits.
```

**Final decision:**

```text
Add — Add an explicit feature-and-leakage workflow using shared Indicator/Analytics formulas where appropriate and research-owned forward/Hurst/regime features.
```

**Reason:**

Leakage foundations are required before statistical/modeling claims and V1 assurance is too weak.

### `WF-RES-004` — Analyze Session and Seasonality Opportunity

**Scope:** `Internal`

**V1 behaviour:**

```text
Prepared data → seasonality aggregations → heatmaps, rankings, best/dead windows.
```

**V2 proposal:**

```text
Same behavior with explicit session configuration and edge-case contracts.
```

**Final decision:**

```text
Modify — Preserve the analysis but use one timezone-aware session authority shared with session EDS and expose sparse/overlap warnings.
```

**Reason:**

V1 is used but conflicting session definitions can change results.

### `WF-RES-005` — Run Edge Study Against Null Evidence

**Scope:** `Internal`

**V1 behaviour:**

```text
Run null, mean reversion, trend persistence, and session EDS; classify results.
```

**V2 proposal:**

```text
Record data/split/config identity, uncertainty, effective seed, warnings, and advisory disclaimer.
```

**Final decision:**

```text
Modify — Keep all three study families and null baseline; match BUY/SELL/mixed samples to correct nulls, use one confirmation policy, and continue independent studies after isolated failure only when explicitly requested.
```

**Reason:**

The studies are operational, but current direction and confirmation inconsistencies undermine statistical validity.

### `WF-RES-006` — Build Market-Structure Profile

**Scope:** `Internal`

**V1 behaviour:**

```text
Detect swings/legs; run EDS; analyze range/distribution/excursions/regimes; score and fit strategies.
```

**V2 proposal:**

```text
Base profile plus optional quality layers and reproducibility metadata.
```

**Final decision:**

```text
Modify — Keep the behavioral pipeline, split focused responsibilities, make quality layers opt-in, and use one scoring/confirmation implementation.
```

**Reason:**

Strong value is proven, but V1 is oversized and internally duplicated.

### `WF-RES-007` — Forward Validate and Calibrate Market Structure

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
API fetches future bars, labels realized behavior, saves evaluations, and runs three calibration implementations.
```

**V2 proposal:**

```text
Versioned labels, explicit horizon/window, ranking criteria, stability evidence, and warnings.
```

**Final decision:**

```text
Modify — Research owns pure labeling/evaluation. The orchestrator owns later-data retrieval and database writes. Consolidate calibration around production scoring.
```

**Reason:**

Preserves the working loop while correcting boundary and scoring drift.

### `WF-RES-008` — Run Unsupervised Market-Structure Research

**Scope:** `Internal`

**V1 behaviour:**

```text
Feature pipeline → stateless service class → feature frame → PCA/K-Means → cluster evidence/context.
```

**V2 proposal:**

```text
Explicit preprocessing, dropped columns, seed, model parameters, and diagnostics.
```

**Final decision:**

```text
Modify — Replace the service class with a workflow function, keep result models, and separate evidence from Strategy/Risk recommendations.
```

**Reason:**

The workflow is used; the service abstraction is not justified and metadata is incomplete.

### `WF-RES-009` — Build Research Scorecard and Profile Snapshot

**Scope:** `Internal`

**V1 behaviour:**

```text
API assembles stage outputs, builds scorecard, and creates a route-specific snapshot payload.
```

**V2 proposal:**

```text
Canonical snapshot and deterministic scorecard with complete metadata.
```

**Final decision:**

```text
Modify — Use one snapshot builder and one scorecard implementation; include stage versions, hashes, warnings, uncertainty, readiness reasons, and advisory status.
```

**Reason:**

Eliminates competing snapshot and strategy-fit shapes.

### `WF-RES-010` — Render and Persist Research Artifact

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Separate EDS/profile renderers write files directly; automation often bypasses them.
```

**V2 proposal:**

```text
Overwrite control, allowed paths, masking, atomic write, permission errors, encoding, metadata.
```

**Final decision:**

```text
Modify — Merge renderers around one snapshot/result schema and one safe artifact writer. Database persistence remains external.
```

**Reason:**

Reporting is valuable, but current side-effect and schema behavior is fragmented.

### `WF-RES-011` — Run Complete Edge Lab Profile

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
API owns provider fetch, stage sequencing, cache reuse, scheduler, database snapshot, and response.
```

**V2 proposal:**

```text
Research requirements imply an end-to-end Edge Lab workflow but also exclude provider/database ownership.
```

**Final decision:**

```text
Modify — Preserve the sequence but not the infrastructure ownership. Research provides a pure profile runner only if it adds value beyond the external orchestrator; otherwise the orchestrator calls stage functions.
```

**Reason:**

This is the real system workflow, but cross-domain ownership must remain explicit.

### `WF-RES-012` — Fetch and Normalize External Research Evidence

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Dynamic standard tool calls direct ForexFactory pages and wraps raw responses.
```

**V2 proposal:**

```text
Full optional-provider lifecycle and standard envelope.
```

**Final decision:**

```text
Defer — Exclude from the initial rebuild. Reconsider after provider ownership, licensing/terms, normalized schema, cache policy, and caller workflow are approved.
```

**Reason:**

High complexity and external fragility have no confirmed current value.

### `WF-RES-013` — Generate and Score Research Hypothesis Evidence Pack

**Scope:** `Internal/Cross-domain`

**V1 behaviour:**

```text
Nine dynamically exposed helpers; no caller confirmed.
```

**V2 proposal:**

```text
Structured hypothesis/evidence workflow.
```

**Final decision:**

```text
Defer — Keep sample-size and lookahead checks in accepted validation capabilities; defer the broader hypothesis workflow until a real agent/analyst use case exists.
```

**Reason:**

Avoids building a parallel, disconnected scoring system.

### `WF-RES-014` — Recommend Cluster-Based Signal Adaptation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Clusters and forward returns from the same sample suppress signals in a copied frame.
```

**V2 proposal:**

```text
Advisory recommendations only.
```

**Final decision:**

```text
Defer — Do not include initially. Require out-of-sample evaluation, minimum observation policy, and explicit Strategy/Risk acceptance contract before revival.
```

**Reason:**

Current behavior risks overfit evidence being treated as control.

## 8. Recommended Minimal Capability Structure

The package path is shown at the current V1 location to minimize migration risk. Pipeline step 05 must resolve whether the system standard instead requires `tools/research`.

```text
app/services/research/
├── contracts/          # Configurations, result models, errors, warnings, API metadata
├── data/               # Canonical preparation, cleaning, validation, enrichment
├── features/           # Research-specific feature and feature-frame behavior
├── leakage/            # Chronological splits, leakage evidence, artifact masking
├── metrics/            # Core metric calculators, registry, profile
├── statistics/         # Bootstrap, permutation, null models, corrections
├── studies/            # Mean reversion, trend persistence, session studies, classification
├── seasonality/        # Unified sessions and calendar/session opportunity analysis
├── market_structure/   # Profiles, quality validation, calibration, advisory strategy fit
├── modeling/           # PCA, clustering, unsupervised insight functions and models
├── profiles/           # Scorecard, snapshot, summaries, comparison/rendering
└── artifacts/          # Safe masked JSON/Markdown persistence
```

| Module | Capability | Source | Main decision |
| --- | --- | --- | --- |
| `contracts/` | Versioned configs/models, typed errors, structured warnings, API classification, reproducibility/resource contracts | Both | Modify/Add |
| `data/` | Research-ready dataset preparation and quality evidence | Both | Modify |
| `features/` | Research-specific returns, Hurst, forward outcomes, excursions, regime frames; shared indicator consumption | Both | Merge/Modify |
| `leakage/` | Time splits, leakage reports, masking | Both | Modify/Add |
| `metrics/` | Schema-aware core metric profile and registry | Both | Modify |
| `statistics/` | Seeded resampling, null distributions, corrections | Both | Modify |
| `studies/` | EDS studies and consistent classification | Both | Modify/Merge |
| `seasonality/` | One session policy and seasonality analysis | Both | Modify |
| `market_structure/` | Focused structure, validation, stability, robustness, calibration, fit | Both | Split/Merge |
| `modeling/` | Stateless PCA/K-Means and insight workflow | Both | Modify |
| `profiles/` | Canonical scorecard, snapshot, summaries, report renderers | Both | Merge/Modify |
| `artifacts/` | Allowed-path, masked, atomic artifact writes | V2 + V1 reporting behavior | Add/Modify |


**Excluded from the initial structure:** provider adapters, generic `helpers.py`, analytics compatibility exports, agent hypothesis tooling, cluster signal adaptation, scheduler/cache/database orchestration, and live-control integrations.

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
| --- | --- | --- | --- | --- |
| 1 | `data/models.py` | Refactor | Contracts and data | Schema/version/serialization tests; payload compatibility. |
| 2 | `data/validation.py`, `cleaning.py`, `enrichment.py`, `preparation.py` | Refactor/Split | Dataset preparation | Golden fixtures for timestamps, OHLC, gaps, spreads, sessions, and fatal/warning behavior. |
| 3 | `core_metrics/base.py`, `registry.py`, `service.py` | Refactor | Core metrics | Schema-indirection, immutable registry, units, undefined values, deterministic profile. |
| 4 | `features/calculations.py` | Refactor/Remove duplicates | Features | Formula parity with Indicators/Analytics; forward-feature leakage labels. |
| 5 | `features/pipeline.py` | Reuse batch; defer incremental | Features/modeling | Batch workflow tests; verify no caller requires incremental mode. |
| 6 | `features/leakage.py` | Refactor | Leakage/artifacts | Structured leakage cases and recursive masking tests. |
| 7 | `null_models.py`, `eds_null_models.py` | Refactor | Statistics | Seed, direction, empty/non-finite, block-size, correction tests. |
| 8 | `eds_mean_reversion.py`, `eds_trend_persistence.py`, `eds_session.py` | Refactor | Studies | Matched nulls, split identity, confirmation policy, isolated-failure behavior. |
| 9 | `classifier.py`, `results_schema.py` | Refactor/Merge policy | Study classification | One confirmation truth table used by reports and scorecards. |
| 10 | `session_config.py`, `config.SessionConfig`, `seasonality.py` | Merge/Refactor | Seasonality | Owner-approved session/timezone fixtures including overlaps and midnight. |
| 11 | `market_structure.py` | Split/Refactor | Market structure | Parity tests for current profile outputs, then focused component tests. |
| 12 | Calibration, stability, robustness, validation modules | Merge/Refactor | Market-structure quality | Same production scoring function; bounded grids; validation-window fixtures. |
| 13 | `modeling/*` | Refactor; replace service class | Modeling | Seeded PCA/K-Means equivalence, metadata, constant/invalid input tests. |
| 14 | `adapt_signals_by_cluster` | Defer | None initially | Caller search and out-of-sample design required before revival. |
| 15 | `scorecard.py` | Refactor | Profiles | Determinism, versioned inputs, no duplicate strategy-fit output. |
| 16 | `reporting.py`, `profile_reporting.py`, `profile_snapshot.py` | Merge/Refactor | Profiles/artifacts | Canonical snapshot schema, rendering parity, masking/path/atomic-write tests. |
| 17 | `app/services/research/__init__.py`, `_common.py` | Replace facade internals | Public API | Unique explicit exports, import-time safety, no callable wrapping. |
| 18 | `standard_tools.py` calculation/detection wrappers | Remove | Canonical feature/metric/study capabilities | Full dynamic caller search plus compatibility migration. |
| 19 | ForexFactory and standard news/evidence helpers | Defer | Future providers/evidence | Approved caller/provider/envelope contract required. |
| 20 | Analytics and validator re-exports | Remove | Direct owning-domain contracts | Repository-wide import migration and deprecation test. |
| 21 | `tests/usage/app/services/12_research.py` | Replace | Executable examples | Examples must execute against approved contracts and documented failures. |


## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
| --- | --- | --- |
| Move the domain to `tools/research` immediately | Package relocation is a system-shape decision and V1 callers use `app.services.research`. | Keep the V1 path during reconciliation; resolve path in pipeline step 05/ADR. |
| Expose all local public-looking classes plus a broad lazy namespace | Preserves accidental implementation surface and repeats V1's 207-symbol problem. | Expose only an explicit stable list; module-path internal support is not guaranteed API. |
| Public `research_modeling_module` | Returns a module rather than domain behavior. | Reject as public API; lazy registry imports modeling internally. |
| Stateless `UnsupervisedResearchService` class | No state, dependency lifecycle, or resource ownership. | Replace with a workflow function and result models. |
| Generic `helpers.py` containing provider, parser, calculations, and evidence tools | Creates another catch-all multi-responsibility file. | Defer provider/evidence helpers; place any future accepted behavior in focused modules. |
| Standard envelope for all public research behavior | Would force pure numerical/dataframe functions into a heavy agent-tool contract. | Typed exceptions/structured result models for library APIs; envelope only for future agent/network helpers. |
| Four ForexFactory adapters with retry/cache/stale/layout policy in the first rebuild | Large unproven network surface with no confirmed caller. | Defer the entire provider slice. |
| Duplicate `calculate_*` and `detect_*` standard wrappers | Duplicates features, metrics, seasonality, market structure, Indicators, and Analytics. | Remove wrappers and use canonical capabilities. |
| Research re-exports of Analytics ratios | Creates ownership and compatibility burden. | Reject; import Analytics directly where Research needs it. |
| Research re-exports of `DataSource` and `OHLCVSchema` | Obscures Data ownership. | Reject; reference shared boundary contracts directly. |
| Separate `build_market_structure_research_profile` | Overlaps the base builder and has no confirmed caller. | One profile builder plus explicit opt-in quality evaluation. |
| Three calibration modules with copied scoring logic | Can rank candidates using logic different from production scoring. | One calibration capability calling the canonical scorer. |
| Separate EDS/profile JSON and Markdown save functions | Duplicates path, masking, overwrite, encoding, and atomicity logic. | One safe artifact writer plus format-specific renderers. |
| `print_result_summary` stable API | Adds console side effects without domain value. | Reject; callers print returned summaries. |
| Hard portable `max_memory_mb` enforcement | Not reliably enforceable in a pure cross-platform Python function. | Use measured/advisory memory budgets plus hard row/duration/artifact-size limits. |
| 1,000,000 rows in 30 seconds placeholder | No approved hardware or benchmark evidence. | Reject as a requirement until measured and approved. |
| Implement/test every V2 helper in the first slice | Would rebuild disconnected V1 breadth instead of proven workflows. | Initial slice recommendation: contracts/errors, data preparation, leakage foundations, core metrics. |


## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
| --- | --- | --- | --- | --- |
| Open — escalate | Final package path: `app/services/research` or `tools/research` | V1 runtime uses `app.services.research`; V2 architecture proposes `tools/research`. | Keep V1 path; migrate to `tools/research`; compatibility shim. | All capabilities/public imports |
| Open | Approve the first Builder slice | V2 proposes data + core metrics; reconciliation identifies contracts/errors and leakage foundations as prerequisites. | Data+metrics only; contracts+data+leakage+metrics. | `CAP-RES-001`–`005`, `019` |
| Open — escalate | Canonical session windows, overlap precedence, and timezone basis | V1 has conflicting `SessionConfig` and `session_config.py`; seasonality and EDS consume both concepts. | Dataset-index UTC; exchange/provider timezone; configurable policy. | `CAP-RES-007`, `009` |
| Open | Default missing-bar strategy and allowed data-changing strategies | V2 explicitly blocks inference; V1 behavior exists but defaults are not approved. | None/drop only; allow fill/interpolate with explicit opt-in; instrument profile. | `CAP-RES-002` |
| Open | Non-trading-period strategy and holiday/provider-gap policy | V2 requires exact behavior; no approved default is supplied. | Keep+warn; drop known closures; provider calendar policy. | `CAP-RES-002`, `009` |
| Open | Seed source and propagation | V1 has mixed seed fields (`random_state`, config seeds); V2 requires one policy. | Required top-level seed; per-stage derived seeds; explicit per-call overrides. | `CAP-RES-006`, `007`, `011`, `013` |
| Open — escalate | Canonical error taxonomy and shared envelope vocabulary | V2 proposes pending status/error enums; other domains may share the standard envelope. | Research-local typed errors; shared system envelope ADR; hybrid. | `CAP-RES-019`, future `021`/`022` |
| Open | Resource targets and reference hardware | V2 placeholder is unapproved; V1 performance was not measured. | Conservative row/time caps; benchmark-derived caps; per-capability limits. | All heavy capabilities |
| Open — escalate | Artifact storage root and persistence ownership | V1 writes files and API writes database snapshots; V2 gives Research reporting/persistence responsibility. | Research file writer only; shared artifact domain; API/database owner. | `CAP-RES-016`, `017`, `020` |
| Open | Market-structure realized-label horizon and calibration truth definition | V1 labels future windows heuristically; V2 requests explicit validation windows and criteria. | Fixed bars by timeframe; elapsed time; multiple horizons. | `CAP-RES-011` |
| Open — escalate | Shared Indicator/Analytics dependency contracts and deprecation of Research wrappers | V1 duplicates and re-exports these calculations; final direction removes wrappers. | Direct imports now; compatibility aliases for one release; copied formulas retained (not recommended). | `CAP-RES-003`, `023` |
| Open — escalate | External research-feed roadmap and provider ownership | V1 ForexFactory tools are unverified; V2 proposes optional providers. | Permanent removal; future Research evidence adapters; Data-owned provider normalization. | Deferred `CAP-RES-021` |
| Open | Conditions for reviving cluster signal adaptation | V1 is in-sample and uncalled; V2 limits it to advisory output. | Remove permanently; out-of-sample recommendation only; Strategy-owned experimentation. | Deferred `CAP-RES-014` |


**Escalation:** Rows marked **escalate** affect package shape, shared contracts, or multiple domains. They must be copied to the top-level system document and resolved there with an ADR. Deferred external-provider and signal-adaptation capabilities must be reflected in the top-level Deferred Capabilities section if they affect actors, cross-domain workflows, or shared contracts.

## 12. Inputs for the Final Domain README

### Approved capabilities

* Versioned Research configurations, result models, typed errors, structured warnings, and reproducibility metadata.
* Deterministic research dataset preparation and machine-readable quality evidence.
* Research-specific features and feature frames using shared Indicator/Analytics calculations where appropriate.
* Chronological splits, structured leakage reports, and artifact masking.
* Schema-aware core metric profiles.
* Seeded bootstrap, permutation, null models, percentiles, thresholds, and multiple-testing corrections.
* Mean-reversion, trend-persistence, and session edge studies.
* One consistent edge classification/confirmation policy.
* Unified session and seasonality analysis.
* Market-structure profiles, opt-in stability/robustness, forward validation, and consolidated calibration.
* Advisory strategy-fit evidence.
* Deterministic PCA/K-Means insight generation.
* Deterministic scorecard/readiness, canonical snapshots, and report renderers.
* Safe masked artifact persistence.
* Explicit classified lazy public API.
* Pure stage contracts for external Edge Lab orchestration.

### Approved workflows

* `WF-RES-001` — Prepare Research Dataset (Modify).
* `WF-RES-002` — Build Core Metric Profile (Modify).
* `WF-RES-003` — Build Leakage-Safe Feature Frame and Time Splits (Add).
* `WF-RES-004` — Analyze Session and Seasonality Opportunity (Modify).
* `WF-RES-005` — Run Edge Study Against Null Evidence (Modify).
* `WF-RES-006` — Build Market-Structure Profile (Modify).
* `WF-RES-007` — Forward Validate and Calibrate Market Structure (Modify).
* `WF-RES-008` — Run Unsupervised Market-Structure Research (Modify).
* `WF-RES-009` — Build Research Scorecard and Profile Snapshot (Modify).
* `WF-RES-010` — Render and Persist Research Artifact (Modify).
* `WF-RES-011` — Run Complete Edge Lab Profile (Modify).


### V1 behaviours to preserve

* Prepared-dataset schema/report behavior and the validate → clean → enrich sequence (`V1-CAP-RESEARCH-001`–`005`).
* Seven-family core metric profile (`V1-CAP-RESEARCH-009`).
* Null, mean-reversion, trend-persistence, and session studies (`V1-CAP-RESEARCH-010`–`013`).
* Calendar/session/hour opportunity analysis (`V1-CAP-RESEARCH-015`).
* Swing/leg/range/distribution/regime market-structure evidence (`V1-CAP-RESEARCH-016`).
* Stability, robustness, forward validation, and calibration behavior (`V1-CAP-RESEARCH-018`–`020`).
* PCA/K-Means and insight reports (`V1-CAP-RESEARCH-021`–`023`).
* Deterministic scorecard/readiness output (`V1-CAP-RESEARCH-025`).
* The complete Edge Lab stage sequence (`V1-WF-RESEARCH-007`) with corrected ownership.

### V1 behaviours to modify

* Provider-to-preparation orchestration: pass research-ready data instead of owning provider connectivity.
* Duplicate feature calculations: delegate common indicators/analytics and keep research-specific transformations.
* Leakage validation: replace heuristic assurance with structured evidence and declarations.
* Session definitions: unify timezone/windows/overlap precedence.
* Edge confirmation and null direction: one policy and matched-side statistics.
* Market structure: split focused responsibilities and make expensive quality layers opt-in.
* Calibration: use the same scoring function as production profile construction.
* Unsupervised modeling: use stateless functions and explicit preprocessing/seed metadata.
* Reporting/snapshots: one schema, one scorecard, shared renderers, one safe writer.
* Package facade: explicit classified exports without recursive scans or import-time callable wrapping.

### V1 behaviours to remove

* Duplicate standardized market calculation/detection wrappers, after dynamic-caller verification and migration.
* Analytics and shared-validator convenience re-exports, after repository-wide import migration.
* Public module-returning `research_modeling_module` behavior.
* Mutable global defaults and duplicate scoring/session/snapshot implementations.
* Stale usage examples; replace rather than preserve.

### V2 behaviours to add

* Versioned model schemas and exact serialization contracts.
* Canonical typed error families and structured warning records.
* Per-call failure-pattern declarations and first-slice behavior/error tables.
* Structured `LeakageReport` and forward-feature declarations.
* Dataset/config hashes, seeds, UTC timestamps, dependency versions, source references, duration, and resource metadata.
* Allowed-path, overwrite-safe, masked, atomic artifact persistence.
* Public API classification and import-time safety tests.
* Requirement-to-test traceability for accepted capabilities.

### V2 proposals to reject or defer

* Reject Analytics and validator compatibility re-exports.
* Reject duplicate `calculate_*`/`detect_*` standard wrappers.
* Reject public `research_modeling_module` and stateless `UnsupervisedResearchService`.
* Reject console printing as a stable domain API.
* Reject the unapproved 1,000,000-row/30-second benchmark.
* Defer ForexFactory/network providers and related standard envelopes/retry/cache behavior.
* Defer broad hypothesis generation/evidence scoring helpers.
* Defer cluster-based signal adaptation until out-of-sample and cross-domain contracts exist.
* Defer incremental feature-pipeline behavior unless a real caller is confirmed.

### Required open decisions before README completion

* Package path and compatibility strategy.
* Approved first implementation slice.
* Missing-bar and non-trading-period defaults.
* Canonical session windows/timezone/overlap policy.
* Seed propagation policy.
* Error taxonomy and, for future helpers, envelope vocabulary.
* Resource limits and reference hardware.
* Artifact storage/persistence ownership.
* Market-structure validation horizon/ground truth.
* Shared Indicator/Analytics dependency contracts.

## 13. Final Reconciliation Checklist

| Verified | Checklist item |
| --- | --- |
| Yes | Every one of the 35 `V1-CAP-RESEARCH-*` capabilities appears in Section 5. |
| Yes | All 264 explicit V2 functional/non-functional checkboxes are dispositioned in Section 6. |
| Yes | V2 ownership, API, edge-case, test/clarification, and acceptance statements are also dispositioned in Section 6. |
| Yes | Every `V1-WF-RESEARCH-001` through `009` is represented in the final workflow set. |
| Yes | V2 usage-example and implicit end-to-end workflows are reconciled, including deferred provider/hypothesis/adaptation workflows. |
| Yes | Confirmed working V1 behavior is preserved unless a documented defect or ownership violation requires change. |
| Yes | Questionable V1 behavior is removed or deferred with caller/deletion conditions. |
| Yes | V2 implementation complexity is simplified rather than accepted automatically. |
| Yes | The recommended structure follows Domain package → Feature module → Focused file → Public behavior. |
| Yes | Potential cross-domain ownership issues are flagged for pipeline step 05. |
| Yes | Unresolved decisions are listed in Section 11. |
| Yes | Cross-domain open decisions and shape-changing deferrals are marked for top-level escalation. |
| Yes | No code was inspected or modified in this step. |
| Yes | Neither source document was modified. |
| Yes | The document provides approved capabilities, workflows, migrations, exclusions, and open decisions for the final domain README. |


**Reconciliation result:** `REVISION REQUIRED BEFORE BUILDER HANDOFF` — the final direction is sufficiently defined for README drafting only after the listed README-blocking open decisions are resolved or explicitly carried as approved open decisions.

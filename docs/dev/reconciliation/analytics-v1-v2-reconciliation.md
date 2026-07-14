# Analytics — V1/V2 Reconciliation
## 1. Reconciliation Scope

* **Domain:** analytics
* **Domain ID:** `anlt`
* **V1 audit report:** `docs/dev/audits/analytics-v1-audit.md`
* **V2 requirements:** `06_analytics.md`
* **Comparison limitations:**
  * This reconciliation uses only the two supplied documents. No code, repository, runtime, tests, logs, or external sources were inspected.
  * The V1 audit states that the audited package is a merged V1/V2 code surface rather than a clean historical V1 snapshot; V1 evidence therefore describes the audited implementation, not a pristine legacy release.
  * V1 caller absence and unused-code findings retain the confidence limitations recorded in the audit.
  * The V2 document contains 430 checkbox requirements, 175 additional requirement/test/boundary bullets, and implementation prescriptions without native IDs. Stable reconciliation IDs were assigned here so every item can receive a disposition.
  * Package location and shared upstream/downstream schemas are intentionally not finalized here; those decisions affect multiple domains and belong in pipeline step 05.
  * Tests were not run and proposed formulas, thresholds, performance limits, FX authority, and schema-version support were not independently validated.

## 2. Executive Summary

The final Analytics direction should preserve the proven read-only metric kernels, deterministic input canonicalization, the core report workflow, benchmark calculations, seeded bootstrap/permutation behavior, dashboard projection, serialization, and report hashing. These are the strongest V1 capabilities because they participate in actual internal workflows and have test/example evidence.

The main V1 corrections are structural and correctness-related:

* replace the 351-name accidental public facade with a small explicit high-level tool surface;
* unify competing response envelopes, request-ID behavior, report/dashboard models, redaction, and distribution implementations;
* correct report-to-scorecard and report-to-dashboard contract mismatches;
* replace fabricated/default analytical values with `None`, skipped sections, or structured warnings;
* remove fixed-value portfolio, comparison, compliance, White’s Reality Check, PBO, and backtest-resampling outputs;
* remove the mutable unpopulated registry and legacy compatibility aliases after import verification;
* enforce workload limits at official boundaries;
* make formulas, units, annualization, precision, sample rules, and undefined behavior catalog-driven.

Important V2 behavior to add includes a real Official Analytics Tool Catalog, a complete Metric Definition Catalog, canonical warning/quality-flag contracts, explicit adapter field mappings, full report lineage and reproducibility hashes, section criticality, currency/FX lineage, deterministic dashboard limits, schema compatibility, and requirement-to-test traceability.

The V2 proposal is intentionally simplified. The initial rebuild should not introduce mandatory metric interfaces, builder/manager classes, local caches, distributed infrastructure, thirteen separate ADRs, every historical metric name as a public requirement, or advanced TCA/attribution/explainability/live-degradation sections without approved workflows. Stateless calculations remain functions; classes are limited to immutable contracts/configuration or genuinely stateful adapters.

Major open decisions are the exact official tool list, canonical cross-domain result schemas, package location, core formula conventions, scorecard thresholds, report section criticality, FX authority/staleness, dashboard classes/algorithm, schema versions, and measurable production limits.

**Recommended migration direction:** refactor the working V1 core into a small contract-first Analytics domain; replace unsafe placeholders; merge duplicates; defer specialized metrics and cross-domain advanced evidence; expose only approved high-level functions.

## 3. Decision Principles

* Preserve proven, read-only analytical behavior.
* Treat V1 as evidence, not future authority.
* Treat V2 as a proposal, not an automatic commitment.
* Expose high-level tools only; keep metric kernels internal.
* Prefer pure functions for stateless calculations and orchestration.
* Use classes only for immutable contracts, configuration, state, dependencies, or lifecycle.
* Use one canonical response envelope, report model, warning model, redaction policy, and metric implementation per concept.
* Return undefined/skipped evidence explicitly; never fabricate zero, infinity, caps, or compliance.
* Require cataloged formulas, units, annualization, precision, sample rules, aliases, and warnings before a metric enters an official contract.
* Add advanced statistics, explainability, live degradation, caching, or portfolio complexity only when a real workflow and stable inputs justify them.
* Keep Analytics non-binding and downstream of execution, simulation, market data, risk authority, and governance.
* Resolve shared schemas, FX authority, package location, and cross-domain workflows in pipeline step 05.
* Keep one focused capability per module and one focused responsibility per file.
## 4. Capability Reconciliation Matrix
| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
|---|---|---|---|---|---|---|---|---|
| CAP-ANLT-001 | Official public surface and catalog | V1-CAP-ANALYTICS-025, -029, -030; 351-name root facade | V2-FR-PUB-001–011; V2-API-007–012 | V1 exposes kernels/aliases and mutable registry; exact official list unresolved. | Modify | Explicit static high-level tool catalog and package-root exports; kernels remain internal. | Refactor | Preserves safe facade intent while removing accidental API surface. |
| CAP-ANLT-002 | Canonical response envelope and traceability | V1-CAP-ANALYTICS-030; V1-WF-ANALYTICS-001–011 | V2-FR-ENV-002–008; V2-NFR-007 | V1 has competing envelopes and inconsistent request-ID validation/metadata. | Modify | One versioned success/error envelope for official tools with required safe request ID and side-effect metadata. | Refactor | Needed for reliable API/agent consumption. |
| CAP-ANLT-003 | Canonical result adapters | V1-CAP-ANALYTICS-001, -002; V1-WF-ANALYTICS-006 | V2-FR-RPT-002–003, -018; V2-OWN-010 | V1 canonicalization is valuable but field mappings and cross-domain schemas are incomplete. | Modify | Deterministic mappings from approved upstream result contracts into one canonical `TradingResult`, preserving bounded lineage and failing closed. | Refactor | Reuse validation/conversion logic; replace unapproved compatibility aliases. |
| CAP-ANLT-004 | Trade outcome metrics | V1-CAP-ANALYTICS-003; V1-WF-ANALYTICS-001–002 | V2-FR-ENV-010–012; historical trade metrics | V1 works but classification, undefined values, aliases, and public exposure need correction. | Modify | Internal closed-trade kernels with epsilon-based classification, source context, warnings, and cataloged formulas. | Refactor | Core proven workflow. |
| CAP-ANLT-005 | Equity, return, and PnL metrics | V1-CAP-ANALYTICS-004; V1-WF-ANALYTICS-001 | V2 historical Returns; V2-FR-ENV-014–015 | V1 has broad useful behavior but inconsistent ordering, annualization, non-finite handling, and aliases. | Modify | Canonical internal curve/return/PnL kernels with explicit frequency, units, precision, and undefined-result rules. | Refactor | Core report dependency. |
| CAP-ANLT-006 | Drawdown metrics | V1-CAP-ANALYTICS-005; V1-WF-ANALYTICS-001–002 | V2 historical Drawdowns | Core metrics work; file is broad and specialized metrics are not all needed initially. | Split | Keep core depth/duration/recovery metrics; defer specialized trade-level and account-size measures. | Refactor | Smaller report-focused kernel set. |
| CAP-ANLT-007 | Risk and exposure metrics | V1-CAP-ANALYTICS-006; V1-WF-ANALYTICS-001 | V2 historical Risks; V2-FR-RPT-005 | Return risk works; some exposure names overstate calculations and portfolio/Monte Carlo metrics are unproven. | Split | Initial volatility/VaR/CVaR/ES plus validated basic exposure evidence; defer ruin, portfolio covariance, and margin curves. | Refactor | Correct semantics before reuse. |
| CAP-ANLT-008 | Ratio metrics | V1-CAP-ANALYTICS-007; V1-WF-ANALYTICS-001 | V2 historical Ratios; Metric Catalog requirements | V1 has many formulas and aliases without one approved convention. | Modify | Cataloged internal core ratios; undefined denominators yield `None` plus warning; specialized ratios deferred. | Refactor | Preserves core Sharpe/Sortino/Calmar/PF/payoff value. |
| CAP-ANLT-009 | Benchmark comparison | V1-CAP-ANALYTICS-008; V1-WF-ANALYTICS-003 | V2-FR-EVID-001–004; historical Benchmark | V1 uses truncation/default values that can misstate non-overlap or zero variance. | Modify | UTC/timestamp-aligned benchmark evidence with window/currency checks and explicit skipped/undefined results. | Refactor | Real workflow with correctness gaps. |
| CAP-ANLT-010 | Distribution diagnostics | V1-CAP-ANALYTICS-009; V1-WF-ANALYTICS-001 | V2 historical Distributions | Two implementations overlap and use different contracts/approximations. | Merge | One internal distribution kernel set for moments, percentiles, tails, histogram/outliers as approved; advanced fitting deferred. | Refactor | Eliminates formula drift. |
| CAP-ANLT-011 | Deterministic statistical validation | V1-CAP-ANALYTICS-010, -011; V1-WF-ANALYTICS-007 | V2-FR-ENV-020; historical Statistical Tests | Seeded bootstrap/permutation work, but several advertised methods are constants. | Modify | Initial real bootstrap CI, permutation, multiple-comparison corrections, and sample-size diagnostics; remove hard-coded outputs; defer advanced overfitting methods. | Refactor | Preserves proven value without false evidence. |
| CAP-ANLT-012 | Cost, efficiency, and time evidence | V1-CAP-ANALYTICS-020–022; V1-WF-ANALYTICS-002 | V2-FR-ENV-016–018; historical Efficiency/Overview | Useful kernels are disconnected and some semantics/sign conventions are unclear. | Merge | Selected cataloged cost, duration, MAE/MFE, and source-context metrics under internal metrics and report sections. | Refactor | Avoids separate thin modules and unused public functions. |
| CAP-ANLT-013 | Canonical analytics report | V1-CAP-ANALYTICS-012; V1-WF-ANALYTICS-001 | V2-FR-RPT-001–018 | V1 report path works but omits sections, lineage, complete hashes, output validation, and general section criticality. | Modify | One versioned report builder with required/optional section policy, warnings, lineage, hashes, partial mode, and non-binding status. | Refactor | Primary domain workflow. |
| CAP-ANLT-014 | Portfolio analytics report | V1-CAP-ANALYTICS-013; V1-WF-ANALYTICS-009 | V2-API-002; V2-FR-EVID-005–009 | V1 returns fixed zeros and only partially validates currencies. | Modify | Aggregate validated component evidence only after currency/FX checks; no fabricated values. | Replace | Behavior is required, current implementation is not analytical. |
| CAP-ANLT-015 | Report comparison | V1-CAP-ANALYTICS-014; V1-WF-ANALYTICS-010 | V2-API-004; report comparison requirements | V1 returns fixed zero differences. | Modify | Compare schema-compatible report metrics with explicit pairing metadata, omitted/undefined handling, and no source mutation. | Replace | Confirmed use case, placeholder implementation. |
| CAP-ANLT-016 | Strategy-quality evidence | V1-CAP-ANALYTICS-016; V1-WF-ANALYTICS-004 | V2-FR-ENV-022; V2-FR-WARN-004–006 | V1 scorecard is useful but cannot consume the canonical nested report directly and embeds promotion language. | Modify | Consume canonical report sections, emit facts/warnings/non-binding recommendation context, and use owner-approved thresholds only. | Refactor | Preserves review value without governance authority. |
| CAP-ANLT-017 | Dashboard payloads and truncation | V1-CAP-ANALYTICS-017; V1-WF-ANALYTICS-005 | V2-FR-DASH-001–008 | V1 payload is small, return type varies, and truncation may exceed limits. | Modify | Versioned payload from report sections only, one response contract, approved charts, deterministic bounded truncation, section status and warnings. | Refactor | Real downstream need. |
| CAP-ANLT-018 | Warnings, quality flags, and redaction | V1-CAP-ANALYTICS-024; report warnings | V2-FR-WARN-001–008; V2-NFR-008, -034 | V1 duplicates redaction and builds ad hoc warning dictionaries. | Merge | One catalog and builder for warnings/quality flags plus one recursive redaction policy applied to outputs/logs/errors. | Refactor | Safety and consistency. |
| CAP-ANLT-019 | Metric definition catalog | V1-CAP-ANALYTICS-026 | V2-FR-METCAT-001–005 | V1 catalog exists but does not govern every exposed/report metric or formula edge case. | Modify | Authoritative catalog for every approved report/scorecard/dashboard metric, including formulas, units, defaults, undefined behavior, confidence, and fixtures. | Refactor | Needed before locking contracts. |
| CAP-ANLT-020 | Schema compatibility, lineage, and reproducibility | V1-CAP-ANALYTICS-019, -026, -027 | V2-FR-RPT-014–018; V2-NFR-013–017 | V1 has partial schema validation and one report hash but duplicated contracts and incomplete lineage. | Modify | Versioned schemas, approved compatibility matrix, canonical JSON, deterministic hashes, precision metadata, and lineage. | Refactor | Cross-domain reliability. |
| CAP-ANLT-021 | Currency and FX evidence handling | V1 portfolio currency check; V1-CAP-ANALYTICS-013 | V2-FR-EVID-004–009 | V1 only fails mixed currencies without conversions; no lineage/staleness policy. | Add | Require explicit/inherited currency lineage and caller-supplied validated FX; block affected aggregation when missing. | New | Required for truthful portfolio/money analytics. |
| CAP-ANLT-022 | Limits, performance, and deterministic execution | V1-CAP-ANALYTICS-023 | V2-NFR-001, -018–040 | V1 limit helpers are disconnected and exact budgets are absent. | Modify | Enforce approved input/iteration/payload limits at official boundaries; deterministic ordering and parallel equivalence; no initial cache. | Refactor | Safety without infrastructure overdesign. |
| CAP-ANLT-023 | Report serialization | V1-CAP-ANALYTICS-018; V1-WF-ANALYTICS-008 | V2 JSON-safe/report documentation requirements | V1 JSON/Markdown serialization works; empty row/text formatters do not. | Modify | Retain canonical JSON and minimal documented human-readable serialization; remove empty placeholder formatters. | Reuse/Refactor | Proven utility with small cleanup. |
| CAP-ANLT-024 | Prop-firm evidence | V1-CAP-ANALYTICS-015; V1-WF-ANALYTICS-011 | V2-API-005; warning/governance rules | V1 always passes; exact rules/authority are not supplied. | Defer | Remove current calculator; later add only non-binding evidence against caller-supplied, versioned rule profiles. | Remove/New later | Prevents false compliance claims. |
| CAP-ANLT-025 | Live/paper degradation and explainability | No working V1 capability; V1 comparison is placeholder | V2-FR-WARN-009–012 | No stable pairing/evidence contract or proven workflow exists. | Defer | Exclude from initial rebuild; require approved cross-domain pairing and explainability contracts before addition. | New later | High complexity and cross-domain dependencies. |
| CAP-ANLT-026 | Shared audit/event contracts | V1-CAP-ANALYTICS-028 | V2 boundary excludes governance/audit ownership | V1 contains unexported duplicate audit contracts. | Remove | Analytics emits lineage/warnings only; durable audit/event contracts belong to shared Governance/Audit. | Remove | No demonstrated analytics-specific need. |

## 5. V1 Disposition Register
| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
|---|---|---|---|---|---|---|
| `V1-CAP-ANALYTICS-001` | Trading-result canonicalization | `adapters/canonicalize.py` | Essential | **Modify** | Canonical input and adapter capability | n/a |
| `V1-CAP-ANALYTICS-002` | Simulation/live journal adaptation | `journal_adapters.py` | Useful | **Modify** | Canonical input and adapter capability | Remove unapproved journal-specific adapters only after confirming no runtime imports. |
| `V1-CAP-ANALYTICS-003` | Trade outcome analytics | `trade_outcomes.py`, `aggregate.py` | Essential | **Modify** | Internal trade metric kernels | n/a |
| `V1-CAP-ANALYTICS-004` | Equity and return analytics | `equity.py`, `pnl.py`, `curves.py` | Essential | **Modify** | Internal equity, return, and PnL kernels | n/a |
| `V1-CAP-ANALYTICS-005` | Drawdown analytics | `drawdown.py` | Essential | **Modify** | Internal drawdown kernels and report section | n/a |
| `V1-CAP-ANALYTICS-006` | Risk analytics | `risk.py` | Essential | **Split** | Return-risk metrics plus deferred exposure/portfolio-risk metrics | Verify no consumer relies on misleading exposure implementations before removing them. |
| `V1-CAP-ANALYTICS-007` | Ratio analytics | `ratios.py` | Essential | **Modify** | Internal ratio kernels | n/a |
| `V1-CAP-ANALYTICS-008` | Benchmark comparison | `benchmarks/*` | Essential | **Modify** | Benchmark comparison capability | n/a |
| `V1-CAP-ANALYTICS-009` | Distribution profiling | `statistics/distributions.py`, `metrics/distribution.py` | Useful | **Merge** | One distribution/statistics capability | Delete duplicate formulas only after golden fixtures identify the canonical implementation. |
| `V1-CAP-ANALYTICS-010` | Seeded bootstrap/permutation | `statistics/resampling.py` | Useful | **Modify** | Initial deterministic statistical validation capability | n/a |
| `V1-CAP-ANALYTICS-011` | Multiple-testing/overfitting diagnostics | `statistics/multiple_testing.py` | Questionable | **Remove** | Deferred advanced statistical validation | Verify no external caller consumes fixed placeholder values; then remove them. |
| `V1-CAP-ANALYTICS-012` | Canonical report generation | `reports/sections.py`, `tool_api.py` | Essential | **Modify** | Canonical report capability | n/a |
| `V1-CAP-ANALYTICS-013` | Portfolio report | `build_portfolio_analytics_report` | No demonstrated value | **Modify** | Portfolio analytics capability | Replace fixed-zero behavior; verify callers do not depend on placeholder schema. |
| `V1-CAP-ANALYTICS-014` | Report comparison | `compare_analytics_reports` | No demonstrated value | **Modify** | Report comparison capability | Replace fixed-zero behavior; verify callers do not depend on placeholder output. |
| `V1-CAP-ANALYTICS-015` | Prop-firm compliance evidence | `calculate_prop_firm_compliance` | No demonstrated value | **Remove** | Deferred prop-firm evidence capability | Verify no consumer treats the always-pass response as authoritative; remove before production use. |
| `V1-CAP-ANALYTICS-016` | Strategy quality scorecard | `scorecards/quality.py` | Useful | **Modify** | Strategy-quality evidence capability | n/a |
| `V1-CAP-ANALYTICS-017` | Dashboard projection | `dashboards/*` | Useful | **Modify** | Dashboard payload capability | n/a |
| `V1-CAP-ANALYTICS-018` | Report serialization | `reports/formatters.py::serialize_report` | Useful | **Keep** | Report serialization capability | n/a |
| `V1-CAP-ANALYTICS-019` | Deterministic report hashing | `reports/hashes.py` | Useful | **Modify** | Reproducibility hashes in report contracts | Remove MD5 after verifying no compatibility consumer requires it. |
| `V1-CAP-ANALYTICS-020` | Cost analytics | `costs.py`, exposure cost functions | Useful | **Modify** | Cost evidence within metric/report capability | n/a |
| `V1-CAP-ANALYTICS-021` | MAE/MFE and capital efficiency | `efficiency.py` | Useful | **Merge** | Selected efficiency metrics under internal metrics | Remove/defer specialized metrics only after confirming no report or consumer references them. |
| `V1-CAP-ANALYTICS-022` | Time/session analysis | `time_analysis.py` | Useful | **Merge** | Trade/return context metrics under internal metrics | Remove duplicate standalone time-analysis surface after consumer verification. |
| `V1-CAP-ANALYTICS-023` | Workload limit validation | `boundaries/limits.py` | Useful | **Modify** | Official boundary validation and limits | n/a |
| `V1-CAP-ANALYTICS-024` | Redaction and warning evidence | boundaries/contracts warnings | Useful | **Merge** | Canonical warnings, quality flags, and redaction contracts | Delete duplicate redactors after security fixtures select one implementation. |
| `V1-CAP-ANALYTICS-025` | Tool/request registry | `registry/analytics_registry.py` | Questionable | **Remove** | Static official catalog and explicit exports | Verify no dynamic registration/plugin consumer exists before deleting mutable registry state. |
| `V1-CAP-ANALYTICS-026` | Catalog and schema validation | `contracts/metric_catalog.py`, `models.py` | Supporting | **Modify** | Metric catalog and schema compatibility capability | n/a |
| `V1-CAP-ANALYTICS-027` | Portfolio snapshot contracts | `contracts/portfolio.py` | Questionable | **Merge** | Canonical portfolio input/report contracts | Delete duplicate snapshot/base contracts after shared contract mapping is approved. |
| `V1-CAP-ANALYTICS-028` | Audit event contracts | `contracts/audit.py` | Questionable | **Remove** | Shared Governance/Audit domain, not Analytics | Verify no analytics-specific caller imports these unexported contracts. |
| `V1-CAP-ANALYTICS-029` | V1 compatibility aliases | root, adapter init, metrics exports, app root | Questionable | **Remove** | Explicit official exports with temporary deprecation shims only if approved | Inventory external imports and complete a deprecation window before deletion. |
| `V1-CAP-ANALYTICS-030` | Standard read-only tool responses | `app.utils.StandardResponse` wrappers | Supporting | **Modify** | Single canonical analytics response envelope | n/a |

## 6. V2 Requirement Disposition Register
The V2 source did not assign requirement IDs. This register assigns stable IDs in source order within each subsection. Historical metric inventory items remain individually classified even though the V2 document labels them reference-only.

For implementation-heavy items, the **Final requirement direction** column states the accepted behavior and the implementation that is rejected, simplified, deferred, or left open.

### 6.1 Purpose and domain scope
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-SCOPE-001` | Analytics is a read-only, non-binding evidence layer and must not approve, promote, allocate, execute, or claim live readiness. | **Keep** | Retain the read-only, non-binding evidence boundary exactly. | It is supported by V1 side-effect behavior and is a critical safety boundary. |
| `V2-SCOPE-002` | Canonical analytics evidence may be consumed by Simulation, Optimization, Risk review, Portfolio review, Dashboard/UI, Agentic workflows, and Governance/Audit. | **Modify** | Retain these as potential consumers, but approve each concrete cross-domain contract during step 05. | The consumer list is valid context, not proof that every integration exists. |

### 6.2 Ownership
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-OWN-001` | The approved public analytics tool registry exposed by `app.services.analytics.__all__` after official/internal classification is complete. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-002` | Standard analytics tool responses for analytics functions, including success/error status, data payloads, error details, and tool metadata. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-003` | Read-only analytics calculations for trades, returns, equity curves, benchmark curves, distributions, drawdowns, risk statistics, ratios, efficiency, statistical validation, and overview/report payloads. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-004` | Analytics-specific normalization of common caller inputs, such as lists of trade dictionaries into tabular trade inputs and numeric lists into series-like return inputs. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-005` | Closed-trade filtering, trade classification, R-multiple extraction, exposure/time-in-market primitives, and other analytics-only helper behavior. | **Keep** | Retain this as an Analytics-owned internal behavior under the final explicit contracts. | It supports a proven analytics workflow. |
| `V2-OWN-006` | Dashboard-ready and report-ready analytics payload composition. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-007` | Strategy-quality scorecard output based on supplied analytics report material. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-008` | Metric caveats, warnings, and diagnostics that are observable in result payloads. | **Add** | Add this ownership explicitly to the final domain contract and implement it only for approved public/report behavior. | V1 has partial or disconnected support but no single authoritative contract. |
| `V2-OWN-009` | Canonical analytics report schemas, portfolio analytics report schemas, dashboard payload schemas, metric warning objects, quality flag objects, report lineage, and reproducibility hashes. | **Add** | Add this ownership explicitly to the final domain contract and implement it only for approved public/report behavior. | V1 has partial or disconnected support but no single authoritative contract. |
| `V2-OWN-010` | Deterministic analytics adapters that convert `BacktestResult`, `PaperTradingResult`, `LiveTradingResult`, portfolio results, and other normalized caller outputs into a canonical `TradingResult` view without silent field loss; adapters must fail closed with structured errors when required fields, schema versions, or compatibility mappings are missing or incompatible. | **Modify** | Retain the business responsibility but simplify it around explicit high-level tools, canonical contracts, and internal pure kernels. | V1 demonstrates value but its current files/registries/contracts are fragmented. |
| `V2-OWN-011` | An Official Analytics Tool Catalog that defines each public tool name, callable path, stability level, input schema, output schema, error behavior, side-effect policy, risk level, and support status. | **Add** | Add this ownership explicitly to the final domain contract and implement it only for approved public/report behavior. | V1 has partial or disconnected support but no single authoritative contract. |
| `V2-OWN-012` | A Metric Definition Catalog for every official metric exposed through official tools, canonical reports, dashboard payloads, or scorecard evidence. | **Add** | Add this ownership explicitly to the final domain contract and implement it only for approved public/report behavior. | V1 has partial or disconnected support but no single authoritative contract. |
| `V2-OWN-013` | Warning-code and quality-flag catalogs used by analytics reports, portfolio reports, dashboard payloads, and strategy-quality evidence. | **Add** | Add this ownership explicitly to the final domain contract and implement it only for approved public/report behavior. | V1 has partial or disconnected support but no single authoritative contract. |

### 6.3 Excluded responsibilities
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-BOUND-001` | Market-data ingestion, provider adapters, broker account reads, or raw market-data normalization. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-002` | Strategy signal generation, strategy lifecycle promotion, or strategy governance decisions. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-003` | Risk approval, position sizing policy approval, kill-switch behavior, or live-trading authorization. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-004` | Trading order-intent creation, idempotency records, broker submission, paper fills, or execution receipts. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-005` | Simulation runtime, fill modeling, replay orchestration, or optimization run orchestration. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-006` | Durable persistence, migrations, repositories, or local database mutation. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-007` | UI layout, chart rendering, frontend state, or API authentication/authorization. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-008` | Live-readiness certification or claims that a strategy is safe for production trading. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-009` | Financial advice or owner decisions about acceptable thresholds. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-010` | Strategy promotion approval, prop-firm rule enforcement, final portfolio allocation decisions, benchmark/FX source authority, or execution evidence generation. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-011` | Generating, certifying, or repairing missing execution evidence; Analytics may validate, summarize, and warn about supplied evidence only. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-012` | Running simulations, executing backtests, orchestrating optimization searches, or reaching into unstable upstream implementation details. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-013` | Arbitrary file loading, parser selection, file-system traversal, or report-file ingestion inside analytics core; future file loading belongs at adapter boundaries with path safety, file hashes, parser versions, size limits, and schema validation. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |
| `V2-BOUND-014` | Distributed state management, distributed cache invalidation, message queues, or async/background job orchestration; those belong to orchestration and infrastructure layers. | **Keep** | Keep this responsibility outside Analytics; Analytics may consume only normalized, supplied evidence at its boundary. | This boundary prevents execution, governance, persistence, infrastructure, and UI responsibilities from leaking into the domain. |

### 6.4 API and public/internal contract
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-API-001` | Build canonical analytics reports from validated trading results. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-002` | Build portfolio analytics reports from validated portfolio result inputs. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-003` | Evaluate supplied analytics reports into non-binding strategy-quality evidence. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-004` | Compare supplied analytics reports without mutating source reports. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-005` | Calculate approved trade, equity, drawdown, risk, benchmark, statistical-validation, and prop-firm evidence groups when those tool contracts are approved. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-006` | Build dashboard/report payloads from validated report sections without recomputing or fabricating core metrics. | **Keep** | Retain this public/internal boundary rule in the final API contract. | It supports a small, safe public surface. |
| `V2-API-007` | Return official tool results in the standard response envelope with `status`, `message`, `data`, `error`, and `metadata`. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-008` | Internal/support-only functions may calculate trade counts, return streams, drawdowns, ratios, risk statistics, distribution diagnostics, benchmark-relative measures, efficiency metrics, statistical diagnostics, and helper transformations required by official tools. | **Keep** | Retain this public/internal boundary rule in the final API contract. | It supports a small, safe public surface. |
| `V2-API-009` | Internal/support-only functions may exist for developer reuse and tests, but they are not agent/API-facing and do not define the public contract. | **Keep** | Retain this public/internal boundary rule in the final API contract. | It supports a small, safe public surface. |
| `V2-API-010` | Compatibility aliases may exist only when approved in the Official Analytics Tool Catalog or Metric Definition Catalog with stability, deprecation, and collision behavior. | **Modify** | Accept the behavior but expose it through the approved static high-level tool catalog; incomplete tools and compatibility aliases are excluded. | V1’s public surface is oversized or the implementation is incomplete. |
| `V2-API-011` | The official/public contract is the approved high-level tool catalog, not the existence of low-level functions in source files or `__all__`. | **Keep** | Retain this public/internal boundary rule in the final API contract. | It supports a small, safe public surface. |
| `V2-API-012` | A public capability contract table must be approved before Builder implementation and must define name, path, status, stability, schemas, defaults, units, warnings, errors, side effects, risk, and agent/API exposure. | **Add** | Create one concise official-tool contract/catalog before coding. | This replaces V1’s accidental export-driven public API. |

### 6.5 Canonical tool boundaries and metric behavior
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-ENV-001` | The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed. | **Modify** | Expose an explicit, static official tool list; classify collisions in catalogs and keep low-level names internal. | V1’s dynamic 351-name facade and aliases are the main source of ambiguity. |
| `V2-FR-ENV-002` | Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability. | **Modify** | Require `request_id` on every official tool only; internal kernels do not need it. | Traceability belongs at official boundaries, not every private helper. |
| `V2-FR-ENV-003` | Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope. | **Modify** | Official calls require a non-empty safe request ID and return the canonical error envelope on failure. | V1 validation is inconsistent across tools. |
| `V2-FR-ENV-004` | Official analytics tools must be low-risk, read-only operations. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-ENV-005` | Official analytics tools must not write files, modify databases, place trades, or require network access. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-ENV-006` | Official analytics tools must return the standard tool envelope on success and on controlled validation failure. | **Modify** | Use one canonical analytics response envelope for all official tools. | V1 has competing `StandardResponse` and `ToolEnvelope` systems. |
| `V2-FR-ENV-007` | Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags. | **Add** | Add version, timing, request ID, category/risk, and complete side-effect metadata. | V1 metadata is incomplete and inconsistent. |
| `V2-FR-ENV-008` | Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-FR-ENV-009` | Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them. | **Modify** | Normalize pandas/list inputs only at approved adapter/tool boundaries, then pass canonical types internally. | Broad coercion in every kernel would retain V1 ambiguity. |
| `V2-FR-ENV-010` | Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-ENV-011` | Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required. | **Modify** | Use one catalog-defined closed-trade filter covering open and placeholder records. | V1 has useful filtering but needs explicit placeholder semantics. |
| `V2-FR-ENV-012` | Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss. | **Add** | Add a cataloged `breakeven_epsilon` and use it consistently. | Near-zero classification is a confirmed numerical correctness need. |
| `V2-FR-ENV-013` | R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent. | **Modify** | Use explicit risk; allow only named, cataloged proxies and otherwise return undefined/degraded evidence. | V1’s implicit risk=1 fallback changes units and can mislead. |
| `V2-FR-ENV-014` | Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`. | **Add** | Add deterministic ordering and explicit non-finite handling at official boundaries. | V1 often returns neutral values or silently drops invalid observations. |
| `V2-FR-ENV-015` | Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-FR-ENV-016` | Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-ENV-017` | Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-ENV-018` | Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades. | **Modify** | Calculate cost components with documented sign/currency conventions and source lineage. | V1 sums fields but does not fully define gross/net or rebate semantics. |
| `V2-FR-ENV-019` | Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely. | **Modify** | Align by normalized UTC timestamps; non-overlap returns skipped/undefined evidence, not default market values. | V1 truncation/default beta semantics can misrepresent missing evidence. |
| `V2-FR-ENV-020` | Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported. | **Add** | Expose seeds and bounded iteration/config options for the approved initial bootstrap/permutation tools. | Advanced methods remain deferred; deterministic controls are required for retained methods. |
| `V2-FR-ENV-021` | Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-FR-ENV-022` | Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns. | **Modify** | Evaluate the canonical nested report contract and emit non-binding facts/warnings; overfitting warnings only when real evidence exists. | V1 scorecard shape does not compose with V1 report output. |
| `V2-FR-ENV-023` | Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-ENV-024` | The module must separate calculated facts from warnings, caveats, decisions, and recommended actions. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-ENV-025` | Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps. | **Modify** | Use `None`/omission plus warnings for undefined values; prohibit caps such as 999 and fabricated zeros. | V1 uses misleading defaults in several edge cases. |
| `V2-FR-ENV-026` | R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |

### 6.6 Canonical reports and contracts
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-RPT-001` | The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available. | **Modify** | Support canonical reports for approved normalized result phases through adapters; phase-specific sections are conditional. | The behavior is valid, but one report must not imply all source types provide identical evidence. |
| `V2-FR-RPT-002` | Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-FR-RPT-003` | Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss. | **Modify** | Preserve all approved canonical fields and unknown source metadata in a bounded lineage container; fail on conflicting required fields. | Lossless behavior is needed, but unlimited pass-through payloads are unsafe. |
| `V2-FR-RPT-004` | Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response. | **Modify** | Implement a deterministic report pipeline: validate → adapt → calculate approved sections → collect evidence → validate/serialize/hash. | V1 has the core calculation path but lacks complete contracts, hashes, and section handling. |
| `V2-FR-RPT-005` | `AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable. | **Modify** | Initial report includes summary, trade, equity/returns, drawdown, risk, ratios, benchmark, distribution, selected cost/efficiency, warnings, lineage, metadata, and optional dashboard references when applicable. | Do not require empty advanced sections merely for completeness. |
| `V2-FR-RPT-006` | Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed. | **Modify** | Keep the calculated/skipped/failed status model; defer TCA, attribution, dynamic correlation, live degradation, walk-forward, and explainability until their workflows are approved. | The status behavior is valuable; the proposed section list is overbroad for the initial rebuild. |
| `V2-FR-RPT-007` | Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-RPT-008` | Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-RPT-009` | Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values. | **Modify** | Return explicit section status, warnings, lineage, non-promotable flag, and JSON-safe values for partial reports. | V1 partial reporting exists but is benchmark-centric and incomplete. |
| `V2-FR-RPT-010` | Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-RPT-011` | Required-section failure must return an error unless diagnostic partial mode is explicitly enabled. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-RPT-012` | Optional-section failure must produce skipped or failed section metadata without fabricating the missing section. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-RPT-013` | Partial reports must be marked non-promotable and must not be consumed as final approval evidence. | **Modify** | Label partial reports as non-final analytics evidence; governance decides whether they block promotion. | Analytics must not enforce promotion decisions. |
| `V2-FR-RPT-014` | Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-RPT-015` | Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists. | **Add** | Add input/config/report/trade/equity hashes and benchmark hash when present. | V1 only computes a report projection hash. |
| `V2-FR-RPT-016` | Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-RPT-017` | Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields. | **Modify** | Use canonical JSON and one approved numeric normalization/exclusion policy. | V1 hashing is useful but incomplete and also exposes MD5. |
| `V2-FR-RPT-018` | Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |

### 6.7 Official tool surface
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-PUB-001` | Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog. | **Modify** | Expose only approved high-level functions at package root; keep kernels importable only from internal modules for developers/tests. | This directly corrects V1’s oversized facade. |
| `V2-FR-PUB-002` | ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`. | **Open Decision** | Select the exact initial official tool list before README completion and record it in one public-surface decision record. | The candidate list includes incomplete tools and cannot be approved wholesale. |
| `V2-FR-PUB-003` | Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-PUB-004` | Each official public capability must document whether it is safe for agent/API use. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-PUB-005` | Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-PUB-006` | Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog. | **Keep** | Keep all named low-level metrics internal unless separately approved. | The V2 historical inventory is reference material, not a public API commitment. |
| `V2-FR-PUB-007` | Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-PUB-008` | The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports. | **Modify** | Replace the mutable registry with a static catalog plus explicit exports/deprecation metadata. | V1’s registry is unpopulated and adds mutable state. |
| `V2-FR-PUB-009` | Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files. | **Modify** | Agentic callers use the domain root’s approved tools; exact package location is resolved in cross-domain alignment. | Deep imports would bypass the official contract. |
| `V2-FR-PUB-010` | Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-PUB-011` | Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |

### 6.8 Metric Definition Catalog
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-METCAT-001` | Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-METCAT-002` | No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-METCAT-003` | Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-METCAT-004` | Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-METCAT-005` | Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |

### 6.9 Warnings, quality flags, and governance evidence
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-WARN-001` | Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-WARN-002` | Warning severity must support at least informational, warning, major, critical, and blocker-level meanings. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-WARN-003` | Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions. | **Modify** | Separate facts, warnings, score inputs, and recommendation evidence; final governance decisions are external references, never Analytics outputs. | The proposed taxonomy is valid only if Analytics does not own final decisions. |
| `V2-FR-WARN-004` | Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-WARN-005` | Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only. | **Modify** | Label scorecard and any future prop-firm evidence as non-binding; defer the prop-firm calculator until real rule inputs exist. | V1 currently always passes compliance. |
| `V2-FR-WARN-006` | Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-WARN-007` | Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-WARN-008` | Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-WARN-009` | Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing. | **Defer** | Defer live/paper degradation pairing to a later capability with an approved cross-domain comparison contract. | No working V1 workflow or stable upstream contract was confirmed. |
| `V2-FR-WARN-010` | Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores. | **Defer** | Exclude this from the initial rebuild and mark it as a deferred capability. | No proven V1 workflow or immediate consumer justifies the added scope. |
| `V2-FR-WARN-011` | Low-sample explainability drivers must not appear in ranked driver lists. | **Defer** | Exclude this from the initial rebuild and mark it as a deferred capability. | No proven V1 workflow or immediate consumer justifies the added scope. |
| `V2-FR-WARN-012` | Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied. | **Defer** | Exclude this from the initial rebuild and mark it as a deferred capability. | No proven V1 workflow or immediate consumer justifies the added scope. |

### 6.10 Dashboard and API payloads
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-DASH-001` | Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers. | **Modify** | Produce versioned, finite, unit-bearing chart/table payloads from report sections. | V1 has a useful starting payload but lacks complete metadata. |
| `V2-FR-DASH-002` | Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-DASH-003` | If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-DASH-004` | Dashboard/UI consumers must not need to recalculate core metrics. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-DASH-005` | Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation. | **Open Decision** | Approve the initial required/optional chart classes and size limits before implementation. | The full candidate chart list is not justified yet. |
| `V2-FR-DASH-006` | Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist. | **Modify** | Initial payloads: summary cards, equity curve, drawdown curve, warnings, and quality flags; monthly heatmap optional; rolling, cost, distribution, and contribution charts deferred until source sections are approved. | This preserves real UI value without building speculative charts. |
| `V2-FR-DASH-007` | Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings. | **Modify** | Use one audited deterministic algorithm that never exceeds the limit and preserves endpoints plus approved critical points. | V1 decimation can exceed `max_points` and does not preserve all proposed points. |
| `V2-FR-DASH-008` | Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |

### 6.11 Currency, benchmark, and evidence handling
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-EVID-001` | Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-EVID-002` | Strategy and benchmark timestamps must be normalized to UTC before alignment. | **Add** | Normalize all comparison timestamps to UTC at adapter boundaries before alignment. | V1 alignment may discard index semantics. |
| `V2-FR-EVID-003` | Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-EVID-004` | Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists. | **Add** | Without benchmark currency metadata, calculate only explicitly currency-neutral comparisons and emit a warning. | Avoid fabricated cross-currency comparisons. |
| `V2-FR-EVID-005` | Portfolio analytics must not sum raw PnL across different profit currencies. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-FR-EVID-006` | Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies. | **Add** | Require caller-supplied validated FX evidence; Analytics never sources FX. | This preserves the domain boundary. |
| `V2-FR-EVID-007` | Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-FR-EVID-008` | Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used. | **Open Decision** | Resolve FX staleness thresholds and authoritative metadata contract at system level before enabling stale-rate estimates. | FX authority affects Data, Portfolio, Risk, and Analytics. |
| `V2-FR-EVID-009` | All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |

### 6.12 Historical inventory — Benchmark
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-BENCH-001` | `benchmark_returns` shall generate a return series from benchmark equity or price values. | **Keep** | Retain `benchmark_returns` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-BENCH-002` | `beta` shall calculate the strategy beta coefficient relative to benchmark returns. | **Modify** | Refactor `beta` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-BENCH-003` | `alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns. | **Modify** | Refactor `alpha` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-BENCH-004` | `r_squared` shall calculate coefficient of determination between strategy and benchmark returns. | **Modify** | Refactor `r_squared` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-BENCH-005` | `tracking_error` shall calculate annualized tracking error between strategy and benchmark returns. | **Modify** | Refactor `tracking_error` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-BENCH-006` | `information_ratio` shall calculate relative Sharpe-style information ratio. | **Modify** | Refactor `information_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-BENCH-007` | `benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `benchmark_information_ratio` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-BENCH-008` | `relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity. | **Keep** | Retain `relative_drawdown_series` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-BENCH-009` | `max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage. | **Keep** | Retain `max_relative_drawdown_percent` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-BENCH-010` | `batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark. | **Keep** | Retain `batting_average` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-BENCH-011` | `up_down_capture` shall calculate up-capture and down-capture ratios. | **Keep** | Retain `up_down_capture` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-BENCH-012` | `calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta. | **Modify** | Refactor `calculate_benchmark_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.13 Historical inventory — Common
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-COMMON-001` | `get_closed_trades` shall filter trade records to realized closed trades. | **Modify** | Refactor `get_closed_trades` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-COMMON-002` | `classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold. | **Modify** | Refactor `classify_trades` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-COMMON-003` | `avg_loss` shall calculate the mean loss of losing trades. | **Keep** | Retain `avg_loss` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-COMMON-004` | `common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `common_avg_loss` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-COMMON-005` | `get_r_multiples` shall calculate R-multiples for trades. | **Modify** | Refactor `get_r_multiples` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-COMMON-006` | `common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `common_get_r_multiples` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-COMMON-007` | `max_gross_size_held` shall calculate the maximum absolute total size held across positions. | **Modify** | Refactor `max_gross_size_held` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-COMMON-008` | `time_in_market_duration` shall calculate total duration where at least one position was open. | **Keep** | Retain `time_in_market_duration` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-COMMON-009` | `percent_time_in_market` shall calculate percent of the trading period spent in the market. | **Modify** | Refactor `percent_time_in_market` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.14 Historical inventory — Decision Scorecard
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-SCORE-001` | `evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action. | **Modify** | Refactor `evaluate_strategy_quality` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.15 Historical inventory — Distributions
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-DIST-001` | `return_distribution` shall calculate a statistical summary of returns. | **Modify** | Refactor `return_distribution` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-002` | `trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL. | **Modify** | Refactor `trade_pnl_distribution` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-003` | `r_multiple_distribution` shall calculate a statistical summary of R-multiple values. | **Modify** | Refactor `r_multiple_distribution` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-004` | `distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `distributions_r_multiple_distribution` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-DIST-005` | `percentile_summary` shall return selected percentile values. | **Modify** | Refactor `percentile_summary` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-006` | `upside_downside_summary` shall summarize positive and negative outcome distributions. | **Keep** | Retain `upside_downside_summary` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-DIST-007` | `skewness` shall calculate return or value skewness. | **Modify** | Refactor `skewness` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-008` | `kurtosis` shall calculate excess kurtosis. | **Modify** | Refactor `kurtosis` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-009` | `higher_moments` shall calculate detailed skewness and kurtosis context. | **Modify** | Refactor `higher_moments` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-010` | `fat_tail_score` shall estimate tail heaviness relative to normal behavior. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `fat_tail_score` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-DIST-011` | `tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes. | **Modify** | Refactor `tail_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-012` | `jarque_bera_test` shall run a Jarque-Bera normality diagnostic. | **Modify** | Refactor `jarque_bera_test` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DIST-013` | `shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic. | **Defer** | Exclude `shapiro_wilk_test` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-014` | `qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting. | **Defer** | Exclude `qq_plot_data` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-015` | `fit_distribution` shall fit a theoretical distribution and return fit parameters. | **Defer** | Exclude `fit_distribution` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-016` | `distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria. | **Defer** | Exclude `distribution_fit_quality` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-017` | `histogram_data` shall generate histogram bin data for plotting. | **Add** | Add `histogram_data` as an internal helper only when required by an approved report/dashboard section. | The behavior is useful but is not an official public tool. |
| `V2-FR-HIST-DIST-018` | `detect_outliers` shall identify outliers with the requested method and threshold. | **Defer** | Exclude `detect_outliers` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-019` | `outlier_ratio` shall calculate the percentage of data points flagged as outliers. | **Defer** | Exclude `outlier_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DIST-020` | `calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values. | **Modify** | Refactor `calculate_distribution_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.16 Historical inventory — Drawdowns
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-DD-001` | `drawdown_series` shall calculate drawdown values from an equity curve. | **Modify** | Refactor `drawdown_series` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-002` | `drawdown_duration_series` shall calculate drawdown duration values from an equity curve. | **Modify** | Refactor `drawdown_duration_series` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-003` | `max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units. | **Modify** | Refactor `max_strategy_drawdown` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-004` | `max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak. | **Modify** | Refactor `max_strategy_drawdown_percent` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-005` | `max_drawdown` shall calculate maximum drawdown from returns. | **Modify** | Refactor `max_drawdown` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-006` | `avg_drawdown` shall calculate average drawdown depth. | **Modify** | Refactor `avg_drawdown` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-007` | `drawdown_distribution` shall calculate detailed drawdown distribution statistics. | **Defer** | Exclude `drawdown_distribution` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-008` | `max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values. | **Modify** | Refactor `max_drawdown_duration_from_equity` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-009` | `max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values. | **Modify** | Refactor `max_drawdown_duration_from_returns` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-010` | `max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type. | **Modify** | Refactor `max_drawdown_duration` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-011` | `avg_drawdown_duration` shall calculate average duration of drawdown episodes. | **Modify** | Refactor `avg_drawdown_duration` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-012` | `time_to_recovery` shall calculate recovery periods for unique drawdowns. | **Modify** | Refactor `time_to_recovery` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-013` | `recovery_factor` shall calculate net profit relative to maximum drawdown. | **Modify** | Refactor `recovery_factor` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-014` | `trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points. | **Defer** | Exclude `trade_level_drawdowns` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-015` | `max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available. | **Defer** | Exclude `max_close_to_close_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-016` | `max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage. | **Defer** | Exclude `max_close_to_close_drawdown_percent` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-017` | `avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth. | **Defer** | Exclude `avg_trade_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-018` | `account_size_required` shall estimate capital required to withstand max close-to-close dips. | **Defer** | Exclude `account_size_required` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-019` | `max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown. | **Defer** | Exclude `max_consecutive_drawdown_trades` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-020` | `avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year. | **Defer** | Exclude `avg_yearly_max_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-021` | `max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley. | **Modify** | Refactor `max_strategy_drawdown_date` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-022` | `max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley. | **Modify** | Refactor `max_close_to_close_drawdown_date` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-023` | `ulcer_index` shall calculate squared-drawdown-based ulcer index. | **Modify** | Refactor `ulcer_index` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-DD-024` | `pain_index` shall calculate mean absolute percentage drawdown. | **Defer** | Exclude `pain_index` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-025` | `avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak. | **Defer** | Exclude `avg_underwater_drawdown_percent` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-026` | `pain_ratio` shall calculate return relative to pain index. | **Defer** | Exclude `pain_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-DD-027` | `calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve. | **Modify** | Refactor `calculate_drawdown_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.17 Historical inventory — Efficiency
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-EFF-001` | `capital_efficiency` shall calculate return per unit of nominal capital deployed. | **Defer** | Exclude `capital_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-002` | `avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name. | **Defer** | Exclude `avg_trade_notional_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-003` | `return_per_unit_mae` shall calculate total return relative to adverse excursion experienced. | **Keep** | Retain `return_per_unit_mae` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-EFF-004` | `risk_adjusted_efficiency` shall calculate return relative to total defined initial risk. | **Defer** | Exclude `risk_adjusted_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-005` | `avg_return_per_risk_unit` shall calculate average R-multiple per closed trade. | **Modify** | Refactor `avg_return_per_risk_unit` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-006` | `return_per_trade_hour` shall calculate net profit per hour spent in active trades. | **Modify** | Refactor `return_per_trade_hour` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-007` | `return_per_market_hour` shall calculate net profit per hour where at least one trade was open. | **Modify** | Refactor `return_per_market_hour` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-008` | `trades_per_day` shall calculate average number of closed trades per calendar day in the test period. | **Defer** | Exclude `trades_per_day` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-009` | `return_per_calendar_day` shall calculate net profit per calendar day in the test period. | **Modify** | Refactor `return_per_calendar_day` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-010` | `profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days. | **Defer** | Exclude `profit_per_trade_per_day` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-011` | `mfe_efficiency` shall calculate average percentage of MFE captured by winning trades. | **Modify** | Refactor `mfe_efficiency` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-012` | `aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades. | **Modify** | Refactor `aggregate_mfe_capture_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-013` | `profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips. | **Defer** | Exclude `profit_per_pip_risk` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-014` | `mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades. | **Defer** | Exclude `mae_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-015` | `exit_efficiency` shall calculate combined win-capture and loss-containment efficiency. | **Defer** | Exclude `exit_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-016` | `loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion. | **Modify** | Refactor `loss_containment_efficiency` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-017` | `aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades. | **Modify** | Refactor `aggregate_loss_containment_efficiency` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-EFF-018` | `position_size_efficiency` shall calculate relationship between position size and normalized trade outcome. | **Defer** | Exclude `position_size_efficiency` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-EFF-019` | `calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades. | **Modify** | Refactor `calculate_efficiency_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.18 Historical inventory — Metrics
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-METRIC-001` | `metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_get_r_multiples` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-002` | `get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics. | **Modify** | Refactor `get_ordered_closed_trades` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-003` | `win_rate_fraction` shall calculate win rate on a 0-to-1 scale. | **Keep** | Retain `win_rate_fraction` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-004` | `metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_win_rate_fraction` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-005` | `avg_win_loss` shall calculate mean winning and losing outcomes. | **Keep** | Retain `avg_win_loss` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-006` | `consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes. | **Keep** | Retain `consecutive_wins_losses` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-007` | `median_mae_mfe` shall calculate median MAE and MFE values. | **Keep** | Retain `median_mae_mfe` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-008` | `get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space. | **Keep** | Retain `get_mae_mfe_r` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-009` | `t_statistic` shall calculate the t-statistic for mean outcome. | **Defer** | Exclude `t_statistic` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-010` | `open_position_pnl` shall calculate total unrealized PnL from open positions. | **Modify** | Refactor `open_position_pnl` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-011` | `total_trades` shall count closed trades. | **Keep** | Retain `total_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-012` | `winning_trades` shall count closed winning trades. | **Keep** | Retain `winning_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-013` | `losing_trades` shall count closed losing trades. | **Keep** | Retain `losing_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-014` | `breakeven_trades` shall count closed breakeven trades. | **Keep** | Retain `breakeven_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-015` | `long_trades` shall count closed long trades. | **Keep** | Retain `long_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-016` | `short_trades` shall count closed short trades. | **Keep** | Retain `short_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-017` | `count_open_trades` shall count currently open trades. | **Keep** | Retain `count_open_trades` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-018` | `slippage_paid` shall calculate total absolute slippage costs paid. | **Modify** | Refactor `slippage_paid` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-019` | `commission_paid` shall calculate total absolute commission costs paid. | **Modify** | Refactor `commission_paid` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-020` | `swap_paid` shall calculate total absolute swap costs paid. | **Modify** | Refactor `swap_paid` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-021` | `win_rate` shall calculate percentage of winning trades. | **Modify** | Refactor `win_rate` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-022` | `loss_rate` shall calculate percentage of losing trades. | **Modify** | Refactor `loss_rate` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-023` | `avg_win` shall calculate mean profit of winning trades. | **Keep** | Retain `avg_win` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-024` | `metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_avg_loss` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-025` | `largest_win` shall calculate maximum single-trade profit. | **Keep** | Retain `largest_win` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-026` | `largest_loss` shall calculate maximum single-trade loss. | **Keep** | Retain `largest_loss` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-027` | `median_win` shall calculate median PnL of winning trades. | **Keep** | Retain `median_win` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-028` | `median_loss` shall calculate median PnL of losing trades. | **Keep** | Retain `median_loss` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-029` | `expectancy` shall calculate trade expectancy. | **Modify** | Refactor `expectancy` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-030` | `metrics_expectancy` shall expose metrics-module expectancy behavior without colliding with ratios exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_expectancy` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-031` | `expectancy_r` shall calculate R-expectancy. | **Modify** | Refactor `expectancy_r` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-032` | `metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_expectancy_r` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-033` | `max_size_held` shall calculate maximum total contracts held. | **Modify** | Refactor `max_size_held` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-034` | `max_net_size_held` shall calculate maximum net directional size held. | **Modify** | Refactor `max_net_size_held` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-035` | `max_long_size_held` shall calculate maximum total long contracts held. | **Modify** | Refactor `max_long_size_held` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-036` | `max_short_size_held` shall calculate maximum total short contracts held. | **Modify** | Refactor `max_short_size_held` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-037` | `avg_r_multiple` shall calculate average R-multiple. | **Keep** | Retain `avg_r_multiple` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-038` | `median_r_multiple` shall calculate median R-multiple. | **Keep** | Retain `median_r_multiple` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-039` | `metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `metrics_r_multiple_distribution` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-040` | `r_expectancy` shall calculate R-space expectancy. | **Keep** | Retain `r_expectancy` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-041` | `max_r_multiple` shall calculate maximum R-multiple. | **Keep** | Retain `max_r_multiple` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-042` | `min_r_multiple` shall calculate minimum R-multiple. | **Keep** | Retain `min_r_multiple` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-043` | `median_mae_r` shall calculate median MAE in R-multiple terms. | **Keep** | Retain `median_mae_r` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-044` | `median_mfe_r` shall calculate median MFE in R-multiple terms. | **Keep** | Retain `median_mfe_r` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-045` | `max_consecutive_wins` shall calculate maximum consecutive winning trades. | **Keep** | Retain `max_consecutive_wins` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-046` | `max_consecutive_losses` shall calculate maximum consecutive losing trades. | **Keep** | Retain `max_consecutive_losses` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-047` | `avg_consecutive_wins` shall calculate average length of winning streaks. | **Keep** | Retain `avg_consecutive_wins` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-048` | `avg_consecutive_losses` shall calculate average length of losing streaks. | **Keep** | Retain `avg_consecutive_losses` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-049` | `win_loss_streaks` shall return winning and losing streak sequences. | **Keep** | Retain `win_loss_streaks` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-050` | `avg_time_in_trade` shall calculate average trade duration. | **Keep** | Retain `avg_time_in_trade` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-051` | `median_time_in_trade` shall calculate median trade duration. | **Keep** | Retain `median_time_in_trade` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-052` | `max_time_in_trade` shall calculate maximum trade duration. | **Keep** | Retain `max_time_in_trade` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-053` | `min_time_in_trade` shall calculate minimum trade duration. | **Keep** | Retain `min_time_in_trade` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-054` | `sqn` shall calculate system quality number. | **Modify** | Refactor `sqn` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-055` | `kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns. | **Defer** | Exclude `kelly_criterion` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-056` | `compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs. | **Modify** | Refactor `compute_r_trade_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-057` | `compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `compute_trade_metrics` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-METRIC-058` | `compute_equity_metrics` shall calculate equity metrics from return inputs. | **Modify** | Refactor `compute_equity_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-059` | `trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion. | **Modify** | Refactor `trade_efficiency` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-METRIC-060` | `r_signal_to_noise` shall calculate mean R relative to R volatility. | **Defer** | Exclude `r_signal_to_noise` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-061` | `rolling_expectancy_stability` shall calculate expectancy stability over a rolling window. | **Defer** | Exclude `rolling_expectancy_stability` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-062` | `win_after_win_probability` shall calculate probability that a win follows a win. | **Defer** | Exclude `win_after_win_probability` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-063` | `runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score. | **Defer** | Exclude `runs_test_zscore` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-064` | `trading_period_duration` shall calculate total duration of the trading period. | **Keep** | Retain `trading_period_duration` as an internal cataloged metric kernel; expose it only through approved grouped tools/reports. | V1 already provides useful behavior and no major gap was identified. |
| `V2-FR-HIST-METRIC-065` | `trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes. | **Defer** | Exclude `trade_outcome_entropy` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-066` | `longest_flat_period_duration` shall calculate longest period without an active trade. | **Defer** | Exclude `longest_flat_period_duration` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-METRIC-067` | `calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records. | **Modify** | Refactor `calculate_trade_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.19 Historical inventory — Overview
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-OVR-001` | `calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset. | **Modify** | Refactor `calculate_analytics_for_subset` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-002` | `get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets. | **Modify** | Refactor `get_analytics_overview` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-003` | `format_summary_as_rows` shall format raw summary data into report/display rows. | **Reject** | Do not create `format_summary_as_rows` as a final requirement; use the canonical report/dashboard workflow instead. | V1 provides no demonstrated implementation value and no independent workflow requires it. |
| `V2-FR-HIST-OVR-004` | `build_overview_payload` shall build the API/dashboard analytics overview payload. | **Modify** | Refactor `build_overview_payload` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-005` | `calculate_spread_cost_impact` shall calculate spread cost drag. | **Modify** | Refactor `calculate_spread_cost_impact` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-006` | `calculate_slippage_impact` shall calculate slippage cost drag. | **Modify** | Refactor `calculate_slippage_impact` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-007` | `calculate_commission_impact` shall calculate commission cost drag. | **Modify** | Refactor `calculate_commission_impact` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-OVR-008` | `build_backtest_report` shall build a structured backtest analytics report payload. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `build_backtest_report` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |

### 6.20 Historical inventory — Ratios
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-RATIO-001` | `ratios_win_rate_fraction` shall expose ratios-module win-rate fraction behavior without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `ratios_win_rate_fraction` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RATIO-002` | `sharpe_ratio` shall calculate excess return per unit of volatility. | **Modify** | Refactor `sharpe_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-003` | `annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs. | **Modify** | Refactor `annualized_sharpe_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-004` | `sortino_ratio` shall calculate excess return per unit of downside volatility. | **Modify** | Refactor `sortino_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-005` | `calmar_ratio` shall calculate annualized return relative to maximum drawdown. | **Modify** | Refactor `calmar_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-006` | `ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `ratios_information_ratio` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RATIO-007` | `fouse_ratio` shall calculate Fouse drawdown-index-style ratio. | **Defer** | Exclude `fouse_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-008` | `upside_potential_ratio` shall calculate upside potential relative to downside risk. | **Defer** | Exclude `upside_potential_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-009` | `omega_ratio` shall calculate probability-weighted gains relative to losses. | **Modify** | Refactor `omega_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-010` | `gain_to_pain_ratio` shall calculate gains relative to absolute negative returns. | **Modify** | Refactor `gain_to_pain_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-011` | `kappa_ratio` shall calculate generalized Sortino-style Kappa ratio. | **Defer** | Exclude `kappa_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-012` | `sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown. | **Defer** | Exclude `sterling_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-013` | `rina_index` shall calculate select net profit relative to average drawdown and time in market. | **Defer** | Exclude `rina_index` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-014` | `profit_factor` shall calculate gross profit relative to gross loss. | **Modify** | Refactor `profit_factor` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-015` | `payoff_ratio` shall calculate average win relative to average loss. | **Modify** | Refactor `payoff_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-016` | `edge_ratio` shall calculate payoff edge adjusted by win rate. | **Defer** | Exclude `edge_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-017` | `profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion. | **Modify** | Refactor `profit_to_mae_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-018` | `mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion. | **Modify** | Refactor `mfe_to_mae_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RATIO-019` | `return_over_drawdown` shall calculate total return relative to maximum trade drawdown. | **Defer** | Exclude `return_over_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-020` | `expectancy_over_std` shall calculate expectancy stability relative to standard deviation. | **Defer** | Exclude `expectancy_over_std` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-021` | `net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss. | **Defer** | Exclude `net_profit_as_percent_of_largest_loss` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-022` | `net_profit_as_percent_of_max_trade_drawdown` shall calculate net profit as a percentage of max trade drawdown. | **Defer** | Exclude `net_profit_as_percent_of_max_trade_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-023` | `net_profit_as_percent_of_max_strategy_drawdown` shall calculate net profit as a percentage of max strategy drawdown. | **Defer** | Exclude `net_profit_as_percent_of_max_strategy_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-024` | `select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss. | **Defer** | Exclude `select_net_profit_as_percent_of_largest_loss` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-025` | `select_net_profit_as_percent_of_max_trade_drawdown` shall calculate selected net profit as a percentage of max trade drawdown. | **Defer** | Exclude `select_net_profit_as_percent_of_max_trade_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-026` | `select_net_profit_as_percent_of_max_strategy_drawdown` shall calculate selected net profit as a percentage of max strategy drawdown. | **Defer** | Exclude `select_net_profit_as_percent_of_max_strategy_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-027` | `adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss. | **Defer** | Exclude `adjusted_net_profit_as_percent_of_largest_loss` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-028` | `adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown. | **Defer** | Exclude `adjusted_net_profit_as_percent_of_max_trade_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-029` | `adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown. | **Defer** | Exclude `adjusted_net_profit_as_percent_of_max_strategy_drawdown` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-030` | `adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss. | **Defer** | Exclude `adjusted_profit_factor` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-031` | `select_profit_factor` shall calculate selected gross profit relative to selected gross loss. | **Defer** | Exclude `select_profit_factor` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RATIO-032` | `ratios_expectancy` shall expose ratios-module expectancy behavior without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `ratios_expectancy` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RATIO-033` | `ratios_expectancy_r` shall expose ratios-module R-expectancy behavior without colliding with metrics exports. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `ratios_expectancy_r` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RATIO-034` | `calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values. | **Modify** | Refactor `calculate_ratio_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.21 Historical inventory — Returns
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-RET-001` | `total_return_usd` shall calculate total return in currency units from an equity curve. | **Modify** | Refactor `total_return_usd` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-002` | `total_return` shall calculate total return as a percentage of initial capital. | **Modify** | Refactor `total_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-003` | `net_profit` shall calculate total realized profit or loss from closed trades. | **Modify** | Refactor `net_profit` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-004` | `gross_profit` shall sum winning closed-trade profit. | **Modify** | Refactor `gross_profit` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-005` | `gross_loss` shall sum losing closed-trade loss. | **Modify** | Refactor `gross_loss` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-006` | `balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades. | **Modify** | Refactor `balance_curve_from_closed_trades` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-007` | `balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `balance_curve` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RET-008` | `equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `equity_curve` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-RET-009` | `returns_series` shall calculate percentage returns between equity points. | **Modify** | Refactor `returns_series` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-010` | `log_returns_series` shall calculate logarithmic returns between equity points. | **Modify** | Refactor `log_returns_series` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-011` | `daily_returns` shall calculate daily percentage returns from an equity curve. | **Modify** | Refactor `daily_returns` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-012` | `weekly_returns` shall calculate weekly percentage returns from an equity curve. | **Modify** | Refactor `weekly_returns` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-013` | `monthly_returns` shall calculate monthly percentage returns from an equity curve. | **Modify** | Refactor `monthly_returns` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-014` | `annual_returns` shall calculate annual percentage returns from an equity curve. | **Modify** | Refactor `annual_returns` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-015` | `cagr` shall calculate compound annual growth rate. | **Modify** | Refactor `cagr` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-016` | `compound_monthly_growth_rate` shall calculate compound monthly growth rate. | **Modify** | Refactor `compound_monthly_growth_rate` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-017` | `avg_monthly_return` shall calculate arithmetic average monthly return. | **Modify** | Refactor `avg_monthly_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-018` | `monthly_return_stddev` shall calculate monthly return volatility. | **Modify** | Refactor `monthly_return_stddev` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-019` | `annualized_return` shall calculate geometric annualized return. | **Modify** | Refactor `annualized_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-020` | `geometric_mean_return` shall calculate geometric mean return. | **Modify** | Refactor `geometric_mean_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-021` | `best_return` shall calculate best single-period return. | **Modify** | Refactor `best_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-022` | `worst_return` shall calculate worst single-period return. | **Modify** | Refactor `worst_return` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-023` | `buy_and_hold_return` shall calculate total buy-and-hold return from price data. | **Defer** | Exclude `buy_and_hold_return` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-024` | `buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data. | **Defer** | Exclude `buy_and_hold_cagr` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-025` | `return_volatility` shall calculate return standard deviation. | **Modify** | Refactor `return_volatility` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-026` | `downside_return_volatility` shall calculate volatility of returns below target. | **Modify** | Refactor `downside_return_volatility` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-027` | `return_skewness` shall calculate return-distribution skewness. | **Modify** | Refactor `return_skewness` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-028` | `return_kurtosis` shall calculate return-distribution excess kurtosis. | **Modify** | Refactor `return_kurtosis` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-029` | `adjusted_gross_profit` shall calculate adjusted gross profit. | **Defer** | Exclude `adjusted_gross_profit` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-030` | `adjusted_gross_loss` shall calculate adjusted gross loss. | **Defer** | Exclude `adjusted_gross_loss` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-031` | `adjusted_net_profit` shall calculate adjusted net profit. | **Defer** | Exclude `adjusted_net_profit` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-032` | `select_net_profit` shall calculate net profit after outlier selection. | **Defer** | Exclude `select_net_profit` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-033` | `select_gross_profit` shall calculate gross profit after outlier selection. | **Defer** | Exclude `select_gross_profit` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-034` | `select_gross_loss` shall calculate gross loss after outlier selection. | **Defer** | Exclude `select_gross_loss` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-035` | `return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown. | **Modify** | Refactor `return_on_max_strategy_drawdown` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-036` | `return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown. | **Modify** | Refactor `return_on_max_close_to_close_drawdown` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-037` | `return_on_account` shall calculate return on required account size. | **Defer** | Exclude `return_on_account` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-038` | `return_on_initial_capital` shall calculate net profit as a percentage of initial capital. | **Modify** | Refactor `return_on_initial_capital` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-039` | `max_runup` shall calculate maximum gain from valley to peak. | **Modify** | Refactor `max_runup` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-040` | `max_runup_date` shall identify the timestamp of maximum runup peak. | **Modify** | Refactor `max_runup_date` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-041` | `calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve. | **Modify** | Refactor `calculate_return_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-042` | `calculate_period_analysis` shall calculate performance by timestamp bucket. | **Defer** | Exclude `calculate_period_analysis` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RET-043` | `calculate_long_short_split` shall calculate long-versus-short profit split. | **Modify** | Refactor `calculate_long_short_split` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RET-044` | `calculate_session_performance` shall calculate session performance from timestamped records. | **Defer** | Exclude `calculate_session_performance` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |

### 6.22 Historical inventory — Risks
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-RISK-001` | `volatility` shall calculate return standard deviation as a positive percentage. | **Modify** | Refactor `volatility` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-002` | `annualized_volatility` shall calculate annualized volatility as a positive percentage. | **Modify** | Refactor `annualized_volatility` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-003` | `downside_volatility` shall calculate downside deviation as a positive percentage. | **Modify** | Refactor `downside_volatility` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-004` | `value_at_risk` shall calculate value-at-risk as a positive percentage. | **Modify** | Refactor `value_at_risk` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-005` | `conditional_var` shall calculate conditional value-at-risk as a positive percentage. | **Modify** | Refactor `conditional_var` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-006` | `expected_shortfall` shall calculate expected shortfall. | **Modify** | Refactor `expected_shortfall` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-007` | `max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold. | **Defer** | Exclude `max_loss_probability` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-008` | `drawdown_probability` shall calculate probability of drawdown exceeding a threshold. | **Defer** | Exclude `drawdown_probability` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-009` | `risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes. | **Defer** | Exclude `risk_of_ruin` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-010` | `max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time. | **Defer** | Exclude `max_nominal_exposure_simple` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-011` | `max_gross_exposure` shall calculate maximum gross nominal exposure. | **Defer** | Exclude `max_gross_exposure` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-012` | `avg_trade_nominal_exposure` shall calculate average nominal exposure per trade. | **Defer** | Exclude `avg_trade_nominal_exposure` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-013` | `exposure_time_ratio` shall calculate percentage of total period spent in market. | **Modify** | Refactor `exposure_time_ratio` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-RISK-014` | `max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity. | **Defer** | Exclude `max_single_trade_margin_utilization` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-015` | `avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity. | **Defer** | Exclude `avg_single_trade_margin_utilization` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-016` | `time_weighted_avg_exposure` shall calculate time-weighted average notional exposure. | **Defer** | Exclude `time_weighted_avg_exposure` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-017` | `portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time. | **Defer** | Exclude `portfolio_margin_utilization_curve` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-018` | `compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk. | **Defer** | Exclude `compounding_risk_of_ruin` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-019` | `risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon. | **Defer** | Exclude `risk_of_ruin_with_custom_horizon` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-020` | `historical_var_by_symbol` shall calculate historical value-at-risk by symbol. | **Defer** | Exclude `historical_var_by_symbol` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-021` | `portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights. | **Defer** | Exclude `portfolio_var_from_covariance` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-RISK-022` | `calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility. | **Modify** | Refactor `calculate_risk_metrics` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |

### 6.23 Historical inventory — Statistical Tests
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-FR-HIST-STAT-001` | `whites_reality_check` shall assess data-snooping bias with White's Reality Check. | **Defer** | Exclude `whites_reality_check` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-002` | `permutation_test` shall run significance testing through random reshuffling or sign-flipping. | **Modify** | Refactor `permutation_test` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-003` | `bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap. | **Modify** | Refactor `bootstrap_confidence_intervals` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-004` | `deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality. | **Defer** | Exclude `deflated_sharpe_ratio` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-005` | `probability_of_backtest_overfitting` shall estimate probability of backtest overfitting. | **Defer** | Exclude `probability_of_backtest_overfitting` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-006` | `walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores. | **Defer** | Exclude `walk_forward_degradation_score` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-007` | `bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold. | **Modify** | Refactor `bootstrap_probability_above_threshold` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-008` | `bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing. | **Modify** | Refactor `bonferroni_correction` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-009` | `benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control. | **Modify** | Refactor `benjamini_hochberg_correction` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-010` | `sample_size_warning` shall assess metric reliability based on sample size. | **Modify** | Refactor `sample_size_warning` into a single internal cataloged kernel with explicit inputs, units, formula, undefined-result rules, warnings, and tests. | V1 provides useful behavior, but its contract or edge semantics are not sufficient for the final design. |
| `V2-FR-HIST-STAT-011` | `stability_score` shall calculate performance consistency across walk-forward windows. | **Defer** | Exclude `stability_score` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-012` | `whites_reality_check_backtests` shall run White's Reality Check against backtest result objects. | **Defer** | Exclude `whites_reality_check_backtests` from the initial rebuild; reconsider only with an approved formula, inputs, workflow, and metric-catalog entry. | It is specialized, currently disconnected, approximate, or placeholder behavior. |
| `V2-FR-HIST-STAT-013` | `permutation_test_backtest` shall run permutation testing against a backtest result object. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `permutation_test_backtest` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-STAT-014` | `bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object. | **Merge** | Retain the behavior, if needed, under one canonical internal metric name; do not preserve `bootstrap_confidence_intervals_backtest` as a separate public capability. | This item is an alias, duplicate, or equivalent wrapper and would inflate the surface. |
| `V2-FR-HIST-STAT-015` | `print_statistical_validation_report` shall package a comprehensive statistical validation report. | **Reject** | Do not create `print_statistical_validation_report` as a final requirement; use the canonical report/dashboard workflow instead. | V1 provides no demonstrated implementation value and no independent workflow requires it. |

### 6.24 Non-functional requirements
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-NFR-001` | Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-NFR-002` | Analytics functions must be read-only and side-effect free at the domain level. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-003` | Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-004` | Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-NFR-005` | The module must degrade safely when optional acceleration libraries are unavailable. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-006` | Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded. | **Modify** | Prefer vectorized implementations when justified; otherwise enforce input/runtime limits. Do not require a chunking framework before benchmarks prove it is needed. | The proposed implementation prescription is premature. |
| `V2-NFR-007` | Tool metadata must consistently identify the category as `analytics` and risk level as `low`. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-008` | Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-009` | The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-010` | Public registry changes must remain auditable through tests and catalog updates. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-011` | Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-012` | Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-013` | Report generation must be idempotent for the same input, configuration, and analytics engine version. | **Modify** | Make deterministic report content and hashes idempotent; generation timestamp and execution timing remain non-deterministic metadata excluded from hashes. | Absolute byte-for-byte idempotence conflicts with timestamp metadata. |
| `V2-NFR-014` | Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-015` | Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-016` | All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-017` | Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely. | **Add** | Require explicit frequency/annualization configuration or return undefined evidence; never silently assume 252 when frequency is unknown. | V1 often assumes daily 252. |
| `V2-NFR-018` | Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-019` | Metric kernels must not depend on mutable global calculation state. | **Modify** | Remove mutable calculation/registration state from metric execution; immutable catalogs are allowed. | V1 has mutable request/tool registries. |
| `V2-NFR-020` | Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version. | **Defer** | No cache in the initial rebuild; apply these rules only if a later measured need approves caching. | No V1 cache or demonstrated bottleneck exists. |
| `V2-NFR-021` | Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff. | **Defer** | Defer cache design entirely until a cache capability is approved. | TTL/locks/single-flight are unnecessary initial complexity. |
| `V2-NFR-022` | Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes. | **Defer** | Defer cache invariance tests with the cache capability; retain general deterministic-output tests now. | There is no initial cache. |
| `V2-NFR-023` | Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-024` | Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-025` | Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-026` | Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-NFR-027` | Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts. | **Modify** | Use `Decimal` for canonical monetary contracts, aggregation, and hashing; conversion from source floats must be explicit and documented. | Applying Decimal to every internal intermediate is unnecessary. |
| `V2-NFR-028` | Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata. | **Modify** | Use float64 for derived statistical ratios with cataloged tolerances and finite-result checks. | This is proportionate to statistical calculations. |
| `V2-NFR-029` | Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-030` | Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined. | **Modify** | Retain the behavioral intent but refactor the contract/implementation to fit the canonical, minimal design. | V1 provides partial value or V2 prescribes more complexity than necessary. |
| `V2-NFR-031` | Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-032` | Portfolio aggregation must fail closed when required base-currency conversion is unavailable. | **Keep** | Retain this behavior substantially unchanged, with final naming and catalog documentation. | V1 already demonstrates the required value. |
| `V2-NFR-033` | Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts. | **Open Decision** | Define mappings against shared upstream/downstream contracts during pipeline step 05. | This is a cross-domain contract decision. |
| `V2-NFR-034` | Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-035` | The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-036` | The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-037` | The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-038` | ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff. | **Modify** | Record limits and benchmark assumptions in one consolidated Analytics limits/performance decision, not necessarily a standalone ADR per topic. | Exact values are still open. |
| `V2-NFR-039` | `build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff. | **Add** | Add this behavior to the final contract using pure internal functions and the canonical official-tool/report boundary. | The requirement supports correctness, safety, traceability, or a confirmed consumer but V1 lacks it. |
| `V2-NFR-040` | Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits. | **Modify** | Make performance tests a handoff gate only after approved fixtures and limits exist. | Do not block design work on undefined benchmarks. |

### 6.25 Edge-case requirements
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-EDGE-001` | Empty trade records, empty return arrays, empty equity curves, and empty benchmark series. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-002` | Missing required columns such as `profit_loss`, `open_time`, `close_time`, trade direction, size/quantity/volume, cost fields, MAE/MFE fields, or initial-risk fields. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-003` | Open trades mixed with closed trades. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-004` | End-of-data placeholder exits mixed with true closed exits. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-005` | Zero gross loss, zero gross profit, zero drawdown, zero volatility, zero benchmark variance, zero account equity, or zero initial capital. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-006` | Negative or non-positive equity values in percent-return and drawdown calculations. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-007` | Duplicate timestamps, unsorted timestamps, overlapping trade intervals, simultaneous open/close events, and close timestamps before open timestamps. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-008` | NaN, infinity, strings in numeric fields, malformed timestamps, and partially missing rows. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-009` | Trade records with different size field names. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-010` | All winning trades, all losing trades, all breakeven trades, or no trades after closed-trade filtering. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-011` | Non-overlapping strategy and benchmark return indexes. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-012` | Benchmark supplied as equity/prices instead of returns. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-013` | Very small sample sizes for statistical tests or scorecard decisions. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-014` | Bootstrap/permutation counts that are too small to support meaningful inference or too large for practical runtime. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-015` | Multiple-testing inputs with invalid p-values or mismatched score arrays. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-016` | Distribution fitting on constant data, very short samples, heavy outliers, or unsupported distribution names. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-017` | Mixed long/short direction labels or missing direction labels. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-018` | Cost-impact calculations where gross profit is zero or negative. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-019` | Report payloads missing expected summary, ratio, drawdown, metric, or statistical-validation sections. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-020` | Values that serialize poorly, such as pandas timestamps, timedeltas, series, dataframes, NumPy scalars, or arrays. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-021` | Empty trade ledger with configured minimum trades set to zero. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-022` | Empty trade ledger with configured minimum trades greater than zero. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-023` | Equity curve with only one point. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-024` | Flat equity curve where volatility-dependent ratios become undefined. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-025` | Profit factor when gross profit is positive and gross loss is zero. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-026` | Profit factor when gross profit and gross loss are both zero, including zero trades and all-breakeven trades. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-027` | Critical required report sections failing while optional sections remain available. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-028` | Optional report sections missing input data, failing independently, or being configured as required. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-029` | Partial report outputs that must remain non-promotable and JSON-safe. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-030` | Benchmark series with partial coverage, excessive gaps, duplicate timestamps, unknown currency metadata, or mismatched frequency. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-031` | Multi-currency portfolio, benchmark, or TCA analytics with missing FX conversion rates. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-032` | Stale FX rates used for paper/live valuation or base-currency aggregation. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-033` | Paper/live result inputs missing order, fill, slippage, rejection, latency, broker-health, position, money, margin, or kill-switch evidence. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-034` | Live analytics with missing, unknown, active, historical, or unverifiable kill-switch state. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-035` | Strategy-version mismatch, failed result pairing, mismatched symbols, mismatched timeframe, or incompatible cost/slippage models during live-vs-backtest degradation comparison. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-036` | Dashboard time-series payloads larger than configured point limits. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-037` | Dashboard truncation that must preserve first/last points, important extrema, drawdown troughs, equity highs, and major warning timestamps. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-038` | Explainability metadata coverage below the configured threshold or driver samples below the configured minimum. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |
| `V2-EDGE-039` | Legacy report schemas accepted through adapters and reports with missing, unsupported, or future schema versions. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-040` | Duplicate trade IDs or duplicate result IDs. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-041` | Negative trade size, zero trade size, or mixed signed/absolute size conventions. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-042` | Conflicting PnL field names with inconsistent values, such as `profit_loss` and `net_pnl`. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-043` | Conflicting currency metadata between trade records, equity curves, benchmark data, and account base currency. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-044` | Invalid ISO currency codes. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-045` | Ambiguous local timestamps without timezone. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-046` | Clock drift or timezone mismatches between strategy timestamps such as `open_time`/`close_time` and benchmark, equity, paper, or live data sources. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-047` | Daylight-saving-time boundary timestamps. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-048` | Extremely large payloads that exceed configured memory, runtime, or response-size limits. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-049` | Unsupported future schema versions that cannot be safely downgraded. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-050` | Legacy schema versions that can be adapted only with degraded confidence. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-051` | Missing, empty, malformed, duplicate, or unsafe `request_id` values. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-052` | Negative slippage, negative commission, rebates, or mixed cost sign conventions. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-053` | Flat benchmark series with zero variance where beta, alpha, R-squared, tracking error, or information ratio may be undefined. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-054` | Input dataframes with unsupported indexes such as MultiIndex, non-unique indexes, or index-carried timestamps that conflict with timestamp columns. | **Add** | Add this case to the validation/golden-test matrix for the corresponding approved capability. | It represents a concrete correctness, safety, or serialization boundary. |
| `V2-EDGE-055` | Cache stampede/thundering-herd scenarios for highly requested identical report hashes, input hashes, or request IDs. | **Defer** | Move this case with the deferred capability; it is not an initial handoff gate. | The related cache, explainability, live-evidence, degradation, or advanced statistical workflow is deferred. |

### 6.26 Test requirements
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-TEST-001` | Registry tests proving `app.services.analytics.__all__` contains only approved official tools, approved support helpers, or explicitly classified compatibility exports. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-002` | Official Tool Catalog tests proving every official tool has schema, stability status, risk level, side-effect metadata, support status, and request ID support. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-003` | Public/internal boundary tests proving internal kernels are not exposed as official agent/API tools unless explicitly approved. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-004` | Signature tests proving every exported analytics tool accepts `request_id`. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-005` | Request ID validation tests proving official tools reject missing, empty, malformed, duplicate-in-context, or unsafe request IDs with structured errors. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-006` | Standard-envelope snapshot tests for success, validation failure, controlled warning, partial report, skipped section, failed section, and critical failure. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-007` | Golden-file tests for every official high-level tool proving exact output schema, metadata, warning shape, and error-envelope shape. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-008` | Invalid-input tests proving missing required inputs return structured error envelopes with traceable metadata. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-009` | Catalog-backed smoke tests for approved common, benchmark, decision scorecard, distribution, drawdown, efficiency, metric, overview, ratio, return, risk, and statistical-validation metrics after those metrics are classified. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-010` | Golden-fixture tests for core trade metrics, return metrics, drawdown metrics, ratio metrics, risk metrics, benchmark metrics, distribution metrics, and efficiency metrics. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-011` | Formula golden tests proving exact expected values for every official metric, including Sharpe, Sortino, Calmar, beta, alpha, tracking error, information ratio, VaR, CVaR, profit factor, expectancy, SQN, Kelly, drawdown duration, and CAGR. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-012` | Metric convention tests proving annualization, return scale, risk-free rate, and sample/population standard deviation behavior. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-013` | Requirement-to-test traceability tests proving each official public tool and canonical report contract has coverage. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-014` | Empty-input and partial-input tests for every public category. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-015` | Closed-trade filtering tests for open trades, missing close timestamps, and end-of-data placeholder exits. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-016` | Trade classification tests around the breakeven tolerance. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-017` | R-multiple tests covering explicit initial risk, zero risk, missing risk, fallback behavior, and no-loss fallback. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-018` | Time-in-market and exposure tests covering overlapping intervals, simultaneous events, open trades with supplied end time, invalid intervals, and multiple size field names. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-019` | Date/time tests covering strings, pandas timestamps, numeric timestamps, unsorted rows, and malformed values. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-020` | Divide-by-zero and non-finite-value tests for ratios, volatility, drawdowns, benchmark variance, cost impacts, and account/equity denominators. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-021` | Benchmark alignment tests for matched, partially overlapping, and non-overlapping return streams. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-022` | Statistical validation tests with fixed seeds for bootstrap, permutation, Monte Carlo, and overfitting diagnostics. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-023` | Sample-size and caveat tests proving warnings are surfaced rather than hidden. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-024` | Overview/report contract tests proving all expected categories are present and JSON-safe. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-025` | Strategy scorecard tests covering pass, reject, warning-heavy, missing-section, small-sample, high-drawdown, and overfitting-risk scenarios. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-026` | Serialization tests proving outputs do not leak pandas/NumPy objects that API responses cannot encode. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-027` | Security tests proving analytics payloads and error messages do not expose secrets or credentials when sensitive-looking fields are present in input records. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-028` | Integration tests with simulation/backtest callers proving analytics can consume the expected trade/equity outputs without live side effects. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-029` | Canonical `TradingResult` adapter tests covering backtest, optimization, out-of-sample, walk-forward, paper, live, and portfolio result inputs. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-030` | `AnalyticsReport` and `PortfolioAnalyticsReport` contract tests covering schema version, metadata, warnings, quality flags, optional-section status, lineage, and deterministic hashes. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-031` | Hash reproducibility tests proving stable input/config/report hashes for repeated runs and changed hashes for material input changes. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-032` | Partial-report tests proving skipped, failed, degraded, and affected sections are represented explicitly and remain JSON-safe. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-033` | Warning and quality-flag severity tests covering informational, warning, major, critical, and blocker-level evidence. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-034` | Warning and quality-flag schema tests covering code, severity, affected section, source context, bounded detail, and deterministic ordering. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-035` | Dashboard payload contract tests covering chart/table metadata, finite values, ISO timestamps, units, warnings, and no metric recomputation. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-036` | Dashboard truncation/downsampling golden tests proving deterministic output and preservation of first/last points, extrema, drawdown troughs, equity highs, and warning timestamps. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-037` | Multi-currency and FX tests covering required conversion, missing conversion blockers, stale-rate warnings, estimated converted values, and currency lineage. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-038` | Benchmark metadata and alignment tests covering UTC normalization, missing benchmark currency, partial coverage, duplicate timestamps, and non-overlapping windows. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-039` | Live-vs-backtest and paper-vs-backtest degradation tests covering strategy-version mismatch, failed pairing, cost degradation, drawdown expansion, trade-frequency drift, and insufficient observation windows. | **Defer** | Defer this test until its related advanced capability is approved. | Testing an excluded cache, explainability, live-evidence, or degradation feature would preserve unnecessary scope. |
| `V2-TEST-040` | Execution-evidence tests covering missing or malformed order events, fill events, slippage observations, rejected orders, latency observations, broker-health summaries, position snapshots, money series, margin snapshots, and kill-switch state. | **Defer** | Defer this test until its related advanced capability is approved. | Testing an excluded cache, explainability, live-evidence, or degradation feature would preserve unnecessary scope. |
| `V2-TEST-041` | Tests proving Analytics validates and summarizes supplied execution evidence but does not generate, certify, repair, or enforce execution evidence. | **Defer** | Defer this test until its related advanced capability is approved. | Testing an excluded cache, explainability, live-evidence, or degradation feature would preserve unnecessary scope. |
| `V2-TEST-042` | Profit-factor edge-case fixtures covering all-win, all-loss, all-breakeven, zero-trade, zero-gross-profit, zero-gross-loss, and mixed breakeven cases. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-043` | Parallel-determinism tests proving sequential and parallel analytics produce equivalent report content, warning order, dashboard payloads, and hashes. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-044` | Monetary precision tests comparing accepted precision modes within documented tolerances. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-045` | Explainability tests covering sufficient metadata coverage, insufficient metadata coverage, exact threshold coverage, low driver sample exclusion, and driver stability output. | **Defer** | Defer this test until its related advanced capability is approved. | Testing an excluded cache, explainability, live-evidence, or degradation feature would preserve unnecessary scope. |
| `V2-TEST-046` | Schema compatibility tests covering accepted minor-compatible reports, legacy adapters, downgrade warnings, missing schema version, and unsupported future schema versions. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-047` | Performance benchmark tests using the exact fixture, hardware profile, dataset sizes, memory limits, runtime thresholds, and statistical iteration limits recorded in `ADR-ANALYTICS-LIMITS`. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-048` | Placeholder stress tests must exercise owner-approved maximum input sizes once those limits exist and must fail safely on memory explosion, timeout, oversized response, or deterministic truncation failure. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-049` | Concurrency tests proving parallel requests for the same `request_id`, input hash, configuration hash, or report hash yield identical deterministic outputs without race conditions or cache stampedes. | **Modify** | Require the test for the approved initial scope only, using official tools and real implemented statistics/contracts. | The original wording includes unapproved exports, advanced features, or undefined limits. |
| `V2-TEST-050` | Cache tests, when any local/read-through cache is implemented, proving TTL, eviction, lock timeout, single-flight behavior, and stale-read rules do not alter analytics outputs. | **Defer** | Defer this test until its related advanced capability is approved. | Testing an excluded cache, explainability, live-evidence, or degradation feature would preserve unnecessary scope. |
| `V2-TEST-051` | Usage-example tests proving all documented success, validation-failure, partial-report, and dashboard-truncation examples match public contracts. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |
| `V2-TEST-052` | Redaction tests for sensitive key names such as token, secret, password, authorization, broker_key, api_key, and account credentials. | **Add** | Add this test as a handoff requirement for the corresponding approved capability. | V1 tests do not fully prove the final contract, edge behavior, or cross-domain boundary. |

### 6.27 Documentation requirements
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-DOC-001` | Documentation must include the Official Analytics Tool Catalog. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-002` | Documentation must include the Metric Definition Catalog. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-003` | Documentation must include the warning-code and quality-flag catalog. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-004` | Documentation must include report section criticality and partial-report behavior. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-005` | Documentation must include adapter field-mapping tables for every supported upstream result type. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-006` | Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-007` | Documentation must include required, optional, and future dashboard payload classes. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-008` | Documentation must include success examples for each approved official high-level tool. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-009` | Documentation must include validation-failure examples showing the standard error envelope. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-010` | Documentation must include partial-report examples showing skipped, failed, and degraded section metadata. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-011` | Documentation must include dashboard truncation examples showing truncation metadata. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |
| `V2-DOC-012` | Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools. | **Add** | Include this material in the domain README or linked decision/catalog document for approved initial capabilities. | It is required to make the final contracts implementable and testable. |

### 6.28 Metric ownership and dependency model
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-DEP-001` | Architectural Mandate: Analytics owns canonical metric kernels as private/internal implementation details consumed by official high-level tools and canonical report builders. | **Keep** | Retain this ownership/dependency rule. | It prevents low-level kernels or upstream implementation details from becoming public contracts. |
| `V2-DEP-002` | Metric kernels are exposed only through stable, versioned official tool/report interfaces and must not be treated as agent/API-facing just because they exist in source files, imports, or historical examples. | **Keep** | Retain this ownership/dependency rule. | It prevents low-level kernels or upstream implementation details from becoming public contracts. |
| `V2-DEP-003` | ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must classify existing `app.services.analytics` metric functions as official high-level tools, internal kernels, compatibility exports, deprecated exports, or reference-only historical names before Builder handoff. | **Modify** | Keep the private-kernel/public-tool model, but document it in the consolidated public-surface contract rather than multiplying layers. | The behavior is valid; the prescribed ADR structure can be simplified. |
| `V2-DEP-004` | Metric kernels must not be treated as agent/API-facing just because they exist in the repository or appear in historical examples. | **Keep** | Retain this ownership/dependency rule. | It prevents low-level kernels or upstream implementation details from becoming public contracts. |
| `V2-DEP-005` | Upstream result schemas from Simulation, Backtesting, Paper, Live, Optimization, Trading receipts, and Portfolio must be versioned and mapped through a schema compatibility matrix. | **Open Decision** | Resolve the shared schema/adapter contract during cross-domain alignment and record the result in the top-level system decision/ADR. | The decision affects multiple domains and cannot be made safely from Analytics alone. |
| `V2-DEP-006` | Adapter logic from approved upstream result schemas into canonical `TradingResult` is Analytics responsibility; breaking upstream schema changes must be recorded through the compatibility matrix before Analytics can safely consume them. | **Open Decision** | Resolve the shared schema/adapter contract during cross-domain alignment and record the result in the top-level system decision/ADR. | The decision affects multiple domains and cannot be made safely from Analytics alone. |

### 6.29 ADR and architectural decisions
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-ADR-001` | ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the Official Analytics Tool Catalog, including official names, callable paths, public/internal status, stability, input schemas, output schemas, warning schemas, deterministic errors, side-effect flags, risk levels, and agent/API exposure. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |
| `V2-ADR-002` | ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must resolve export classification by recording which current exports are official high-level tools, internal kernels, compatibility aliases, deprecated exports, or reference-only historical names. | **Merge** | Merge this with the consolidated Analytics public-surface decision record. | A separate ADR would duplicate the same decision. |
| `V2-ADR-003` | Architectural Mandate: Analytics owns canonical metric kernels as private/internal implementation details; no separate metric-ownership ADR may choose a different model without updating this source requirement and `docs/ROADMAP.md`. | **Keep** | Retain this architectural boundary as an approved domain principle. | It supports a minimal public surface and private stateless kernels. |
| `V2-ADR-004` | ADR Required: `ADR-ANALYTICS-METRIC-CATALOG` must approve the Metric Definition Catalog for all official metrics, including formulas, units, annualization basis, return scale, sample/population convention, minimum sample size, undefined-result behavior, `breakeven_epsilon`, non-finite handling, and golden-fixture expectations. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |
| `V2-ADR-005` | ADR Required: `ADR-ANALYTICS-REPORT-CONTRACTS` must approve report section criticality for `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, prop-firm evidence, live degradation, and diagnostic partial mode. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |
| `V2-ADR-006` | ADR Required: `ADR-ANALYTICS-THRESHOLDS` must approve minimum thresholds for trade count, return observations, tail-risk observations, benchmark coverage, explainability samples, dashboard point counts, and promotion-blocking quality flags. | **Open Decision** | Resolve this cross-domain or owner-threshold decision before Builder handoff and escalate it to the top-level system Open Decisions section. | The available V1/V2 evidence does not define authoritative values or shared contracts. |
| `V2-ADR-007` | ADR Required: `ADR-ANALYTICS-LIMITS` must approve maximum accepted input sizes, response payload sizes, runtime budgets, memory budgets, statistical iteration limits, reference hardware profile, and performance benchmark method. | **Open Decision** | Resolve this cross-domain or owner-threshold decision before Builder handoff and escalate it to the top-level system Open Decisions section. | The available V1/V2 evidence does not define authoritative values or shared contracts. |
| `V2-ADR-008` | Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation use `Decimal`; derived ratios use deterministic `float64` tolerance only where exact decimal arithmetic is not appropriate. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |
| `V2-ADR-009` | ADR Required: `ADR-ANALYTICS-FX` must approve authoritative FX conversion source, stale-rate age limits, currency override workflow, and blocker behavior for missing multi-currency conversion. | **Open Decision** | Resolve this cross-domain or owner-threshold decision before Builder handoff and escalate it to the top-level system Open Decisions section. | The available V1/V2 evidence does not define authoritative values or shared contracts. |
| `V2-ADR-010` | ADR Required: `ADR-ANALYTICS-SCHEMA-COMPATIBILITY` must approve accepted, deprecated, legacy-adapted, and unsupported analytics/report schema versions for Risk Governor, Portfolio Manager, UI/API, Strategy Reviewer, Simulation, Optimization, and Trading receipts. | **Open Decision** | Resolve this cross-domain or owner-threshold decision before Builder handoff and escalate it to the top-level system Open Decisions section. | The available V1/V2 evidence does not define authoritative values or shared contracts. |
| `V2-ADR-011` | ADR Required: `ADR-ANALYTICS-DASHBOARD` must approve dashboard required/optional/future payload classes and deterministic downsampling/truncation method. | **Open Decision** | Resolve this cross-domain or owner-threshold decision before Builder handoff and escalate it to the top-level system Open Decisions section. | The available V1/V2 evidence does not define authoritative values or shared contracts. |
| `V2-ADR-012` | ADR Required: `ADR-ANALYTICS-WARNINGS` must approve the warning-code and quality-flag catalog, including severity meanings, promotion-blocking behavior, source-backed status, bounded detail limits, and linked test fixtures. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |
| `V2-ADR-013` | ADR Required: `ADR-ANALYTICS-TRACEABILITY` must approve requirement-to-test traceability matrix coverage for every official public tool, canonical report contract, dashboard payload, adapter mapping, and failure envelope. | **Modify** | Keep the decision content, but consolidate related topics into a small number of ADRs/decision records. | Thirteen separate ADRs are disproportionate for the initial domain rebuild. |

### 6.30 Builder handoff Definition of Done
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-DOD-001` | Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-002` | Metric Definition Catalog is approved and no official schema references uncataloged metrics. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-003` | Public/internal export classification is approved, including compatibility aliases and deprecated exports. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-004` | Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-005` | `TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-006` | Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions. | **Open Decision** | Complete this gate only after the corresponding cross-domain schema or exact limits decision is resolved. | The evidence source does not define the final values. |
| `V2-DOD-007` | Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context. | **Open Decision** | Complete this gate only after the corresponding cross-domain schema or exact limits decision is resolved. | The evidence source does not define the final values. |
| `V2-DOD-008` | Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-009` | Report section criticality and partial-report non-promotable behavior are approved. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-010` | Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |
| `V2-DOD-011` | Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability. | **Add** | Keep this as a Builder handoff gate, scoped to approved initial capabilities and consolidated decision records. | It directly verifies the final domain contract. |

### 6.31 Notes and future requirements
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-NOTE-001` | The current implementation exposes a large analytics registry; future work should keep catalog generation and registry tests synchronized whenever public tools change. | **Modify** | Accept the safety/correctness intent but apply it through the simplified final contracts and catalog. | The V1 behavior or V2 wording needs correction. |
| `V2-NOTE-002` | Some analytics tools provide broad wrappers around pandas/NumPy objects; API-facing calls must not be treated as production-ready until stricter input schemas are approved in the Official Analytics Tool Catalog. | **Keep** | Retain this note as a final boundary or safety rule. | It is proportionate and supports the read-only evidence role. |
| `V2-NOTE-003` | Analytics should carry explicit environment/source labels for simulated, paper, live, and historical data so mixed-environment results cannot be misread. | **Add** | Add this as a final documentation/contract rule for the approved capability. | V1 does not consistently provide it. |
| `V2-NOTE-004` | Statistical and Monte Carlo helpers must document runtime limits, default seeds, and reproducibility expectations before production handoff. | **Add** | Add this as a final documentation/contract rule for the approved capability. | V1 does not consistently provide it. |
| `V2-NOTE-005` | Strategy-quality score thresholds are implementation-derived observations and should not be treated as approved production promotion rules until owner/governance approval records them. | **Keep** | Retain this note as a final boundary or safety rule. | It is proportionate and supports the read-only evidence role. |
| `V2-NOTE-006` | The module should continue to avoid live side effects and should remain downstream of Simulation, Trading receipts, Data, and Risk rather than owning those workflows. | **Keep** | Retain this note as a final boundary or safety rule. | It is proportionate and supports the read-only evidence role. |
| `V2-NOTE-007` | Do not implement distributed caching, message queues, or async background workers in Analytics; those belong to orchestration and infrastructure layers. | **Keep** | Retain this note as a final boundary or safety rule. | It is proportionate and supports the read-only evidence role. |
| `V2-NOTE-008` | Architectural Mandate: represent zero-activity profit factor as `None` with a warning rather than serializing infinity or a display-only cap. | **Modify** | Accept the safety/correctness intent but apply it through the simplified final contracts and catalog. | The V1 behavior or V2 wording needs correction. |
| `V2-NOTE-009` | ADR Required: `ADR-ANALYTICS-DASHBOARD` must select a deterministic, auditable dashboard downsampling algorithm before production handoff. | **Merge** | Merge this note into the relevant approved dashboard/public-surface decision. | It duplicates a formal requirement. |
| `V2-NOTE-010` | Architectural Mandate: maintain a warning and quality-flag catalog with code, severity, affected sections, blocks-promotion status, source-backed/recommended status, and linked test fixture. | **Add** | Add this as a final documentation/contract rule for the approved capability. | V1 does not consistently provide it. |
| `V2-NOTE-011` | Architectural Mandate: maintain a requirement-to-test traceability matrix for Analytics once the official tool surface and schema contracts are approved. | **Add** | Add this as a final documentation/contract rule for the approved capability. | V1 does not consistently provide it. |

### 6.32 Proposed module architecture
| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-ARCH-001` | Move the domain to `tools/analytics` with adapters, metrics files, scorecard, report, dashboard, and mirrored tests. | **Open Decision** | Keep the capability grouping but defer the package-root move (`app.services.analytics` versus `tools.analytics`) to cross-domain alignment. | Package location changes imports across the system. |
| `V2-ARCH-002` | Require `TradingResultAdapter`, `MetricKernel` interface, `AnalyticsReportBuilder`, and `StrategyQualityScorecard` classes. | **Reject** | Use functions for stateless calculations/builders and dataclasses only for contracts/configuration; retain a class only if an adapter truly owns multiple mappings or state. | V1 is predominantly pure/stateless; mandatory interfaces/builders add ceremony without lifecycle or dependency needs. |

## 7. Workflow Reconciliation
| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
|---|---|---|---|---|---|---|
| WF-ANLT-001 | Build canonical analytics report | Cross-domain | V1-WF-ANALYTICS-001 — Working with limitations | Complete versioned report pipeline | Modify | Validated upstream result → Analytics adapts/calculates required and approved optional sections → versioned non-binding report response. |
| WF-ANLT-002 | Calculate grouped analytics evidence | Internal | V1-WF-ANALYTICS-002 — Working | Approved grouped trade/equity/drawdown/risk/benchmark/statistical tools | Modify | Canonical trade/series input → internal cataloged kernels → grouped official response with source context. |
| WF-ANLT-003 | Benchmark-relative analysis | Internal | V1-WF-ANALYTICS-003 — Working with edge gaps | UTC/window/currency-aware alignment | Modify | Strategy and benchmark series → normalize/align/validate → benchmark evidence or explicit skipped/undefined section. |
| WF-ANLT-004 | Evaluate strategy quality | Internal | V1-WF-ANALYTICS-004 — Partial | Non-binding scorecard from supplied report | Modify | Canonical report → approved score rules and caveats → non-binding scorecard evidence; no governance decision. |
| WF-ANLT-005 | Build dashboard payload | Cross-domain | V1-WF-ANALYTICS-005 — Working with contract gaps | Validated report sections to chart/table payloads | Modify | Canonical report → project approved charts/tables without recomputation → bounded versioned dashboard payload. |
| WF-ANLT-006 | Adapt upstream result | Cross-domain | V1-WF-ANALYTICS-006 — Unverified | Schema-mapped adapters for approved result types | Modify | Versioned upstream result → deterministic field mapping/validation → canonical TradingResult or structured error. |
| WF-ANLT-007 | Run statistical validation | Internal | V1-WF-ANALYTICS-007 — Partial | Deterministic bounded bootstrap/permutation/sample evidence | Modify | Canonical numeric series + explicit config/seed → real approved statistical diagnostics → evidence with confidence/warnings. |
| WF-ANLT-008 | Serialize and hash report | Internal | V1-WF-ANALYTICS-008 — Working | Canonical serialization, lineage, and full reproducibility hashes | Modify | Validated report → canonical JSON/human-readable representation + deterministic hashes excluding documented nondeterminism. |
| WF-ANLT-009 | Build portfolio analytics report | Cross-domain | V1-WF-ANALYTICS-009 — Broken | Currency-safe aggregation of component evidence | Replace | Validated component reports + base currency/FX evidence → compatible aggregation → portfolio report or blocker error. |
| WF-ANLT-010 | Compare analytics reports | Internal | V1-WF-ANALYTICS-010 — Broken | Schema- and pairing-aware metric comparison | Replace | Compatible reference/candidate reports → validate pairing → actual metric deltas and caveats. |
| WF-ANLT-011 | Produce prop-firm evidence | Cross-domain | V1-WF-ANALYTICS-011 — Broken | Non-binding rule-profile evidence | Defer | No initial workflow. Later: report + versioned caller-supplied rule profile → calculated evidence only. |
| WF-ANLT-012 | Compare live/paper/backtest degradation | Cross-domain | Missing | Proposed pairing and degradation evidence | Defer | Later: comparable versioned reports + approved pairing metadata → degradation evidence; no promotion decision. |

### `WF-ANLT-001` — Build canonical analytics report

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
validated trading result
→ canonical adapter
→ required metric groups
→ approved optional groups
→ warnings / quality flags / lineage
→ output validation and hashes
→ standard report response
```

**V2 proposal:**

```text
validate
→ deterministic adapt
→ calculate core sections
→ mark optional sections calculated/skipped/failed
→ build non-binding versioned report
→ serialize/hash
```

**Final decision:**

```text
Modify — Validated upstream result → Analytics adapts/calculates required and approved optional sections → versioned non-binding report response.
```

**Reason:**

Preserve the working V1 core and refactor the report contract, section model, warning catalog, and hash pipeline.

### `WF-ANLT-002` — Calculate grouped analytics evidence

**Scope:** `Internal`

**V1 behaviour:**

```text
request.trades
→ split all / long / short
→ calculate subset metrics
→ overview response
```

**V2 proposal:**

```text
canonical inputs
→ approved grouped metric capability
→ source-context labels
→ standard response
```

**Final decision:**

```text
Modify — Canonical trade/series input → internal cataloged kernels → grouped official response with source context.
```

**Reason:**

Keep the grouped evidence use case, but do not expose the entire low-level metric inventory publicly.

### `WF-ANLT-003` — Benchmark-relative analysis

**Scope:** `Internal`

**V1 behaviour:**

```text
strategy/benchmark values
→ list conversion or truncation/alignment
→ relative metrics
```

**V2 proposal:**

```text
UTC-normalized indexed series
→ window/currency validation
→ deterministic intersection
→ relative metrics or skipped/undefined evidence
```

**Final decision:**

```text
Modify — Strategy and benchmark series → normalize/align/validate → benchmark evidence or explicit skipped/undefined section.
```

**Reason:**

Retain the metrics but replace positional truncation/default beta semantics with evidence-safe alignment.

### `WF-ANLT-004` — Evaluate strategy quality

**Scope:** `Internal`

**V1 behaviour:**

```text
flat report sections
→ threshold score
→ recommendation
```

**V2 proposal:**

```text
canonical nested report
→ approved score inputs and sample checks
→ facts / warnings / non-binding recommendation context
```

**Final decision:**

```text
Modify — Canonical report → approved score rules and caveats → non-binding scorecard evidence; no governance decision.
```

**Reason:**

Fix direct report composability and remove promotion/rejection authority from Analytics.

### `WF-ANLT-005` — Build dashboard payload

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
report
→ summary extraction
→ curve truncation
→ response or DashboardPayload depending on arguments
```

**V2 proposal:**

```text
validated report sections
→ project approved charts/tables
→ deterministic bounded truncation
→ one versioned response contract
```

**Final decision:**

```text
Modify — Canonical report → project approved charts/tables without recomputation → bounded versioned dashboard payload.
```

**Reason:**

Preserve projection and truncation; remove return-type ambiguity and never recompute missing metrics.

### `WF-ANLT-006` — Adapt upstream result

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
simulation/live journal
→ adapter
→ analytics-shaped dictionary
```

**V2 proposal:**

```text
approved upstream schema
→ explicit mapping and compatibility check
→ canonical TradingResult + lineage or structured error
```

**Final decision:**

```text
Modify — Versioned upstream result → deterministic field mapping/validation → canonical TradingResult or structured error.
```

**Reason:**

Retain adapter responsibility, but exact upstream schemas are a cross-domain open decision.

### `WF-ANLT-007` — Run statistical validation

**Scope:** `Internal`

**V1 behaviour:**

```text
returns
→ seeded bootstrap CI
→ fixed reality-check value in wrapper
```

**V2 proposal:**

```text
returns + explicit bounded config/seed
→ real bootstrap/permutation/sample diagnostics
→ warnings/confidence
```

**Final decision:**

```text
Modify — Canonical numeric series + explicit config/seed → real approved statistical diagnostics → evidence with confidence/warnings.
```

**Reason:**

Remove fixed outputs and defer advanced overfitting algorithms until real formulas and fixtures are approved.

### `WF-ANLT-008` — Serialize and hash report

**Scope:** `Internal`

**V1 behaviour:**

```text
report
→ JSON or minimal Markdown
→ report projection hash
```

**V2 proposal:**

```text
validated report
→ canonical JSON / approved human-readable output
→ input/config/trade/equity/benchmark/report hashes
```

**Final decision:**

```text
Modify — Validated report → canonical JSON/human-readable representation + deterministic hashes excluding documented nondeterminism.
```

**Reason:**

Reuse working serialization and hash ideas; remove MD5 and placeholder formatters.

### `WF-ANLT-009` — Build portfolio analytics report

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
portfolio input
→ currency check
→ fixed zero aggregate metrics
```

**V2 proposal:**

```text
validated component reports
→ schema/currency/FX compatibility
→ actual aggregation
→ portfolio report or blocker
```

**Final decision:**

```text
Replace — Validated component reports + base currency/FX evidence → compatible aggregation → portfolio report or blocker error.
```

**Reason:**

Replace the placeholder implementation while preserving fail-closed multi-currency behavior.

### `WF-ANLT-010` — Compare analytics reports

**Scope:** `Internal`

**V1 behaviour:**

```text
reference/candidate IDs
→ fixed zero differences
```

**V2 proposal:**

```text
validate report schemas and pairing
→ compare approved common metrics
→ deltas, missing metrics, caveats
```

**Final decision:**

```text
Replace — Compatible reference/candidate reports → validate pairing → actual metric deltas and caveats.
```

**Reason:**

Replace fixed values with real comparison or do not expose the tool.

### `WF-ANLT-011` — Produce prop-firm evidence

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
any report, including None
→ compliant=True
```

**V2 proposal:**

```text
deferred
```

**Final decision:**

```text
Defer — No initial workflow. Later: report + versioned caller-supplied rule profile → calculated evidence only.
```

**Reason:**

Remove the unsafe always-pass behavior. A later capability requires a versioned caller-owned rule profile.

### `WF-ANLT-012` — Compare live/paper/backtest degradation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
missing
```

**V2 proposal:**

```text
deferred pending shared pairing contract
```

**Final decision:**

```text
Defer — Later: comparable versioned reports + approved pairing metadata → degradation evidence; no promotion decision.
```

**Reason:**

Useful future evidence, but it depends on stable Simulation/Trading/Portfolio metadata and is not needed for the initial rebuild.

## 8. Recommended Minimal Capability Structure

The exact package root remains open for cross-domain alignment. The capability structure is:

```text
analytics/
├── contracts/      # Official tools, report/input schemas, metric catalog, warnings, errors, compatibility
├── adapters/       # Approved upstream result → canonical TradingResult mappings
├── metrics/        # Internal pure trade, return, drawdown, risk, ratio, benchmark, distribution, statistics, cost/efficiency kernels
├── reports/        # Canonical report, portfolio report, comparison, serialization, hashes
├── scorecards/     # Non-binding strategy-quality evidence
└── dashboards/     # Report-section projection and deterministic truncation
```

The package root should explicitly export the approved high-level tools. No mutable registry module, boundary-service layer, manager, factory, repository, command layer, or mandatory metric interface is recommended.

| Module | Capability | Source | Main decision |
|---|---|---|---|
| `contracts/` | Public tool catalog, canonical schemas, metric catalog, warnings/quality flags, errors, lineage, compatibility | Both | Modify / Add / Merge |
| `adapters/` | Deterministic upstream result mapping | Both | Modify |
| `metrics/` | Private canonical metric kernels and selected statistical validation | V1-led | Modify / Merge / Split |
| `reports/` | Canonical, portfolio, comparison, serialization, and hashes | Both | Modify / Replace |
| `scorecards/` | Non-binding strategy-quality evidence | Both | Modify |
| `dashboards/` | UI/API-ready payloads from report sections | Both | Modify |

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
|---:|---|---|---|---|
| 1 | `TradingResultAdapter.to_canonical()` and schema validation | Refactor | Canonical input adapters | Golden mappings for each approved upstream schema; conflict and future-version tests. |
| 2 | Trade filtering/classification and aggregate trade metrics | Refactor | Trade metric kernels | Closed/open/placeholder fixtures; epsilon classification; undefined values. |
| 3 | Equity/return/PnL kernels | Refactor | Return/equity metrics | Ordering, UTC, frequency, annualization, non-finite, precision golden fixtures. |
| 4 | Core drawdown functions | Refactor | Drawdown metrics | Depth/duration/recovery golden fixtures and edge cases. |
| 5 | Core risk/ratio kernels | Refactor | Risk and ratio metrics | Catalog formula fixtures; zero denominator and finite output tests. |
| 6 | Benchmark calculations | Refactor | Benchmark comparison | Timestamp/window/currency alignment and zero-variance fixtures. |
| 7 | Duplicate distribution implementations | Replace/Merge | Distribution diagnostics | Select one canonical formula set through golden fixtures. |
| 8 | Seeded bootstrap/permutation implementations | Reuse/Refactor | Statistical validation | Seed reproducibility, iteration limits, sample warnings. |
| 9 | `build_analytics_report()` | Refactor | Canonical report | Contract snapshots, section criticality, partial mode, hashes. |
| 10 | `serialize_report()` and `compute_report_hash()` | Reuse/Refactor | Serialization/reproducibility | Canonical JSON, nondeterministic exclusions, full hash set; remove MD5. |
| 11 | Dashboard overview and truncation | Refactor | Dashboard payloads | One response type; strict point limit; critical-point preservation. |
| 12 | Scorecard evaluator | Refactor | Strategy-quality evidence | Consume canonical report shape; approved thresholds; non-binding language. |
| 13 | Portfolio/comparison/compliance placeholders | Replace/Remove | Portfolio/report comparison; deferred prop-firm evidence | Prove real calculations before exposing official tools. |
| 14 | Mutable registry, compatibility exports, duplicate envelopes/contracts/redactors | Remove/Merge | Public surface, contracts, warnings | External import inventory and deprecation verification. |
| 15 | Efficiency/time/cost kernels | Selectively Refactor/Defer | Selected internal metrics and report sections | Workflow-specific fixtures; remove unapproved specialized metrics. |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
|---|---|---|
| Dynamic registry plus `__all__` classification machinery | V1 registry is unpopulated and root exports 351 names. | Use a static Official Tool Catalog and explicit root exports; no mutable registry. |
| Mandatory `MetricKernel` interface | Kernels are stateless functions with no lifecycle/dependency ownership. | Use typed pure functions and catalog records. |
| Mandatory `AnalyticsReportBuilder` class | Report construction is stateless orchestration. | Use `build_analytics_report()` plus private functions; class only if state/lifecycle later appears. |
| Mandatory `StrategyQualityScorecard` class | Evaluation is stateless and config can be an immutable dataclass. | Use `evaluate_strategy_quality(report, config, request_id)`. |
| Separate boundary envelope system | V1 already has a standard response utility; parallel envelopes conflict. | Choose one versioned analytics envelope and delete the duplicate. |
| Separate folders for registry, boundaries, statistics, and overlapping distributions | Creates thin layers and duplicate contracts. | Keep contracts/adapters/metrics/reports/scorecards/dashboards; place private helpers with their capability. |
| Every historical metric name as a requirement/export | The inventory is reference-only and contains aliases, obscure ratios, and placeholders. | Approve only cataloged internal metrics required by final reports/tools. |
| Thirteen separate Analytics ADRs | Several decisions overlap and some are domain documentation. | Consolidate into public/contracts, metric policy, limits/dashboard, and cross-domain schema/FX decisions. |
| Local/read-through cache design | No V1 cache or measured bottleneck exists. | No cache initially; revisit after benchmarks. |
| TCA, attribution, dynamic correlation, explainability, live degradation, execution-evidence analysis in initial report | No working V1 workflow or stable shared contract. | Mark section status capability now; defer the actual advanced sections. |
| Broad pandas/NumPy acceptance in every function | Retains ambiguous coercion and serialization risk. | Normalize at approved adapter/official-tool boundaries; kernels consume canonical types. |
| Complete candidate dashboard chart suite | Many charts lack approved source sections. | Initial summary/equity/drawdown/warning payloads; classify others optional/future. |
| Move to `tools/analytics` immediately | Package location changes cross-domain imports and conflicts with current `app.services.analytics`. | Treat package root as an open cross-domain decision in step 05. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
|---|---|---|---|---|
| Open | Exact initial Official Analytics Tool Catalog | V1 has working report/metric tools but also broken portfolio/comparison/compliance tools and 351 exports. | Approve a minimal set such as report, portfolio report after implementation, comparison after implementation, scorecard, dashboard, and selected grouped metrics; or expose report-only first. | CAP-ANLT-001, -013–017, -024 |
| Open | Authoritative cross-domain `TradingResult` schemas and package location | V1 adapters exist; V2 proposes `tools/analytics`; upstream domains own their schemas. | Keep `app.services.analytics`; move to `tools.analytics`; define another shared package. Resolve in pipeline step 05 with ADR. | CAP-ANLT-003, -020 |
| Open | FX source, staleness limits, and conversion evidence schema | V1 only checks missing conversions; Analytics must not source FX. | Caller supplies validated FX snapshots; shared Data/Portfolio FX contract; defer converted portfolio analytics. | CAP-ANLT-014, -021 |
| Open | Approved metric formulas, annualization, undefined semantics, and minimum samples | V1 implementations differ and V2 lists many formulas without final conventions. | Approve core catalog first; defer non-core metrics; choose sample/population and return scales. | CAP-ANLT-004–012, -019 |
| Open | Initial scorecard thresholds and recommendation language | V1 thresholds are implementation-derived; Analytics cannot own promotion rules. | Owner-approved analytics-only diagnostic thresholds; score without action text; defer scorecard. | CAP-ANLT-016 |
| Open | Report section criticality and initial optional-section set | V1 only treats trade/equity as required and benchmark as optional; V2 proposes many sections. | Approve a core required set and small optional set; defer advanced sections. | CAP-ANLT-013 |
| Open | Dashboard required/optional/future payload classes and truncation algorithm | V1 has summary/equity only and a limit bug; V2 candidate set is broad. | Approve minimal charts and audited deterministic sampling. | CAP-ANLT-017 |
| Open | Concrete input, iteration, runtime, memory, and response-size limits | V1 has disconnected defaults; V2 provides no values/reference hardware. | Benchmark on owner-approved hardware and publish exact limits before Builder handoff. | CAP-ANLT-022 |
| Open | Accepted/legacy/unsupported schema versions | V1 has a partial matrix; V2 requires consumers across domains. | Approve shared compatibility matrix and deprecation policy during step 05. | CAP-ANLT-003, -020 |

**Escalation:**

* Package location, canonical upstream/downstream schemas, FX authority, and schema-version compatibility affect multiple domains and must be added to the top-level system Open Decisions section and resolved during pipeline step 05 with the appropriate ADR/decision record.
* Deferral of live/paper degradation, explainability, execution-evidence analytics, and multi-currency conversion changes cross-domain workflow scope and must be reflected in the top-level Deferred Capabilities section.
* Metric formulas, scorecard thresholds, dashboard classes, and domain-local performance limits remain Analytics open decisions unless their chosen values alter shared contracts.

## 12. Inputs for the Final Domain README

### Approved capabilities

* Explicit Official Analytics Tool Catalog and package-root high-level exports.
* One canonical official response/error envelope with request-ID traceability.
* Deterministic adapters into canonical `TradingResult`.
* Internal trade, PnL, equity/return, drawdown, core risk, core ratio, benchmark, distribution, cost, selected efficiency/time, and deterministic statistical kernels.
* Versioned canonical Analytics report with section criticality, partial-report evidence, warnings, lineage, and hashes.
* Currency-safe portfolio analytics after FX contract approval.
* Real report comparison.
* Non-binding strategy-quality evidence.
* Dashboard/report payload projection with deterministic limits.
* Metric Definition Catalog.
* Warning-code and quality-flag catalog.
* Canonical JSON serialization, report lineage, schema compatibility, reproducibility hashes, redaction, and enforced limits.

### Approved workflows

* Build canonical analytics report.
* Calculate approved grouped analytics evidence.
* Run benchmark-relative analysis.
* Evaluate non-binding strategy quality.
* Build dashboard payload from report sections.
* Adapt approved upstream results.
* Run bounded deterministic statistical validation.
* Serialize and hash reports.
* Build currency-safe portfolio report after FX/schema decisions.
* Compare compatible reports using actual metrics.

### V1 behaviours to preserve

* `TradingResultAdapter.to_canonical()` validation and normalization pattern.
* Closed-trade filtering and core trade aggregation.
* Core equity/return/PnL, drawdown, risk, ratio, benchmark, and distribution calculations.
* Overlapping-interval merge for market-presence duration.
* Seeded bootstrap confidence intervals and generic permutation testing.
* Main `build_analytics_report()` calculation path.
* Deterministic dashboard truncation intent.
* JSON/Markdown serialization and metadata-excluding hashing.
* Read-only, no-network, no-trading side-effect boundary.

### V1 behaviours to modify

* Replace the broad root facade with explicit high-level exports.
* Unify envelopes, request IDs, contracts, warnings, redaction, and duplicated metrics.
* Correct undefined-value handling, annualization, alignment, precision, exposure semantics, and R-proxy behavior.
* Make the scorecard consume canonical nested report sections.
* Make dashboards consume canonical report sections through one response type.
* Add full report section status, lineage, hashes, currency evidence, and enforced limits.
* Replace portfolio and report-comparison placeholders with real calculations.

### V1 behaviours to remove

* Fixed-value White’s Reality Check, PBO, backtest permutation/bootstrap, comparison, portfolio aggregate, and always-pass compliance outputs.
* Empty summary-row and statistical-text formatters.
* Mutable unpopulated tool/request registries.
* Duplicate error, report/dashboard model, contract, redaction, response-envelope, and distribution implementations after consumer verification.
* Compatibility aliases and private-looking public exports after an import inventory/deprecation check.
* MD5 report hashing.
* Analytics-owned duplicate audit-event contracts.

### V2 behaviours to add

* Static Official Analytics Tool Catalog and explicit public/internal classification.
* Complete Metric Definition Catalog.
* Versioned adapter mapping and schema compatibility policy.
* Canonical warning/quality-flag catalog and deterministic ordering.
* Required/optional/degraded report section model and non-binding partial status.
* Full lineage and reproducibility hash set.
* Currency/FX validation and inheritance lineage.
* Concrete input, iteration, runtime, memory, response, and dashboard limits.
* Golden formulas, contract snapshots, redaction, cross-domain integration, determinism, precision, and performance tests.

### V2 proposals to reject or defer

* Mandatory `MetricKernel`, report-builder, and scorecard classes.
* Immediate move to `tools/analytics` before cross-domain alignment.
* A mutable runtime tool registry.
* Public exposure of the historical metric inventory.
* Local/distributed cache architecture in the initial rebuild.
* Advanced TCA, attribution, dynamic correlation, explainability, live degradation, execution-evidence analysis, and extensive rolling dashboards.
* Specialized/obscure metrics without an approved workflow and catalog formula.
* Separate ADRs for every closely related internal topic.
* Prop-firm evidence until a versioned caller-owned rule profile exists.

### Required open decisions before README completion

* Exact official high-level tool list and stability classification.
* Package root and shared canonical result contracts.
* Initial required and optional report sections.
* Core metric formulas, annualization, precision, undefined values, and minimum samples.
* Scorecard thresholds and allowed recommendation language.
* FX authority, conversion schema, stale-rate policy, and currency inheritance.
* Dashboard classes, point limits, and truncation algorithm.
* Accepted/legacy/unsupported schema versions.
* Concrete input/runtime/memory/payload/statistical limits.

## 13. Final Reconciliation Checklist

* [x] Every V1 capability received a disposition: 30 of 30.
* [x] Every V2 checkbox requirement received a disposition: 430 of 430.
* [x] Every additional V2 ownership, boundary, API, edge-case, test, dependency, ADR, handoff, and future requirement bullet received a disposition: 175 of 175.
* [x] V2 purpose, public capability contract, and module/class prescriptions received explicit dispositions.
* [x] Every V1 workflow was reconciled: 11 of 11.
* [x] Proposed V2 report, portfolio, scorecard, comparison, dashboard, adapter, grouped metric, statistical, degradation, and evidence workflows were reconciled.
* [x] Confirmed working V1 behavior was not discarded without a reason.
* [x] Placeholder, duplicated, unsafe, and unproven V1 behavior was not preserved automatically.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The proposed direction follows the package → capability module → focused file → public function/class structure.
* [x] Responsibilities that may belong to shared Data, Simulation, Trading, Risk, Portfolio, UI/API, Governance/Audit, or orchestration domains are flagged for step 05.
* [x] Unresolved conflicts are listed under Open Decisions.
* [x] Cross-domain open decisions and shape-changing deferrals are explicitly marked for top-level escalation.
* [x] No code was inspected or changed during reconciliation.
* [x] Neither source document was modified.
* [x] The output provides the decisions required to write the final domain README.

## Evidence That Was Unavailable

* A clean historical V1-only implementation snapshot.
* Executed V1 tests, coverage, runtime logs, deployed callers, and dynamic-import evidence.
* Owner-approved formulas, scorecard thresholds, annualization policy, schema versions, FX authority/staleness limits, dashboard classes, and performance limits.
* Final cross-domain contracts and package-location decision, which are reserved for pipeline step 05.

# Indicators — V1/V2 Reconciliation

## 1. Reconciliation Scope

* **Domain:** `indicators` (`indi`)
* **V1 audit report:** `docs/dev/audits/indicators-v1-audit.md`
* **V2 requirements:** `03-indicator.md` (attached as `03-indicator(1).md`)
* **Current V1 package:** `app/services/indicators`
* **Intended V2 package:** `tools/indicators`
* **Comparison method:** Capability-to-capability comparison using only the V1 audit and V2 requirements. No code was inspected or modified.
* **Comparison limitations:**
  * The V1 audit had no runtime telemetry, external-consumer inventory, executed tests, or local repository checkout.
  * The V2 document contains 769 normative/proposed items when purpose, ownership, API, checklist requirements, edge cases, architecture prescriptions, prerequisites, acceptance items, and future items are counted. It does not assign stable IDs to most items; this reconciliation assigns traceable `V2-IND-*` IDs without modifying the source.
  * Cross-domain ownership for data normalization, shared audit infrastructure, release engineering, and compatibility migration is identified but remains subject to pipeline step 05.

## 2. Executive Summary

The valuable V1 behaviour is the small, deterministic, side-effect-free DataFrame calculation kernel demonstrated by SMA, EMA, RSI, Williams %R, ATR, and other formulas. That behaviour should be preserved conceptually, but not as the existing duplicated class hierarchy or package surface. The V1 audit found no confirmed production consumer of the plural package, no unit tests for it, generic/inconsistent errors, ad-hoc output schemas, a broken MFI index-alignment implementation, and retrospective lookahead in SMC.

The recommended V2 direction is a single canonical `tools/indicators` package containing stateless batch functions, a compact typed result/manifest contract, deterministic validation/errors, approved formula tables, explicit warmup and `available_at` metadata, a static official registry, and only eight initial built-ins: EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R.

V1 EMA, SMA, RSI, ATR, and Williams %R are refactor candidates. V1 rolling standard deviation is merged conceptually into a newly specified rolling-volatility capability rather than reused unchanged. WMA, Bollinger Bands, MACD, OBV, CMF, candlestick patterns, and HMA are deferred. Broken MFI, unused price-volume POC, non-causal SMC labels, and unrelated helpers are removed from the approved indicator baseline.

The V2 proposal contains important safety requirements—formula specifications, no-lookahead availability, deterministic errors, manifests, quality/provenance propagation, golden fixtures, and API traceability—but also substantial premature complexity. Runtime plugin registration, streaming/incremental state, caching, out-of-core execution, acceleration, composition graphs, rich notebook rendering, audit sinks, distributed tracing, canary routing, SLO enforcement, proprietary-entitlement controls, and release-signing/SBOM machinery are rejected from the initial domain shape or explicitly deferred.

**V2 disposition metrics:** Keep: 33 | Add: 292 | Modify: 91 | Merge: 60 | Defer: 246 | Reject: 35 | Open Decision: 12 | Total: 769

**Recommended migration direction:** establish the minimal contracts and formula tables first; implement and golden-test the eight causal batch built-ins; add availability/manifest/error behaviour; integrate with normalized data and downstream consumers; then retire duplicate V1 surfaces only after compatibility evidence is obtained.

## 3. Decision Principles

* Preserve proven deterministic calculation behaviour, not obsolete package structure.
* Use pure stateless functions for built-ins; use classes only for immutable data contracts or justified lifecycle/state.
* Treat V1 as evidence, not authority, and V2 as a proposal, not automatic approval.
* Require exact formula, warmup, seed, null, dtype, and tolerance conventions before implementation.
* Keep indicators as decision-support calculations; data normalization, strategy decisions, risk approval, execution, fills, and account mutation remain outside.
* Expose no-lookahead timing and quality/provenance metadata, while downstream domains enforce their own decision policies.
* Prefer a static official registry over runtime plugin lifecycle.
* Add optional infrastructure only after a confirmed workflow and measurable need exist.
* Keep one focused responsibility per module and avoid redundant batch/service/manager layers.
* Make every deferred, rejected, or removed item explicit and traceable.

## 4. Capability Reconciliation Matrix

| Capability ID | Capability | V1 evidence | V2 requirement | Gap | Decision | Final behaviour | Reuse approach | Reason |
|---|---|---|---|---|---|---|---|---|
| CAP-INDI-001 | Pure indicator-domain boundary | All V1 calculations are side-effect-free; `V1-WF-INDICATORS-001..003` mix data acquisition only in external usage scripts. | `V2-IND-PUR-002`, `V2-IND-FR-1.1-003..006`, `V2-IND-BOUNDARY-*` | V1 package location and workflows are duplicated/disconnected; V2 mixes pure calculation with optional adapters. | Modify | `tools/indicators` owns deterministic decision-support calculations only; no broker, execution, persistence, cache, audit or telemetry I/O in Core MVP. | Refactor | Preserves proven calculation purity while enforcing a single boundary. |
| CAP-INDI-002 | Minimal typed calculation contract | `V1-CAP-INDICATORS-001`; every class inherits `BaseIndicator` and returns a DataFrame. | `V2-IND-API-001`, `V2-IND-FR-1.8.2-*`, `V2-IND-TYPE-*` | V1 inheritance is weak; V2 proposes too many context/state interfaces. | Modify | Use stateless typed functions, immutable indicator specs, minimal structural protocol, typed result/manifest/error contracts and shared validation. | Refactor | Functions fit stateless behaviour; classes remain only for immutable data contracts. |
| CAP-INDI-003 | Vectorized result, naming and join contract | V1 built-ins copy the source DataFrame and append ad-hoc columns. | `V2-IND-FR-1.3-*`, `V2-IND-FR-1.3.1-*`, `V2-IND-IO-OUT-001..012` | No canonical alignment, collision, warmup-state or values-only contract. | Add | Return `IndicatorResult(values, output_columns, availability, quality, manifest, errors)` with deterministic names and copied `join_to`. | New | The V1 copy behaviour is reusable, but the public contract is new. |
| CAP-INDI-004 | Formula specifications and deterministic numeric policy | V1 formulas are implicit; `V1-CAP-INDICATORS-010` documentation mismatch and `V1-CAP-INDICATORS-012` defect demonstrate risk. | `V2-IND-FR-1.5-*`, `V2-IND-FR-1.9-*`, `V2-IND-FR-1.9.1-*`, `V2-IND-NFR-2.6-*` | Exact seed, null, degeneracy, dtype and tolerance rules are missing. | Add | Approve formula tables, float64 policy, warmup, seed, window, null and tolerance behaviour before implementation. | New | This is the main correctness prerequisite. |
| CAP-INDI-005 | Core trend indicators | `V1-CAP-INDICATORS-002` SMA; `003` EMA; `004` WMA; `005` Bollinger Bands. | `V2-IND-FR-1.2-001`, `V2-IND-FR-1.8.2-019`, formula-table requirements | ADX is missing; WMA/Bollinger are outside V2 Core MVP. | Modify | Core trend set is EMA, SMA and ADX. Refactor V1 EMA/SMA; add ADX; defer WMA and Bollinger Bands. | Refactor/New | Keeps proven simple calculations and avoids preserving unused extras. |
| CAP-INDI-006 | Core volatility indicators | `V1-CAP-INDICATORS-009` ATR; `010` rolling price standard deviation. | `V2-IND-FR-1.2-002`, `V2-IND-FR-1.8.2-019`, formula-table requirements | ADR and returns-based rolling volatility are absent; V1 standard deviation is not the approved contract. | Modify | Core set is ATR, ADR and explicitly specified rolling volatility. Refactor ATR; add ADR; replace/merge V1 standard deviation. | Refactor/Replace/New | The V1 concept is useful but formula semantics must change. |
| CAP-INDI-007 | Core momentum indicators | `V1-CAP-INDICATORS-006` RSI; `007` MACD; `008` Williams %R. | `V2-IND-FR-1.2-003`, `V2-IND-FR-1.8.2-019` | RSI/Williams need formal conventions; MACD is outside initial scope. | Modify | Core set is RSI and Williams %R. Refactor both; defer MACD. | Refactor | Preserves useful formulas while keeping scope minimal. |
| CAP-INDI-008 | No-lookahead availability | V1 has no availability metadata; `V1-CAP-INDICATORS-020..022` are retrospectively calculated. | `V2-IND-FR-1.4-*`, `V2-IND-FR-1.10-*` | Unsafe causal interpretation is possible. | Add | Every result exposes `available_at`, source window bounds, timeframe and lookahead flag; strategy/simulation filter by decision time. | New | Required for official backtests and live-safe decision support. |
| CAP-INDI-009 | Warmup requirements | V1 exposes NaN warmup implicitly and performs inconsistent sufficiency checks. | `V2-IND-FR-1.2-004..006`, `V2-IND-FR-1.19-*` | No explicit requirement exchange or unavailable-state distinction. | Add | Each indicator spec reports exact warmup; caller/data domain supplies data; outputs retain explicitly marked warmup rows. | New | Preserves no-I/O while making warmup enforceable. |
| CAP-INDI-010 | Deterministic manifest and checksums | V1 returns only enriched DataFrames. | `V2-IND-FR-1.5-007`, `V2-IND-MAN-001..023`, `IND-PREQ-004` | No version, hash, provenance or output contract metadata; V2 manifest is overgrown and mixes volatile diagnostics. | Modify | Use a compact deterministic manifest: versions, canonical parameters/hash, input/output checksum, output contract, availability policy, precision and propagated provenance/quality. Keep runtime timing separate. | New | Supports replay without coupling calculations to platform telemetry. |
| CAP-INDI-011 | Static registry and capability matrix | V1 uses export-only `__init__.py` files; no registry exists. | `V2-IND-API-002`, `V2-IND-API-006..008`, `V2-IND-FR-1.7-*` | Exports do not describe schemas, versions or supported modes. | Add | Provide immutable official specs with `get`, `list`, `validate` and machine-readable capability matrix; reject unsupported modes before calculation. | New | Needed for discoverability and agent/tool integration without mutable plugin complexity. |
| CAP-INDI-012 | Deterministic validation and errors | V1 raises generic `ValueError`/`LookupError`; `V1-ISSUE-INDICATORS-009/010/014`. | `V2-IND-ERR-REQ-*`, approved subset of `V2-IND-ERR-CODE-*`, `V2-IND-FR-1.15-*` | Validation and error taxonomy are inconsistent. | Add | Fail before calculation with a compact core `IND_*` catalogue and one approved default error mode. | New | A stable machine-readable contract is required by strategies, simulation and agents. |
| CAP-INDI-013 | Data quality and provenance propagation | V1 ignores quality/provenance. | `V2-IND-FR-1.12-*`, `V2-IND-FR-1.17-*` | V2 assigns some upstream normalization duties to indicators. | Modify | Consume data-owned provenance/quality metadata, apply documented inclusion policy and propagate window severity; do not own provider normalization, symbol mapping or quote-quality rules. | New | Retains reproducibility while preserving the data-domain boundary. |
| CAP-INDI-014 | Multi-symbol and limited multi-timeframe alignment | V1 examples are single-symbol and do not encode timeframe availability. | `V2-IND-FR-1.3-003`, `V2-IND-FR-1.20-*` | No grouping or higher-timeframe timing contract. | Add | Support explicit symbol/timestamp grouping and one caller-supplied higher-timeframe source with close-plus-latency availability; defer multi-source orchestration. | New | Required for official multi-asset/backtest use but kept proportionate. |
| CAP-INDI-015 | Resource limits and benchmark baseline | No limits or benchmark evidence in V1. | `V2-IND-NFR-2.4-*`, `V2-IND-FR-1.6.1-*`, `V2-IND-NFR-2.8-*` | Proposed numeric limits/SLOs are unverified. | Open Decision | Add basic validated row/symbol/column/timeout limits and reproducible benchmarks; approve numeric defaults and binding SLOs only after measurement. | New | Safety is needed, but arbitrary targets should not block implementation. |
| CAP-INDI-016 | Custom indicator extensions | V1 has hard-coded custom classes but no extension governance. | `V2-IND-FR-1.7-003..004`, `V2-IND-FR-1.14-*` | Large conformance/sandbox lifecycle proposed without a confirmed user. | Defer | Initial registry contains reviewed official built-ins only; revisit custom registration after a concrete workflow exists. | None initially | Avoids plugin and side-effect-enforcement complexity. |
| CAP-INDI-017 | Caching | No V1 cache or cache caller. | `V2-IND-FR-1.6-*`, cache inputs/outputs/errors/tests | No demonstrated need; V2 proposes policies, adapters and SLOs. | Defer | Preserve canonical hash/checksum material; add a cache adapter only after measured repeated-workload need. | None initially | Identity material is cheap; storage lifecycle is not. |
| CAP-INDI-018 | Incremental, streaming, chunked, out-of-core and accelerated execution | No V1 state/update protocol; V1 is batch DataFrame calculation. | `V2-IND-FR-1.6.2-*`, `1.13-*`, `1.13.1-*` | Substantial optional architecture has no confirmed workflow. | Defer | Core MVP supports deterministic vectorized batch only and reports other modes unsupported. | None initially | Keeps one reference implementation before adding parity burdens. |
| CAP-INDI-019 | Indicator composition engine | V1 usage scripts manually chain DataFrames. | `V2-IND-FR-1.16-*` | A graph engine, cycle validation and cache invalidation are proposed. | Defer | Allow explicit caller-side chaining with availability/provenance preservation; no composition graph engine initially. | None initially | Manual composition already satisfies simple workflows. |
| CAP-INDI-020 | Audit, observability, canary and proprietary integrations | V1 has none. | `V2-IND-FR-1.18-*`, `1.21-*`, `V2-IND-NFR-2.3-*` | These are optional platform/security capabilities, many outside domain ownership. | Defer | Core emits deterministic result/manifest only. Shared platform integrations may be added later through approved boundaries. | None initially | Avoids coupling formula code to platform concerns. |

## 5. V1 Disposition Register

Every V1 capability from the audit catalogue is explicitly dispositioned below.

| V1 capability ID | V1 capability | Current implementation | Current value | Decision | Final destination | Removal condition |
|---|---|---|---|---|---|---|
| V1-CAP-INDICATORS-001 | Common indicator class contract | `base.py:BaseIndicator.calculate` | Supporting | Modify | `CAP-INDI-002` minimal structural contract and stateless functions | Confirm no external subclass imports before deleting the inheritance API. |
| V1-CAP-INDICATORS-002 | Simple moving average | `trend/sma.py:SMA.calculate` | Questionable | Modify | `CAP-INDI-005` SMA built-in | Golden-test formula, seed, warmup, naming, availability and result contract. |
| V1-CAP-INDICATORS-003 | Exponential moving average | `trend/ema.py:EMA.calculate` | Questionable | Modify | `CAP-INDI-005` EMA built-in | Golden-test exact seed/smoothing convention and external-import compatibility. |
| V1-CAP-INDICATORS-004 | Weighted moving average | `trend/wma.py:WMA.calculate` | Questionable | Defer | Future trend extension | Verify no external consumer; retain only as historical reference until compatibility window closes. |
| V1-CAP-INDICATORS-005 | Bollinger Bands | `trend/bollinger_bands.py:BollingerBands.calculate` | Questionable | Defer | Future trend/volatility extension | Verify no external consumer and approve formula/output contract before reintroduction. |
| V1-CAP-INDICATORS-006 | Relative Strength Index | `momentum/rsi.py:RSI.calculate` | Questionable | Modify | `CAP-INDI-007` RSI built-in | Approve Wilder seed/zero-loss/null policy and cross-validate golden fixtures. |
| V1-CAP-INDICATORS-007 | MACD | `momentum/macd.py:MACD.calculate` | Questionable | Defer | Future momentum extension | Verify no external consumer; require formula and warmup specification before reintroduction. |
| V1-CAP-INDICATORS-008 | Williams %R | `momentum/will_r.py:WilliamsR.calculate` | Questionable | Modify | `CAP-INDI-007` Williams %R built-in | Approve degenerate-range and warmup policy; validate causal availability. |
| V1-CAP-INDICATORS-009 | Average True Range | `volatility/atr.py:ATR.calculate` | Questionable | Modify | `CAP-INDI-006` ATR built-in | Approve Wilder smoothing/seed and golden fixtures. |
| V1-CAP-INDICATORS-010 | Rolling standard deviation | `volatility/standard_deviation.py:StandardDeviation.calculate` | Questionable | Merge | `CAP-INDI-006` rolling volatility | Do not reuse the price-level standard-deviation formula until the final return/annualization convention is approved. |
| V1-CAP-INDICATORS-011 | On-Balance Volume | `volume/obv.py:OBV.calculate` | Questionable | Defer | Future volume extension | Verify no external consumer and correct empty-input behavior before any reintroduction. |
| V1-CAP-INDICATORS-012 | Money Flow Index | `volume/mfi.py:MFI.calculate` | Questionable | Remove | None in initial/final approved baseline | Confirm no external import; current implementation is index-alignment defective and no V2 workflow requires it. |
| V1-CAP-INDICATORS-013 | Chaikin Money Flow | `volume/cmf.py:CMF.calculate` | Questionable | Defer | Future volume extension | Verify no external consumer and approve zero-volume/null policy. |
| V1-CAP-INDICATORS-014 | Rolling volume-profile point of control | `volume/price_volume_distribution.py:PriceVolumeDistribution.calculate` | No demonstrated value | Remove | None | Complete external-import search/telemetry check; no V1 workflow or V2 requirement supports retention. |
| V1-CAP-INDICATORS-015 | Doji detection | `candles/doji.py:Doji.calculate` | Questionable | Defer | Future candlestick/research extension | Verify actual strategy use and approve parameter/causality contract. |
| V1-CAP-INDICATORS-016 | Engulfing detection | `candles/engulfing.py:Engulfing.calculate` | Questionable | Defer | Future candlestick/research extension | Verify external usage and correct empty-input behavior. |
| V1-CAP-INDICATORS-017 | Inside-bar detection | `candles/inside_bar.py:InsideBar.calculate` | Questionable | Defer | Future candlestick/research extension | Verify external usage and correct empty-input behavior. |
| V1-CAP-INDICATORS-018 | Pinbar detection | `candles/pinbar.py:Pinbar.calculate` | Questionable | Defer | Future candlestick/research extension | Verify external usage and approve configurable thresholds. |
| V1-CAP-INDICATORS-019 | Hull Moving Average | `custom/hull_moving_average.py:HullMovingAverage.calculate` | Questionable | Defer | Future trend extension | Verify external usage and approve formula/warmup conventions. |
| V1-CAP-INDICATORS-020 | Fair Value Gap and mitigation labelling | `custom/smc.py:SMC.calculate`, `_fvg` | Questionable | Remove | None in production indicators; possible future research label | Confirm whether retrospective research labels are required; current next-candle lookahead is unsafe for causal indicator use. |
| V1-CAP-INDICATORS-021 | Swing-high/low labelling | `custom/smc.py:SMC.calculate`, `_swing_highs_lows` | Questionable | Remove | None in production indicators; possible future research label | Confirm research ownership; current centered future window is non-causal. |
| V1-CAP-INDICATORS-022 | BOS/CHoCH and break-index labelling | `custom/smc.py:SMC.calculate`, `_bos_choch` | Questionable | Remove | None in production indicators; possible future research label | Confirm research ownership and redesign from a causal specification before any reuse. |
| V1-CAP-INDICATORS-023 | Up/down crossover detection | `base.py:crossed_above`, `crossed_below` | No demonstrated value | Remove | Strategy/signal logic if later required | Verify no external imports; crossover interpretation belongs to strategy logic. |
| V1-CAP-INDICATORS-024 | Pip-distance conversion | `base.py:pips_to_price` | No demonstrated value | Remove | Trading/symbol utility domain | Verify no external imports; this is not indicator calculation behavior. |
| V1-CAP-INDICATORS-025 | Balance-scaled broker volume | `base.py:balance_scaled_volume` | No demonstrated value | Remove | Risk/trading sizing domain | Verify no external imports; broker bounds and account sizing are outside indicator ownership. |
| V1-CAP-INDICATORS-026 | Arithmetic and weighted averaging | `base.py:arithmetic_average`, `weighted_average` | No demonstrated value | Remove | General/strategy utility only if separately required | Verify no external imports; duplicate basket averaging already exists outside this package. |

## 6. V2 Requirement Disposition Register

The V2 source does not provide stable IDs for most requirements. The IDs below are reconciliation-only traceability IDs assigned in source order. Every normative/proposed item extracted from purpose, assumptions, ownership, public API, functional requirements, inputs/outputs, manifests, errors, NFRs, edge cases, tests, examples, architecture, documentation, acceptance, prerequisites, tiers, type definitions, and future improvements is included.

### Source section: `1. Purpose`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-PUR-001` | Define the production requirements for the `tools/indicators/` domain. | **Keep** | Use `tools/indicators/` as the intended V2 package boundary. | The V1 audit found a duplicated and disconnected package; a single canonical V2 location is required. |
| `V2-IND-PUR-002` | Provide a pure deterministic calculation library with no direct I/O in indicator calculation paths; all trade, order, fill, and final decision behavior remains owned by downstream simulation, strategy, risk, trading, and live modules. | **Keep** | Provide a pure deterministic calculation library with no direct I/O in indicator calculation paths; all trade, order, fill, and final decision behavior remains owned by downstream simulation, strategy, risk, trading, and live modules. | This boundary or purpose statement is proportionate and directly supports safe indicator use. |
| `V2-IND-PUR-003` | Provide reusable, deterministic indicator calculation primitives for strategy, research, simulation, notebook, CLI, and agentic workflows. | **Keep** | Provide reusable, deterministic indicator calculation primitives for strategy, research, simulation, notebook, CLI, and agentic workflows. | This boundary or purpose statement is proportionate and directly supports safe indicator use. |
| `V2-IND-PUR-004` | Ensure indicator outputs are safe decision-support artifacts with explicit no-lookahead timing, availability metadata, provenance, manifests, reproducibility, cache behavior, and auditability. | **Modify** | Keep calculation paths free of direct I/O; defer all optional adapters and retain only deterministic metadata hooks. | The no-I/O boundary is valid, but introducing adapter contracts before a confirmed workflow would add premature architecture. |
| `V2-IND-PUR-005` | Keep the indicator module separate from trade execution, broker interaction, account mutation, risk approval, and simulation fill ownership. | **Keep** | Keep the indicator module separate from trade execution, broker interaction, account mutation, risk approval, and simulation fill ownership. | This boundary or purpose statement is proportionate and directly supports safe indicator use. |
| `V2-IND-PUR-006` | The initial production baseline covers deterministic batch built-ins before optional streaming, out-of-core, acceleration, proprietary, canary, and release-engineering features. | **Keep** | Use deterministic batch built-ins as the initial scope; classify optional execution modes outside Core MVP. | This is the smallest scope that supports actual strategy, research and simulation consumption. |
| `V2-IND-PUR-007` | No direct I/O includes cache reads/writes, audit writes, telemetry export, plugin discovery, and external clock synchronization; those operations shall occur only through injected, mockable adapter interfaces when explicitly enabled. | **Modify** | Keep calculation paths free of direct I/O; defer all optional adapters and retain only deterministic metadata hooks. | The no-I/O boundary is valid, but introducing adapter contracts before a confirmed workflow would add premature architecture. |

### Source section: `1.1 Assumptions`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ASM-001` | Indicator implementations target Python. | **Keep** | Indicator implementations target Python. | This assumption is consistent with the V1 evidence and the final domain boundary. |
| `V2-IND-ASM-002` | Indicator outputs are decision support artifacts, not official execution artifacts. | **Keep** | Indicator outputs are decision support artifacts, not official execution artifacts. | This assumption is consistent with the V1 evidence and the final domain boundary. |
| `V2-IND-ASM-003` | Official fills, orders, account state, journals, and reports are produced by the simulation module. | **Keep** | Official fills, orders, account state, journals, and reports are produced by the simulation module. | This assumption is consistent with the V1 evidence and the final domain boundary. |
| `V2-IND-ASM-004` | Data normalization and source-readiness rules are owned by the data module. | **Keep** | Data normalization and source-readiness rules are owned by the data module. | This assumption is consistent with the V1 evidence and the final domain boundary. |

### Source section: `Core Ownership`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-OWN-CORE-001` | Indicator calculation primitives and official built-in indicator implementations. | **Add** | Indicator calculation primitives and official built-in indicator implementations. | V1 has fragments of this behaviour but not a coherent production contract. |
| `V2-IND-OWN-CORE-002` | Indicator contracts, including input schema, output schema, parameter schema, warmup policy, availability metadata, and result manifests. | **Add** | Indicator contracts, including input schema, output schema, parameter schema, warmup policy, availability metadata, and result manifests. | V1 has fragments of this behaviour but not a coherent production contract. |
| `V2-IND-OWN-CORE-003` | Built-in indicator families: trend, volatility, and momentum indicators. | **Add** | Built-in indicator families: trend, volatility, and momentum indicators. | V1 has fragments of this behaviour but not a coherent production contract. |
| `V2-IND-OWN-CORE-004` | Indicator registry, custom indicator conformance, public protocols, result types, manifests, incremental state protocol, and extension governance. | **Modify** | Own deterministic built-ins, minimal public contracts, result manifests and a static official registry; defer incremental and custom-extension governance. | The core contract is required, but optional extension infrastructure is not justified for the initial rebuild. |
| `V2-IND-OWN-CORE-005` | Vectorized and batch indicator calculation behavior for supported Core MVP indicators. | **Add** | Vectorized and batch indicator calculation behavior for supported Core MVP indicators. | V1 has fragments of this behaviour but not a coherent production contract. |
| `V2-IND-OWN-CORE-006` | Indicator-specific deterministic output naming, no-lookahead metadata, data-quality propagation, manifest fields, cache-key material, and formula definitions. | **Modify** | Own deterministic identity/checksum material and benchmark definitions; defer cache and observability payload implementations. | Identity and reproducibility are core, while optional integrations are not. |

### Source section: `Optional Capability Ownership`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-OWN-OPT-001` | Incremental, streaming, out-of-core, accelerated, composed, proprietary, feature-flagged, and canary-routed indicator behavior only when the capability is explicitly enabled, documented, and classified outside Core MVP. | **Defer** | Exclude this optional capability from the initial rebuild and reconsider only after the batch core is proven. | No confirmed V1 production workflow requires this capability. |
| `V2-IND-OWN-OPT-002` | Indicator-specific cache-key derivation, cache invalidation triggers, observability metric payloads, benchmarks, and audit-entry payloads where approved sinks or adapters exist. | **Defer** | Exclude this optional capability from the initial rebuild and reconsider only after the batch core is proven. | No confirmed V1 production workflow requires this capability. |

### Source section: `Integrates With / Emits Metadata For`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-OWN-INT-001` | Cache storage backends, audit sinks, tracing backends, alert routing, package release controls, and SLO systems through documented interfaces rather than direct ownership unless a later approved architecture decision assigns ownership to this module. | **Modify** | Expose deterministic metadata only; external sinks, tracing, alerting and release controls remain outside the indicator domain. | The integration boundary is valid, but adapter contracts should be added only when a consuming workflow exists. |
| `V2-IND-OWN-INT-002` | Observability metrics, logs, traces, and alerts shall be emitted only through approved injection points or adapter contracts; the module shall not directly ship telemetry to external collectors from calculation code. | **Modify** | Expose deterministic metadata only; external sinks, tracing, alerting and release controls remain outside the indicator domain. | The integration boundary is valid, but adapter contracts should be added only when a consuming workflow exists. |

### Source section: `2.2 Does Not Own`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-BOUNDARY-001` | Trade execution, order placement, order matching, fills, broker state, account state, portfolio mutation, or live trading actions. | **Keep** | Trade execution, order placement, order matching, fills, broker state, account state, portfolio mutation, or live trading actions. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-002` | Final official position sizing, margin acceptance, risk approval, or risk-governor decisions. | **Keep** | Final official position sizing, margin acceptance, risk approval, or risk-governor decisions. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-003` | Simulation journals, official fill reports, or execution artifacts owned by `app/services/simulation/`. | **Keep** | Simulation journals, official fill reports, or execution artifacts owned by `app/services/simulation/`. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-004` | Market-data source readiness, source adapters, and normalization rules owned by the data module. | **Keep** | Market-data source readiness, source adapters, and normalization rules owned by the data module. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-005` | Strategy logic beyond providing indicator outputs as decision inputs. | **Keep** | Strategy logic beyond providing indicator outputs as decision inputs. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-006` | Network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations inside custom indicator calculation. | **Keep** | Network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations inside custom indicator calculation. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-007` | Cache storage backend implementation, external audit storage, tracing backend implementation, SLO alert routing, release artifact signing, SBOM generation, vulnerability scanning, or release provenance attestation unless explicitly assigned by a later approved decision. | **Keep** | Cache storage backend implementation, external audit storage, tracing backend implementation, SLO alert routing, release artifact signing, SBOM generation, vulnerability scanning, or release provenance attestation unless explicitly assigned by a later approved decision. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-008` | Simulation-layer lookahead errors, fills, orders, journals, and official execution reports; the indicator module only emits metadata needed by downstream layers. | **Keep** | Simulation-layer lookahead errors, fills, orders, journals, and official execution reports; the indicator module only emits metadata needed by downstream layers. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |
| `V2-IND-BOUNDARY-009` | System clock synchronization, NTP configuration, host clock drift remediation, and timezone database update management; the module owns timestamp validation and UTC normalization only at its data boundary. | **Keep** | System clock synchronization, NTP configuration, host clock drift remediation, and timezone database update management; the module owns timestamp validation and UTC normalization only at its data boundary. | This prevents the indicator domain from absorbing execution, data-source or platform responsibilities. |

### Source section: `3.1 Public Capabilities`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-API-001` | Provide public protocols and types such as `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError`. | **Modify** | Expose a minimal `IndicatorProtocol`, `IndicatorResult`, `IndicatorManifest`, `IndicatorSpec`, `WarmupRequirement`, and `IndicatorError`; omit context/state types until needed. | The proposed type set is broader than the approved batch-only scope. |
| `V2-IND-API-002` | Provide registry operations such as `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and allowed `unregister_indicator(...)`. | **Modify** | Provide read-only static registry operations (`get`, `list`, `validate`); defer runtime register/unregister. | A static official registry supports discoverability without plugin lifecycle complexity. |
| `V2-IND-API-003` | Provide typed built-in convenience functions for `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`. | **Add** | Provide typed built-in convenience functions for `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`. | This public behaviour is missing from V1 and supports safe deterministic use. |
| `V2-IND-API-004` | Provide vectorized `IndicatorResult` outputs with generated column names, `values_only`, manifest metadata, availability metadata, quality metadata, and `join_to(input_data, mode="copy")`. | **Add** | Provide vectorized `IndicatorResult` outputs with generated column names, `values_only`, manifest metadata, availability metadata, quality metadata, and `join_to(input_data, mode="copy")`. | This public behaviour is missing from V1 and supports safe deterministic use. |
| `V2-IND-API-005` | Provide no-lookahead availability metadata through `available_at`, `computed_from_start`, `computed_from_end`, `source_timeframe`, and related timing fields. | **Add** | Provide no-lookahead availability metadata through `available_at`, `computed_from_start`, `computed_from_end`, `source_timeframe`, and related timing fields. | This public behaviour is missing from V1 and supports safe deterministic use. |
| `V2-IND-API-006` | Publish a capability matrix declaring which indicators and execution modes support batch, incremental, streaming, composition, cache, audit, observability, benchmarking, and custom indicator governance. | **Modify** | Publish only capabilities supported by Core MVP and report optional modes as unsupported. | The capability matrix is useful, but optional features are deferred. |
| `V2-IND-API-007` | Generate or expose the capability matrix from registry metadata in a machine-readable JSON or YAML-compatible representation. | **Add** | Generate or expose the capability matrix from registry metadata in a machine-readable JSON or YAML-compatible representation. | This public behaviour is missing from V1 and supports safe deterministic use. |
| `V2-IND-API-008` | Unsupported capability requests shall fail before calculation with deterministic `IND_UNSUPPORTED_*` errors. | **Add** | Unsupported capability requests shall fail before calculation with deterministic `IND_UNSUPPORTED_*` errors. | This public behaviour is missing from V1 and supports safe deterministic use. |

### Source section: `1.1 Indicator Domain Boundary`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.1-001` | The indicator module shall live under `tools/indicators/`. | **Add** | Move the canonical V2 domain to `tools/indicators/` and retire duplicate V1 package paths after compatibility checks. | V1 has singular/plural duplication and no canonical production surface. |
| `V2-IND-FR-1.1-002` | The indicator module shall provide reusable indicator calculation primitives for strategy, research, and simulation workflows. | **Add** | The indicator module shall provide reusable indicator calculation primitives for strategy, research, and simulation workflows. | V1 provides calculations but lacks a stable production contract. |
| `V2-IND-FR-1.1-003` | The indicator module shall not execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations. | **Keep** | The indicator module shall not execute trades, create fills, mutate account state, mutate simulation journals, or perform broker-state operations. | This is a necessary domain safety boundary. |
| `V2-IND-FR-1.1-004` | The indicator module shall not determine final official position size, margin acceptance, risk approval, or order matching. | **Keep** | The indicator module shall not determine final official position size, margin acceptance, risk approval, or order matching. | This is a necessary domain safety boundary. |
| `V2-IND-FR-1.1-005` | The indicator module shall expose typed, deterministic functions or classes that can be consumed by strategies and simulation orchestration. | **Add** | The indicator module shall expose typed, deterministic functions or classes that can be consumed by strategies and simulation orchestration. | V1 provides calculations but lacks a stable production contract. |
| `V2-IND-FR-1.1-006` | Indicator outputs shall be treated as decision inputs only; official execution remains owned by `app/services/simulation/`. | **Keep** | Indicator outputs shall be treated as decision inputs only; official execution remains owned by `app/services/simulation/`. | This is a necessary domain safety boundary. |

### Source section: `1.2 Supported Indicator Families`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.2-001` | The module shall support trend indicators including EMA, SMA, and ADX. | **Add** | The module shall support trend indicators including EMA, SMA, and ADX. | The approved batch baseline requires these families; V1 covers only part of them. |
| `V2-IND-FR-1.2-002` | The module shall support volatility indicators including ATR, ADR, and rolling volatility. | **Add** | The module shall support volatility indicators including ATR, ADR, and rolling volatility. | The approved batch baseline requires these families; V1 covers only part of them. |
| `V2-IND-FR-1.2-003` | The module shall support momentum indicators including RSI and Williams %R. | **Add** | The module shall support momentum indicators including RSI and Williams %R. | The approved batch baseline requires these families; V1 covers only part of them. |
| `V2-IND-FR-1.2-004` | Indicator implementations shall define required input columns, output column names, parameter schema, warmup length, and missing-data behavior. | **Add** | Indicator implementations shall define required input columns, output column names, parameter schema, warmup length, and missing-data behavior. | V1 lacks explicit schemas, warmup and missing-data contracts. |
| `V2-IND-FR-1.2-005` | Indicator implementations shall validate parameter ranges before calculation. | **Add** | Indicator implementations shall validate parameter ranges before calculation. | V1 lacks explicit schemas, warmup and missing-data contracts. |
| `V2-IND-FR-1.2-006` | Indicator implementations shall return deterministic errors for invalid input schema, invalid parameter values, insufficient data, non-monotonic timestamps, duplicate timestamps, or impossible OHLCV values. | **Modify** | Validate domain-owned schema, parameters, timestamps and OHLC consistency with deterministic errors; rely on the data domain for source-readiness validation. | The behaviour is required, but data-source quality ownership must stay outside this domain. |

### Source section: `1.3 Input and Output Contracts`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.3-001` | Indicators shall accept normalized historical market data from the data module contract. | **Add** | Indicators shall accept normalized historical market data from the data module contract. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-002` | Indicators shall accept OHLCV inputs with explicit timestamp, symbol, timeframe, and timezone metadata. | **Add** | Indicators shall accept OHLCV inputs with explicit timestamp, symbol, timeframe, and timezone metadata. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-003` | Indicators shall support multi-symbol input only when output grouping preserves symbol identity. | **Add** | Support single-symbol first and allow grouped multi-symbol batch input only when symbol/timestamp identity is explicit. | Multi-symbol support is useful but must not complicate the first implementation slice. |
| `V2-IND-FR-1.3-004` | Indicators shall preserve input row order after deterministic timestamp and symbol validation. | **Add** | Indicators shall preserve input row order after deterministic timestamp and symbol validation. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-005` | Indicator outputs shall include timestamp and symbol alignment metadata. | **Add** | Indicator outputs shall include timestamp and symbol alignment metadata. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-006` | Indicator outputs shall expose warmup or unavailable regions explicitly rather than silently filling values. | **Add** | Indicator outputs shall expose warmup or unavailable regions explicitly rather than silently filling values. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-007` | Indicator outputs shall distinguish computed values, warmup nulls, missing-input nulls, and rejected rows. | **Add** | Indicator outputs shall distinguish computed values, warmup nulls, missing-input nulls, and rejected rows. | V1 returns copied DataFrames but lacks contract metadata and row-state distinctions. |
| `V2-IND-FR-1.3-008` | Indicator outputs used by official backtests shall be serializable in the precision policy required by the downstream workflow. | **Add** | Indicator outputs used by official backtests shall be serializable in the precision policy required by the downstream workflow. | Official replay requires stable numeric serialization. |

### Source section: `1.3.1 Vectorized DataFrame Output and Column Contract`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.3.1-001` | Batch indicators shall calculate outputs through vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. | **Add** | Batch indicators shall calculate outputs through vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-002` | Official production batch indicators shall not rely on per-row Python loops except for formulas with documented stateful dependencies that cannot be vectorized safely. | **Modify** | Require vectorization where safe; permit documented bounded loops for inherently stateful formulas and benchmark them. | A categorical prohibition could reject correct algorithms such as certain path-dependent calculations. |
| `V2-IND-FR-1.3.1-003` | Indicator calculation shall not mutate the input dataframe by default. | **Add** | Indicator calculation shall not mutate the input dataframe by default. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-004` | Official workflows shall treat in-place input mutation as prohibited unless an explicitly configured internal optimization proves copy-equivalent output and records the optimization in the manifest. | **Defer** | Core MVP supports copied output, deterministic default naming, and collision failure only; custom mutation and naming policies are deferred. | The additional modes create configuration surface without a demonstrated workflow. |
| `V2-IND-FR-1.3.1-005` | The default batch result shall be an `IndicatorResult` containing an aligned `values` dataframe with timestamp, symbol, generated indicator columns, availability metadata, and quality metadata. | **Add** | The default batch result shall be an `IndicatorResult` containing an aligned `values` dataframe with timestamp, symbol, generated indicator columns, availability metadata, and quality metadata. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-006` | The result object shall expose a `join_to(input_data, mode="copy")` helper that returns a copy of the source dataframe with generated indicator columns appended. | **Add** | The result object shall expose a `join_to(input_data, mode="copy")` helper that returns a copy of the source dataframe with generated indicator columns appended. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-007` | The result object shall expose generated column names through `output_columns`. | **Add** | The result object shall expose generated column names through `output_columns`. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-008` | The result object shall expose `values_only` output for workflows that require indicator columns without the original OHLCV columns. | **Add** | The result object shall expose `values_only` output for workflows that require indicator columns without the original OHLCV columns. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-009` | A call equivalent to `ema(data, period=10, source="close")` shall generate an indicator column named `ema_10` when `close` is the default source. | **Add** | A call equivalent to `ema(data, period=10, source="close")` shall generate an indicator column named `ema_10` when `close` is the default source. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-010` | When the source column is not the default source or when naming ambiguity exists, output column names shall include the source column, such as `ema_open_10` or `ema_close_10`. | **Add** | When the source column is not the default source or when naming ambiguity exists, output column names shall include the source column, such as `ema_open_10` or `ema_close_10`. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-011` | Multi-output indicators shall expose deterministic output column names for each component, such as `adx_14`, `plus_di_14`, and `minus_di_14`. | **Add** | Multi-output indicators shall expose deterministic output column names for each component, such as `adx_14`, `plus_di_14`, and `minus_di_14`. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-012` | Output column naming shall use stable lowercase snake_case names derived from indicator id, source column, period, and named parameters in canonical parameter order. | **Add** | Output column naming shall use stable lowercase snake_case names derived from indicator id, source column, period, and named parameters in canonical parameter order. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-013` | Custom output column names shall be accepted only when they pass schema validation, collision checks, and deterministic naming policy checks. | **Defer** | Core MVP supports copied output, deterministic default naming, and collision failure only; custom mutation and naming policies are deferred. | The additional modes create configuration surface without a demonstrated workflow. |
| `V2-IND-FR-1.3.1-014` | Output column collisions with existing input columns shall fail with a deterministic error by default. | **Add** | Output column collisions with existing input columns shall fail with a deterministic error by default. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-015` | Explicit overwrite, suffix, prefix, or namespace behavior for output column collisions shall require configuration and shall be recorded in the manifest. | **Defer** | Core MVP supports copied output, deterministic default naming, and collision failure only; custom mutation and naming policies are deferred. | The additional modes create configuration surface without a demonstrated workflow. |
| `V2-IND-FR-1.3.1-016` | Joined output shall preserve original input columns, row count, row ordering, timestamp alignment, symbol grouping, and index policy. | **Add** | Joined output shall preserve original input columns, row count, row ordering, timestamp alignment, symbol grouping, and index policy. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-017` | Warmup and unavailable rows shall remain present in joined output with nullable indicator values and explicit metadata rather than being dropped. | **Add** | Warmup and unavailable rows shall remain present in joined output with nullable indicator values and explicit metadata rather than being dropped. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |
| `V2-IND-FR-1.3.1-018` | Vectorized output alignment shall be verified by timestamp and symbol keys rather than by positional row number alone when the input dataframe has an external index. | **Add** | Vectorized output alignment shall be verified by timestamp and symbol keys rather than by positional row number alone when the input dataframe has an external index. | V1 copy-and-enrich behaviour is useful but must become an explicit result contract. |

### Source section: `1.4 No-Lookahead and Timing`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.4-001` | Indicator-derived trade signals shall obey no-lookahead timing. | **Modify** | Indicators emit availability metadata; strategies create signals and simulation enforces decision-time access. | Signal ownership belongs downstream even though indicator timing metadata is required. |
| `V2-IND-FR-1.4-002` | Indicators used for bar-open strategies shall expose only fully closed-bar values available before the first tick of the next bar. | **Add** | Indicators used for bar-open strategies shall expose only fully closed-bar values available before the first tick of the next bar. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-003` | Indicator calculations shall not use current incomplete bar high, low, close, volume, or derived values for previous-closed-bar decisions. | **Add** | Indicator calculations shall not use current incomplete bar high, low, close, volume, or derived values for previous-closed-bar decisions. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-004` | At the first tick of bar `N`, indicator-derived data with timestamp greater than or equal to bar `N` open time shall be masked, dropped, or rejected before strategy access. | **Add** | At the first tick of bar `N`, indicator-derived data with timestamp greater than or equal to bar `N` open time shall be masked, dropped, or rejected before strategy access. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-005` | Multi-timeframe indicator alignment shall not expose higher-timeframe values until the higher-timeframe bar is fully closed. | **Add** | Multi-timeframe indicator alignment shall not expose higher-timeframe values until the higher-timeframe bar is fully closed. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-006` | The module shall provide `available_at`, source `bar_close_time`, source `bar_open_time` when available, `computed_from_start`, `computed_from_end`, `source_timeframe`, and a `lookahead_prohibited` flag for downstream lookahead enforcement. | **Add** | The module shall provide `available_at`, source `bar_close_time`, source `bar_open_time` when available, `computed_from_start`, `computed_from_end`, `source_timeframe`, and a `lookahead_prohibited` flag for downstream lookahead enforcement. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-007` | The module shall provide metadata required for downstream layers to raise their own lookahead errors while keeping simulation-layer errors outside indicator ownership. | **Add** | The module shall provide metadata required for downstream layers to raise their own lookahead errors while keeping simulation-layer errors outside indicator ownership. | V1 has no availability contract and SMC contains confirmed lookahead. |
| `V2-IND-FR-1.4-008` | Vectorized indicator generation shall provide explicit utilities to shift outputs, such as `.shift(1)`, to align with bar-open execution logic. | **Modify** | Document and test consumer-side shifting/alignment; do not add a special domain API beyond normal DataFrame operations and availability metadata. | The required behaviour is alignment, not a custom wrapper around pandas `shift`. |
| `V2-IND-FR-1.4-009` | Documentation shall warn against using unshifted current-bar values for bar-open decisions. | **Add** | Documentation shall warn against using unshifted current-bar values for bar-open decisions. | V1 has no availability contract and SMC contains confirmed lookahead. |

### Source section: `1.5 Determinism, Precision, and Reproducibility`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.5-001` | The same indicator input data, parameter set, implementation version, and precision policy shall produce the same output. | **Add** | The same indicator input data, parameter set, implementation version, and precision policy shall produce the same output. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-002` | Indicator implementations shall avoid hidden global mutable state. | **Add** | Indicator implementations shall avoid hidden global mutable state. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-003` | Indicator implementations shall define numeric precision behavior. | **Add** | Indicator implementations shall define numeric precision behavior. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-004` | Core MVP numeric behavior shall use IEEE 754 `float64` outputs with default relative tolerance `1e-9` and default absolute tolerance `1e-12` for golden and cross-validation tests unless an approved formula table overrides the tolerance. | **Add** | Core MVP numeric behavior shall use IEEE 754 `float64` outputs with default relative tolerance `1e-9` and default absolute tolerance `1e-12` for golden and cross-validation tests unless an approved formula table overrides the tolerance. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-005` | Floating-point arithmetic may be used for research indicators when outputs are not directly used for official accounting or official fill prices. | **Add** | Floating-point arithmetic may be used for research indicators when outputs are not directly used for official accounting or official fill prices. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-006` | Indicator outputs that feed official simulation decisions shall be reproducible across replay runs. | **Add** | Indicator outputs that feed official simulation decisions shall be reproducible across replay runs. | V1 has deterministic calculations but no explicit precision, versioning or manifest contract. |
| `V2-IND-FR-1.5-007` | Indicator result manifests shall include input data checksum, parameter hash, implementation version, output schema version, and calculation timestamp. | **Modify** | Keep deterministic identity fields separate from volatile runtime diagnostics; calculation timestamps must not affect output identity or replay equality. | A wall-clock field conflicts with the requirement that identical inputs produce identical manifests. |

### Source section: `1.6 Caching and Performance`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.6-001` | Indicator calculations may be cached by indicator id, parameter hash, input data checksum, implementation version, schema version, and precision policy. | **Defer** | Defer cache adapters and cache policies; preserve deterministic checksum and parameter-hash material for future use. | No V1 workflow demonstrates a cache requirement. |
| `V2-IND-FR-1.6-002` | Cache hits shall be deterministic and shall never reuse results across incompatible input data, parameter sets, implementation versions, or schema versions. | **Defer** | Defer cache adapters and cache policies; preserve deterministic checksum and parameter-hash material for future use. | No V1 workflow demonstrates a cache requirement. |
| `V2-IND-FR-1.6-003` | If an optional cache adapter is unreachable and `cache_policy="best_effort"`, the module shall degrade to uncached calculation with warning metadata rather than raising an unhandled exception. | **Defer** | Defer cache adapters and cache policies; preserve deterministic checksum and parameter-hash material for future use. | No V1 workflow demonstrates a cache requirement. |
| `V2-IND-FR-1.6-004` | If an optional cache adapter is unreachable and `cache_policy="strict"`, the request shall fail before calculation with deterministic cache-unavailable diagnostics. | **Defer** | Defer cache adapters and cache policies; preserve deterministic checksum and parameter-hash material for future use. | No V1 workflow demonstrates a cache requirement. |
| `V2-IND-FR-1.6-005` | Uncached first-run batch calculation for each official built-in indicator over 10 symbols and 10 years of M1 bars shall target p99 less than or equal to 5 seconds on the documented benchmark hardware profile. | **Open Decision** | Benchmark the approved core on named hardware before setting binding p99 targets. | The proposed targets are unverified and may be unrealistic for the stated data volumes. |
| `V2-IND-FR-1.6-006` | Warm-cache batch calculation for official indicator workloads shall target p99 less than or equal to 250 milliseconds for up to 10 symbols and 100,000 input rows, aligned with the service-level objective section. | **Open Decision** | Benchmark the approved core on named hardware before setting binding p99 targets. | The proposed targets are unverified and may be unrealistic for the stated data volumes. |
| `V2-IND-FR-1.6-007` | Indicator calculations shall support chunked processing where mathematically valid and shall preserve warmup continuity across chunks. | **Defer** | Defer chunked execution until full-run formulas and golden fixtures are stable. | Chunk continuity adds state complexity not required by the initial batch workflow. |
| `V2-IND-FR-1.6-008` | Chunked indicator output shall match full-run output within the documented precision policy. | **Defer** | Defer chunked execution until full-run formulas and golden fixtures are stable. | Chunk continuity adds state complexity not required by the initial batch workflow. |

### Source section: `1.6.1 Performance Benchmark Specifications`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.6.1-001` | Performance benchmarks shall specify hardware profile, including CPU model, core count, RAM, and disk type when caching is disk-backed. | **Add** | Performance benchmarks shall specify hardware profile, including CPU model, core count, RAM, and disk type when caching is disk-backed. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-002` | Performance benchmarks shall specify Python version and key dependency versions, including NumPy, pandas, and any optional acceleration dependencies. | **Add** | Performance benchmarks shall specify Python version and key dependency versions, including NumPy, pandas, and any optional acceleration dependencies. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-003` | Performance benchmarks shall state whether cached or uncached performance is being measured. | **Add** | Performance benchmarks shall state whether cached or uncached performance is being measured. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-004` | Performance benchmarks shall define warmup iterations before measurement. | **Add** | Performance benchmarks shall define warmup iterations before measurement. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-005` | Performance benchmarks shall define measurement methodology, including wall-clock timing and min, median, and p99 over a documented run count. | **Add** | Performance benchmarks shall define measurement methodology, including wall-clock timing and min, median, and p99 over a documented run count. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-006` | The benchmark suite shall fail CI when performance regresses by more than 20 percent without explicit approval. | **Defer** | Record benchmark baselines first; add a CI regression gate only after stable, low-noise measurements exist. | An immediate hard gate would be brittle without established hardware and variance controls. |
| `V2-IND-FR-1.6.1-007` | Per-indicator benchmarks shall be maintained and tracked over releases. | **Add** | Per-indicator benchmarks shall be maintained and tracked over releases. | Reproducible benchmark metadata is needed before approving performance targets. |
| `V2-IND-FR-1.6.1-008` | Performance benchmark specifications shall be the source for the p99 uncached and warm-cache targets defined in the service-level objective section. | **Add** | Performance benchmark specifications shall be the source for the p99 uncached and warm-cache targets defined in the service-level objective section. | Reproducible benchmark metadata is needed before approving performance targets. |

### Source section: `1.6.2 Scalability and Out-of-Core Processing`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.6.2-001` | Indicator calculations shall support out-of-core processing for datasets that exceed configured memory budgets when the indicator formula permits bounded-state or chunked computation. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-002` | Out-of-core outputs shall match in-memory full-run outputs within the documented precision policy. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-003` | Out-of-core processing shall preserve warmup continuity, symbol grouping, timestamp ordering, provenance metadata, and cache-key determinism across chunks. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-004` | Out-of-core processing shall expose deterministic errors when an indicator requires full in-memory context and cannot be safely chunked. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-005` | Optional hardware acceleration backends, including Numba, CuPy, SIMD, or equivalent backends, shall be isolated behind explicit feature flags or extras. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-006` | Every accelerated indicator path shall provide a pure NumPy, pandas, or standard Python fallback with identical public API behavior. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-007` | Accelerated and fallback paths shall produce outputs that match within the documented precision policy and shall record backend metadata in the result manifest. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-008` | Parallel execution across symbols shall be configurable by thread pool, process pool, worker count, chunk size, and cache synchronization mode. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |
| `V2-IND-FR-1.6.2-009` | The module shall document whether each accelerated or parallel backend releases the GIL, uses multiprocessing, or requires single-threaded execution. | **Defer** | Exclude out-of-core, acceleration and parallel execution from Core MVP; retain pure batch semantics as the reference. | These are explicitly optional and have no confirmed V1 production workflow. |

### Source section: `1.7 Registry and Extensibility`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.7-001` | The module shall provide an indicator registry for approved indicator implementations. | **Add** | Provide a static official built-in registry with immutable specs and validation. | Discoverability and capability reporting are useful without dynamic plugin lifecycle. |
| `V2-IND-FR-1.7-002` | Registered indicators shall declare id, name, version, parameter schema, input schema, output schema, warmup policy, and deterministic behavior. | **Add** | Provide a static official built-in registry with immutable specs and validation. | Discoverability and capability reporting are useful without dynamic plugin lifecycle. |
| `V2-IND-FR-1.7-003` | Custom indicators shall be registered through approved extension points before use in official workflows. | **Defer** | Defer runtime custom-indicator registration and official extension governance. | No confirmed workflow requires third-party registration in the initial rebuild. |
| `V2-IND-FR-1.7-004` | Custom indicator registration shall not bypass input validation, no-lookahead metadata, schema validation, or deterministic replay requirements. | **Defer** | Defer runtime custom-indicator registration and official extension governance. | No confirmed workflow requires third-party registration in the initial rebuild. |

### Source section: `1.8 Public API and Compatibility`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.8-001` | The indicator module shall explicitly declare its public API surface. | **Add** | The indicator module shall explicitly declare its public API surface. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-002` | Public APIs shall include stable import paths, function and class signatures, parameter schemas, result schemas, error schemas, and registry contracts. | **Add** | Public APIs shall include stable import paths, function and class signatures, parameter schemas, result schemas, error schemas, and registry contracts. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-003` | Internal modules shall be clearly marked as private and shall not be consumed directly by strategy or simulation code. | **Add** | Internal modules shall be clearly marked as private and shall not be consumed directly by strategy or simulation code. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-004` | Public API changes shall follow semantic versioning. | **Add** | Public API changes shall follow semantic versioning. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-005` | Backward-incompatible public API, schema, formula, or behavior changes shall require a major version bump or documented migration path. | **Add** | Backward-incompatible public API, schema, formula, or behavior changes shall require a major version bump or documented migration path. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-006` | Deprecated APIs, indicators, parameters, or schemas shall emit deterministic deprecation warnings and remain supported for a documented compatibility window. | **Modify** | Adopt basic semantic versioning and documented migration; defer the formal multi-release lifecycle until the public API reaches v1 stability. | A full lifecycle is premature during a clean rebuild. |
| `V2-IND-FR-1.8-007` | Indicator result schema versions shall be independently versioned from implementation versions. | **Add** | Indicator result schema versions shall be independently versioned from implementation versions. | V1 has exports but no stable compatibility or schema version policy. |
| `V2-IND-FR-1.8-008` | Public indicator interfaces shall use `typing.Protocol` or equivalent structural typing contracts so custom indicators can integrate without inheriting from framework base classes. | **Modify** | Use a minimal structural protocol only for registry/custom compatibility; built-ins remain stateless functions. | Inheritance is unnecessary, but the proposed broad interface is excessive. |
| `V2-IND-FR-1.8-009` | Indicator result objects shall implement rich notebook inspection methods, including `_repr_html_` and `_repr_pretty_`, with summary statistics, warmup visualization, unavailable-region visibility, and manifest summary. | **Defer** | Defer rich notebook representations until result and manifest contracts are stable. | This is convenience, not core correctness. |
| `V2-IND-FR-1.8-010` | Debug-mode APIs shall enforce strict typing and runtime validation before calculation begins, using validated schemas or equivalent runtime guards. | **Merge** | Perform fail-fast validation in all official calls; do not create a separate debug-mode contract. | Validation should not depend on a mode switch. |
| `V2-IND-FR-1.8-011` | Type mismatch failures in debug mode shall fail fast with deterministic errors before any output, state mutation, cache read, or cache write occurs. | **Add** | Type mismatch failures in debug mode shall fail fast with deterministic errors before any output, state mutation, cache read, or cache write occurs. | V1 has exports but no stable compatibility or schema version policy. |

### Source section: `1.8.1 Deprecation Lifecycle`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.8.1-001` | Deprecated indicators, parameters, schemas, or APIs shall follow a three-phase lifecycle. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |
| `V2-IND-FR-1.8.1-002` | The deprecation warning phase shall last at least two minor releases, emit structured warnings on every use, and continue full support. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |
| `V2-IND-FR-1.8.1-003` | The deprecation error with opt-in phase shall last at least two minor releases, raise `IND_DEPRECATED` by default, and support an explicit opt-in flag to restore behavior with a warning. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |
| `V2-IND-FR-1.8.1-004` | The removal phase shall occur only in a major version and shall return `IND_UNSUPPORTED_INDICATOR` or the closest deterministic unsupported-API error. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |
| `V2-IND-FR-1.8.1-005` | Deprecation timelines shall be documented in the changelog and migration guide. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |
| `V2-IND-FR-1.8.1-006` | The deprecation phase for each indicator, parameter, schema, or API shall be machine-readable through the registry. | **Defer** | Defer the three-phase deprecation mechanism until the V2 public API is declared stable. | The clean rebuild has no established V2 compatibility window yet. |

### Source section: `1.8.2 Indicator Anatomy and Required Interfaces`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.8.2-001` | The indicator module shall expose a documented anatomy for every official and custom indicator. | **Add** | The indicator module shall expose a documented anatomy for every official and custom indicator. | This supports a coherent batch public API absent from V1. |
| `V2-IND-FR-1.8.2-002` | The public package shall expose `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` with exact approved type contracts. | **Defer** | Exclude incremental state and update methods from the initial public anatomy. | Batch-only Core MVP does not need state lifecycle. |
| `V2-IND-FR-1.8.2-003` | `IndicatorProtocol` shall define required attributes for `indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, and `status`. | **Add** | `IndicatorProtocol` shall define required attributes for `indicator_id`, `name`, `version`, `formula_version`, `input_schema`, `parameter_schema`, `output_schema`, `warmup_policy`, `capabilities`, and `status`. | This supports a coherent batch public API absent from V1. |
| `V2-IND-FR-1.8.2-004` | `IndicatorProtocol` shall define `validate_parameters(parameters)`. | **Modify** | Expose these behaviours through immutable indicator specifications and shared validation, not mandatory instance methods on every built-in. | Metadata-driven functions are simpler than framework-style classes. |
| `V2-IND-FR-1.8.2-005` | `IndicatorProtocol` shall define `required_columns(parameters)`. | **Modify** | Expose these behaviours through immutable indicator specifications and shared validation, not mandatory instance methods on every built-in. | Metadata-driven functions are simpler than framework-style classes. |
| `V2-IND-FR-1.8.2-006` | `IndicatorProtocol` shall define `output_columns(parameters, source=None, naming_policy=None)`. | **Modify** | Expose these behaviours through immutable indicator specifications and shared validation, not mandatory instance methods on every built-in. | Metadata-driven functions are simpler than framework-style classes. |
| `V2-IND-FR-1.8.2-007` | `IndicatorProtocol` shall define `warmup_requirement(parameters, timeframe, calendar=None)`. | **Modify** | Expose these behaviours through immutable indicator specifications and shared validation, not mandatory instance methods on every built-in. | Metadata-driven functions are simpler than framework-style classes. |
| `V2-IND-FR-1.8.2-008` | `IndicatorProtocol` shall define `validate_input(data, config, context)`. | **Modify** | Expose these behaviours through immutable indicator specifications and shared validation, not mandatory instance methods on every built-in. | Metadata-driven functions are simpler than framework-style classes. |
| `V2-IND-FR-1.8.2-009` | `IndicatorProtocol` shall define `calculate(data, config, context)`. | **Add** | `IndicatorProtocol` shall define `calculate(data, config, context)`. | This supports a coherent batch public API absent from V1. |
| `V2-IND-FR-1.8.2-010` | `IndicatorProtocol` shall define `calculate_vectorized(data, config, context)` when the indicator supports vectorized batch execution separately from generic calculation. | **Merge** | Use one `calculate` contract whose official batch implementations are vectorized; do not duplicate generic and vectorized methods. | Two methods add no value for a batch-only API. |
| `V2-IND-FR-1.8.2-011` | `IndicatorProtocol` shall define `update(bar, state, config, context)` when the indicator supports incremental or streaming execution. | **Defer** | Exclude incremental state and update methods from the initial public anatomy. | Batch-only Core MVP does not need state lifecycle. |
| `V2-IND-FR-1.8.2-012` | `IndicatorProtocol` shall define `serialize_state(state)` and `deserialize_state(payload)` when the indicator supports incremental or streaming execution. | **Defer** | Exclude incremental state and update methods from the initial public anatomy. | Batch-only Core MVP does not need state lifecycle. |
| `V2-IND-FR-1.8.2-013` | `IndicatorConfig` shall contain indicator id, parameters, source column, output naming policy, output mode, column conflict policy, precision policy, cache policy, calendar policy, availability policy, and execution backend configuration. | **Modify** | Keep indicator id, parameters, source, output mode, precision and availability policy; defer cache, calendar and backend fields. | The proposed config aggregates optional capabilities. |
| `V2-IND-FR-1.8.2-014` | `IndicatorContext` shall contain request id, correlation id, actor, workflow, environment, entitlement context, tracing context, observability context, and SLO context where applicable. | **Reject** | Do not place actor, entitlement, tracing, observability and SLO context in the core calculation contract; pass only calculation-relevant metadata. | This couples pure formulas to unrelated platform concerns. |
| `V2-IND-FR-1.8.2-015` | `IndicatorResult` shall contain `values`, `output_columns`, `manifest`, `availability`, `quality`, `state`, `errors`, `metrics`, and `join_to(...)`. | **Modify** | Core result contains values, output columns, availability, quality, errors and manifest plus `join_to`; omit state and metrics initially. | State and observability are deferred. |
| `V2-IND-FR-1.8.2-016` | `IndicatorManifest` shall contain calculation identity, formula identity, input checksum, output checksum, parameter hash, output schema version, output column contract, data provenance, execution backend, timing, environment, and audit metadata. | **Modify** | Use a deterministic core manifest; put volatile runtime diagnostics outside identity fields and omit optional audit/backend sections. | The proposed manifest mixes deterministic identity with operational context. |
| `V2-IND-FR-1.8.2-017` | `IndicatorState` shall contain serializable incremental accumulators, last processed timestamp, last processed symbol, warmup completion status, input checksum, and state schema version. | **Defer** | Exclude incremental state and update methods from the initial public anatomy. | Batch-only Core MVP does not need state lifecycle. |
| `V2-IND-FR-1.8.2-018` | The public package shall expose registry operations for `register_indicator(...)`, `get_indicator(...)`, `list_indicators(...)`, `validate_indicator(...)`, and `unregister_indicator(...)` where unregistering is allowed outside official production registries. | **Modify** | Expose `get_indicator`, `list_indicators`, and `validate_indicator` over a static registry; defer register/unregister mutation. | A mutable runtime registry is unnecessary for official built-ins. |
| `V2-IND-FR-1.8.2-019` | Official indicator convenience functions shall expose typed wrappers for supported built-ins, including `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`. | **Add** | Official indicator convenience functions shall expose typed wrappers for supported built-ins, including `ema(...)`, `sma(...)`, `adx(...)`, `atr(...)`, `adr(...)`, `rolling_volatility(...)`, `rsi(...)`, and `williams_r(...)`. | This supports a coherent batch public API absent from V1. |
| `V2-IND-FR-1.8.2-020` | Convenience functions shall return `IndicatorResult` and shall use the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry-driven execution. | **Add** | Convenience functions shall return `IndicatorResult` and shall use the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry-driven execution. | This supports a coherent batch public API absent from V1. |
| `V2-IND-FR-1.8.2-021` | Public module layout shall separate core protocols, result types, registry code, built-in indicator implementations, error definitions, and test fixtures. | **Modify** | Separate core contracts/errors/results/registry from the three built-in families; keep tests outside the runtime package. | The separation is useful but the proposed layout is over-fragmented. |
| `V2-IND-FR-1.8.2-022` | Private helper modules shall not be required for downstream strategy, simulation, notebook, or custom-indicator integration. | **Add** | Private helper modules shall not be required for downstream strategy, simulation, notebook, or custom-indicator integration. | This supports a coherent batch public API absent from V1. |

### Source section: `1.9 Mathematical Convention Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.9-001` | Every indicator shall define its exact mathematical formula. | **Add** | Every indicator shall define its exact mathematical formula. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-002` | Every built-in indicator shall provide a concrete formula specification before implementation begins. | **Add** | Every built-in indicator shall provide a concrete formula specification before implementation begins. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-003` | Every built-in indicator shall define default parameters, allowed parameter ranges, default source columns, required input columns, warmup length, output columns, null behavior, and degenerate-window behavior. | **Add** | Every built-in indicator shall define default parameters, allowed parameter ranges, default source columns, required input columns, warmup length, output columns, null behavior, and degenerate-window behavior. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-004` | Every rolling-window indicator shall define whether windows are left-closed, right-closed, and whether the current row is included. | **Add** | Every rolling-window indicator shall define whether windows are left-closed, right-closed, and whether the current row is included. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-005` | Every smoothed indicator shall define smoothing method, alpha convention, and initial seed behavior. | **Add** | Every smoothed indicator shall define smoothing method, alpha convention, and initial seed behavior. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-006` | RSI, ATR, and ADX implementations shall explicitly state whether they use Wilder smoothing or another smoothing convention. | **Add** | RSI, ATR, and ADX implementations shall explicitly state whether they use Wilder smoothing or another smoothing convention. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-007` | Rolling volatility shall define return type, log-return versus simple-return behavior, sample versus population standard deviation, degrees of freedom, and annualization factor. | **Add** | Rolling volatility shall define return type, log-return versus simple-return behavior, sample versus population standard deviation, degrees of freedom, and annualization factor. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-008` | ADR shall define whether it uses high-low range, close-to-close range, session range, calendar-day range, or trading-day range. | **Add** | ADR shall define whether it uses high-low range, close-to-close range, session range, calendar-day range, or trading-day range. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-009` | Williams %R shall define behavior when highest high equals lowest low. | **Add** | Williams %R shall define behavior when highest high equals lowest low. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-010` | Division-by-zero, all-null windows, constant-price windows, zero-volume windows, flat-market windows, NaN inputs, infinite values, overflow, underflow, and negative zero shall produce deterministic outputs or deterministic errors. | **Add** | Division-by-zero, all-null windows, constant-price windows, zero-volume windows, flat-market windows, NaN inputs, infinite values, overflow, underflow, and negative zero shall produce deterministic outputs or deterministic errors. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |
| `V2-IND-FR-1.9-011` | Indicator formulas shall be documented with enough precision that an independent implementation can reproduce the same output. | **Add** | Indicator formulas shall be documented with enough precision that an independent implementation can reproduce the same output. | V1 formulas are under-specified and already show a documented standard-deviation mismatch. |

### Source section: `1.9.1 Built-in Formula Specification Tables`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.9.1-001` | Each official built-in indicator shall include a formula specification table defining indicator id, required columns, default source column, parameters, default parameter values, valid parameter ranges, formula, smoothing convention, seed behavior, warmup length, window inclusivity, null handling, degenerate-window behavior, output columns, and precision tolerance. | **Add** | Each official built-in indicator shall include a formula specification table defining indicator id, required columns, default source column, parameters, default parameter values, valid parameter ranges, formula, smoothing convention, seed behavior, warmup length, window inclusivity, null handling, degenerate-window behavior, output columns, and precision tolerance. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-002` | Formula specification tables shall be completed for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins. | **Add** | Formula specification tables shall be completed for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R before implementation begins. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-003` | Formula tables must be approved before any Core MVP implementation begins; their absence shall halt coding for `tools/indicators/`. | **Add** | Formula tables must be approved before any Core MVP implementation begins; their absence shall halt coding for `tools/indicators/`. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-004` | Formula specification tables shall state whether each indicator is Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement. | **Add** | Formula specification tables shall state whether each indicator is Core MVP, Official Backtest Required, Production Required, Optional Extension, or Future Improvement. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-005` | The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ. | **Add** | The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-006` | Any formula, seed, warmup, tolerance, or default-parameter change shall require an implementation version update, golden fixture review, and documented migration or changelog note. | **Add** | Any formula, seed, warmup, tolerance, or default-parameter change shall require an implementation version update, golden fixture review, and documented migration or changelog note. | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |
| `V2-IND-FR-1.9.1-007` | Formula specification tables shall use this minimum template: | **Add** | Formula specification tables shall use this minimum template: | Formula approval is the key prerequisite for correcting V1 ambiguity and ensuring reproducibility. |

### Source section: `1.10 Indicator Availability Contract`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.10-001` | Every indicator output row shall include or derive a deterministic `available_at` timestamp. | **Add** | Every indicator output row shall include or derive a deterministic `available_at` timestamp. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-002` | `available_at` shall represent the earliest time at which the value may be consumed by a strategy without lookahead. | **Add** | `available_at` shall represent the earliest time at which the value may be consumed by a strategy without lookahead. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-003` | Indicator output rows shall include `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. | **Add** | Indicator output rows shall include `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-004` | Higher-timeframe indicator values shall set `available_at` no earlier than the close of the higher-timeframe source bar plus configured data latency. | **Add** | Higher-timeframe indicator values shall set `available_at` no earlier than the close of the higher-timeframe source bar plus configured data latency. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-005` | Strategy-facing APIs shall filter by `available_at <= decision_time`, not merely by indicator timestamp. | **Add** | Strategy-facing APIs shall filter by `available_at <= decision_time`, not merely by indicator timestamp. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-006` | Indicator outputs shall expose `label_time`, `bar_open_time`, `bar_close_time`, and `available_at` when these differ. | **Add** | Indicator outputs shall expose `label_time`, `bar_open_time`, `bar_close_time`, and `available_at` when these differ. | V1 lacks availability metadata and includes retrospective outputs. |
| `V2-IND-FR-1.10-007` | If a strategy-facing consumer attempts to read a value with `available_at > decision_time`, the retrieval shall raise `IND_LOOKAHEAD_RISK` or return a masked/unavailable result according to the configured error mode. | **Modify** | Indicator results expose mask/filter helpers and `IND_LOOKAHEAD_RISK`; downstream strategy/simulation remains responsible for access enforcement. | The indicator domain provides metadata and safe helpers but does not own simulation policy. |

### Source section: `1.11 Calendar and Session Semantics`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.11-001` | Indicator calculations shall define whether windows operate over rows, elapsed time, trading sessions, or calendar time. | **Add** | Indicator calculations shall define whether windows operate over rows, elapsed time, trading sessions, or calendar time. | UTC and explicit window semantics are required for deterministic availability. |
| `V2-IND-FR-1.11-002` | Session-aware indicators shall use an explicit trading calendar. | **Modify** | Core row-based indicators consume UTC-normalized data; session-aware behaviour is specified only for indicators that need it and relies on data-provided calendar metadata. | General market-session normalization belongs primarily to the data domain. |
| `V2-IND-FR-1.11-003` | The module shall define behavior for weekends, exchange holidays, half-days, daylight-saving transitions, and missing session opens or closes. | **Modify** | Core row-based indicators consume UTC-normalized data; session-aware behaviour is specified only for indicators that need it and relies on data-provided calendar metadata. | General market-session normalization belongs primarily to the data domain. |
| `V2-IND-FR-1.11-004` | Multi-session rolling windows shall define whether overnight gaps are included. | **Modify** | Core row-based indicators consume UTC-normalized data; session-aware behaviour is specified only for indicators that need it and relies on data-provided calendar metadata. | General market-session normalization belongs primarily to the data domain. |
| `V2-IND-FR-1.11-005` | Indicators shall define whether pre-market, regular-session, post-market, and 24/7 market data are treated separately or continuously. | **Modify** | Core row-based indicators consume UTC-normalized data; session-aware behaviour is specified only for indicators that need it and relies on data-provided calendar metadata. | General market-session normalization belongs primarily to the data domain. |
| `V2-IND-FR-1.11-006` | Session resets shall be explicit for indicators that require them. | **Modify** | Core row-based indicators consume UTC-normalized data; session-aware behaviour is specified only for indicators that need it and relies on data-provided calendar metadata. | General market-session normalization belongs primarily to the data domain. |
| `V2-IND-FR-1.11-007` | Official workflows shall reject timezone-naive, ambiguous, or nonexistent local timestamps. | **Add** | Official workflows shall reject timezone-naive, ambiguous, or nonexistent local timestamps. | UTC and explicit window semantics are required for deterministic availability. |
| `V2-IND-FR-1.11-008` | All internal timestamp arithmetic and cache keys shall be normalized to UTC. | **Add** | All internal timestamp arithmetic and cache keys shall be normalized to UTC. | UTC and explicit window semantics are required for deterministic availability. |
| `V2-IND-FR-1.11-009` | Local time or exchange time conversion shall occur only at input, output, display, or external integration boundaries. | **Add** | Local time or exchange time conversion shall occur only at input, output, display, or external integration boundaries. | UTC and explicit window semantics are required for deterministic availability. |
| `V2-IND-FR-1.11-010` | Timezone database dependent conversions shall be confined to I/O boundaries and shall record timezone database version or conversion policy when available. | **Modify** | Require UTC-normalized inputs and record conversion policy when supplied; do not make the indicator package manage timezone databases. | Host timezone management is outside the domain. |
| `V2-IND-FR-1.11-011` | Historical indicator calculation shall not depend on host timezone database changes after inputs are normalized to UTC. | **Modify** | Require UTC-normalized inputs and record conversion policy when supplied; do not make the indicator package manage timezone databases. | Host timezone management is outside the domain. |
| `V2-IND-FR-1.11-012` | Internal processing shall use UTC-aware timestamps or documented naive UTC representations only. | **Add** | Internal processing shall use UTC-aware timestamps or documented naive UTC representations only. | UTC and explicit window semantics are required for deterministic availability. |

### Source section: `1.12 Market Data Provenance and Adjustment Policy`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.12-001` | Indicator inputs shall declare price adjustment status: raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, or synthetic. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-002` | Indicator inputs shall declare price source: trade, bid, ask, mid, mark, settlement, or vendor-derived. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-003` | Indicator inputs shall declare venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version when available. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-004` | Continuous futures or synthetic instruments shall declare roll method and adjustment method. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-005` | Indicator manifests shall include data provenance fields required to reproduce the calculation. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-006` | Official workflows shall reject inputs with unknown adjustment status unless explicitly configured to allow them. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-007` | Official workflows shall reject bars affected by intra-bar corporate-action adjustments unless a deterministic intra-bar adjustment policy is configured before calculation. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-008` | Deterministic intra-bar adjustment policies shall be recorded in the indicator manifest and shall not differ across batch, incremental, streaming, or cached execution. | **Modify** | Accept and propagate provenance supplied by the data contract; indicators must not derive or repair source provenance. | Reproducibility needs provenance, but normalization ownership remains with data. |
| `V2-IND-FR-1.12-009` | Symbol changes, mergers, ticker replacements, and vendor remaps shall use an explicit symbol mapping contract. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-010` | Symbol mapping shall preserve indicator state continuity across equivalent instrument identities without resetting warmup unless the mapping policy marks the instrument as discontinuous. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-011` | Bid, ask, and mid-price indicators shall define behavior for stub quotes, inverted markets, missing bid or ask values, and extreme spreads. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-012` | Official workflows shall reject stub quotes or spreads greater than the configured threshold, with a default rejection threshold of 50 percent of mid price, unless an explicit fallback policy is configured. | **Reject** | Move this validation and policy to the data domain; indicators consume data already accepted under that contract and propagate its metadata/quality flags. | These are source normalization and market-data quality responsibilities, not indicator formula responsibilities. |
| `V2-IND-FR-1.12-013` | Mid-price indicators shall deterministically reject missing or inverted bid/ask inputs unless configured to fall back to last valid mid, trade price, mark price, or unavailable output. | **Modify** | Propagate data-owned provenance without taking ownership of source policies. | The boundary must remain clear. |

### Source section: `1.13 Batch and Incremental Calculation`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.13-001` | Indicators shall define whether they support batch calculation, incremental calculation, streaming calculation, or a subset of these modes. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-002` | Incremental indicators shall expose serializable state. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-003` | Incremental state shall include enough information to resume calculation without recomputing the full history. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-004` | Incremental updates shall be idempotent for the same input bar. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-005` | Incremental and batch outputs shall match within the documented precision policy. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-006` | Late-arriving, corrected, or revised bars shall trigger deterministic recomputation or deterministic rejection. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-007` | The module shall define whether out-of-order incremental updates are supported. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |
| `V2-IND-FR-1.13-008` | Unsupported incremental mode requests shall fail deterministically. | **Defer** | Support batch mode only in the initial rebuild; report incremental/streaming requests as unsupported. | No confirmed workflow requires incremental state. |

### Source section: `1.13.1 Incremental State Protocol`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.13.1-001` | Serialized incremental state shall use a documented binary or text serialization format. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-002` | Serialized incremental state shall include indicator id. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-003` | Serialized incremental state shall include implementation version. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-004` | Serialized incremental state shall include incremental state schema version. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-005` | Serialized incremental state shall include parameter hash. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-006` | Serialized incremental state shall include input checksum of all data processed so far. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-007` | Serialized incremental state shall include internal accumulator values sufficient to resume without recomputation. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-008` | Serialized incremental state shall include last-processed timestamp and symbol. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-009` | Serialized incremental state shall include warmup completion flag. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-010` | Deserialization shall validate that provided state matches current indicator id, implementation version, schema version, and parameter set. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-011` | Deserialization of state from a different indicator version, schema version, or parameter set shall return `IND_STATE_INCOMPATIBLE`. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-012` | Corrupted or unreadable serialized state shall return `IND_STATE_CORRUPTED`. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |
| `V2-IND-FR-1.13.1-013` | Incremental state size shall be bounded and shall not grow proportionally to the total number of bars processed. | **Defer** | Defer the entire incremental state protocol until an approved streaming workflow exists. | The protocol is substantial and unsupported by V1 evidence. |

### Source section: `1.14 Custom Indicator Governance`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.14-001` | Custom indicators shall pass a conformance test suite before registration in official workflows. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-002` | Custom indicators shall declare status: official, experimental, deprecated, or research-only. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-003` | Experimental indicators shall not be used in official simulation workflows unless explicitly allowed. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-004` | Custom indicators shall not perform network I/O, broker calls, filesystem writes, account mutations, or nondeterministic random operations during calculation. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-005` | Custom indicators shall declare all external dependencies. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-006` | Custom indicator conformance shall verify prohibited side effects through a documented enforcement mechanism before registration in official workflows. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-007` | Official workflows shall reject custom indicators whose prohibited-operation checks cannot be executed, cannot be trusted, or return an inconclusive result. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-008` | Custom indicator enforcement shall document whether validation uses static analysis, sandbox execution, runtime guards, process isolation, conformance tests, policy review, or a combination of these mechanisms. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-009` | Custom indicators shall be reviewed before promotion to official status. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |
| `V2-IND-FR-1.14-010` | Promotion of custom indicators to official status shall require documentation, golden fixtures, conformance tests, no-lookahead tests, determinism tests, and benchmark coverage. | **Defer** | Defer custom-indicator registration and enforcement; official Core MVP contains only reviewed built-ins. | Side-effect enforcement and promotion workflows are not needed for the first safe slice. |

### Source section: `1.15 Input Validation Timing`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.15-001` | Indicator functions shall validate all inputs at call time before any calculation begins. | **Add** | Indicator functions shall validate all inputs at call time before any calculation begins. | V1 validation is partial and inconsistent; fail-fast validation is core. |
| `V2-IND-FR-1.15-002` | Parameter validation, schema validation, and data sufficiency checks shall be performed as the first operation and shall fail fast with deterministic error codes. | **Add** | Parameter validation, schema validation, and data sufficiency checks shall be performed as the first operation and shall fail fast with deterministic error codes. | V1 validation is partial and inconsistent; fail-fast validation is core. |
| `V2-IND-FR-1.15-003` | For batch calculations, full input validation shall complete before any output rows are computed. | **Add** | For batch calculations, full input validation shall complete before any output rows are computed. | V1 validation is partial and inconsistent; fail-fast validation is core. |
| `V2-IND-FR-1.15-004` | For incremental calculations, state deserialization validation and new-bar validation shall complete before incremental state is updated. | **Add** | For incremental calculations, state deserialization validation and new-bar validation shall complete before incremental state is updated. | V1 validation is partial and inconsistent; fail-fast validation is core. |

### Source section: `1.16 Indicator Composition`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.16-001` | The module shall support indicator composition where one indicator output serves as another indicator input. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-002` | When composition is enabled, the module shall accept only validated acyclic indicator graphs. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-003` | Composition shall reject cycles, missing upstream outputs, incompatible source timeframes, unavailable upstream values, and output column collisions with deterministic errors before calculation. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-004` | Composed indicator chains shall preserve `available_at` correctly. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-005` | No composed indicator shall consume a value before it is available. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-006` | Composed indicator chains shall preserve provenance metadata through the chain. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-007` | The cache layer shall support composition. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-008` | The indicator module shall own cache-key derivation and downstream invalidation triggers for composition when upstream inputs, upstream parameters, upstream formulas, or upstream implementation versions change. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |
| `V2-IND-FR-1.16-009` | External cache storage backends shall own eviction, physical invalidation, consistency, and synchronization mechanisms through documented adapter contracts. | **Defer** | Defer graph composition; callers may explicitly chain batch results while preserving availability metadata. | A composition engine and cache invalidation graph are not justified initially. |

### Source section: `1.17 Market Data Quality Handling`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.17-001` | Indicator inputs may include per-row data quality flags from the data module. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-002` | Supported quality flags shall include interpolated, backfilled, suspect, corrected, synthetic, auction, and vendor-specific flags when provided by the data module. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-003` | Indicator implementations shall document how each quality flag affects calculation. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-004` | Flagged rows shall be excluded from official calculations by default unless explicitly configured otherwise. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-005` | Configured inclusion of flagged rows shall be recorded in the indicator manifest. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-006` | Indicator output rows derived from flagged inputs shall propagate the highest-severity quality flag present in the source data for that calculation window. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |
| `V2-IND-FR-1.17-007` | Strategy-facing outputs shall expose quality metadata so strategies can require a minimum data quality level for consumption. | **Modify** | Accept data-owned quality flags, apply an explicit include/exclude policy, and propagate window severity; do not define vendor-specific quality taxonomies here. | Quality propagation is valuable, while source flag definition belongs to data. |

### Source section: `1.18 Audit Trail`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.18-001` | Official simulation and production workflows may require indicator calculation audit entries. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |
| `V2-IND-FR-1.18-002` | When audit mode is enabled, the indicator module shall produce an immutable audit log entry. | **Reject** | The indicator domain emits a deterministic manifest; immutable storage and integrity mechanisms belong to shared audit/security infrastructure. | No indicator-specific audit store is justified and ownership is external. |
| `V2-IND-FR-1.18-003` | When `audit_mode=true` or the workflow policy requires audit, the module shall emit an immutable audit entry containing the full indicator manifest, request metadata, input checksum, output checksum, and tamper-evident integrity metadata. | **Reject** | The indicator domain emits a deterministic manifest; immutable storage and integrity mechanisms belong to shared audit/security infrastructure. | No indicator-specific audit store is justified and ownership is external. |
| `V2-IND-FR-1.18-004` | The module shall emit audit payloads through a documented audit sink interface rather than owning external audit storage unless a later approved architecture decision assigns that responsibility. | **Reject** | The indicator domain emits a deterministic manifest; immutable storage and integrity mechanisms belong to shared audit/security infrastructure. | No indicator-specific audit store is justified and ownership is external. |
| `V2-IND-FR-1.18-005` | Audit entries shall include the full indicator manifest. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |
| `V2-IND-FR-1.18-006` | Audit entries shall include request metadata containing actor, workflow, correlation id, request id, and timestamp when available. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |
| `V2-IND-FR-1.18-007` | Audit entries shall include input data checksum. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |
| `V2-IND-FR-1.18-008` | Audit entries shall include output data checksum. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |
| `V2-IND-FR-1.18-009` | Audit entries shall be append-only and tamper-evident through the approved Audit Policy appendix, which must define either chained SHA-256 HMAC with managed signing-key handling or a tamper-evident Merkle-tree policy before production use. | **Reject** | The indicator domain emits a deterministic manifest; immutable storage and integrity mechanisms belong to shared audit/security infrastructure. | No indicator-specific audit store is justified and ownership is external. |
| `V2-IND-FR-1.18-010` | Pending: Audit integrity mechanism selection, signing-key custody, rotation, and verification rules require owner/security approval before production audit mode is accepted. | **Reject** | The indicator domain emits a deterministic manifest; immutable storage and integrity mechanisms belong to shared audit/security infrastructure. | No indicator-specific audit store is justified and ownership is external. |
| `V2-IND-FR-1.18-011` | Audit mode shall not change indicator outputs except for additional audit metadata. | **Defer** | Defer optional audit emission until a shared audit contract and consuming workflow are approved. | Core reproducibility is satisfied by the result manifest. |

### Source section: `1.19 Warmup Data Request Protocol`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.19-001` | The indicator module shall define a protocol to request minimum required warmup data from the data module before calculation. | **Modify** | Expose `WarmupRequirement` metadata for the caller/data domain; do not fetch or request market data from indicator calculation code. | This preserves the no-I/O boundary. |
| `V2-IND-FR-1.19-002` | Warmup requests shall include requested symbol, timeframe, and lookback period. | **Modify** | Expose `WarmupRequirement` metadata for the caller/data domain; do not fetch or request market data from indicator calculation code. | This preserves the no-I/O boundary. |
| `V2-IND-FR-1.19-003` | Warmup requests shall include indicator id and parameter set to determine exact warmup length. | **Modify** | Expose `WarmupRequirement` metadata for the caller/data domain; do not fetch or request market data from indicator calculation code. | This preserves the no-I/O boundary. |
| `V2-IND-FR-1.19-004` | Warmup requests shall declare whether warmup data must be closed-bar only or may include the current incomplete bar. | **Modify** | Expose `WarmupRequirement` metadata for the caller/data domain; do not fetch or request market data from indicator calculation code. | This preserves the no-I/O boundary. |
| `V2-IND-FR-1.19-005` | The indicator module shall request warmup data through the data module contract and shall validate that returned warmup data conforms to the same schema and provenance requirements as the primary input before using it. | **Modify** | Expose `WarmupRequirement` metadata for the caller/data domain; do not fetch or request market data from indicator calculation code. | This preserves the no-I/O boundary. |
| `V2-IND-FR-1.19-006` | The indicator module shall not directly own market-data fetching, source readiness, vendor adapters, or normalization logic. | **Add** | The indicator module shall not directly own market-data fetching, source readiness, vendor adapters, or normalization logic. | Warmup semantics are needed for safe result interpretation. |
| `V2-IND-FR-1.19-007` | Indicators shall consume warmup data for calculation state but shall not emit output rows for the warmup period unless those rows are explicitly marked as warmup. | **Add** | Indicators shall consume warmup data for calculation state but shall not emit output rows for the warmup period unless those rows are explicitly marked as warmup. | Warmup semantics are needed for safe result interpretation. |

### Source section: `1.20 Multi-Timeframe Alignment Protocol`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.20-001` | When an indicator is configured with a higher-timeframe source, the module shall request higher-timeframe bars through the data module contract alongside the primary timeframe. | **Reject** | The orchestrator/data domain supplies normalized higher-timeframe data; indicators do not fetch it. | Direct requests conflict with the pure calculation boundary. |
| `V2-IND-FR-1.20-002` | Higher-timeframe bars shall be validated before calculation and shall not make the indicator module responsible for market-data fetching, provider readiness, or normalization. | **Add** | Higher-timeframe bars shall be validated before calculation and shall not make the indicator module responsible for market-data fetching, provider readiness, or normalization. | Availability-aware higher-timeframe alignment is required before official multi-timeframe use. |
| `V2-IND-FR-1.20-003` | Higher-timeframe indicator values may be forward-filled onto the primary timeframe only after the higher-timeframe source bar is fully closed plus configured data latency. | **Add** | Higher-timeframe indicator values may be forward-filled onto the primary timeframe only after the higher-timeframe source bar is fully closed plus configured data latency. | Availability-aware higher-timeframe alignment is required before official multi-timeframe use. |
| `V2-IND-FR-1.20-004` | The module shall set `available_at` for each primary-timeframe row to the higher-timeframe bar close time plus configured data latency. | **Add** | The module shall set `available_at` for each primary-timeframe row to the higher-timeframe bar close time plus configured data latency. | Availability-aware higher-timeframe alignment is required before official multi-timeframe use. |
| `V2-IND-FR-1.20-005` | Higher-timeframe bars shall be aligned using left-closed, right-closed boundaries matching the primary timeframe bar edges. | **Add** | Higher-timeframe bars shall be aligned using left-closed, right-closed boundaries matching the primary timeframe bar edges. | Availability-aware higher-timeframe alignment is required before official multi-timeframe use. |
| `V2-IND-FR-1.20-006` | The module shall support multiple higher-timeframe sources simultaneously with independent availability timestamps. | **Defer** | Defer multi-source multi-timeframe orchestration; support one pre-aligned higher-timeframe source after the core is stable. | The proposed breadth is not required initially. |
| `V2-IND-FR-1.20-007` | Weekend and holiday gaps in higher-timeframe data shall not cause forward-fill of stale values across session boundaries unless explicitly configured. | **Modify** | Use data-provided session boundaries and reject stale alignment; do not own holiday calendars. | Calendar ownership remains outside indicators. |

### Source section: `1.21 Proprietary Indicator Access Control`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FR-1.21-001` | Proprietary or licensed indicator implementations shall require an access-control decision before execution. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |
| `V2-IND-FR-1.21-002` | Access-control checks shall validate actor, workflow, entitlement, environment, indicator id, indicator version, and intended use before calculation begins. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |
| `V2-IND-FR-1.21-003` | Unauthorized proprietary indicator requests shall fail before input data is read, state is deserialized, cache entries are read, or calculation begins. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |
| `V2-IND-FR-1.21-004` | Proprietary indicator result manifests shall record non-sensitive access-control decision metadata, including decision id, entitlement policy version, and authorized workflow. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |
| `V2-IND-FR-1.21-005` | Proprietary indicator execution shall be supported only through approved protected packaging mechanisms. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |
| `V2-IND-FR-1.21-006` | The selected protection mechanism shall be outside the public API contract and shall not change deterministic outputs, error behavior, manifest content, cache keys, or test expectations. | **Defer** | Exclude proprietary indicator execution and entitlement controls from the initial rebuild. | No V1 or V2 core workflow demonstrates this need. |

### Source section: `3.1 Inputs`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-IO-IN-001` | Normalized OHLCV market data. | **Add** | Normalized OHLCV market data. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-002` | Optional normalized tick or lower-timeframe data when an indicator explicitly requires it. | **Add** | Optional normalized tick or lower-timeframe data when an indicator explicitly requires it. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-003` | Symbol metadata. | **Add** | Symbol metadata. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-004` | Timeframe metadata. | **Add** | Timeframe metadata. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-005` | Indicator id. | **Add** | Indicator id. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-006` | Indicator parameter set. | **Add** | Indicator parameter set. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-007` | Source column selection for indicators that operate on a specific price or value column. | **Add** | Source column selection for indicators that operate on a specific price or value column. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-008` | Output mode: values-only result, joined copy result, or explicitly configured internal optimization. | **Add** | Output mode: values-only result, joined copy result, or explicitly configured internal optimization. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-009` | Output naming policy. | **Add** | Output naming policy. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-010` | Output column conflict policy. | **Add** | Output column conflict policy. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-011` | Precision policy. | **Add** | Precision policy. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-012` | Optional cache policy. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-013` | Trading calendar or session policy when an indicator is session-aware. | **Reject** | Receive normalized/validated data and provenance from the data domain instead of importing source-policy configuration into indicators. | This configuration belongs to data normalization. |
| `V2-IND-IO-IN-014` | Timezone metadata with unambiguous timestamp handling. | **Add** | Timezone metadata with unambiguous timestamp handling. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-015` | Price adjustment status. | **Modify** | Accept this as read-only provenance metadata when supplied by the data contract. | Indicators propagate but do not own provenance policy. |
| `V2-IND-IO-IN-016` | Price source. | **Modify** | Accept this as read-only provenance metadata when supplied by the data contract. | Indicators propagate but do not own provenance policy. |
| `V2-IND-IO-IN-017` | Venue, exchange, data vendor, symbol normalization version, and corporate-action adjustment version where available. | **Modify** | Accept this as read-only provenance metadata when supplied by the data contract. | Indicators propagate but do not own provenance policy. |
| `V2-IND-IO-IN-018` | Optional intra-bar corporate-action adjustment policy. | **Reject** | Receive normalized/validated data and provenance from the data domain instead of importing source-policy configuration into indicators. | This configuration belongs to data normalization. |
| `V2-IND-IO-IN-019` | Optional symbol mapping contract for symbol changes, mergers, ticker replacements, and vendor remaps. | **Reject** | Receive normalized/validated data and provenance from the data domain instead of importing source-policy configuration into indicators. | This configuration belongs to data normalization. |
| `V2-IND-IO-IN-020` | Optional microstructure quality policy containing stub quote, inverted market, missing bid/ask, spread threshold, and mid-price fallback configuration. | **Reject** | Receive normalized/validated data and provenance from the data domain instead of importing source-policy configuration into indicators. | This configuration belongs to data normalization. |
| `V2-IND-IO-IN-021` | Data latency configuration for availability-time calculation. | **Add** | Data latency configuration for availability-time calculation. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-022` | Calculation mode: batch, incremental, streaming, or explicitly unsupported. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-023` | Optional incremental state for incremental calculations. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-024` | Optional indicator composition graph. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-025` | Optional out-of-core processing configuration containing memory budget, chunk size, storage backend, and spill directory. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-026` | Optional acceleration backend configuration containing backend id, feature flag, worker pool, worker count, and fallback policy. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-027` | Optional feature flag and canary routing configuration for indicator implementation rollout. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-028` | Optional proprietary indicator access context containing actor, workflow, entitlement, environment, and intended use. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-029` | Optional per-row data quality flags from the data module. | **Add** | Optional per-row data quality flags from the data module. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-030` | Optional audit mode. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-031` | Optional warmup data request configuration. | **Add** | Optional warmup data request configuration. | This input is required by the approved batch contract and absent from V1. |
| `V2-IND-IO-IN-032` | Resource limit configuration. | **Add** | Accept a small validated resource-limit policy for rows, symbols, columns and timeout; defer memory spill and backend controls. | Basic failure isolation is useful, but optional execution infrastructure is not. |
| `V2-IND-IO-IN-033` | Optional observability context containing request id and correlation id. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-034` | Optional tracing context containing trace id, parent span id, baggage, and sampling decision. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-035` | Optional SLO configuration containing latency target, cache-hit target, error-rate target, timeout-rate target, measurement window, and alert routing. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |
| `V2-IND-IO-IN-036` | Optional benchmark context containing hardware profile, Python version, dependency versions, cache mode, warmup iterations, and measurement methodology. | **Defer** | Exclude this optional input from the Core MVP contract. | The associated capability is deferred. |

### Source section: `3.2 Outputs`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-IO-OUT-001` | Indicator result data aligned to timestamp and symbol. | **Add** | Indicator result data aligned to timestamp and symbol. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-002` | Generated indicator column names. | **Add** | Generated indicator column names. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-003` | Indicator values dataframe containing timestamp, symbol, indicator columns, availability metadata, and quality metadata. | **Add** | Indicator values dataframe containing timestamp, symbol, indicator columns, availability metadata, and quality metadata. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-004` | Joined dataframe copy when join output mode is requested. | **Add** | Joined dataframe copy when join output mode is requested. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-005` | Original input dataframe preserved without default mutation. | **Add** | Original input dataframe preserved without default mutation. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-006` | `available_at` timestamp or deterministic availability metadata for every output row. | **Add** | `available_at` timestamp or deterministic availability metadata for every output row. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-007` | `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. | **Add** | `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and `source_timeframe` metadata where applicable. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-008` | Warmup and missing-data metadata. | **Add** | Warmup and missing-data metadata. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-009` | Indicator result manifest. | **Add** | Indicator result manifest. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-010` | Input checksum. | **Add** | Input checksum. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-011` | Parameter hash. | **Add** | Parameter hash. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-012` | Implementation version. | **Add** | Implementation version. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-013` | Formula version. | **Add** | Formula version. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-014` | Output schema version. | **Add** | Output schema version. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-015` | Dtype metadata. | **Add** | Dtype metadata. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-016` | Data provenance metadata required to reproduce the calculation. | **Add** | Data provenance metadata required to reproduce the calculation. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-017` | Serializable incremental state when incremental calculation is enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-018` | Out-of-core execution metadata when out-of-core processing is enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-019` | Acceleration backend metadata when an accelerated or fallback backend is used. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-020` | Feature flag, canary route, baseline implementation, selected implementation, and canary comparison metadata when rollout controls are enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-021` | Non-sensitive proprietary access-control decision metadata when proprietary indicator execution is requested. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-022` | Output checksum. | **Add** | Output checksum. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-023` | Propagated data quality metadata. | **Add** | Propagated data quality metadata. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-024` | Indicator composition lineage where applicable. | **Add** | Indicator composition lineage where applicable. | This output supports deterministic consumption and is missing from V1. |
| `V2-IND-IO-OUT-025` | Audit log entry when audit mode is enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-026` | Observability metrics when enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-027` | Trace ids and span ids when distributed tracing is enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-028` | SLO measurement fields when SLO tracking is enabled. | **Defer** | Do not include this optional output in Core MVP; add it only with the corresponding approved capability. | The related execution or platform feature is deferred. |
| `V2-IND-IO-OUT-029` | Structured error result with deterministic error code on failure. | **Add** | Structured error result with deterministic error code on failure. | This output supports deterministic consumption and is missing from V1. |

### Source section: `3.3 Manifest Structure`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-MAN-001` | Every indicator result shall include a machine-readable manifest as a standalone serializable object. | **Add** | Every indicator result shall include a machine-readable manifest as a standalone serializable object. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-002` | The manifest shall include `manifest_version`. | **Add** | The manifest shall include `manifest_version`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-003` | The manifest shall include `indicator_id`. | **Add** | The manifest shall include `indicator_id`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-004` | The manifest shall include `indicator_version`. | **Add** | The manifest shall include `indicator_version`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-005` | The manifest shall include `formula_version`. | **Add** | The manifest shall include `formula_version`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-006` | The manifest shall include `output_schema_version`. | **Add** | The manifest shall include `output_schema_version`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-007` | The manifest shall include `parameter_hash` derived from a canonical parameter representation. | **Add** | The manifest shall include `parameter_hash` derived from a canonical parameter representation. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-008` | The manifest shall include `input_checksum` derived from input data including timestamps, symbols, and OHLCV values in canonical order. | **Add** | The manifest shall include `input_checksum` derived from input data including timestamps, symbols, and OHLCV values in canonical order. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-009` | The manifest shall include `output_checksum`. | **Add** | The manifest shall include `output_checksum`. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-010` | The module shall define the exact canonical representation used for parameter hashing, including key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, and version material. | **Add** | The module shall define the exact canonical representation used for parameter hashing, including key ordering, defaults, omitted optional values, numeric formatting, null representation, string normalization, and version material. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-011` | The module shall define the exact input and output checksum policy, including included columns, dtype normalization, timestamp normalization, symbol ordering, row ordering, float handling, null representation, precision policy, and excluded metadata. | **Add** | The module shall define the exact input and output checksum policy, including included columns, dtype normalization, timestamp normalization, symbol ordering, row ordering, float handling, null representation, precision policy, and excluded metadata. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-012` | The manifest shall include `data_provenance` with adjustment status, price source, vendor, venue, symbol normalization version, corporate-action version, and continuous contract roll method when applicable. | **Modify** | Include data-provided provenance fields without making indicators validate provider-specific source policies. | The metadata is useful but owned upstream. |
| `V2-IND-MAN-013` | The manifest shall include `calculation_config` with precision policy, session calendar identifier, data latency config, calculation mode, resource limits, and cache policy. | **Modify** | Record only core precision, availability, calculation mode and approved limits; omit deferred cache/backend configuration. | The proposed field set exceeds Core MVP. |
| `V2-IND-MAN-014` | The manifest shall include `output_contract` with generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. | **Add** | The manifest shall include `output_contract` with generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-015` | The manifest shall include `execution_backend` with in-memory, out-of-core, accelerated, fallback, parallelism, worker count, and backend version fields where applicable. | **Defer** | Omit this optional manifest section until its capability is approved. | The corresponding optional feature is deferred. |
| `V2-IND-MAN-016` | The manifest shall include `rollout` with feature flag, canary route, selected implementation, baseline implementation, and tolerance status where applicable. | **Defer** | Omit this optional manifest section until its capability is approved. | The corresponding optional feature is deferred. |
| `V2-IND-MAN-017` | The manifest shall include `access_control` with non-sensitive decision metadata for proprietary indicator requests where applicable. | **Defer** | Omit this optional manifest section until its capability is approved. | The corresponding optional feature is deferred. |
| `V2-IND-MAN-018` | The manifest shall include `slo` with configured thresholds and observed latency, cache status, error classification, and timeout status where applicable. | **Defer** | Omit this optional manifest section until its capability is approved. | The corresponding optional feature is deferred. |
| `V2-IND-MAN-019` | The manifest shall include `timing` with calculation start, calculation end, and wall-clock duration. | **Modify** | Keep runtime diagnostics separate from the deterministic identity/checksum portion of the manifest and exclude host identifiers. | Volatile environment data conflicts with reproducible manifest equality and may leak unnecessary metadata. |
| `V2-IND-MAN-020` | The manifest shall include `output_shape` with row count, symbol count, column list, and dtypes. | **Add** | The manifest shall include `output_shape` with row count, symbol count, column list, and dtypes. | A deterministic serializable manifest is required for replay and auditability. |
| `V2-IND-MAN-021` | The manifest shall include `environment` with Python version, key dependency versions, operating system, and optional host identifier for debugging. | **Modify** | Keep runtime diagnostics separate from the deterministic identity/checksum portion of the manifest and exclude host identifiers. | Volatile environment data conflicts with reproducible manifest equality and may leak unnecessary metadata. |
| `V2-IND-MAN-022` | The manifest shall include composition lineage when the result depends on upstream indicator outputs. | **Defer** | Omit this optional manifest section until its capability is approved. | The corresponding optional feature is deferred. |
| `V2-IND-MAN-023` | The manifest shall include quality-flag policy and propagated quality summary when data quality flags are present. | **Add** | The manifest shall include quality-flag policy and propagated quality summary when data quality flags are present. | A deterministic serializable manifest is required for replay and auditability. |

### Source section: `Error Handling Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ERR-REQ-001` | Every invalid indicator request shall return a deterministic error code. | **Add** | Every invalid indicator request shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-002` | The module shall document whether deterministic errors are raised as exceptions, returned inside `IndicatorResult.errors`, or both, and shall document the default mode. | **Add** | The module shall document whether deterministic errors are raised as exceptions, returned inside `IndicatorResult.errors`, or both, and shall document the default mode. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-003` | Every invalid input schema shall return a deterministic error code. | **Add** | Every invalid input schema shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-004` | Every invalid parameter set shall return a deterministic error code. | **Add** | Every invalid parameter set shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-005` | Invalid output names, invalid output modes, invalid naming policies, and output column collisions shall return deterministic error codes. | **Add** | Invalid output names, invalid output modes, invalid naming policies, and output column collisions shall return deterministic error codes. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-006` | Unexpected input mutation during official calculation shall return a deterministic error code. | **Add** | Unexpected input mutation during official calculation shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-007` | Every insufficient-data condition shall return a deterministic error code or explicit unavailable output according to configuration. | **Add** | Every insufficient-data condition shall return a deterministic error code or explicit unavailable output according to configuration. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-008` | Lookahead-sensitive indicator access shall provide metadata required for `SIM_LOOKAHEAD_DETECTED`. | **Modify** | Emit indicator availability metadata and `IND_LOOKAHEAD_RISK`; simulation retains its own error code. | Cross-domain ownership must remain explicit. |
| `V2-IND-ERR-REQ-009` | Unsupported indicator ids shall return a deterministic error code. | **Add** | Unsupported indicator ids shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-010` | Unsupported timeframes shall return a deterministic error code. | **Add** | Unsupported timeframes shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-011` | Unsupported dtypes shall return a deterministic error code. | **Add** | Unsupported dtypes shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-012` | Ambiguous, nonexistent, or timezone-naive timestamps shall return deterministic error codes in official workflows. | **Add** | Ambiguous, nonexistent, or timezone-naive timestamps shall return deterministic error codes in official workflows. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-013` | Unknown adjustment status shall return a deterministic error code unless explicitly allowed. | **Reject** | Handle this condition in the data domain and propagate its quality/error result rather than duplicating policy here. | It is a market-data validation responsibility. |
| `V2-IND-ERR-REQ-014` | Intra-bar corporate-action adjustment inputs without a configured deterministic policy shall return a deterministic error code. | **Reject** | Handle this condition in the data domain and propagate its quality/error result rather than duplicating policy here. | It is a market-data validation responsibility. |
| `V2-IND-ERR-REQ-015` | Missing or incompatible symbol mapping for symbol changes, mergers, ticker replacements, or vendor remaps shall return a deterministic error code. | **Reject** | Handle this condition in the data domain and propagate its quality/error result rather than duplicating policy here. | It is a market-data validation responsibility. |
| `V2-IND-ERR-REQ-016` | Stub quotes, inverted markets, missing bid or ask values, and spread-threshold violations shall return deterministic error codes unless an explicit fallback policy is configured. | **Reject** | Handle this condition in the data domain and propagate its quality/error result rather than duplicating policy here. | It is a market-data validation responsibility. |
| `V2-IND-ERR-REQ-017` | Formula version mismatches shall return a deterministic error code. | **Add** | Formula version mismatches shall return a deterministic error code. | V1 raises inconsistent generic exceptions and lacks deterministic codes. |
| `V2-IND-ERR-REQ-018` | Resource-limit, timeout, cancellation, partial-result, cache-write, unsupported out-of-core, unavailable acceleration backend, and unsupported incremental mode conditions shall return deterministic error codes. | **Add** | Define deterministic failure for approved resource limits and timeout; do not return partial official results. | Basic failure isolation is part of production readiness. |
| `V2-IND-ERR-REQ-019` | Custom indicators rejected by conformance, status, dependency, or governance checks shall return deterministic error codes. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |
| `V2-IND-ERR-REQ-020` | Incompatible incremental state shall return a deterministic error code before state is updated. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |
| `V2-IND-ERR-REQ-021` | Corrupted incremental state shall return a deterministic error code before state is updated. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |
| `V2-IND-ERR-REQ-022` | Unauthorized proprietary indicator requests shall return deterministic access-control error codes. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |
| `V2-IND-ERR-REQ-023` | SLO violations detected during production monitoring shall emit deterministic metric events and shall return deterministic error codes when the request policy requires synchronous enforcement. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |
| `V2-IND-ERR-REQ-024` | Deprecated indicator, parameter, schema, or API use in the deprecation error phase shall return a deterministic error code unless an explicit opt-in flag is configured. | **Defer** | Add this error behaviour only when the associated optional capability is implemented. | The feature is deferred. |

### Source section: `Confirmed Error Codes`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ERR-CODE-001` | `IND_INVALID_CONFIG` | **Add** | Include `IND_INVALID_CONFIG` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-002` | `IND_INVALID_PARAMETER` | **Add** | Include `IND_INVALID_PARAMETER` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-003` | `IND_UNSUPPORTED_INDICATOR` | **Add** | Include `IND_UNSUPPORTED_INDICATOR` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-004` | `IND_UNSUPPORTED_TIMEFRAME` | **Add** | Include `IND_UNSUPPORTED_TIMEFRAME` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-005` | `IND_UNSUPPORTED_DTYPE` | **Add** | Include `IND_UNSUPPORTED_DTYPE` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-006` | `IND_INVALID_INPUT_SCHEMA` | **Add** | Include `IND_INVALID_INPUT_SCHEMA` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-007` | `IND_MISSING_REQUIRED_COLUMN` | **Add** | Include `IND_MISSING_REQUIRED_COLUMN` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-008` | `IND_INVALID_OUTPUT_COLUMN` | **Add** | Include `IND_INVALID_OUTPUT_COLUMN` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-009` | `IND_OUTPUT_COLUMN_CONFLICT` | **Add** | Include `IND_OUTPUT_COLUMN_CONFLICT` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-010` | `IND_INVALID_OUTPUT_MODE` | **Add** | Include `IND_INVALID_OUTPUT_MODE` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-011` | `IND_INPUT_MUTATION_DETECTED` | **Add** | Include `IND_INPUT_MUTATION_DETECTED` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-012` | `IND_DUPLICATE_TIMESTAMP` | **Add** | Include `IND_DUPLICATE_TIMESTAMP` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-013` | `IND_NON_MONOTONIC_TIME` | **Add** | Include `IND_NON_MONOTONIC_TIME` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-014` | `IND_AMBIGUOUS_TIMESTAMP` | **Add** | Include `IND_AMBIGUOUS_TIMESTAMP` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-015` | `IND_INVALID_TIMEZONE` | **Add** | Include `IND_INVALID_TIMEZONE` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-016` | `IND_INVALID_OHLC` | **Add** | Include `IND_INVALID_OHLC` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-017` | `IND_INSUFFICIENT_DATA` | **Add** | Include `IND_INSUFFICIENT_DATA` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-018` | `IND_LOOKAHEAD_RISK` | **Add** | Include `IND_LOOKAHEAD_RISK` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-019` | `IND_UNKNOWN_ADJUSTMENT_STATUS` | **Reject** | Do not define `IND_UNKNOWN_ADJUSTMENT_STATUS` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-020` | `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED` | **Reject** | Do not define `IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-021` | `IND_SYMBOL_MAPPING_REQUIRED` | **Reject** | Do not define `IND_SYMBOL_MAPPING_REQUIRED` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-022` | `IND_STUB_QUOTE_REJECTED` | **Reject** | Do not define `IND_STUB_QUOTE_REJECTED` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-023` | `IND_INVERTED_MARKET` | **Reject** | Do not define `IND_INVERTED_MARKET` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-024` | `IND_SPREAD_THRESHOLD_EXCEEDED` | **Reject** | Do not define `IND_SPREAD_THRESHOLD_EXCEEDED` in indicators; use the data-domain error/quality contract. | The condition is owned by market-data normalization. |
| `V2-IND-ERR-CODE-025` | `IND_FORMULA_VERSION_MISMATCH` | **Add** | Include `IND_FORMULA_VERSION_MISMATCH` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-026` | `IND_STATE_INCOMPATIBLE` | **Defer** | Reserve `IND_STATE_INCOMPATIBLE` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-027` | `IND_STATE_CORRUPTED` | **Defer** | Reserve `IND_STATE_CORRUPTED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-028` | `IND_DEPRECATED` | **Defer** | Reserve `IND_DEPRECATED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-029` | `IND_CACHE_INVALID` | **Defer** | Reserve `IND_CACHE_INVALID` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-030` | `IND_CACHE_WRITE_FAILED` | **Defer** | Reserve `IND_CACHE_WRITE_FAILED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-031` | `IND_UNSUPPORTED_OUT_OF_CORE` | **Defer** | Reserve `IND_UNSUPPORTED_OUT_OF_CORE` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-032` | `IND_ACCELERATION_BACKEND_UNAVAILABLE` | **Defer** | Reserve `IND_ACCELERATION_BACKEND_UNAVAILABLE` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-033` | `IND_RESOURCE_LIMIT_EXCEEDED` | **Add** | Include `IND_RESOURCE_LIMIT_EXCEEDED` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-034` | `IND_TIMEOUT` | **Add** | Include `IND_TIMEOUT` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-035` | `IND_CANCELLED` | **Add** | Include `IND_CANCELLED` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-036` | `IND_PARTIAL_RESULT` | **Add** | Include `IND_PARTIAL_RESULT` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |
| `V2-IND-ERR-CODE-037` | `IND_UNSUPPORTED_INCREMENTAL_MODE` | **Defer** | Reserve `IND_UNSUPPORTED_INCREMENTAL_MODE` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-038` | `IND_CUSTOM_INDICATOR_REJECTED` | **Defer** | Reserve `IND_CUSTOM_INDICATOR_REJECTED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-039` | `IND_ACCESS_DENIED` | **Defer** | Reserve `IND_ACCESS_DENIED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-040` | `IND_PROPRIETARY_UNAUTHORIZED` | **Defer** | Reserve `IND_PROPRIETARY_UNAUTHORIZED` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-041` | `IND_SLO_VIOLATION` | **Defer** | Reserve `IND_SLO_VIOLATION` only if the associated optional capability is later approved. | The capability is outside Core MVP. |
| `V2-IND-ERR-CODE-042` | `IND_INTERNAL_ERROR` | **Add** | Include `IND_INTERNAL_ERROR` in the Core MVP deterministic error catalogue. | The code maps to an approved core validation or failure mode. |

### Source section: `2.1 General Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.1-001` | Indicator code shall be typed, documented, deterministic, and testable. | **Add** | Indicator code shall be typed, documented, deterministic, and testable. | This is a proportionate quality or import-safety requirement. |
| `V2-IND-NFR-2.1-002` | Indicator APIs shall remain separate from strategy execution and simulation execution services. | **Add** | Indicator APIs shall remain separate from strategy execution and simulation execution services. | This is a proportionate quality or import-safety requirement. |
| `V2-IND-NFR-2.1-003` | Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is required. | **Add** | Indicator functions shall avoid production `print()` output and shall use structured logging only through approved utility logging contracts where logging is required. | This is a proportionate quality or import-safety requirement. |
| `V2-IND-NFR-2.1-004` | Indicator errors shall be safe, deterministic, and machine-readable. | **Add** | Indicator errors shall be safe, deterministic, and machine-readable. | This is a proportionate quality or import-safety requirement. |
| `V2-IND-NFR-2.1-005` | Indicator implementations shall be reusable by notebook, CLI, agentic, and simulation workflows without changing semantics. | **Add** | Indicator implementations shall be reusable by notebook, CLI, agentic, and simulation workflows without changing semantics. | This is a proportionate quality or import-safety requirement. |
| `V2-IND-NFR-2.1-006` | Importing `tools.indicators` shall not perform network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins. | **Add** | Importing `tools.indicators` shall not perform network I/O, filesystem writes, cache writes, plugin execution, long-running computation, environment mutation, or registration from untrusted plugins. | This is a proportionate quality or import-safety requirement. |

### Source section: `2.2 Packaging and Distribution`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.2-001` | The module shall be packageable through standard Python packaging metadata. | **Modify** | Follow the project packaging contract rather than introducing an independent package lifecycle. | The indicator domain is currently part of a larger repository. |
| `V2-IND-NFR-2.2-002` | Build-system and project metadata shall be declared in `pyproject.toml`. | **Modify** | Use the repository-level packaging and dependency metadata; do not create indicator-specific packaging unless the domain becomes independently distributed. | Packaging ownership is project-wide. |
| `V2-IND-NFR-2.2-003` | Runtime dependencies, optional acceleration dependencies, development dependencies, and test dependencies shall be separated. | **Modify** | Use the repository-level packaging and dependency metadata; do not create indicator-specific packaging unless the domain becomes independently distributed. | Packaging ownership is project-wide. |
| `V2-IND-NFR-2.2-004` | Distributed typed packages shall include `py.typed` when public inline type annotations are intended for downstream type checking. | **Add** | Include `py.typed` only if `tools.indicators` is distributed as a typed package. | Public typing is useful and low cost when packaging applies. |
| `V2-IND-NFR-2.2-005` | Public type information shall be maintained for downstream users when the package is published as typed. | **Add** | Include `py.typed` only if `tools.indicators` is distributed as a typed package. | Public typing is useful and low cost when packaging applies. |

### Source section: `2.3 Observability`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.3-001` | Indicator calculations shall emit structured operational metrics where enabled. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-002` | Metrics shall include calculation duration, input row count, output row count, symbol count, cache hit or miss, memory usage estimate, rejected row count, warmup row count, and error code counts. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-003` | Logs shall include indicator id, implementation version, parameter hash, input checksum, symbol count, timeframe, and request id when available. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-004` | Logs shall not include full market data payloads by default. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-005` | Indicator execution shall support correlation ids for strategy and simulation workflow tracing. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-006` | Indicator execution shall support distributed tracing across data fetch, indicator calculation, strategy consumption, and simulation integration boundaries when tracing is enabled. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-007` | Trace spans shall carry request id, correlation id, indicator id, implementation version, parameter hash, input checksum, cache status, backend id, and error code when available. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-008` | The module shall support OpenTelemetry-compatible trace propagation or an equivalent vendor-neutral tracing contract. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-009` | Indicator implementations shall support feature-flagged and canary-routed execution for controlled rollout of new implementations. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-010` | Canary execution shall allow a configured subset of actors, workflows, symbols, or requests to receive a new implementation while comparing outputs against the baseline implementation. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-011` | Canary comparison shall record output deltas, tolerance status, performance deltas, and rollback decisions without changing official outputs unless the canary route is explicitly selected. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |
| `V2-IND-NFR-2.3-012` | Observability shall be optional and shall not change calculation semantics. | **Keep** | Observability must remain optional and semantics-neutral if later added. | This preserves calculation purity. |
| `V2-IND-NFR-2.3-013` | Distributed tracing, feature-flagged execution, canary routing, SLO alert routing, and rollback metadata shall be classified as Optional Extension unless a later approved decision promotes them. | **Defer** | Defer metrics, tracing, feature flags, canary routing and SLO payloads until a platform workflow requires them. | No confirmed V1 workflow uses this infrastructure. |

### Source section: `2.4 Resource Limits and Failure Isolation`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.4-001` | Indicator requests shall support configurable maximum rows, maximum symbols, maximum columns, memory budget, and execution timeout. | **Add** | Indicator requests shall support configurable maximum rows, maximum symbols, maximum columns, memory budget, and execution timeout. | Basic request limits and deterministic failure isolation are production safeguards. |
| `V2-IND-NFR-2.4-002` | The module shall define default resource limits for maximum rows, symbols, columns, memory budget, chunk size, and timeout before production use. | **Open Decision** | Approve measured defaults for rows, symbols, columns and timeout; defer memory spill/chunk defaults. | The proposed values lack evidence and include deferred processing modes. |
| `V2-IND-NFR-2.4-003` | Proposed Core MVP default resource limits are `default_max_rows=10_000_000`, `default_max_symbols=1_000`, `default_max_columns=256`, `default_memory_budget_bytes=4_294_967_296`, `default_chunk_rows=1_000_000`, and `default_timeout_seconds=60`, pending owner/architect approval. | **Open Decision** | Approve measured defaults for rows, symbols, columns and timeout; defer memory spill/chunk defaults. | The proposed values lack evidence and include deferred processing modes. |
| `V2-IND-NFR-2.4-004` | Resource-limit defaults shall live in an approved configuration schema before Builder handoff and shall be overrideable only through validated configuration. | **Add** | Resource-limit defaults shall live in an approved configuration schema before Builder handoff and shall be overrideable only through validated configuration. | Basic request limits and deterministic failure isolation are production safeguards. |
| `V2-IND-NFR-2.4-005` | Requests exceeding configured resource limits shall fail with deterministic machine-readable errors. | **Add** | Requests exceeding configured resource limits shall fail with deterministic machine-readable errors. | Basic request limits and deterministic failure isolation are production safeguards. |
| `V2-IND-NFR-2.4-006` | Cache writes shall be atomic and shall not corrupt existing valid cache entries on failure. | **Defer** | Apply this requirement only when cache or out-of-core processing is implemented. | The underlying capability is deferred. |
| `V2-IND-NFR-2.4-007` | Partial outputs shall not be returned as successful official results unless explicitly marked partial. | **Add** | Partial outputs shall not be returned as successful official results unless explicitly marked partial. | Basic request limits and deterministic failure isolation are production safeguards. |
| `V2-IND-NFR-2.4-008` | The module shall define behavior under memory pressure, cancellation, timeout, and interrupted cache writes. | **Defer** | Apply this requirement only when cache or out-of-core processing is implemented. | The underlying capability is deferred. |
| `V2-IND-NFR-2.4-009` | Cancellation, timeout, and memory-pressure handling shall clean up partial cache writes, audit writes, and out-of-core spill artifacts according to a documented cleanup policy. | **Defer** | Apply this requirement only when cache or out-of-core processing is implemented. | The underlying capability is deferred. |
| `V2-IND-NFR-2.4-010` | Chunked, parallel, and out-of-core processing shall define backpressure behavior before implementation. | **Defer** | Apply this requirement only when cache or out-of-core processing is implemented. | The underlying capability is deferred. |

### Source section: `2.5 Dependency and Supply-Chain Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.5-001` | Runtime dependencies shall be explicitly declared and version-constrained. | **Modify** | Apply the repository-wide dependency and lockfile policy to indicator dependencies. | This is a project-level mechanism. |
| `V2-IND-NFR-2.5-002` | Optional acceleration dependencies shall be isolated behind extras or feature flags. | **Defer** | Apply only when the corresponding optional dependency is introduced. | The feature is deferred. |
| `V2-IND-NFR-2.5-003` | Missing optional acceleration, proprietary, tracing, or audit dependencies shall produce deterministic unsupported-backend or not-configured errors without changing default built-in indicator semantics. | **Defer** | Apply only when the corresponding optional dependency is introduced. | The feature is deferred. |
| `V2-IND-NFR-2.5-004` | Dependency upgrades shall run the full indicator correctness, determinism, no-lookahead, cache, and benchmark suite. | **Modify** | Run approved core correctness and determinism tests on dependency upgrades; omit deferred feature suites. | The principle is valid but the proposed suite is broader than Core MVP. |
| `V2-IND-NFR-2.5-005` | The project shall maintain a lockfile or equivalent reproducible dependency mechanism for official workflows. | **Modify** | Apply the repository-wide dependency and lockfile policy to indicator dependencies. | This is a project-level mechanism. |
| `V2-IND-NFR-2.5-006` | SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering responsibilities, not Python indicator module runtime responsibilities, unless explicitly assigned by a later approved architecture decision. | **Keep** | SBOM generation, cryptographic package signing, vulnerability checks, license gates, and release provenance attestations shall be CI/CD and release-engineering responsibilities, not Python indicator module runtime responsibilities, unless explicitly assigned by a later approved architecture decision. | This explicitly keeps release engineering outside runtime ownership. |
| `V2-IND-NFR-2.5-007` | The project shall generate or support generating a software bill of materials for production releases. | **Modify** | Run approved core correctness and determinism tests on dependency upgrades; omit deferred feature suites. | The principle is valid but the proposed suite is broader than Core MVP. |
| `V2-IND-NFR-2.5-008` | Distributed Python wheels, source distributions, and production packages shall be cryptographically signed by the approved CI/CD release pipeline using Sigstore, PEP 740-compatible attestations, or an equivalent approved signing mechanism. | **Reject** | Move this requirement to project CI/CD and release engineering, not the indicator domain reconciliation. | It affects the whole system and does not define indicator behaviour. |
| `V2-IND-NFR-2.5-009` | Release artifacts shall include provenance attestations that identify source revision, build workflow, build environment, package hash, and signing identity. | **Reject** | Move this requirement to project CI/CD and release engineering, not the indicator domain reconciliation. | It affects the whole system and does not define indicator behaviour. |
| `V2-IND-NFR-2.5-010` | Dependency licenses shall be compatible with the intended deployment and distribution model. | **Reject** | Move this requirement to project CI/CD and release engineering, not the indicator domain reconciliation. | It affects the whole system and does not define indicator behaviour. |
| `V2-IND-NFR-2.5-011` | Known vulnerable dependencies shall not be allowed in production releases unless explicitly waived. | **Reject** | Move this requirement to project CI/CD and release engineering, not the indicator domain reconciliation. | It affects the whole system and does not define indicator behaviour. |

### Source section: `2.6 Numeric Type and Floating-Point Policy`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.6-001` | Official indicator workflows shall declare supported numeric dtypes. | **Add** | Official indicator workflows shall declare supported numeric dtypes. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-002` | Indicator implementations shall define whether outputs use `float64`, nullable floats, decimals, fixed-point integers, or another representation. | **Add** | Indicator implementations shall define whether outputs use `float64`, nullable floats, decimals, fixed-point integers, or another representation. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-003` | Unless an indicator formula specification explicitly overrides this policy, NaN input values shall propagate to NaN outputs for affected rows or windows and shall be represented as unavailable values with quality metadata. | **Add** | Unless an indicator formula specification explicitly overrides this policy, NaN input values shall propagate to NaN outputs for affected rows or windows and shall be represented as unavailable values with quality metadata. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-004` | Unless an indicator formula specification explicitly overrides this policy, positive and negative infinity inputs shall be rejected with deterministic numeric errors in official workflows before calculation. | **Add** | Unless an indicator formula specification explicitly overrides this policy, positive and negative infinity inputs shall be rejected with deterministic numeric errors in official workflows before calculation. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-005` | Unless an indicator formula specification explicitly overrides this policy, division by zero shall produce NaN unavailable outputs with deterministic warning metadata rather than silently clipping or filling values. | **Add** | Unless an indicator formula specification explicitly overrides this policy, division by zero shall produce NaN unavailable outputs with deterministic warning metadata rather than silently clipping or filling values. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-006` | Negative zero shall be normalized to zero for hashing, checksums, output comparison, and display. | **Add** | Negative zero shall be normalized to zero for hashing, checksums, output comparison, and display. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-007` | Overflow and underflow shall return deterministic errors or unavailable outputs according to the indicator formula specification and shall be recorded in result errors or warning metadata. | **Add** | Overflow and underflow shall return deterministic errors or unavailable outputs according to the indicator formula specification and shall be recorded in result errors or warning metadata. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-008` | Floating-point warning and error handling shall be deterministic within official workflows. | **Add** | Floating-point warning and error handling shall be deterministic within official workflows. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-009` | Indicator comparisons in tests shall use documented absolute and relative tolerances. | **Add** | Indicator comparisons in tests shall use documented absolute and relative tolerances. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |
| `V2-IND-NFR-2.6-010` | Cached outputs shall preserve dtype metadata. | **Add** | Cached outputs shall preserve dtype metadata. | V1 uses implicit pandas/NumPy behaviour and requires an explicit deterministic numeric policy. |

### Source section: `2.7 Concurrency and Thread Safety`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.7-001` | Indicator implementations shall document thread-safety guarantees. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-002` | Stateless indicator functions shall be thread-safe by default. | **Add** | Stateless indicator functions shall be thread-safe by default. | The recommended final API is stateless and should be safe for concurrent independent calls. |
| `V2-IND-NFR-2.7-003` | Stateful incremental indicators shall be single-owner or lock-free according to their documented state model. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-004` | Single-owner incremental state objects shall not be safe for concurrent mutation. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-005` | Lock-free incremental state objects shall be safe for concurrent reads with immutable state snapshots. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-006` | The cache layer shall be thread-safe for concurrent reads and atomic writes. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-007` | Cache implementations shall support multiple concurrent readers. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-008` | Cache implementations shall support single-writer or multi-writer operation with documented synchronization. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |
| `V2-IND-NFR-2.7-009` | The module shall document whether parallel symbol execution is supported and how it interacts with the cache. | **Defer** | Defer incremental-state, cache-concurrency and parallel-worker guarantees with their optional capabilities. | Core MVP does not own mutable shared state. |

### Source section: `2.8 Service Level Objectives`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-NFR-2.8-001` | Production indicator workflows shall define service level objectives for calculation latency, cache hit ratio, non-transient error rate, and timeout rate. | **Defer** | Define SLOs only after measured production usage exists; keep benchmark telemetry outside core semantics. | No baseline or workload evidence is available. |
| `V2-IND-NFR-2.8-002` | Default warm-cache calculation latency for official indicator workloads shall target p99 less than or equal to 250 milliseconds per indicator request for up to 10 symbols and 100,000 input rows. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |
| `V2-IND-NFR-2.8-003` | Default uncached first-run calculation latency for official indicator workloads shall target p99 less than or equal to 5 seconds for 10 years by 10 symbols of M1 bars on the documented benchmark hardware profile. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |
| `V2-IND-NFR-2.8-004` | Repeated research and simulation runs with stable inputs shall target cache hit ratio of at least 95 percent after cache warmup. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |
| `V2-IND-NFR-2.8-005` | Production non-transient indicator error rate shall target less than 0.1 percent over the configured measurement window, excluding deterministic user input validation failures. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |
| `V2-IND-NFR-2.8-006` | Production indicator timeout rate shall target less than 0.05 percent over the configured measurement window. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |
| `V2-IND-NFR-2.8-007` | SLO thresholds, measurement windows, included workflows, excluded error categories, and alert routing shall be configurable. | **Defer** | Define SLOs only after measured production usage exists; keep benchmark telemetry outside core semantics. | No baseline or workload evidence is available. |
| `V2-IND-NFR-2.8-008` | SLO measurements shall be emitted through observability metrics and summarized in production readiness reports. | **Open Decision** | Measure actual workloads and hardware before approving this numeric SLO. | The proposed threshold is unsupported by evidence. |

### Source section: `6.1 Edge Cases`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-EDGE-001` | Invalid indicator IDs, unsupported indicators, unsupported timeframes, unsupported dtypes, and unsupported incremental or out-of-core modes shall fail deterministically. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-002` | Missing columns, invalid input schema, invalid OHLC values, duplicate timestamps, non-monotonic timestamps, ambiguous timestamps, timezone-naive timestamps, and insufficient data shall fail or produce explicit unavailable outputs according to configuration. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-003` | Output column collisions, invalid output names, invalid output modes, invalid naming policies, unexpected input mutation, formula-version mismatches, cache-invalid states, and cache-write failures shall be handled with deterministic error codes. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-004` | Lookahead-sensitive access shall expose `available_at`, source `bar_close_time`, `lookahead_prohibited`, and related timing metadata for downstream layers to detect and reject prohibited usage. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-005` | Unknown price adjustment status, unsupported intra-bar corporate-action adjustment, missing symbol mapping, stub quotes, inverted markets, missing bid/ask inputs, and spread-threshold violations shall be rejected unless an explicit deterministic fallback policy is configured. | **Reject** | Move this edge case to the data-domain contract and propagate its result into indicator quality metadata. | The source condition is owned upstream. |
| `V2-IND-EDGE-006` | NaN, infinity, negative zero, overflow, underflow, divide-by-zero, all-null windows, constant-price windows, zero-volume windows, flat markets, degenerate Williams %R windows, and floating-point warnings shall produce deterministic outputs or deterministic errors. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-007` | Corrupted or incompatible incremental state shall fail before state updates. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-008` | Resource-limit breaches, timeout, cancellation, partial results, memory pressure, interrupted cache writes, unavailable acceleration backends, unauthorized proprietary indicator access, SLO violations, and deprecated API usage shall be handled deterministically. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-009` | Late-arriving, corrected, revised, or out-of-order bars shall trigger deterministic recomputation or deterministic rejection. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-010` | Weekend gaps, holidays, half-days, daylight-saving transitions, missing session opens or closes, inactive symbols, delisted symbols, bankrupt symbols, merged symbols, and vendor remaps shall be handled through explicit calendar, provenance, quality, and symbol-mapping policies. | **Reject** | Move this edge case to the data-domain contract and propagate its result into indicator quality metadata. | The source condition is owned upstream. |
| `V2-IND-EDGE-011` | Malformed config payloads, invalid combinations of otherwise valid configuration values, conflicting output/caching/execution options, and unsupported capability combinations shall fail deterministically before calculation. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-012` | Corrupt manifests, checksum mismatches, stale cache entries, cache entries with incompatible dependency versions, and manifest/output checksum mismatches shall fail deterministically. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-013` | Cache hits created under a different compatible dependency patch version shall hit with warning metadata or miss based on the configured dependency-compatibility policy. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-014` | Cache adapter connection failures shall degrade to uncached calculation with warning metadata when `cache_policy="best_effort"` and shall fail before calculation with deterministic diagnostics when `cache_policy="strict"`. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-015` | Timezone database updates shall not change historical indicator outputs after inputs are normalized to UTC; timezone-database-dependent conversions shall remain confined to I/O boundaries and shall be versioned or policy-recorded when available. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |
| `V2-IND-EDGE-016` | Missing optional acceleration, tracing, audit, proprietary, or release-integration dependencies shall fail deterministically when the optional capability is requested. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-017` | Custom indicator import failure, dependency conflict, unsupported Python version, prohibited-operation enforcement failure, and inconclusive side-effect checks shall fail deterministically. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-018` | Composition cycles, missing upstream columns, unavailable upstream values, incompatible source timeframes, and invalid composition graphs shall fail deterministically. | **Defer** | Cover this edge case when the associated optional capability is implemented. | The capability is deferred. |
| `V2-IND-EDGE-019` | Empty dataframes, single-row inputs, all-warmup outputs, all-null source columns, and no-output conditions shall follow documented output or error policies. | **Merge** | Cover this case in the approved validation, numeric, availability or error capability rather than as a separate capability. | It is a verification case, not a standalone behaviour. |

### Source section: `6.2 Tests Required`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-TEST-001` | Every functional and non-functional requirement shall have a stable requirement id before implementation begins. | **Modify** | Trace every approved, non-deferred requirement to tests; rejected and deferred requirements receive explicit disposition instead of executable tests. | Testing must follow the reconciled scope. |
| `V2-IND-TEST-002` | The test plan shall include a requirement-to-test traceability matrix mapping each requirement id to one or more unit, contract, integration, performance, security, or documentation tests. | **Add** | The test plan shall include a requirement-to-test traceability matrix mapping each requirement id to one or more unit, contract, integration, performance, security, or documentation tests. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-003` | Indicator tests shall cover EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. | **Add** | Indicator tests shall cover EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-004` | Import-time tests shall verify importing `tools.indicators` performs no network I/O, filesystem writes, cache writes, plugin execution, long-running computation, or environment mutation. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-005` | Input validation tests shall cover missing columns, duplicate timestamps, non-monotonic timestamps, invalid OHLC, empty data, insufficient warmup, and invalid parameters. | **Add** | Input validation tests shall cover missing columns, duplicate timestamps, non-monotonic timestamps, invalid OHLC, empty data, insufficient warmup, and invalid parameters. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-006` | Input validation tests shall cover malformed config payloads and invalid configuration combinations, including valid parameters that are incompatible when combined. | **Add** | Input validation tests shall cover malformed config payloads and invalid configuration combinations, including valid parameters that are incompatible when combined. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-007` | Input validation tests shall verify simultaneous conflicting options, such as `values_only=True` with `output_mode="join"`, fail with `IND_INVALID_CONFIG`. | **Add** | Input validation tests shall verify simultaneous conflicting options, such as `values_only=True` with `output_mode="join"`, fail with `IND_INVALID_CONFIG`. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-008` | Default-parameter tests shall verify default parameter values and valid parameter ranges for every built-in indicator. | **Add** | Default-parameter tests shall verify default parameter values and valid parameter ranges for every built-in indicator. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-009` | Input validation timing tests shall verify parameter validation, schema validation, data sufficiency checks, state deserialization validation, and new-bar validation fail before calculation or state mutation. | **Add** | Input validation timing tests shall verify parameter validation, schema validation, data sufficiency checks, state deserialization validation, and new-bar validation fail before calculation or state mutation. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-010` | Public API contract tests shall verify every public callable against the documented API contract table. | **Add** | Public API contract tests shall verify every public callable against the documented API contract table. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-011` | Capability-matrix tests shall verify every built-in indicator against its machine-readable capability matrix. | **Add** | Capability-matrix tests shall verify every built-in indicator against its machine-readable capability matrix. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-012` | Error-mode tests shall verify deterministic exception mode and deterministic `IndicatorResult.errors` mode if both are supported. | **Add** | Error-mode tests shall verify deterministic exception mode and deterministic `IndicatorResult.errors` mode if both are supported. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-013` | Error-mode tests shall verify that result-error mode does not raise exceptions and instead populates `IndicatorResult.errors` with deterministic codes. | **Add** | Error-mode tests shall verify that result-error mode does not raise exceptions and instead populates `IndicatorResult.errors` with deterministic codes. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-014` | Indicator anatomy tests shall verify `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` contracts. | **Add** | Indicator anatomy tests shall verify `IndicatorProtocol`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, `IndicatorManifest`, `IndicatorState`, `WarmupRequirement`, `IndicatorRegistration`, and `IndicatorError` contracts. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-015` | Indicator anatomy tests shall verify required methods for `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, and `deserialize_state` where applicable. | **Add** | Indicator anatomy tests shall verify required methods for `validate_parameters`, `required_columns`, `output_columns`, `warmup_requirement`, `validate_input`, `calculate`, `calculate_vectorized`, `update`, `serialize_state`, and `deserialize_state` where applicable. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-016` | Registry API tests shall verify `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, and allowed `unregister_indicator` behavior. | **Add** | Registry API tests shall verify `register_indicator`, `get_indicator`, `list_indicators`, `validate_indicator`, and allowed `unregister_indicator` behavior. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-017` | Built-in convenience function tests shall verify `ema`, `sma`, `adx`, `atr`, `adr`, `rolling_volatility`, `rsi`, and `williams_r` return `IndicatorResult` and follow the same validation, naming, manifest, cache, availability, and no-lookahead rules as registry execution. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-018` | Debug-mode validation tests shall verify type mismatches fail before calculation, state mutation, cache reads, cache writes, or output generation. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-019` | Public API tests shall verify `typing.Protocol` compatibility for custom indicators that do not inherit from framework base classes. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-020` | Notebook representation tests shall verify indicator result `_repr_html_` and `_repr_pretty_` output includes summary statistics, warmup visualization, unavailable-region visibility, and manifest summary without exposing full market data payloads. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-021` | Vectorized output tests shall verify batch indicators use vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. | **Add** | Vectorized output tests shall verify batch indicators use vectorized dataframe, array, or columnar operations where the formula permits vectorized calculation. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-022` | Vectorized output tests shall verify `ema(data, period=10, source="close")` produces `ema_10` when `close` is the default source. | **Add** | Vectorized output tests shall verify `ema(data, period=10, source="close")` produces `ema_10` when `close` is the default source. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-023` | Vectorized output tests shall verify non-default source naming such as `ema_open_10` and deterministic multi-output names such as `adx_14`, `plus_di_14`, and `minus_di_14`. | **Add** | Vectorized output tests shall verify non-default source naming such as `ema_open_10` and deterministic multi-output names such as `adx_14`, `plus_di_14`, and `minus_di_14`. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-024` | Output contract tests shall verify custom output names, invalid output names, output naming policies, output modes, column conflict policies, and deterministic collision errors. | **Add** | Output contract tests shall verify custom output names, invalid output names, output naming policies, output modes, column conflict policies, and deterministic collision errors. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-025` | Join helper tests shall verify `IndicatorResult.join_to(input_data, mode="copy")` appends generated indicator columns while preserving original columns, row count, row order, timestamp alignment, symbol grouping, index policy, warmup rows, and unavailable rows. | **Add** | Join helper tests shall verify `IndicatorResult.join_to(input_data, mode="copy")` appends generated indicator columns while preserving original columns, row count, row order, timestamp alignment, symbol grouping, index policy, warmup rows, and unavailable rows. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-026` | Input immutability tests shall verify indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official calculation detects unexpected mutation. | **Add** | Input immutability tests shall verify indicator calculations do not mutate the input dataframe by default and raise `IND_INPUT_MUTATION_DETECTED` when official calculation detects unexpected mutation. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-027` | No-lookahead tests shall cover previous-closed-bar availability, current-bar masking, multi-timeframe alignment, and vectorized signal shifting. | **Add** | No-lookahead tests shall cover previous-closed-bar availability, current-bar masking, multi-timeframe alignment, and vectorized signal shifting. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-028` | Availability tests shall verify strategy-facing APIs filter by `available_at <= decision_time`. | **Add** | Availability tests shall verify strategy-facing APIs filter by `available_at <= decision_time`. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-029` | Availability tests shall verify higher-timeframe values are unavailable until the higher-timeframe source bar is fully closed plus configured latency. | **Add** | Availability tests shall verify higher-timeframe values are unavailable until the higher-timeframe source bar is fully closed plus configured latency. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-030` | UTC normalization tests shall verify internal timestamp arithmetic and cache keys are UTC-normalized while local and exchange time conversions occur only at I/O boundaries. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-031` | Timezone database tests shall verify historical outputs remain stable after UTC-normalized inputs are supplied and that timezone-database-dependent conversions occur only at I/O boundaries. | **Add** | Timezone database tests shall verify historical outputs remain stable after UTC-normalized inputs are supplied and that timezone-database-dependent conversions occur only at I/O boundaries. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-032` | Determinism tests shall verify identical inputs and parameters produce identical outputs and manifests. | **Add** | Determinism tests shall verify identical inputs and parameters produce identical outputs and manifests. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-033` | Chunking tests shall verify chunked output matches full-run output within documented precision policy. | **Add** | Chunking tests shall verify chunked output matches full-run output within documented precision policy. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-034` | Out-of-core tests shall verify datasets exceeding memory budget produce the same output as full in-memory runs within documented precision policy. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-035` | Out-of-core tests shall verify deterministic rejection for indicators that require full in-memory context and cannot be safely chunked. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-036` | Acceleration backend tests shall verify feature-flag isolation, fallback behavior, backend metadata, and parity between accelerated and fallback paths within documented precision policy. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-037` | Batch and incremental tests shall verify incremental output matches batch output within the documented precision policy. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-038` | Incremental tests shall verify state serialization, resume behavior, idempotent repeated input bars, late-arriving bars, corrected bars, revised bars, and out-of-order updates. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-039` | Incremental state tests shall verify state format, indicator id, implementation version, schema version, parameter hash, processed input checksum, accumulator values, last-processed timestamp, last-processed symbol, warmup completion flag, bounded state size, `IND_STATE_INCOMPATIBLE`, and `IND_STATE_CORRUPTED`. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-040` | Cache tests shall cover cache hits, cache misses, schema-version changes, implementation-version changes, parameter changes, and input checksum changes. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-041` | Cache tests shall verify atomic cache writes and failure behavior for interrupted cache writes. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-042` | Cache degradation tests shall verify cache adapter connection failures fall back to uncached calculation with warning metadata under `cache_policy="best_effort"` and fail before calculation under `cache_policy="strict"`. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-043` | Cache tests shall verify corrupt manifest rejection, stale cache rejection when dependency versions or schema versions change, output checksum mismatch detection, and canonical parameter hash stability across equivalent parameter ordering. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-044` | Composition tests shall verify `available_at` preservation, provenance propagation, downstream cache invalidation, and rejection of unavailable upstream values. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-045` | Composition tests shall verify cyclic graphs, missing upstream columns, incompatible source timeframes, unavailable upstream values, and output column collisions fail deterministically. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-046` | Market data quality tests shall verify default exclusion of flagged rows, explicit inclusion configuration, quality-flag propagation, highest-severity quality summarization, and strategy-facing quality metadata. | **Add** | Market data quality tests shall verify default exclusion of flagged rows, explicit inclusion configuration, quality-flag propagation, highest-severity quality summarization, and strategy-facing quality metadata. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-047` | Performance benchmark tests shall verify benchmark metadata, cached and uncached modes, warmup iterations, min/median/p99 measurement, per-indicator tracking, and CI failure on unapproved regressions above 20 percent. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-048` | Performance benchmark tests shall prove the CI regression gate fails the build when the greater-than-20-percent regression threshold is triggered without explicit approval. | **Add** | Performance benchmark tests shall prove the CI regression gate fails the build when the greater-than-20-percent regression threshold is triggered without explicit approval. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-049` | Manifest tests shall verify every required manifest field, nested data provenance, calculation config, timing, output shape, environment, composition lineage, and quality summary. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-050` | Manifest tests shall verify output contract fields for generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. | **Add** | Manifest tests shall verify output contract fields for generated column names, source column, output mode, naming policy, column conflict policy, join mode, input mutation flag, and index alignment policy. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-051` | Manifest tests shall verify parameter hash canonicalization and input/output checksum policies are stable and documented. | **Add** | Manifest tests shall verify parameter hash canonicalization and input/output checksum policies are stable and documented. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-052` | Deprecation lifecycle tests shall verify deprecation warning phase, deprecation error with opt-in phase, removal phase, registry machine-readable phase, `IND_DEPRECATED`, and migration-guide coverage. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-053` | Formula golden tests shall verify exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. | **Add** | Formula golden tests shall verify exact formula conventions, seed behavior, warmup length, rolling-window inclusivity, null handling, and degenerate-window behavior for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-054` | Golden fixtures shall cover normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup. | **Add** | Golden fixtures shall cover normal data, flat markets, gaps, missing bars, duplicated timestamps, extreme volatility, zero volume, all-null windows, and insufficient warmup. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-055` | Reference outputs shall be reviewed and pinned by implementation version. | **Add** | Reference outputs shall be reviewed and pinned by implementation version. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-056` | Changes to golden outputs shall require explicit approval and changelog entry. | **Add** | Changes to golden outputs shall require explicit approval and changelog entry. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-057` | EMA, SMA, RSI, ATR, and ADX outputs shall be cross-validated against at least two industry-standard libraries, including TA-Lib and pandas-ta, tulipy, or equivalent libraries, on fixed golden fixtures. | **Modify** | Cross-validate against one approved independent reference plus pinned golden fixtures; add a second library only when conventions match and maintenance cost is justified. | Two mandatory third-party libraries add dependency and convention risk. |
| `V2-IND-TEST-058` | Cross-validation deviations beyond documented tolerance shall require formula justification, implementation-version pinning, golden fixture approval, and changelog entry. | **Add** | Cross-validation deviations beyond documented tolerance shall require formula justification, implementation-version pinning, golden fixture approval, and changelog entry. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-059` | The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ. | **Add** | The HaruQuant formula specification shall remain the source of truth when third-party library conventions differ. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-060` | Calendar and session tests shall cover weekends, exchange holidays, half-days, daylight-saving transitions, session gaps, missing opens, missing closes, pre-market, regular-session, post-market, and 24/7 market data. | **Add** | Calendar and session tests shall cover weekends, exchange holidays, half-days, daylight-saving transitions, session gaps, missing opens, missing closes, pre-market, regular-session, post-market, and 24/7 market data. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-061` | Provenance tests shall cover raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, synthetic, bid, ask, mid, mark, settlement, vendor-derived, continuous futures, and unknown adjustment status inputs. | **Add** | Provenance tests shall cover raw, split-adjusted, dividend-adjusted, total-return-adjusted, back-adjusted, synthetic, bid, ask, mid, mark, settlement, vendor-derived, continuous futures, and unknown adjustment status inputs. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-062` | Corporate-action tests shall cover intra-bar adjustment rejection, deterministic intra-bar adjustment policies, manifest recording, and parity across batch, incremental, streaming, and cached execution. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-063` | Symbol mapping tests shall cover symbol changes, mergers, ticker replacements, vendor remaps, state continuity, discontinuity markers, and warmup reset behavior. | **Modify** | Test propagation/rejection at the indicator boundary using data-contract fixtures; source normalization itself remains tested by the data domain. | The cross-domain contract matters, but ownership must not duplicate. |
| `V2-IND-TEST-064` | Microstructure tests shall cover stub quotes, inverted markets, missing bid or ask values, spreads above the configured threshold, and mid-price fallback policies. | **Modify** | Test propagation/rejection at the indicator boundary using data-contract fixtures; source normalization itself remains tested by the data domain. | The cross-domain contract matters, but ownership must not duplicate. |
| `V2-IND-TEST-065` | Survivorship bias tests shall verify indicators do not silently produce misleading signals for delisted, bankrupt, merged, or inactive symbols without data-quality flags and provenance metadata. | **Modify** | Test propagation/rejection at the indicator boundary using data-contract fixtures; source normalization itself remains tested by the data domain. | The cross-domain contract matters, but ownership must not duplicate. |
| `V2-IND-TEST-066` | Numeric tests shall cover dtype preservation, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, absolute tolerance, and relative tolerance. | **Add** | Numeric tests shall cover dtype preservation, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, absolute tolerance, and relative tolerance. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-067` | Numeric tests shall verify NaN propagation, infinity rejection in official workflows, division-by-zero unavailable outputs, negative-zero normalization, and overflow/underflow deterministic handling. | **Add** | Numeric tests shall verify NaN propagation, infinity rejection in official workflows, division-by-zero unavailable outputs, negative-zero normalization, and overflow/underflow deterministic handling. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-068` | Resource-limit tests shall cover maximum rows, symbols, columns, memory budget, execution timeout, cancellation, and partial-result handling. | **Add** | Resource-limit tests shall cover maximum rows, symbols, columns, memory budget, execution timeout, cancellation, and partial-result handling. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-069` | Observability tests shall verify metrics, logs, traces, canary comparison metadata, and SLO measurement fields include required fields and do not change calculation semantics. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-070` | Feature flag and canary tests shall verify routed execution, baseline comparison, output delta recording, tolerance status, rollback metadata, and unchanged official outputs when canary route is not selected. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-071` | SLO tests shall verify latency, cache-hit ratio, non-transient error rate, timeout rate, measurement windows, excluded error categories, alert routing metadata, and synchronous enforcement behavior when configured. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-072` | Concurrency tests shall verify stateless function thread safety, single-owner incremental-state behavior, immutable snapshot reads, parallel symbol execution, cache concurrent reads, and atomic synchronized cache writes. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-073` | Audit tests shall verify audit entries include full manifest, request metadata, input checksum, output checksum, append-only behavior, tamper-evident integrity, and unchanged calculation semantics. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-074` | Warmup protocol tests shall verify requested symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy, returned provenance, data-module contract integration through a fake data-module provider, and warmup output marking. | **Add** | Warmup protocol tests shall verify requested symbol, timeframe, lookback, indicator id, parameter set, closed-bar policy, returned provenance, data-module contract integration through a fake data-module provider, and warmup output marking. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-075` | Multi-timeframe alignment tests shall verify higher-timeframe data requests through a fake data-module contract, forward-fill only after availability, independent availability timestamps for multiple higher-timeframe sources, boundary alignment, and stale gap prevention across weekends and holidays. | **Add** | Multi-timeframe alignment tests shall verify higher-timeframe data requests through a fake data-module contract, forward-fill only after availability, independent availability timestamps for multiple higher-timeframe sources, boundary alignment, and stale gap prevention across weekends and holidays. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-076` | Custom indicator conformance tests shall verify status, dependency declarations, no network I/O, no broker calls, no filesystem writes, no account mutations, no nondeterministic random operations, and promotion requirements. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-077` | Custom indicator conformance tests shall verify rejection when prohibited-operation enforcement cannot run, cannot be trusted, or returns an inconclusive result. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-078` | Custom indicator tests shall verify import failure, dependency conflict, unsupported Python version, and side-effect enforcement failure handling. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-079` | Proprietary indicator tests shall verify access checks before execution, unauthorized request rejection before data or cache access, non-sensitive access-control manifest metadata, and deterministic parity for protected-source packages. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-080` | Proprietary indicator tests shall verify entitlement context and protected-package metadata do not leak secrets into logs, traces, manifests, or error messages. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-081` | Supply-chain tests shall verify dependency declarations, lockfile or equivalent reproducibility mechanism, license compatibility checks, vulnerability checks, SBOM generation support, cryptographic package signing, and release provenance attestations. | **Reject** | Move this verification to project release-engineering tests. | It is not an indicator-domain test. |
| `V2-IND-TEST-082` | Property-based tests shall cover valid and invalid OHLCV inputs. | **Add** | Property-based tests shall cover valid and invalid OHLCV inputs. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-083` | Property-based mutation fuzz tests shall inject NaN, infinity, extreme outliers, zero volume, flat prices, negative values, malformed timestamps, duplicate timestamps, and random missing intervals. | **Add** | Property-based mutation fuzz tests shall inject NaN, infinity, extreme outliers, zero volume, flat prices, negative values, malformed timestamps, duplicate timestamps, and random missing intervals. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-084` | Fuzz tests shall verify graceful unavailable outputs or deterministic rejection for invalid mutated inputs without crashes, nondeterminism, cache corruption, or state corruption. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |
| `V2-IND-TEST-085` | Property-based tests shall verify SMA over constant price input equals the constant price after warmup. | **Add** | Property-based tests shall verify SMA over constant price input equals the constant price after warmup. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-086` | Property-based tests shall verify EMA over constant price input converges deterministically according to its seed policy. | **Add** | Property-based tests shall verify EMA over constant price input converges deterministically according to its seed policy. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-087` | Property-based tests shall verify RSI remains within documented bounds for valid inputs. | **Add** | Property-based tests shall verify RSI remains within documented bounds for valid inputs. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-088` | Property-based tests shall verify Williams %R remains within documented bounds for valid non-degenerate windows. | **Add** | Property-based tests shall verify Williams %R remains within documented bounds for valid non-degenerate windows. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-089` | Property-based tests shall verify ATR is non-negative for valid OHLC inputs. | **Add** | Property-based tests shall verify ATR is non-negative for valid OHLC inputs. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-090` | Property-based tests shall verify rolling volatility is non-negative. | **Add** | Property-based tests shall verify rolling volatility is non-negative. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-091` | Property-based tests shall verify indicator output row count and symbol grouping match the documented output policy. | **Add** | Property-based tests shall verify indicator output row count and symbol grouping match the documented output policy. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-092` | Property-based tests shall verify adding future rows does not change previously available closed-bar outputs except when explicitly documented for revision-aware modes. | **Add** | Property-based tests shall verify adding future rows does not change previously available closed-bar outputs except when explicitly documented for revision-aware modes. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-093` | Strategy integration tests shall verify indicator outputs can feed trade-signal generation without exposing prohibited current-bar data. | **Add** | Strategy integration tests shall verify indicator outputs can feed trade-signal generation without exposing prohibited current-bar data. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-094` | Simulation integration tests shall verify indicator-derived signals are converted to trade intents before tick execution. | **Add** | Simulation integration tests shall verify indicator-derived signals are converted to trade intents before tick execution. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-095` | Simulation integration tests shall verify simulation-layer lookahead detection uses indicator-provided availability metadata without making the indicator module own simulation errors. | **Add** | Simulation integration tests shall verify simulation-layer lookahead detection uses indicator-provided availability metadata without making the indicator module own simulation errors. | This test validates an approved Core MVP or official-backtest behaviour. |
| `V2-IND-TEST-096` | Documentation tests shall execute usage examples, invalid-input examples, manifest-inspection examples, multi-symbol examples, multi-timeframe examples, and incremental examples where supported. | **Defer** | Add this test only with the corresponding optional capability. | The tested feature is deferred. |

### Source section: `6.3 Usage Examples`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-EX-001` | Usage examples shall include normal output, invalid parameter handling, missing-column handling, manifest inspection, availability filtering, multi-symbol input, multi-timeframe input, and incremental update behavior where supported. | **Modify** | Provide executable core examples now; add incremental and advanced multi-timeframe examples only when those capabilities are enabled. | Examples must match implemented scope. |
| `V2-IND-EX-002` | Usage examples shall show deterministic structured error behavior rather than relying only on successful calls. | **Add** | Usage examples shall show deterministic structured error behavior rather than relying only on successful calls. | Executable examples are needed because V1 documentation points to a disconnected usage script. |
| `V2-IND-EX-003` | Usage examples shall remain executable documentation examples once implementation begins. | **Add** | Usage examples shall remain executable documentation examples once implementation begins. | Executable examples are needed because V1 documentation points to a disconnected usage script. |

### Source section: `7.1 Target Folder Structure`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ARCH-001` | Adopt the proposed folders registry.py, protocols.py, errors.py, calculations.py, batch/, incremental/, and adapters/ under tools/indicators/. | **Modify** | Keep `tools/indicators/` with `core/`, `trend/`, `volatility/`, and `momentum/`; omit `incremental/`, `adapters/`, and the redundant `batch/` layer initially. | The proposed tree encodes optional architecture before any confirmed need. |

### Source section: `7.2 Class Diagrams`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ARCH-002` | Adopt IndicatorRegistry class managing IndicatorProtocol implementations with IndicatorConfig and IndicatorResult classes as shown. | **Modify** | Use stateless convenience functions plus immutable result/spec types and a simple static registry; do not require a stateful registry class. | V1 calculations are stateless and do not justify manager-style classes. |

### Source section: `8.2 Documentation Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-DOC-001` | Documentation shall include a configuration reference for every supported indicator. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-002` | Documentation shall include the Production Scope Tiers classification for every requirement before implementation begins. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-003` | Documentation shall include public API contract tables covering import paths, signatures, defaults, input schemas, output schemas, error behavior, side effects, cache behavior, stability level, and official-workflow eligibility. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-004` | Documentation shall include a requirement-to-test traceability matrix. | **Add** | Documentation shall include a requirement-to-test traceability matrix. | Traceability is required for the approved reconciled scope. |
| `V2-IND-DOC-005` | Documentation shall include input schema, output schema, parameter schema, warmup policy, and missing-data behavior for every supported indicator. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-006` | Documentation shall describe no-lookahead behavior for indicator-derived signals. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-007` | Documentation shall describe multi-timeframe indicator alignment. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-008` | Documentation shall describe cache keys and invalidation behavior. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-009` | Documentation shall include examples for EMA/SMA trend signals, ATR volatility sizing inputs, RSI momentum signals, vectorized dataframe output, joined indicator columns, and multi-timeframe alignment. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-010` | Documentation shall declare the public API surface, stable import paths, `typing.Protocol` contracts, registry contracts, schema versions, and deprecation policy. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-011` | Documentation shall describe indicator anatomy, required public types, required protocol attributes, required protocol methods, registry operations, built-in convenience functions, result objects, manifests, and state objects. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-012` | Documentation shall include API examples showing `ema(data, period=10, source="close")` returning an `IndicatorResult` with `ema_10` and `result.join_to(data)` returning a copied dataframe with `ema_10` appended. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-013` | Documentation shall describe vectorized calculation requirements, values-only output, joined-copy output, default input immutability, official in-place mutation restrictions, and internal optimization manifest requirements. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-014` | Documentation shall describe output column naming, default source naming, non-default source naming, multi-output naming, custom output names, output column conflict policy, and generated `output_columns`. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-015` | Documentation shall describe notebook result representations, including `_repr_html_`, `_repr_pretty_`, summary statistics, warmup visualization, unavailable-region visibility, and manifest summaries. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-016` | Documentation shall describe debug-mode strict typing and runtime validation behavior. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-017` | Documentation shall describe semantic versioning policy and migration requirements for backward-incompatible changes. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-018` | Documentation shall include exact mathematical formula, smoothing convention, alpha convention, seed behavior, rolling-window inclusivity, and edge-case behavior for every supported indicator. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-019` | Documentation shall describe RSI, ATR, and ADX smoothing conventions. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-020` | Documentation shall describe rolling volatility return type, log/simple return policy, standard-deviation convention, degrees of freedom, and annualization factor. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-021` | Documentation shall describe ADR range convention and Williams %R degenerate-window behavior. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-022` | Documentation shall describe golden fixtures and reference output approval workflow. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-023` | Documentation shall describe the `available_at` contract, `label_time`, `bar_open_time`, `bar_close_time`, `computed_from_start`, `computed_from_end`, and strategy-facing filtering. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-024` | Documentation shall describe calendar, session, weekend, holiday, half-day, daylight-saving, missing-session, pre-market, regular-session, post-market, and 24/7 market semantics. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-025` | Documentation shall describe UTC normalization for internal timestamp arithmetic and cache keys, and shall define local and exchange time handling at I/O boundaries. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-026` | Documentation shall describe market-data provenance, price adjustment status, price source, venue, vendor, symbol normalization version, corporate-action adjustment version, and continuous-instrument adjustment policy. | **Modify** | Document the indicator/data boundary and propagated provenance/quality contract; keep source-policy details in data documentation. | This avoids duplicated ownership. |
| `V2-IND-DOC-027` | Documentation shall describe intra-bar corporate-action adjustment rejection, deterministic intra-bar adjustment policies, symbol mapping continuity, mergers, ticker replacements, vendor remaps, stub quote handling, inverted market handling, spread thresholds, and mid-price fallback behavior. | **Modify** | Document the indicator/data boundary and propagated provenance/quality contract; keep source-policy details in data documentation. | This avoids duplicated ownership. |
| `V2-IND-DOC-028` | Documentation shall describe batch, incremental, and streaming calculation modes. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-029` | Documentation shall describe out-of-core processing, memory budgets, chunk sizes, spill storage, unsupported out-of-core rejection, and in-memory parity requirements. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-030` | Documentation shall describe optional acceleration backends, feature flags, pure fallback behavior, backend metadata, GIL-release behavior, and parallel symbol execution configuration. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-031` | Documentation shall describe incremental state serialization, idempotency, late-arriving data, corrected data, revised data, and out-of-order update behavior. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-032` | Documentation shall describe incremental state format, state compatibility validation, state corruption handling, and bounded state size. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-033` | Documentation shall describe input validation timing and fail-fast behavior. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-034` | Documentation shall describe performance benchmark hardware profile, dependency versions, cached and uncached modes, warmup iterations, measurement methodology, and regression threshold. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-035` | Documentation shall describe indicator result manifest structure and every required manifest field. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-036` | Documentation shall describe indicator composition, `available_at` preservation, provenance propagation, and downstream cache invalidation. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-037` | Documentation shall describe data quality flags, default exclusion policy, explicit inclusion policy, output quality propagation, and strategy-facing quality metadata. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-038` | Documentation shall describe thread-safety guarantees, incremental state ownership, immutable state snapshots, cache concurrency, parallel symbol execution, worker pools, worker counts, chunk sizes, and cache synchronization. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-039` | Documentation shall describe the deprecation lifecycle, machine-readable registry phase, changelog entries, migration guide, and `IND_DEPRECATED`. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-040` | Documentation shall describe audit mode, audit entry structure, tamper-evident integrity, and audit metadata. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-041` | Documentation shall describe warmup data request protocol and warmup output marking. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-042` | Documentation shall describe detailed multi-timeframe alignment, boundary semantics, independent availability timestamps, and stale gap prevention. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-043` | Documentation shall describe observability metrics, log fields, request ids, correlation ids, distributed tracing, OpenTelemetry-compatible propagation, feature flags, canary routing, output delta comparison, and rollback metadata. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-044` | Documentation shall describe service level objectives, latency thresholds, cache-hit thresholds, error-rate thresholds, timeout-rate thresholds, measurement windows, excluded error categories, and alert routing. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-045` | Documentation shall describe resource limits, timeout behavior, cancellation behavior, memory-pressure behavior, interrupted cache-write behavior, and partial-result policy. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-046` | Documentation shall describe packaging metadata, `pyproject.toml`, dependency categories, `py.typed`, and typed package behavior. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-047` | Documentation shall describe dependency pinning, lockfile or equivalent reproducibility mechanism, SBOM generation, license checks, vulnerability checks, cryptographic package signing, release provenance attestations, and waiver process. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-048` | Documentation shall describe custom indicator conformance, status values, prohibited operations, dependency declarations, and promotion review. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |
| `V2-IND-DOC-049` | Documentation shall describe proprietary indicator access control, entitlement checks, authorized workflows, non-sensitive manifest metadata, source protection, and protected-package determinism. | **Defer** | Document this only when the associated optional capability is approved and implemented. | Core documentation should not promise deferred behaviour. |
| `V2-IND-DOC-050` | Documentation shall describe mandatory cross-validation against industry-standard libraries, third-party formula convention differences, golden fixture approval, mutation fuzz testing, and survivorship bias testing. | **Modify** | Document the indicator/data boundary and propagated provenance/quality contract; keep source-policy details in data documentation. | This avoids duplicated ownership. |
| `V2-IND-DOC-051` | Documentation shall describe numeric dtype policy, NaN, infinity, negative zero, overflow, underflow, divide-by-zero, and floating-point tolerance behavior. | **Merge** | Include this material in the final domain README and formula/API references for approved capabilities. | It is documentation of an approved behaviour rather than a separate runtime capability. |

### Source section: `8.4 Production Acceptance Checklist`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-ACC-001` | Public API surface is documented. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-002` | Production Scope Tiers are assigned and approved for every requirement. | **Add** | Production Scope Tiers are assigned and approved for every requirement. | The build must be gated against the reconciled scope. |
| `V2-IND-ACC-003` | Public API contract tables are complete for every public callable. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-004` | Requirement-to-test traceability matrix exists and maps every requirement id to tests or approved deferral. | **Add** | Requirement-to-test traceability matrix exists and maps every requirement id to tests or approved deferral. | The build must be gated against the reconciled scope. |
| `V2-IND-ACC-005` | Indicator anatomy, required interfaces, registry operations, built-in convenience functions, and result object methods are documented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-006` | `typing.Protocol` contracts and notebook result representations are implemented and tested. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-007` | Vectorized dataframe output, deterministic indicator column naming, values-only output, joined-copy output, and output column conflict behavior are implemented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-008` | `ema(data, period=10, source="close")` produces `ema_10`, and `IndicatorResult.join_to(data)` appends `ema_10` to a copied dataframe without mutating the input by default. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-009` | Debug-mode strict typing and runtime validation fail before calculation or state mutation. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-010` | `pyproject.toml` metadata is present and valid. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-011` | Typed distribution includes `py.typed` when public inline type annotations are exported. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-012` | Formula specifications exist for every official indicator. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-013` | Golden fixtures exist for every official indicator. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-014` | Availability-time metadata is implemented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-015` | UTC normalization for internal timestamp arithmetic and cache keys is implemented and tested. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-016` | Calendar and session behavior is documented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-017` | Market-data provenance, adjustment status, intra-bar corporate actions, symbol mapping, and microstructure rules are validated. | **Modify** | Acceptance verifies the indicator boundary and propagated metadata; data-domain acceptance verifies normalization policies. | This is cross-domain rather than indicator-internal. |
| `V2-IND-ACC-018` | Cross-library validation passes for EMA, SMA, RSI, ATR, and ADX against at least two industry-standard libraries. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-019` | Batch and incremental parity tests pass for indicators that support incremental mode. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-020` | Incremental state compatibility and corruption tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-021` | Out-of-core parity and unsupported out-of-core rejection tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-022` | Acceleration backend parity, feature flag, fallback, and backend metadata tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-023` | Performance benchmark metadata and regression gate are implemented. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-024` | Machine-readable manifest structure is implemented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-025` | Manifest output-contract fields are implemented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-026` | Indicator composition tests pass where composition is supported. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-027` | Data-quality flag handling is implemented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-028` | Thread-safety and cache-concurrency tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-029` | Parallel symbol execution configuration and cache synchronization tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-030` | Deprecation lifecycle and `IND_DEPRECATED` behavior are implemented. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-031` | Audit mode entries are append-only, tamper-evident, and tested when audit mode is enabled. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-032` | Warmup data request protocol is documented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-033` | Multi-timeframe alignment protocol is documented and tested. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-034` | Custom indicator conformance suite passes for every registered custom indicator. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-035` | Proprietary indicator access control and protected-source determinism tests pass for every proprietary indicator. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-036` | Property-based and invariant tests pass. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-037` | Mutation fuzz and survivorship bias tests pass. | **Modify** | Acceptance verifies the indicator boundary and propagated metadata; data-domain acceptance verifies normalization policies. | This is cross-domain rather than indicator-internal. |
| `V2-IND-ACC-038` | Resource-limit, timeout, cancellation, and cache-write failure tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-039` | Distributed tracing, feature flag, canary routing, and SLO measurement tests pass. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-040` | Dependency lockfile or equivalent reproducibility mechanism is present for official workflows. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-041` | Dependency license and vulnerability checks pass or have explicit waivers. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-042` | Cryptographic package signing and release provenance attestation are present for production packages. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |
| `V2-IND-ACC-043` | Software bill of materials generation is supported for production releases. | **Merge** | Use this as an acceptance check for the corresponding approved capability/test rather than a new requirement. | It duplicates an approved runtime or testing requirement. |
| `V2-IND-ACC-044` | Indicator documentation is complete for formulas, APIs, schemas, dtypes, cache behavior, observability, and release controls. | **Defer** | Exclude this gate from initial acceptance and activate it with the corresponding optional capability. | The feature is deferred. |

### Source section: `Implementation Pre-requisites`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `IND-PREQ-001` | Built-in formula tables — Approve exact formulas, defaults, seed behavior, warmup behavior, reference implementations, and tolerances for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R. | **Keep** | Resolve formula tables before implementing the Core MVP built-ins. | V1 formulas are ambiguous and include correctness concerns. |
| `IND-PREQ-002` | Public type contracts — Approve exact Python type contracts for `data`, `IndicatorConfig`, `IndicatorContext`, `IndicatorResult`, manifests, errors, and state serialization. | **Modify** | Approve exact batch contracts for data, config, result, manifest and errors; exclude context/state serialization from Core MVP. | The proposed contract includes deferred types. |
| `IND-PREQ-003` | Error mode — Approve the default exception/result-error behavior and all supported error-mode names. | **Keep** | Approve one default error mode and any optional result-error mode before implementation. | V1 error handling is inconsistent. |
| `IND-PREQ-004` | Cache/checksum policy — Approve cache degradation behavior, strict-cache behavior, parameter hash canonicalization, dependency compatibility, input checksum, and output checksum policies. | **Modify** | Approve canonical parameter/input/output hashing now; defer cache degradation and dependency-compatibility policy. | Checksums are core; caching is not. |
| `IND-PREQ-005` | Resource limits — Approve or revise proposed default limits for rows, symbols, columns, memory budget, chunk size, and timeout. | **Open Decision** | Approve measured row/symbol/column/timeout limits; defer memory spill and chunk defaults. | No evidence supports the proposed numeric defaults. |
| `IND-PREQ-006` | Requirement traceability — Assign stable requirement IDs and complete the requirement-to-test traceability matrix. | **Keep** | Assign stable IDs to the reconciled requirements and map approved items to tests. | The source V2 checklist lacks stable IDs. |
| `IND-PREQ-007` | Audit integrity — Approve audit integrity mechanism, signing-key custody, rotation, and verification rules before production audit mode. | **Defer** | Do not block Core MVP on audit integrity; resolve only before optional production audit mode. | Audit emission is deferred. |
| `V2-IND-PREQ-001` | Core MVP coding shall halt until `IND-PREQ-001`, `IND-PREQ-002`, `IND-PREQ-003`, `IND-PREQ-004`, `IND-PREQ-005`, and `IND-PREQ-006` are resolved or explicitly deferred. | **Modify** | Block coding only on formula tables, minimal batch type contracts, error mode, canonical hashing, approved basic limits and traceability. | Cache and deferred architecture must not block the safe batch slice. |
| `V2-IND-PREQ-002` | Production audit mode shall halt until `IND-PREQ-007` is resolved. | **Keep** | Production audit mode shall halt until `IND-PREQ-007` is resolved. | Audit mode must remain blocked until shared security ownership is resolved. |

### Source section: `Production Scope Tiers`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-TIER-001` | Core MVP shall include deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; input validation; output naming; no-lookahead availability metadata; manifests; deterministic errors; and golden tests. | **Keep** | Core MVP shall include deterministic batch calculation for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI, and Williams %R; input validation; output naming; no-lookahead availability metadata; manifests; deterministic errors; and golden tests. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |
| `V2-IND-TIER-002` | Official Backtest Required shall include no-lookahead alignment, reproducible fixtures, manifest/checksum behavior, data-quality propagation, and strategy/simulation integration contracts. | **Keep** | Official Backtest Required shall include no-lookahead alignment, reproducible fixtures, manifest/checksum behavior, data-quality propagation, and strategy/simulation integration contracts. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |
| `V2-IND-TIER-003` | Production Required shall include resource limits, redacted structured diagnostics, documented cache behavior if caching is enabled, public API compatibility rules, and acceptance gates for official workflows. | **Keep** | Production Required shall include resource limits, redacted structured diagnostics, documented cache behavior if caching is enabled, public API compatibility rules, and acceptance gates for official workflows. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |
| `V2-IND-TIER-004` | Optional Extension shall include streaming, out-of-core processing, acceleration backends, proprietary indicator execution, distributed tracing, SLO alert routing, and canary routing unless a later approved decision promotes any item. | **Keep** | Optional Extension shall include streaming, out-of-core processing, acceleration backends, proprietary indicator execution, distributed tracing, SLO alert routing, and canary routing unless a later approved decision promotes any item. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |
| `V2-IND-TIER-005` | Future Improvement shall include capabilities that are useful but not required for the current approved implementation phase. | **Keep** | Future Improvement shall include capabilities that are useful but not required for the current approved implementation phase. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |
| `V2-IND-TIER-006` | Core MVP shall be implementable without optional acceleration backends, proprietary indicator controls, out-of-core execution, distributed tracing, SLO enforcement, or release-signing infrastructure. | **Keep** | Core MVP shall be implementable without optional acceleration backends, proprietary indicator controls, out-of-core execution, distributed tracing, SLO enforcement, or release-signing infrastructure. | Tiering is the correct mechanism for controlling the oversized V2 proposal. |

### Source section: `Public API Contract Requirements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-API-CONTRACT-001` | Every public callable shall define its stable import path, function signature, required parameters, optional parameters and defaults, accepted input schema, returned object type, deterministic error behavior, side effects, cache behavior, stability level, and official-workflow eligibility. | **Add** | Every public callable shall define its stable import path, function signature, required parameters, optional parameters and defaults, accepted input schema, returned object type, deterministic error behavior, side effects, cache behavior, stability level, and official-workflow eligibility. | A stable API contract is necessary to replace V1's duplicated export surfaces. |
| `V2-IND-API-CONTRACT-002` | Every public callable shall be classified as stable, experimental, internal, optional, or future before implementation begins. | **Add** | Every public callable shall be classified as stable, experimental, internal, optional, or future before implementation begins. | A stable API contract is necessary to replace V1's duplicated export surfaces. |
| `V2-IND-API-CONTRACT-003` | The public API contract table shall cover registry operations, built-in convenience functions, result object methods, protocol methods, state serialization functions, and manifest serialization functions. | **Modify** | Document and classify only implemented Core MVP callables; list deferred modes as unsupported without exposing unused APIs. | The contract must reflect actual scope. |
| `V2-IND-API-CONTRACT-004` | Public contracts shall define whether invalid requests raise exceptions, return `IndicatorResult(errors=...)`, or support both modes, and shall document the default mode. | **Open Decision** | Choose a single default error mode before Builder handoff; optionally support result-error mode only when justified. | The V2 proposal leaves the default unresolved. |
| `V2-IND-API-CONTRACT-005` | Every official indicator shall publish a machine-readable capability matrix covering batch, vectorized, incremental, streaming, out-of-core, acceleration, composition, multi-symbol, and multi-timeframe support. | **Modify** | Document and classify only implemented Core MVP callables; list deferred modes as unsupported without exposing unused APIs. | The contract must reflect actual scope. |
| `V2-IND-API-CONTRACT-006` | The machine-readable capability matrix shall be generated from the registry and shall include indicator id, version, tier, supported modes, optional dependencies, unsupported-mode error codes, and official-workflow eligibility. | **Add** | The machine-readable capability matrix shall be generated from the registry and shall include indicator id, version, tier, supported modes, optional dependencies, unsupported-mode error codes, and official-workflow eligibility. | A stable API contract is necessary to replace V1's duplicated export surfaces. |
| `V2-IND-API-CONTRACT-007` | Unsupported modes, unsupported backends, unsupported indicators, unavailable optional dependencies, and unsupported composition requests shall fail before calculation with deterministic errors. | **Modify** | Document and classify only implemented Core MVP callables; list deferred modes as unsupported without exposing unused APIs. | The contract must reflect actual scope. |
| `V2-IND-API-CONTRACT-008` | Public usage examples shall be executable documentation examples once implementation begins. | **Add** | Public usage examples shall be executable documentation examples once implementation begins. | A stable API contract is necessary to replace V1's duplicated export surfaces. |

### Source section: `Type Definitions Appendix`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-TYPE-001` | `IndicatorProtocol.calculate(data, config, context)` shall use approved type hints before implementation begins. | **Add** | `IndicatorProtocol.calculate(data, config, context)` shall use approved type hints before implementation begins. | This defines the Core MVP typed DataFrame contract. |
| `V2-IND-TYPE-002` | `data` shall be a `pandas.DataFrame` for Core MVP batch execution unless a formula table explicitly approves an alternate typed input. | **Add** | `data` shall be a `pandas.DataFrame` for Core MVP batch execution unless a formula table explicitly approves an alternate typed input. | This defines the Core MVP typed DataFrame contract. |
| `V2-IND-TYPE-003` | Core MVP `data` shall contain UTC-normalized timestamp information as either a UTC `DatetimeIndex` for single-symbol input or a `MultiIndex` containing `symbol` and UTC `timestamp` levels for multi-symbol input. | **Modify** | Support explicit `symbol` and UTC `timestamp` keys in columns or index; do not mandate one pandas index layout. | A rigid MultiIndex prescription may hinder compatible normalized inputs. |
| `V2-IND-TYPE-004` | Core MVP `data` shall expose required OHLCV columns through stable lowercase column names and shall reject ambiguous duplicate columns. | **Add** | Core MVP `data` shall expose required OHLCV columns through stable lowercase column names and shall reject ambiguous duplicate columns. | This defines the Core MVP typed DataFrame contract. |
| `V2-IND-TYPE-005` | `IndicatorResult.values` shall be a `pandas.DataFrame` aligned to the accepted input timestamp/symbol keys and containing generated indicator columns plus required availability and quality metadata. | **Add** | `IndicatorResult.values` shall be a `pandas.DataFrame` aligned to the accepted input timestamp/symbol keys and containing generated indicator columns plus required availability and quality metadata. | This defines the Core MVP typed DataFrame contract. |
| `V2-IND-TYPE-006` | `IndicatorConfig` and `IndicatorContext` shall be typed as dataclasses, `TypedDict`, Pydantic models, or equivalent approved Python contracts before Builder handoff. | **Modify** | Approve exact types only for batch config/result/manifest/error; defer platform context and incremental state. | Those types belong to deferred capabilities. |
| `V2-IND-TYPE-007` | `IndicatorManifest`, `IndicatorState`, and `IndicatorError` shall have exact serialized field contracts before implementation begins. | **Modify** | Approve exact types only for batch config/result/manifest/error; defer platform context and incremental state. | Those types belong to deferred capabilities. |
| `V2-IND-TYPE-008` | Any future array-native input such as `numpy.ndarray` shall be an Optional Extension with explicit schema, shape, dtype, symbol/timestamp alignment, and conversion rules. | **Defer** | Any future array-native input such as `numpy.ndarray` shall be an Optional Extension with explicit schema, shape, dtype, symbol/timestamp alignment, and conversion rules. | Array-native input is explicitly future scope. |

### Source section: `Future Improvements`

| V2 requirement ID | Proposed behaviour | Decision | Final requirement direction | Reason |
|---|---|---|---|---|
| `V2-IND-FUT-001` | GPU/SIMD acceleration may be added as an Optional Extension after Core MVP formula and fixture behavior is stable. | **Defer** | GPU/SIMD acceleration may be added as an Optional Extension after Core MVP formula and fixture behavior is stable. | This is explicitly a future optional capability. |
| `V2-IND-FUT-002` | Out-of-core processing may be added as an Optional Extension after chunking parity and cache integrity requirements are approved. | **Defer** | Out-of-core processing may be added as an Optional Extension after chunking parity and cache integrity requirements are approved. | This is explicitly a future optional capability. |
| `V2-IND-FUT-003` | Rich notebook HTML representations may be added after stable result and manifest schemas exist. | **Defer** | Rich notebook HTML representations may be added after stable result and manifest schemas exist. | This is explicitly a future optional capability. |
| `V2-IND-FUT-004` | Proprietary source protection may be added through approved packaging/security controls without changing public indicator semantics. | **Defer** | Proprietary source protection may be added through approved packaging/security controls without changing public indicator semantics. | This is explicitly a future optional capability. |
| `V2-IND-FUT-005` | Canary routing, distributed tracing, SLO alerting, cryptographic package signing, release attestations, SBOM generation, and multi-writer cache synchronization may be added through platform or release-engineering integrations after ownership is approved. | **Reject** | Treat release controls as project/platform improvements, not indicator-domain capabilities. | Ownership is outside this domain. |

## 7. Workflow Reconciliation

| Final workflow ID | Workflow | Scope | V1 status | V2 proposal | Decision | Final boundary and outcome |
|---|---|---|---|---|---|---|
| WF-INDI-001 | Core batch indicator calculation | Internal | V1 examples working at code level but example-only (`V1-WF-INDICATORS-001`, `002`) | Normalized batch functions returning typed results | Replace | Normalized data + indicator config → fail-fast validation → vectorized formula → availability/quality → deterministic manifest/result. |
| WF-INDI-002 | Strategy/research/simulation consumption | Cross-domain | Missing production caller; examples append columns directly | Decision-time filtering and result joining | Add | Data-domain normalized input → indicators calculate decision-support values → strategy/research/simulation consumes only `available_at <= decision_time`. |
| WF-INDI-003 | Warmup coordination | Cross-domain | Implicit NaN warmup only | Indicator requests warmup data from data module | Modify | Indicator exposes `WarmupRequirement` → caller/data domain obtains normalized history → indicator calculates and marks warmup/unavailable rows. |
| WF-INDI-004 | Multi-timeframe calculation | Cross-domain | Missing | Indicator requests and aligns higher-timeframe bars | Modify | Caller supplies validated primary and higher-timeframe data → indicator aligns by closed-bar boundaries → result carries close-plus-latency availability. |
| WF-INDI-005 | Registry discovery and validation | Internal | Missing; export-only initializers | Registry operations and capability matrix | Add | Caller resolves official indicator spec → validates supported mode/config → invokes typed convenience function or generic calculation. |
| WF-INDI-006 | Custom indicator registration | Internal | No registry; hard-coded custom classes only | Conformance, registration and promotion workflow | Defer | No runtime custom registration in Core MVP. |
| WF-INDI-007 | Incremental/streaming update | Internal | Missing | Serializable state and update protocol | Defer | Batch-only initially; unsupported mode fails before calculation. |
| WF-INDI-008 | Cached indicator calculation | Cross-domain | Missing | Strict/best-effort cache adapters | Defer | Canonical hashes are emitted now; cache lookup/write workflow is not implemented. |
| WF-INDI-009 | SMC/HMA enrichment | Internal | Example-only `V1-WF-INDICATORS-003`; SMC contains lookahead | No Core MVP equivalent | Remove | Remove from production indicators. Any future retrospective labels require a research-domain specification; HMA may return as a separately approved trend extension. |
| WF-INDI-010 | Optional audit/observability/proprietary execution | Cross-domain | Missing | Audit sinks, tracing, canary, entitlement and SLO workflows | Defer | Core calculation emits a deterministic manifest only; external platform workflows are excluded. |

### `WF-INDI-001` — Core Batch Indicator Calculation

**Scope:** `Internal`

**V1 behaviour:**

```text
Caller supplies normalized, lowercase OHLCV DataFrame
→ instantiate V1 indicator class
→ `calculate(...)` copies DataFrame
→ append ad-hoc output columns
→ return enriched DataFrame
```

**V2 proposal:**

```text
Resolve indicator through typed wrapper or registry
→ validate full input/config before calculation
→ execute approved vectorized formula
→ attach warmup, availability, quality and manifest metadata
→ return `IndicatorResult`
```

**Final decision:**

```text
Replace the class-instantiation workflow with stateless typed batch calculation. Preserve copy/non-mutation semantics, but replace ad-hoc outputs and generic exceptions with the approved contracts.
```

**Reason:**

V1 calculation behaviour is reusable, while its package/API structure and missing safety metadata are not.

### `WF-INDI-002` — Decision-Time Consumption

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
No confirmed production consumer.
Usage examples inspect newly appended columns directly.
```

**V2 proposal:**

```text
Data domain provides normalized market data
→ indicators calculate values and `available_at`
→ strategy/research/simulation consumes only rows available at decision time
```

**Final decision:**

```text
Add the cross-domain contract. Indicators provide decision-support data and availability metadata; strategy/simulation own signal creation and lookahead enforcement.
```

**Reason:**

V1 SMC demonstrates why timestamp alone is insufficient to prove causal availability.

### `WF-INDI-003` — Warmup Coordination

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Warmup appears only as implicit rolling NaN values.
No data request contract exists.
```

**V2 proposal:**

```text
Indicator module requests minimum warmup history from data.
```

**Final decision:**

```text
Modify the proposal: the indicator spec emits `WarmupRequirement`; the orchestrator/data domain fetches normalized history. Indicators never perform direct I/O.
```

**Reason:**

Direct data requests would violate the accepted pure-domain boundary.

### `WF-INDI-004` — Multi-Timeframe Alignment

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Missing.
```

**V2 proposal:**

```text
Indicators request higher-timeframe data, forward-fill after close, and expose independent availability timestamps.
```

**Final decision:**

```text
Accept one caller-supplied higher-timeframe source with explicit close-plus-latency availability. Reject direct fetching and defer multiple simultaneous higher-timeframe sources.
```

**Reason:**

This provides the safety behaviour without turning indicators into a data orchestrator.

### `WF-INDI-005` — Registry Discovery and Validation

**Scope:** `Internal`

**V1 behaviour:**

```text
Root and category `__init__.py` files re-export classes without schemas or capability metadata.
```

**V2 proposal:**

```text
Mutable registry supports register/get/list/validate/unregister and capability matrix.
```

**Final decision:**

```text
Add an immutable official registry and machine-readable capability matrix. Defer mutation and custom registration.
```

**Reason:**

Static metadata solves discoverability and unsupported-mode validation with less complexity.

### `WF-INDI-006` — Custom Indicator Registration

**Scope:** `Internal`

**V1 behaviour:**

```text
V1 custom classes are hard-coded and ungoverned.
```

**V2 proposal:**

```text
Conformance, side-effect enforcement, status, registration and promotion.
```

**Final decision:**

```text
Defer the whole workflow. Core MVP contains only reviewed official built-ins.
```

**Reason:**

No confirmed initial workflow requires third-party extensions.

### `WF-INDI-007` — Incremental and Streaming Update

**Scope:** `Internal`

**V1 behaviour:**

```text
Missing.
```

**V2 proposal:**

```text
Deserialize state → validate bar → update bounded accumulators → emit parity result/state.
```

**Final decision:**

```text
Defer. Batch is the sole reference mode and unsupported stateful requests fail before calculation.
```

**Reason:**

State compatibility, idempotency, corrections and concurrency multiply risk before the formulas are stable.

### `WF-INDI-008` — Optional Cached Calculation

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Missing.
```

**V2 proposal:**

```text
Derive key → read strict/best-effort cache → calculate → atomic write → emit cache metadata.
```

**Final decision:**

```text
Defer storage and adapter behaviour. Emit canonical parameter/input/output identity material now.
```

**Reason:**

No measured workload justifies a cache subsystem.

### `WF-INDI-009` — SMC/HMA Enrichment

**Scope:** `Internal`

**V1 behaviour:**

```text
`V1-WF-INDICATORS-003`: calculate SMC retrospective labels, then HMA, over a DataFrame.
```

**V2 proposal:**

```text
No Core MVP equivalent.
```

**Final decision:**

```text
Remove the workflow from production indicators. HMA is deferred; SMC implementation is removed because it uses future observations. Retrospective research labels require a separate approved research workflow.
```

**Reason:**

The current workflow is example-only and unsafe for causal decision support.

### `WF-INDI-010` — Audit, Observability, Canary and Proprietary Execution

**Scope:** `Cross-domain`

**V1 behaviour:**

```text
Missing.
```

**V2 proposal:**

```text
Calculation emits audit entries, traces, metrics, canary comparisons, SLO data and entitlement decisions through adapters.
```

**Final decision:**

```text
Defer platform integrations. Core calculations return deterministic manifests only.
```

**Reason:**

These concerns are optional, cross-cutting, and unsupported by current usage evidence.

## 8. Recommended Minimal Capability Structure

```text
tools/indicators/
├── core/          # Minimal contracts, validation, deterministic errors, result/manifest, static registry
├── trend/         # EMA, SMA, ADX
├── volatility/    # ATR, ADR, rolling volatility
└── momentum/      # RSI, Williams %R
```

The initial package does **not** include `batch/`, `incremental/`, `adapters/`, `custom/`, `candles/`, `volume/`, cache infrastructure, composition graphs, or proprietary/platform integration modules. Batch is the default behaviour, so a separate `batch/` layer would add hierarchy without capability.

| Module | Capability | Source | Main decision |
|---|---|---|---|
| `core/` | Typed calculation/result contracts, validation, errors, manifest, warmup/availability metadata, static registry/capability matrix | Both | Modify/Add |
| `trend/` | EMA, SMA and ADX | Both | Modify/Add |
| `volatility/` | ATR, ADR and rolling volatility | Both | Modify/Merge/Add |
| `momentum/` | RSI and Williams %R | Both | Modify |

## 9. Reuse and Migration Plan

| Priority | Existing V1 item | Migration action | Target capability | Validation required |
|---:|---|---|---|---|
| 1 | `trend/sma.py:SMA.calculate` | Refactor | SMA in `CAP-INDI-005` | Approved formula table, constant-series invariant, warmup, naming, availability, index alignment. |
| 2 | `trend/ema.py:EMA.calculate` | Refactor | EMA in `CAP-INDI-005` | Approved smoothing/seed convention, golden fixtures and reference cross-validation. |
| 3 | `volatility/atr.py:ATR.calculate` | Refactor | ATR in `CAP-INDI-006` | Wilder seed/smoothing, non-negative invariant, gap fixtures and availability. |
| 4 | `momentum/rsi.py:RSI.calculate` | Refactor | RSI in `CAP-INDI-007` | Zero-loss/zero-gain/null conventions, bounds, seed and golden fixtures. |
| 5 | `momentum/will_r.py:WilliamsR.calculate` | Refactor | Williams %R in `CAP-INDI-007` | Degenerate range policy, bounds, warmup and causal timing. |
| 6 | `volatility/standard_deviation.py` | Replace/Merge | Rolling volatility in `CAP-INDI-006` | Approve return type, log/simple return, ddof and annualization; do not copy old formula blindly. |
| 7 | `base.py:BaseIndicator` | Replace | Minimal contracts in `CAP-INDI-002` | External subclass/import compatibility check; protocol conformance tests. |
| 8 | All V1 output patterns | Refactor | `CAP-INDI-003`, `008`, `010`, `012` | Result/join immutability, alignment, deterministic naming/errors/manifests. |
| 9 | ADX and ADR | New | `CAP-INDI-005`, `006` | Formula tables, golden fixtures, reference validation. |
| 10 | Static registry/capability matrix | New | `CAP-INDI-011` | Contract tests, unsupported-mode failures, import-side-effect tests. |
| 11 | `MFI`, PVD, SMC and unrelated helpers | Remove | None | Repository/external import check and compatibility decision. |
| 12 | WMA, Bollinger, MACD, OBV, CMF, candles, HMA | Defer | Future extensions | Do not migrate until a real workflow, formula table and acceptance tests are approved. |
| 13 | Plural and singular V1 package surfaces | Remove/compatibility transition | Canonical `tools.indicators` | Top-level compatibility decision and external-consumer evidence. |

## 10. Simplifications from V2

| V2 proposal | Problem | Simplified final direction |
|---|---|---|
| Nine public anatomy types plus broad `IndicatorContext` and `IndicatorState` | Mixes batch formulas with platform identity, tracing, entitlement, SLO and deferred state concerns. | Use minimal spec/protocol, config, result, manifest, warmup requirement and error contracts; no platform context/state in Core MVP. |
| Mandatory `calculate`, `calculate_vectorized`, `update`, serialize and deserialize methods | Duplicates batch APIs and forces every implementation to carry unsupported modes. | One typed batch calculation contract; capability matrix rejects unsupported modes. |
| Mutable register/unregister plugin registry | Adds lifecycle, trust and concurrency complexity without a confirmed custom-indicator workflow. | Immutable official built-in registry with `get`, `list`, `validate`. |
| Separate `batch/` folder plus `calculations.py` | Batch is the only initial mode, so the layer is redundant. | Place focused built-ins directly under trend/volatility/momentum modules. |
| `incremental/` state and accumulator architecture | No V1 state workflow; parity/correction/idempotency requirements are substantial. | Defer the entire mode. |
| `adapters/cache.py` and `adapters/audit.py` | Introduces I/O interfaces before a consumer exists and conflicts with minimal pure-domain scope. | Keep canonical hashes/manifests; add adapters only after a confirmed workflow. |
| Indicator-driven warmup and higher-timeframe data requests | Violates no-I/O calculation boundary and duplicates data orchestration. | Emit warmup/alignment requirements; caller/data domain supplies normalized inputs. |
| Large all-purpose `IndicatorConfig` | Combines output, cache, calendar, backend, entitlement, rollout, tracing and SLO concerns. | Core config contains indicator, parameters, source, output mode/naming, precision, availability and basic limits. |
| Manifest containing volatile timing, environment, host, rollout, access and SLO fields | Conflicts with deterministic manifest equality and mixes runtime diagnostics with calculation identity. | Compact deterministic manifest plus optional external diagnostics not included in identity checksums. |
| Full custom-indicator static-analysis/sandbox/promotion regime | Complex enforcement with no initial custom consumer. | Reviewed official built-ins only; defer extension governance. |
| Composition DAG and downstream cache invalidation | Manual chaining already covers simple use and no cache exists. | Caller-side explicit chaining; revisit only with a real graph workflow. |
| 42 error codes active from day one | Many codes correspond to deferred capabilities or data-domain validation. | Activate the 24 core codes dispositioned as Add; defer optional codes and reject data-owned codes. |
| Binding p99/SLO/cache-hit targets before benchmark evidence | Proposed volumes and thresholds are unverified. | Build reproducible benchmarks, then approve numeric targets. |
| SBOM, signing, release attestations and vulnerability gates as indicator requirements | System-wide CI/CD concerns, not indicator runtime behaviour. | Reference the project release policy; do not model these as indicator capabilities. |

## 11. Open Decisions

| Status | Decision required | Evidence available | Options | Affected capabilities |
|---|---|---|---|---|
| Open; escalate to top-level | Canonical compatibility/removal window for `app.services.indicators` and overlapping `app.services.indicator` | V1 audit found no production consumer of the plural package but found a used singular package; external consumers were inaccessible. | Immediate removal; temporary compatibility facade; telemetry-backed deprecation window | CAP-INDI-001, CAP-INDI-002, CAP-INDI-005..007 |
| Open; domain-internal | Exact formula tables and seed/warmup/null conventions for eight Core MVP indicators | V1 formulas exist for five indicators but conventions are incomplete or inconsistent; ADX/ADR/rolling volatility are missing. | Approve HaruQuant conventions; adopt pinned reference conventions with documented deviations | CAP-INDI-004..007 |
| Open; domain-internal | Default error mode | V2 proposes exception mode and result-error mode but does not select a default; V1 raises generic exceptions. | Exceptions by default; `IndicatorResult.errors` by default; support both with one default | CAP-INDI-012 |
| Open; domain-internal | Basic resource-limit defaults and benchmark/SLO thresholds | No executed benchmark or target hardware evidence was available. | Approve conservative limits now; measure first then approve; leave configurable without defaults temporarily | CAP-INDI-015 |
| Open; escalate to top-level | Data/indicator ownership for provenance, quality, calendar and multi-timeframe alignment | V2 assigns several data-source validation duties to indicators while its ownership section assigns normalization to data. | Data validates and indicators propagate; shared contract; indicator duplicates selected checks | CAP-INDI-009, CAP-INDI-013, CAP-INDI-014 |
| Open; escalate to top-level | Ownership of retrospective SMC/FVG/swing/BOS labels | V1 implementation is non-causal and example-only; potential research value is uncertain. | Remove entirely; move to research as retrospective labels; redesign causal variants as new indicators | V1-CAP-INDICATORS-020..022 |
| Open; domain-internal | Single-symbol/index layout for Core MVP and timing of multi-symbol support | V2 mandates UTC index/MultiIndex; V1 accepts arbitrary DataFrame indexes and has an MFI alignment defect. | Require timestamp/symbol columns; require index contract; support single symbol first | CAP-INDI-002, CAP-INDI-003, CAP-INDI-014 |
| Open; domain-internal | Cross-validation policy | V2 mandates at least two industry libraries; conventions and optional dependencies may differ. | Golden fixtures plus one independent library; two libraries; internal reference plus property tests | CAP-INDI-004 |

Open decisions marked **escalate to top-level** affect more than one domain and must be added to the top-level system document for resolution in pipeline step 05. Deferred optional integrations do not change the initial system shape; if later promoted, the top-level Deferred Capabilities section must be updated.

## 12. Inputs for the Final Domain README

### Approved capabilities

* Pure deterministic batch indicator calculation under `tools/indicators`.
* Minimal typed specs/config/result/manifest/error contracts.
* Full fail-fast schema, parameter, timestamp, OHLC, sufficiency, output and mutation validation.
* Vectorized copied output with deterministic column naming, values-only access and `join_to`.
* Core trend built-ins: EMA, SMA and ADX.
* Core volatility built-ins: ATR, ADR and rolling volatility.
* Core momentum built-ins: RSI and Williams %R.
* Exact formula tables, golden fixtures, float64/tolerance/null/degenerate policies.
* Warmup requirements and explicit warmup/unavailable rows.
* No-lookahead `available_at` and source-window metadata.
* Compact deterministic manifests, hashes/checksums and propagated provenance/quality.
* Immutable official registry and machine-readable capability matrix.
* Basic resource limits and reproducible benchmark methodology, with numeric defaults pending approval.
* Explicit symbol/timestamp grouping and limited caller-supplied multi-timeframe alignment.

### Approved workflows

* `WF-INDI-001` Core batch indicator calculation.
* `WF-INDI-002` Decision-time strategy/research/simulation consumption.
* `WF-INDI-003` Warmup requirement exchange with caller/data domain.
* `WF-INDI-004` Availability-aware caller-supplied multi-timeframe calculation.
* `WF-INDI-005` Static registry discovery and validation.

### V1 behaviours to preserve

* Copy/non-mutation semantics used by V1 indicator calculations.
* Straightforward deterministic pandas/NumPy formula kernels where their conventions are approved.
* V1 SMA, EMA, ATR, RSI and Williams %R as refactor references, not authoritative formulas.
* Composable DataFrame-oriented batch usage demonstrated by `V1-WF-INDICATORS-001` and `002`.

### V1 behaviours to modify

* Replace `BaseIndicator` inheritance with stateless functions and minimal structural contracts.
* Replace ad-hoc enriched DataFrame returns with `IndicatorResult` and deterministic naming/alignment.
* Formalize formulas, seeds, warmup, null and degenerate behaviour.
* Merge V1 rolling standard deviation into an explicitly specified rolling-volatility capability.
* Replace generic/ignored-kwargs error behaviour with fail-fast typed configuration and deterministic codes.
* Add availability, quality, provenance and manifest metadata to all approved calculations.

### V1 behaviours to remove

* Broken MFI implementation after external-import verification.
* Unused rolling volume-profile POC after external-import verification.
* Current FVG/swing/BOS/CHoCH SMC implementations from production indicators because of lookahead.
* Crossover helpers from indicators; strategy owns signal interpretation.
* Pip conversion and balance-scaled volume; trading/risk owns those behaviours.
* General averaging helpers duplicated elsewhere.
* Unused category re-export layers and duplicate package surfaces after compatibility approval.

### V2 behaviours to add

* ADX, ADR and explicitly defined rolling volatility.
* Formula specification tables and golden/reference fixtures.
* Typed result/manifest/error contracts and static registry.
* No-lookahead availability and warmup metadata.
* Canonical hashing/checksum policy.
* Quality/provenance propagation and official input validation.
* Requirement-to-test traceability for all approved requirements.

### V2 proposals to reject or defer

* Defer WMA/Bollinger/MACD/volume/candlestick/HMA migration until a real workflow exists.
* Defer custom registration, incremental/streaming state, chunking, out-of-core, acceleration and composition graphs.
* Defer cache storage, audit sinks, observability/tracing, canary routing, SLO enforcement and proprietary controls.
* Reject direct data fetching/requesting from indicators.
* Reject data-domain normalization policies and market-microstructure validation as indicator-owned behaviour.
* Reject release signing, SBOM, provenance attestation, license and vulnerability gates as indicator-domain capabilities.
* Reject a platform-heavy `IndicatorContext` in the pure calculation API.
* Reject the current non-causal SMC implementation from production indicators.

### Required open decisions before README completion

* Approve exact formula tables for EMA, SMA, ADX, ATR, ADR, rolling volatility, RSI and Williams %R.
* Approve minimal type contracts and default error mode.
* Approve canonical parameter/input/output hashing.
* Approve Core MVP resource-limit defaults or explicitly mark them pending.
* Resolve canonical-package compatibility and retirement of singular/plural V1 surfaces.
* Resolve the data/indicator boundary for provenance, quality, calendar and multi-timeframe contracts.
* Resolve whether retrospective SMC labels belong in research or are removed entirely.

## 13. Final Reconciliation Checklist

* [x] Every one of the 26 V1 capabilities received a disposition.
* [x] Every one of the 769 extracted V2 normative/proposed items received a disposition.
* [x] Every V1 workflow was reconciled.
* [x] Every material V2 workflow family was reconciled, including optional/deferred workflows.
* [x] Confirmed working V1 calculation behaviour was not discarded without reason.
* [x] Unused, broken, duplicated and unsafe V1 behaviour was not preserved automatically.
* [x] V2 implementation complexity was not accepted automatically.
* [x] The recommended direction follows the Package → Module folder → File → Public symbol hierarchy.
* [x] Possible cross-domain responsibilities are flagged for pipeline step 05.
* [x] Unresolved conflicts are listed under Open Decisions.
* [x] Cross-domain open decisions are marked for top-level escalation.
* [x] No code was inspected during reconciliation.
* [x] No code was changed.
* [x] Neither source document was modified.
* [x] The output contains sufficient approved inputs for the final domain README.

## Evidence Unavailable

* Runtime import telemetry or deployment manifests proving whether external code imports `app.services.indicators` or `app.services.indicator`.
* Executed V1 unit/integration tests, coverage, linting, type checking, benchmark results, or golden fixtures.
* Approved Core MVP formula tables and reference-library decisions.
* Approved default error mode, resource limits, benchmark hardware, SLO thresholds, cache/checksum policy, and audit integrity policy.
* The top-level cross-domain contract decisions that will be reviewed in pipeline step 05.

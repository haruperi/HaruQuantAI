# Phase 04 Strategy Service — Full Brownfield Upgrade Plan with Requirement Coverage Matrix

## 0. Purpose

This document is a brownfield upgrade and migration plan for the existing Strategy module. It replaces the prior greenfield-style architecture plan as the upgrade source of truth for `docs/dev/phase-implementation-plan/04-strategy.md`.

The current repository already contains working Strategy code. The upgrade must preserve and harden that code. It must not delete the current implementation and recreate a new `app/services/strategies/` tree simply because the old plan used a plural path.

The inspected current implementation is under:

```text
app/services/strategy/
```

The old plan targets:

```text
app/services/strategies/
```

That mismatch is a compatibility concern. The correct brownfield response is to preserve `app.services.strategy`, add tests, and introduce `app.services.strategies` only as a compatibility facade or controlled migration target if needed.

## 1. Non-Negotiable Brownfield Rules

- Preserve the existing `app/services/strategy/` package and all working strategy behavior.
- Do not delete working code without characterization tests, migration tests, and rollback notes.
- Preserve public imports during the upgrade window.
- Add compatibility wrappers when the old plan's plural package path is needed.
- Build tests before risky refactors.
- Avoid large move-only refactors.
- Introduce new files only when they clarify boundaries or reduce coupling.
- Keep strategies deterministic for identical inputs, configuration, state, and injected runtime context.
- Do not introduce lookahead bias.
- Do not mutate input market data unexpectedly; copy before adding signal columns unless an internal optimization is explicitly documented and tested.
- Do not allow strategies to own broker connections.
- Do not allow strategies to submit live trades directly.
- Do not allow strategies to bypass Risk Governance.
- Strategies produce signals, trade intents, diagnostics, and strategy-local state transitions; they do not own live execution.

## 2. Current Repository Baseline

### 2.1 Current folder structure discovered

```text
app/services/strategy/
├── README.md
├── __init__.py
├── base.py
├── config.py
├── state.py
├── strategy-config.schema.json
└── pybots/
    ├── MQL5_TRANSLATION_AUDIT.md
    ├── __init__.py
    ├── registry.py
    ├── mql5_translation_helpers.py
    ├── _template/
    │   ├── __init__.py
    │   ├── rules.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── sqx_breakout_atr_trailing/
    │   ├── __init__.py
    │   ├── rules.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── naive_ma_trend/
    │   ├── __init__.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── decomposing_trade_ea/
    │   ├── __init__.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── harriet_hedging_ea/
    │   ├── __init__.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── market_structure_ea/
    │   ├── __init__.py
    │   ├── strategy.json
    │   └── strategy.py
    ├── random_walk_ea/
    │   ├── __init__.py
    │   ├── strategy.json
    │   └── strategy.py
    └── white_fairy_ea/
        ├── __init__.py
        ├── strategy.json
        └── strategy.py
```

Related shared contracts are currently in:

```text
app/services/contracts/strategies.py
```

Current tests discovered:

```text
tests/unit/app/services/strategy/test_strategy_service.py
tests/unit/app/services/strategy/test_trend_following.py
tests/usage/04_strategies.py
```

### 2.2 Current exports

`app/services/strategy/__init__.py` currently exports:

- Shared canonical snapshots/contracts from `app.services.contracts.strategies`: `AccountSnapshot`, `Bar`, `Direction`, `EntryType`, `IntentAction`, `MarketContext`, `PendingOrderSnapshot`, `PositionSnapshot`, `ProtectionRequest`, `QuoteSnapshot`, `RuntimeMode`, `SignalSet`, `StrategyDecision`, `TradeIntent`.
- Strategy framework objects: `BaseStrategy`, `StrategyPermissionError`, `StrategyConfig`, `ConfigurationError`, `load_strategy_config`, `validate_strategy_config`, `StrategyState`.

### 2.3 Current public/support functions and classes

Current core framework:

- `BaseStrategy.evaluate(context) -> StrategyDecision`
- `BaseStrategy.evaluate_execution_event(context, event_id) -> StrategyDecision`
- `BaseStrategy.calculate_signals(df, context) -> DataFrame` abstract hook
- `StrategyState.to_dict()` / `StrategyState.from_dict()`
- `load_strategy_config(path) -> StrategyConfig`
- `validate_strategy_config(value) -> StrategyConfig`
- `bundled_strategy_ids() -> tuple[str, ...]`
- `load_bundled_strategy(strategy_id, state=None) -> BaseStrategy`
- `strategy_from_config(config, state=None) -> BaseStrategy`

Current strategy families/templates:

- `naive_ma_trend`
- `sqx_breakout_atr_trailing`
- `decomposing_trade_ea`
- `harriet_hedging_ea`
- `market_structure_ea`
- `random_walk_ea`
- `white_fairy_ea`
- `_template`

### 2.4 Current capabilities that should be preserved

- Broker-neutral strategy decisions and `TradeIntent` proposals.
- Read-only `MarketContext` snapshots and shared strategy contracts.
- JSON configuration loading and deterministic validation.
- Strategy-local state separate from broker ledger state.
- Completed-bar convention and basic warm-up behavior.
- Bundled strategy registry and agent-safe `load_bundled_strategy` entry point.
- MQL5 translation helpers that require quote/position evidence instead of inventing it.
- Existing unit tests and usage example.

### 2.5 Current pain points and gaps

- Old plan targets `app/services/strategies/`, but current code is `app/services/strategy/`.
- Current registry is useful but too lightweight for immutable registry evidence, lifecycle approvals, provenance, and version constraints.
- Current config validation is strong for schema/ranges but incomplete for malicious string patterns, payload bounds, nested depth, and schema migration policy.
- Current diagnostics are mostly strings/logs rather than structured bounded diagnostic contracts.
- Current error handling uses native exceptions rather than a complete `STRATEGY_*` taxonomy.
- Current lookahead protection relies on completed-bar conventions, `MarketContext.as_of`, and strategy discipline; it needs named point-in-time/timing guards and property tests.
- Current state is serializable but lacks checksum/schema/checkpoint compatibility and transaction rollback boundaries.
- Current usage example calls `get_data(... source="mt5")`; this should be mocked/gated for CI-safe executable documentation.
- No explicit sandbox/raw-code rejection boundary exists in Strategy.
- No explicit output allowlist boundary rejects broker payloads or live mutation instructions before leaving Strategy.

## 3. Target Brownfield Architecture

The target architecture is an evolution of the current implementation, not a replacement.

```text
app/services/strategy/                         # KEEP: current compatibility package
├── __init__.py                                # HARDEN: stable public/support exports
├── base.py                                    # KEEP/HARDEN: lifecycle kernel; split later only after tests
├── config.py                                  # KEEP/HARDEN: canonical JSON config validator
├── state.py                                   # KEEP/HARDEN: local strategy state
├── strategy-config.schema.json                # KEEP/HARDEN: schema authority
├── contracts/                                 # ADD: strategy-specific wrappers/declarations only if not shared
├── registry/                                  # ADD: wrapper around pybots registry, not replacement first
├── validation/                                # ADD: config/data/readiness/signal validators
├── timing/                                    # ADD: availability and point-in-time guards
├── runtime/                                   # ADD: resource, lineage, transactions, checkpoints, cancellation
├── execution/                                 # ADD: output boundary, hooks, vectorized/event wrappers
├── errors/                                    # ADD: strategy error codes/mapping
├── sandbox/                                   # ADD: raw-code rejection and metadata policy
├── observability/                             # ADD: structured diagnostics/metrics
├── governance/                                # ADD: evidence declarations only
└── pybots/                                    # KEEP: bundled implementations and templates

app/services/strategies/                       # ADD ONLY AS COMPATIBILITY FACADE if needed
└── __init__.py                                # Re-export approved public API from app.services.strategy

docs/strategies/                               # ADD/HARDEN
├── OPERATING_MANUAL.md
└── TRACEABILITY_MATRIX.md

tests/services/strategies/                     # ADD: requirement-mapped brownfield suite
tests/unit/app/services/strategy/              # KEEP: existing characterization tests
```

## 4. Public Boundary Policy

### Official public API

These become official only after schemas, docs, and tests are added:

- `load_bundled_strategy`
- `bundled_strategy_ids`
- `strategy_from_config`
- `validate_strategy_config`
- `load_strategy_config`
- `BaseStrategy.evaluate`
- `BaseStrategy.evaluate_execution_event`
- canonical contracts imported from `app.services.contracts.strategies`

### Public support API

- `StrategyConfig`
- `StrategyState`
- `StrategyPermissionError`
- `ConfigurationError`
- `mql5_translation_helpers` functions, after internal/support classification is documented.

### Legacy compatibility API

- `app.services.strategy` import path remains valid.
- `app.services.strategies` may be added as a compatibility facade, but must not become a move-only refactor.
- Removed historical files such as `app/services/strategy/models.py` and `app/services/strategy/service.py` should not be resurrected unless needed as compatibility shims with deprecation warnings.

### Internal-only implementation detail

- `pybots/*/strategy.py` concrete implementation classes should not be deep-imported by downstream modules except tests and explicit registry internals.
- `_template` and MQL5 helper internals are implementation details unless promoted through `__all__`.

### `__init__.py` behavior during migration

- It remains import-safe: no broker connections, network calls, data reads, database writes, thread startup, or heavy initialization.
- It explicitly declares `__all__`.
- It should expose only approved public/support/compatibility names.
- Registry/catalog changes require tests and documentation updates.

## 5. Strategy/Data/Indicator/Risk/Trading Boundary Contract

Strategies may consume:

- normalized market data from Data;
- indicator outputs from Indicators;
- portfolio/risk context as read-only inputs from Risk, when required;
- simulation context during backtests;
- configuration, parameters, manifests, and strategy-local state.

Strategies own:

- strategy parameter validation;
- lifecycle hooks;
- strategy-local state transitions;
- signal generation;
- action intent generation;
- deterministic strategy evaluation;
- strategy diagnostics;
- metadata and manifest validation;
- examples/templates;
- lookahead-safety rules.

Strategies must not own:

- broker connections;
- broker reads;
- raw data persistence;
- indicator calculation internals;
- risk approvals;
- final position sizing authority except advisory hints;
- order submission/modification/cancellation;
- live execution;
- reconciliation;
- account mutation;
- UI/API concerns;
- optimization orchestration.

Risk Governance owns final risk checks, exposure limits, drawdown gates, approval/rejection decisions, and signed approval tokens.

Trading owns order lifecycle, execution adapters, position/order/deal/account facades, and broker mutation boundaries.

Simulation owns deterministic backtest event loop, simulated fills, and simulated portfolio state.

Optimization owns parameter search orchestration, objective scoring, and pruning/search-space management.

## 6. Implementation Sequence

1. **Baseline audit and characterization tests.** Freeze current imports, `__all__`, BaseStrategy behavior, StrategyState serialization, config validation, bundled strategy loading, usage examples, and import-side-effect behavior.
2. **Compatibility exports and public boundary classification.** Keep `app.services.strategy` stable. Add `app.services.strategies` only as a thin re-export facade when tests exist. Mark official public API, public support API, compatibility API, and internal-only API.
3. **Core contracts/model alignment.** Reuse `app.services.contracts.strategies` and add missing schema-version, evidence, provenance, declaration, and output-boundary models without duplicating Risk/Trading models.
4. **Config/schema hardening.** Extend `config.py` and `strategy-config.schema.json` for payload bounds, injection rejection, lifecycle mapping, version migration, and deterministic error codes.
5. **Registry/catalog/resolver hardening.** Wrap `pybots/registry.py` with immutable catalog metadata, duplicate detection, approved module allowlist, version/provenance checks, and lifecycle gating.
6. **Preserve and harden existing strategy implementations.** Add tests around every bundled strategy before moving or splitting anything. Strategy logic remains broker-neutral and emits intents only.
7. **Timing/lookahead safety.** Add named availability and point-in-time guards around completed-bar behavior, higher-timeframe data, feature availability, and vectorized current-bar shifting.
8. **Runtime/state/lineage.** Add intent ID, decision ID, sequence, idempotency, state transaction, checkpoint compatibility, rollback, and cancellation boundaries around current BaseStrategy and StrategyState.
9. **Execution output boundary.** Introduce allowlist validation for StrategySignal, TradeIntent, diagnostics, and local state only. Reject broker payloads, risk approvals, live mutation instructions, and raw provider fields.
10. **Error taxonomy and mapping.** Add strategy error code catalog and adapters from current exceptions to deterministic errors without breaking native exceptions used internally.
11. **Sandbox and raw-code rejection.** Add registry-reference-only input gate and sandbox metadata validation; keep actual sandbox execution out of scope unless approved later.
12. **Observability.** Add structured diagnostics and injected metrics emitters with redaction and bounded payloads.
13. **Governance evidence declarations.** Add validation artifact/build artifact/policy models as evidence contracts only; approval remains outside Strategy.
14. **Documentation and examples.** Rewrite README, add operating manual, update usage examples, and record migration notes.
15. **Final traceability and coverage pass.** Every STRAT-FR/STRAT-NFR row maps to a test/evidence target; all tests pass; coverage >=80%.


## 7. File-by-File Upgrade Map

| File path | Current role | Target role | Decision | Requirements covered | Migration action | Tests required |
|---|---|---|---|---|---|---|
| `app/services/strategy/__init__.py` | Current public export gate for contracts, base, config, state. | Keep as compatibility/public support gate during migration. | Preserve + harden | STRAT-FR-003..005, 019..024, 068, 071 | Add explicit public/compat classification; avoid import-time registry execution; later re-export from plural facade. | Import-side-effect test; `__all__` snapshot test. |
| `app/services/strategy/base.py` | Core BaseStrategy with `evaluate`, `evaluate_execution_event`, signal resolution, schedule gates, intents, and local state recording. | Harden as lifecycle kernel; split helper boundaries only after tests. | Preserve + harden + later split | STRAT-FR-027..033, 037, 042, 062, 084, 091..095 | Add output boundary, timing guard, lineage helpers, transaction wrappers, and event queue around current methods. | Lifecycle, no mutation, duplicate event, warmup, schedule, lineage, rollback tests. |
| `app/services/strategy/config.py` | JSON config loader/validator, manifest checks, parameter typing/ranges, runtime permissions. | Harden as brownfield config validator and schema adapter. | Preserve + harden | STRAT-FR-006..009, 016..018, 063, 102 | Add injection-pattern rejection, payload bounds, lifecycle mapping, schema migration, and error codes. | Config success/failure matrix; malicious string tests; schema version tests. |
| `app/services/strategy/state.py` | Serializable local strategy state. | State model behind transaction/checkpoint wrappers. | Preserve + harden | STRAT-FR-033, 054, 079, 092 | Add checksum/schema version, checkpoint compatibility, local transaction rollback. | Serialization round-trip, corruption, rollback, checksum mismatch tests. |
| `app/services/contracts/strategies.py` | Canonical shared contracts: StrategyInput, StrategySignal, RuntimeMode, Direction, TradeIntent, snapshots, MarketContext. | Keep as shared contract source; Strategy wraps/adapts rather than duplicating. | Preserve + align | STRAT-FR-011..013, 024, STRAT-NFR-001..005 | Fill missing signal evidence/validity fields and align enum vocabulary via compatibility mapping. | JSON-safe, risk-consumable, no broker payload contract tests. |
| `app/services/strategy/pybots/registry.py` | Static bundled strategy catalog with `bundled_strategy_ids`, `load_bundled_strategy`, `strategy_from_config`. | Official bundled strategy resolver behind richer registry metadata. | Preserve + wrap | STRAT-FR-006, 008, 009, 016, 017, 081, 100 | Add duplicate/malformed validation, lifecycle/provenance gates, approved module allowlist, and public catalog DTO. | Registry resolution/rejection tests; duplicate catalog fixture tests. |
| `app/services/strategy/pybots/*/strategy.py` | Bundled concrete strategies, including Naive MA trend and MQL5 translations. | Existing strategy families preserved as fixtures/examples and production-candidate strategies after validation. | Preserve + harden | STRAT-FR-028, 030, 037, 046..051, 084, 091 | Add no-lookahead fixtures, non-mutating dataframe policy, config/manifests, diagnostics. | Strategy-specific tests for each bundled strategy; insufficient data; constant data; duplicate timestamps. |
| `app/services/strategy/pybots/*/strategy.json` | Canonical per-strategy JSON config/manifests. | Source manifests for official registry. | Preserve + harden | STRAT-FR-006, 007, 035, 043, 044, 053..061 | Add approval/evidence/provenance fields and schema validation. | Manifest schema and lifecycle tests. |
| `app/services/strategy/pybots/mql5_translation_helpers.py` | Pure helper functions for MQL5 translations; quote and position utility functions. | Internal support API; keep broker-neutral and read-only. | Preserve + classify internal | STRAT-FR-046, 060, 096 | Add docstring API status and tests for invalid/missing quote/positions. | Helper unit tests; no broker import test. |
| `app/services/strategy/README.md` | Existing authoring guide and boundary notes. | Brownfield README/operating guide; split into package README plus docs/strategies manual. | Preserve + rewrite | STRAT-FR-001, 015, 045, 057, 088, 104 | Update to actual package path, public APIs, compatibility policy, and migration notes. | Documentation lint and examples test. |
| `app/services/strategy/strategy-config.schema.json` | JSON schema for config. | Schema authority for config validator and registry. | Preserve + harden | STRAT-FR-007, 013, 063 | Keep in sync with Python validator; add schema-version compatibility matrix. | Schema fixture validation tests. |
| `app/services/strategies/__init__.py` | Does not currently exist. | Optional plural compatibility facade after tests prove safety. | Add cautiously | STRAT-FR-003..005, 019..024, 068, 071 | Re-export stable approved symbols from singular package; do not move code first. | `from app.services.strategy` and `from app.services.strategies` parity tests. |
| `tests/unit/app/services/strategy/` | Existing unit tests for current singular package. | Preserve as characterization tests during migration. | Preserve + extend | STRAT-FR-014, 067, 072, 083, 090, 101 | Keep current tests passing; add parallel brownfield tests under requested path. | Coverage >=80%; import compatibility tests. |
| `tests/services/strategies/` | Not the current test location. | Target brownfield requirement-mapped test suite. | Add | STRAT-FR-014, 067, 072, 083, 090, 101, STRAT-NFR-006 | Add requirement traceability, contract, no-lookahead, sandbox, and boundary tests. | Traceability test maps every row in this matrix. |
| `tests/usage/04_strategies.py` | Usage examples for vectorized and bar-by-bar replay. | Keep as executable documentation, remove broker/network assumptions or gate them. | Preserve + harden | STRAT-FR-066, 088 | Add offline fixture mode and expected output assertions. | Usage examples test in CI. |


## 8. Requirement Coverage Matrix

| Original Requirement ID | Requirement Summary | Brownfield Task(s) | Current Code Anchor | Migration Action | Test/Evidence Target | Status |
|---|---|---|---|---|---|---|
| STRAT-FR-001 | Strategy operating manual, documentation retention, run_backtest input modes, and explicit rationale for future/not-implemented items. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-002 | Strategy declarations must not assume infinite best-bid/ask liquidity. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-003 | Package initialization foundation behavior for the public strategy gateway. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-004 | No file-specific NFR for package initialization; foundation applies. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-005 | No file-specific testing requirement for package initialization; foundation applies. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-006 | Official strategy registry with ids, versions, owners, schemas, required data/indicators, risk assumptions, execution modes, hashes, and risk profile. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-007 | Configuration schema validation, default/unknown-field/type policy, bounded payloads, and configuration-injection rejection. | STR-UPG-006: strengthen config, data, and signal validation | app/services/strategy/config.py; app/services/contracts/strategies.py; app/services/strategy/base.py | Harden current validate_strategy_config and MarketContext checks; add bounded payload, injection, data-quality, and readiness validators. | tests/services/strategies/test_validation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-008 | Deterministic rejection of duplicate or malformed registry entries. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-009 | Deterministic strategy version resolution plus deprecation, lifecycle, artifact, and checkpoint compatibility gates. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-010 | Provisional performance/resource baselines and reference environment for strategy execution. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-011 | TradeIntent schema plus reproducibility, replay, audit, diagnostics, hashes, and decision metadata. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-012 | Registered strategy lifecycle status enum. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-013 | Versioned public capability schemas and compatibility testing before downstream consumption. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-014 | Registry validation tests for resolution, rejection, approved modules, and contract coverage. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-015 | Documentation for registry behavior and configuration schema rules. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-016 | Phase 1 execution limited to registered strategies with validated configuration. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-017 | Strategy files and module paths resolved only through approved registries or allowlisted roots. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-018 | Explicit technology stack constraints for production-eligible strategies. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-019 | No file-specific NFR for package gateway. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-020 | No file-specific FR for package gateway; foundation applies. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-021 | No file-specific NFR for package gateway. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-022 | No file-specific testing requirement for package gateway. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-023 | Document remains a domain-level requirements source until active roadmap approves scope. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-024 | Strategy ownership boundary and separation from data, indicators, simulator, risk, trading, UI, and live execution. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-025 | Declare third-party dependencies and capacity assumptions. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-026 | Document public callable signatures, schemas, stability, side effects, idempotency, error codes, and compatibility guarantees. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-027 | Determinism, redacted diagnostics, isolation, resource timeout/retry handling, and dependency failure policy. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-028 | Strategies emit only decisions, signals, intents, diagnostics, and local state; no external authority mutation. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-029 | TradeIntent emission contract, alpha/cost threshold suppression, partial-fill guidance, and timing/sizing handoff. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-030 | Default BAR_OPEN_PREVIOUS_CLOSE timing and previous-closed-bar-only access at bar open. | STR-UPG-005: add lookahead and point-in-time guards | app/services/contracts/strategies.py; app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Build explicit availability/point-in-time guards around completed-bar convention and indicator availability metadata. | tests/services/strategies/test_timing_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-031 | Point-in-time correctness for feature/indicator lookups and data-latency tolerance. | STR-UPG-005: add lookahead and point-in-time guards | app/services/contracts/strategies.py; app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Build explicit availability/point-in-time guards around completed-bar convention and indicator availability metadata. | tests/services/strategies/test_timing_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-032 | Reject arbitrary source-code execution through run_backtest and enforce resource controls for approved code. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-033 | Strategy-local decision state management, serialization, isolation, and checkpoint-safe state transitions. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-034 | Strategy execution input/output data contract fields. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-035 | Strategy-level risk profile fields and lifecycle-promotion evidence requirements. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-036 | TradeIntent idempotency and lineage fields. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-037 | Indicator readiness and missing/stale-data policies. | STR-UPG-006: strengthen config, data, and signal validation | app/services/strategy/config.py; app/services/contracts/strategies.py; app/services/strategy/base.py | Harden current validate_strategy_config and MarketContext checks; add bounded payload, injection, data-quality, and readiness validators. | tests/services/strategies/test_validation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-038 | Structured diagnostics with request/correlation/run/strategy trace fields. | STR-UPG-016: add diagnostics and metrics boundary | app/services/strategy/base.py; tests/usage/04_strategies.py | Replace free-form diagnostics with bounded structured diagnostics and metric emitters through injected sinks. | tests/services/strategies/test_observability_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-039 | Parameter-optimization validation artifacts and reproducibility validation. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-040 | Computational complexity, concurrency model, and resource budgets. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-041 | Build pipeline artifacts, security gates, SBOM/dependency evidence, and quality gates. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-042 | Strategy failure isolation and external hard-kill signal support. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-043 | Permitted environments: BACKTEST, REPLAY, PAPER, SHADOW, LIVE. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-044 | Paper/live execution gated by validation gates, explicit approval, and deterministic decision inputs. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-045 | Runbook for every production-eligible strategy, turn-off procedure, onboarding metadata, and ownership assumptions. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-046 | Execution assumptions, algorithms, spread/volume limits, and venue eligibility declarations. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-047 | Deterministic halt-like market-state policies and diagnostics. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-048 | Portfolio-interaction mode and exposure/allocation assumptions without portfolio enforcement ownership. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-049 | Health checks, circuit-breaker inputs, deployment/rollback metadata, review bands, drift/canary diagnostics. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-050 | Regulatory regime, reporting, and best-execution assumptions without regulatory enforcement ownership. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-051 | Data-gap, corporate-action, startup-readiness, and delisted-symbol handling assumptions. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-052 | Latency, throughput, recovery, and resource SLOs. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-053 | Calibration, parameter-stability, and overfitting-control policies. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-054 | Strategy-local checkpoint/restore assumptions and degradation communication metadata. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-055 | Market-closure and emergency-liquidation assumptions without owning liquidation enforcement. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-056 | Performance review cadence, A/B testing, shadow testing, and kill criteria. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-057 | Strategy IP classification, licensing, regulatory-filing compliance, and material-change procedures. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-058 | ML model artifact serialization, feature-store dependency, and drift-detection requirements. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-059 | Hardcoded secret prohibition and secrets-manager-only access. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-060 | Order-book depth support and deterministic behavior for degraded order-book data. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-061 | Traceability and sign-off before production readiness. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-062 | Standard strategy processing anatomy and hook contract. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-063 | Invalid or unknown config fields fail deterministically. | STR-UPG-006: strengthen config, data, and signal validation | app/services/strategy/config.py; app/services/contracts/strategies.py; app/services/strategy/base.py | Harden current validate_strategy_config and MarketContext checks; add bounded payload, injection, data-quality, and readiness validators. | tests/services/strategies/test_validation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-064 | Deterministic data-dependency error behavior and concurrent read-only state access. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-065 | Canonical STRATEGY_* error-code catalog. | STR-UPG-014: add strategy error taxonomy and mapping | app/services/strategy/config.py; app/services/strategy/base.py; app/services/contracts/strategies.py | Introduce codes/mapping while preserving current ConfigurationError, StrategyPermissionError, and ValueError behavior through adapters. | tests/services/strategies/test_errors_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-066 | Traceability, executable examples, and Builder-handoff documentation for every requirement. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-067 | Full strategy test suite covering built-ins, timing, fuzz, performance, boundary, security, and clock drift. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-068 | Signals/diagnostics only; no external authority-state mutation. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-069 | Reuse canonical app.utils errors and map lower-level lookahead errors into strategy-domain codes. | STR-UPG-014: add strategy error taxonomy and mapping | app/services/strategy/config.py; app/services/strategy/base.py; app/services/contracts/strategies.py | Introduce codes/mapping while preserving current ConfigurationError, StrategyPermissionError, and ValueError behavior through adapters. | tests/services/strategies/test_errors_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-070 | Deterministic disablement/escalation and safe structured errors for invalid input. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-071 | No file-specific NFR for package gateway. | STR-UPG-002: preserve compatibility exports and define public boundary | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-072 | Decision-table contract, error-code mapping, and dependency-failure tests for every public capability. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-073 | Raw strategy-code injection rejected deterministically with safe journaling and diagnostics. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-074 | Resource exhaustion and secret exposure fail deterministically with redacted security journal events. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-075 | Deprecated/revoked strategies fail deterministically; simulation/risk remain final authority. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-076 | Duplicate intent/idempotency collisions and non-monotonic sequences fail deterministically. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-077 | Malformed/missing/timezone-inconsistent market data and clock drift fail deterministically. | STR-UPG-006: strengthen config, data, and signal validation | app/services/strategy/config.py; app/services/contracts/strategies.py; app/services/strategy/base.py | Harden current validate_strategy_config and MarketContext checks; add bounded payload, injection, data-quality, and readiness validators. | tests/services/strategies/test_validation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-078 | Approval invalidation on provenance changes and deterministic orchestration failure policies. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-079 | Corrupt, incompatible, or unauthorized checkpoints fail before execution. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-080 | Data-failover, backup-venue, recovery assumptions, and post-mortem documentation. | STR-UPG-017: add governance evidence contracts | app/services/strategy/README.md; app/services/strategy/pybots/*/strategy.json | Model validation/build/production evidence as declarations only; leave approval and promotion authority outside Strategy. | tests/services/strategies/test_governance_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-081 | Unknown, empty, or unapproved strategy ids/modules fail deterministically. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-082 | Additional cross-domain codes: SIM_ARBITRARY_CODE_REJECTED, STRATEGY_INTERNAL_ERROR, INDICATOR_MODULE_ERROR, STRATEGY_CHECKPOINT_INVALID, STRATEGY_DATA_QUALITY_GATE_FAILED. | STR-UPG-014: add strategy error taxonomy and mapping | app/services/strategy/config.py; app/services/strategy/base.py; app/services/contracts/strategies.py | Introduce codes/mapping while preserving current ConfigurationError, StrategyPermissionError, and ValueError behavior through adapters. | tests/services/strategies/test_errors_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-083 | Failure-path, scenario, and security tests for every confirmed error code. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-084 | Vectorized signal-strategy processing contract with shifted current-bar handling and no execution/accounting/risk/journal steps. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-085 | Atomic lookahead detection and stable decision clock for vectorized batches. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-086 | Isolated worker process contract for CPU-bound vectorized strategies. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-087 | Deterministic hook order across vectorized, event, replay, checkpoint/restore, and shutdown. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-088 | Documentation for vectorized/event examples and no-lookahead timing. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-089 | No file-specific NFR for vectorized execution. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-090 | Vectorized-strategy and no-lookahead property-based tests. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-091 | Stateful event strategies respond to lifecycle events through controlled read-only interfaces. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — current implementation covers the core behavior but lacks the full target wrapper/tests. |
| STRAT-FR-092 | Atomic per-decision-event local state updates and deterministic rollback. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-093 | Risk/correlation assumptions during stress events and link every intent to originating decision. | STR-UPG-012: harden lifecycle, state, lineage, checkpoints, resources | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-094 | Execution metrics covering intents, decisions, data quality, and latency. | STR-UPG-016: add diagnostics and metrics boundary | app/services/strategy/base.py; tests/usage/04_strategies.py | Replace free-form diagnostics with bounded structured diagnostics and metric emitters through injected sinks. | tests/services/strategies/test_observability_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-095 | Bounded execution, thread-safety/reentrancy declarations, and deterministic event ordering. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-096 | Wash-trade prevention rules and microstructure market-state event behavior. | STR-UPG-004: align canonical contracts and compatibility models | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-097 | Standard event-strategy lifecycle hook interface. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-098 | Measurable resource limits, backpressure behavior, and async/sync compatibility contracts. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-099 | No file-specific NFR for event dispatch. | STR-UPG-013: canonicalize vectorized/event output boundaries | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-100 | Execution gated by approved lifecycle status. | STR-UPG-007: harden bundled registry into approved catalog/resolver | app/services/strategy/pybots/registry.py; app/services/strategy/pybots/*/strategy.json | Preserve pybots registry and strategy.json manifests; wrap with richer catalog, lifecycle, version, provenance, and resolver validation. | tests/services/strategies/test_registry_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-101 | Event-driven test suite covering stress, chaos, memory leak, boundary, and concurrency cases. | STR-UPG-001: add characterization and requirement traceability tests | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |
| STRAT-FR-102 | Strategy code execution restricted to registered, validated, or explicitly sandboxed/vetted paths. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-103 | Disallowed environment-variable access, missing sandbox metadata, or expired approval fails deterministically. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-FR-104 | Sandbox and vetting documentation if code-based strategy execution is ever enabled. | STR-UPG-009: update README/operating manual and migration notes | app/services/strategy/README.md; app/services/strategy/pybots/MQL5_TRANSLATION_AUDIT.md | Update README and add docs/strategies operating manual while reflecting current singular package and planned plural facade. | tests/services/strategies/test_documentation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-FR-105 | No file-specific NFR for sandbox policy. | STR-UPG-015: add raw-code rejection and sandbox metadata policy | app/services/strategy/config.py; app/services/strategy/pybots/registry.py | Add early request gate for raw-code rejection; do not execute sandboxed code until separate approval metadata exists. | tests/services/strategies/test_sandbox_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — add brownfield wrapper/tests before refactor. |
| STRAT-FR-106 | STRATEGY_SANDBOX_REQUIRED error code. | STR-UPG-014: add strategy error taxonomy and mapping | app/services/strategy/config.py; app/services/strategy/base.py; app/services/contracts/strategies.py | Introduce codes/mapping while preserving current ConfigurationError, StrategyPermissionError, and ValueError behavior through adapters. | tests/services/strategies/test_errors_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Gap — not implemented as an explicit first-class boundary yet. |
| STRAT-NFR-001 | Adopt canonical StrategyInput and StrategySignal contracts for all strategy service I/O. | STR-UPG-111: harden contracts boundary for app/services/strategies/contracts/models.py | app/services/contracts/strategies.py; app/services/strategy/config.py | Reuse app.services.contracts.strategies and add missing strategy-domain models/declarations without duplicating broker or risk models. | tests/services/strategies/test_contracts_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-NFR-002 | Enforce canonical flow StrategyInput -> StrategySignal -> RiskDecision -> OrderIntent -> TradeRequest. | STR-UPG-112: harden package_gateway boundary for app/services/strategies/public_api.py | app/services/strategy/__init__.py; app/services/strategy/README.md | Keep singular package imports working; add a controlled plural compatibility facade only after characterization tests pass. | tests/services/strategies/test_package_gateway_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-NFR-003 | Prohibit broker-specific order requests, raw broker payloads, execution commands, and live mutation instructions. | STR-UPG-113: harden execution boundary for app/services/strategies/execution/output_boundary.py | app/services/strategy/base.py; app/services/strategy/pybots/*/strategy.py | Keep BaseStrategy.evaluate and bundled calculate_signals; add output boundary, hook dispatcher, event queue, and worker contracts incrementally. | tests/services/strategies/test_execution_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-NFR-004 | Attach strategy version hash, parameter hash, input dataset hash, signal validity window, confidence, and evidence to every signal. | STR-UPG-114: harden runtime boundary for app/services/strategies/runtime/lineage.py | app/services/strategy/base.py; app/services/strategy/state.py | Preserve BaseStrategy and StrategyState; add resource policy, lineage, transactions, checkpoint compatibility, and cancellation wrappers. | tests/services/strategies/test_runtime_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-NFR-005 | Reject expired, malformed, unsupported, or insufficient-evidence signals before Risk Governance. | STR-UPG-115: harden validation boundary for app/services/strategies/validation/signals.py | app/services/strategy/config.py; app/services/contracts/strategies.py; app/services/strategy/base.py | Harden current validate_strategy_config and MarketContext checks; add bounded payload, injection, data-quality, and readiness validators. | tests/services/strategies/test_validation_brownfield.py; existing compatibility tests stay under tests/unit/app/services/strategy. | Partial — preserve existing code and harden. |
| STRAT-NFR-006 | Tests prove Risk can consume strategy outputs without broker adapter knowledge. | STR-UPG-116: harden verification boundary for tests/services/strategies/ | tests/unit/app/services/strategy/test_strategy_service.py; tests/unit/app/services/strategy/test_trend_following.py; tests/usage/04_strategies.py | Port tests toward tests/services/strategies while preserving existing tests/unit/app/services/strategy coverage and usage examples. | tests/services/strategies/ plus existing tests/unit/app/services/strategy; traceability test maps this requirement. | Partial — preserve existing code and harden. |

## 9. Supplemental Brownfield Tasks

| Task ID | Brownfield task | Why it is needed now | Evidence target |
|---|---|---|---|
| STR-UPG-001 | Add characterization tests for current `app.services.strategy` imports, registry, bundled strategies, and current usage examples. | Prevent accidental breakage before any folder or public API refactor. | `tests/services/strategies/test_current_compatibility.py` |
| STR-UPG-002 | Preserve `app.services.strategy` public imports and optionally add `app.services.strategies` as a compatibility facade. | Old plan uses plural path but current code is singular. | Import parity snapshot. |
| STR-UPG-003 | Verify import-time side effects across `strategy`, `strategy.pybots`, and bundled strategy modules. | `pybots/registry.py` imports all bundled strategies at import time; it must remain lightweight and broker-free. | Import monkeypatch test for no network/filesystem/broker calls. |
| STR-UPG-004 | Align current shared contracts with old-plan canonical models without duplicating risk/trading models. | Current `app.services.contracts.strategies` already owns many canonical models. | JSON-safe contract tests. |
| STR-UPG-005 | Add explicit lookahead-safety and timestamp-alignment guards. | Current code relies on completed bars and `as_of` checks but lacks a named guard/error taxonomy. | Property tests for future perturbation and availability masking. |
| STR-UPG-006 | Harden parameter/config validation with payload bounds and injection rejection. | Current validator covers schema, types, ranges, and unknown top-level keys but not all injection/payload limits. | Malicious config fixture suite. |
| STR-UPG-007 | Wrap current bundled registry with immutable catalog/resolver/lifecycle/provenance layers. | Current registry is useful but too light for lifecycle, approval, and replay evidence. | Registry fixture tests and manifest hash tests. |
| STR-UPG-008 | Add signal/action-intent output boundary tests. | Current BaseStrategy emits TradeIntent objects but no final allowlist boundary rejects broker payloads. | Boundary rejection tests. |
| STR-UPG-009 | Rewrite README and add docs/strategies operating manual. | Current README mixes template, docs, and examples; brownfield plan needs single source of truth. | Documentation checklist. |
| STR-UPG-010 | Make usage examples offline and assertion-backed. | Current usage example calls `get_data(... source="mt5")`, which is not CI-safe unless mocked or gated. | `tests/usage/test_04_strategies.py` |
| STR-UPG-011 | Add final traceability checker for every STRAT-FR and STRAT-NFR row. | Old plan has 112 mapped IDs; brownfield plan must not drop any. | Matrix coverage test. |
| STR-UPG-012 | Add state transaction/checkpoint wrappers around `StrategyState`. | Current state serializes but has no schema/checksum/rollback boundary. | Checkpoint compatibility tests. |
| STR-UPG-013 | Add vectorized/event execution boundary modules as wrappers before splits. | Avoid destructive refactors of `BaseStrategy`. | Existing tests pass plus new wrapper tests. |
| STR-UPG-014 | Introduce strategy error code taxonomy and safe mapping. | Current code raises native exceptions and strings; old plan requires deterministic error codes. | Error mapping decision table. |
| STR-UPG-015 | Add sandbox/raw-code rejection gate. | Simulator must reject arbitrary code; Strategy should supply registry/sandbox validation metadata. | Raw-code payload rejection tests. |
| STR-UPG-016 | Add structured diagnostics and metrics sink interfaces. | Current diagnostics are mostly strings/logs. | Bounded/redacted diagnostics tests. |
| STR-UPG-017 | Add governance evidence contracts only, not approval authority. | Old plan has evidence artifacts but Strategy must not own promotion/risk decisions. | Governance model tests. |


## 10. Testing Strategy

Create or preserve these test areas:

```text
tests/services/strategies/
tests/unit/app/services/strategy/
tests/usage/04_strategies.py
```

Required coverage:

- current imports and `__all__` compatibility;
- public API compatibility between singular/plural package gates, if plural facade is added;
- BaseStrategy lifecycle and schedule behavior;
- parameter validation and malicious config rejection;
- manifest validation;
- bundled registry/catalog behavior;
- every existing bundled strategy;
- template strategy behavior;
- signal generation;
- action intent generation;
- strategy-local state transitions;
- deterministic outputs for identical inputs;
- no mutation of caller-owned data by default;
- insufficient warmup data;
- missing indicator values;
- duplicate timestamps;
- out-of-order timestamps;
- lookahead safety and future perturbation;
- strategy state isolation;
- broker mutation prohibition;
- risk handoff boundary;
- simulator/backtest compatibility;
- JSON-safe public outputs;
- empty data;
- single-row data;
- constant-price data;
- offline usage examples.

Coverage target: total Strategy upgrade coverage >= 80%. Critical contract, lifecycle, validation, output-boundary, and lookahead files should target close to or equal to 100% branch coverage where practical.

## 11. Documentation and README Requirements

Create or update `app/services/strategy/README.md` and add `docs/strategies/OPERATING_MANUAL.md` to cover:

- module boundary;
- singular/plural import compatibility policy;
- supported strategy templates/families;
- public API and compatibility API;
- strategy lifecycle;
- input data expectations;
- indicator dependency expectations;
- output signal/action-intent shape;
- parameter validation;
- manifest format;
- state handling;
- lookahead-safety guarantees;
- deterministic behavior;
- Data/Indicator/Risk/Trading boundaries;
- simulator/backtest usage;
- examples;
- migration notes for downstream modules.

## 12. Definition of Done

The Strategy brownfield upgrade is complete only when:

- existing `app.services.strategy` imports still work;
- any added `app.services.strategies` facade has parity tests;
- all mapped requirements are complete or explicitly deferred with approved rationale;
- all evidence references are added;
- all tests pass;
- coverage is >= 80%;
- critical files have strong branch coverage;
- README and operating manual are updated;
- usage examples are executable offline or safely mocked;
- changelog/migration notes are updated;
- no greenfield destructive rewrite was performed;
- no broker/trading/risk responsibilities leak into Strategy;
- strategy outputs are deterministic and lookahead-safe;
- strategies produce canonical signals/intents rather than direct broker mutations.

## 13. Explicit Non-Goals

Strategies must not own:

- broker connections;
- broker SDK access;
- data provider routing;
- raw market data persistence;
- indicator calculation internals;
- final risk approval;
- live trade execution;
- order lifecycle;
- reconciliation;
- UI/API gateway concerns;
- optimization engine orchestration;
- simulator engine event loop.

## 14. Builder Handoff Prompt

```text
You are Builder for Phase 04 Strategy brownfield upgrade.

Read this file first. Do not delete or replace `app/services/strategy/`. Treat it as the current working implementation. Add tests before refactoring. Preserve all current imports and bundled strategy behavior. Introduce new files only when they create a safer boundary or reduce coupling. Implement tasks in the documented sequence. Keep Strategy broker-neutral, deterministic, lookahead-safe, and risk-governance-bound. Update the requirement coverage matrix as each STRAT-FR/STRAT-NFR row gains evidence. Stop and report if any requirement would require Strategy to own broker execution, final risk approval, simulator event loop, UI/API routing, optimization orchestration, or raw data persistence.
```

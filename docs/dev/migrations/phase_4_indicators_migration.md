# Phase 4 Indicators StandardResponse Migration

> **Plan ID:** `INDI-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/indicators`
> **Migration program:** HaruQuantAI standard public-operation responses
> **Intended reader:** A coding agent with no prior conversation context

## 1. Purpose

This document is the implementation handoff for migrating every qualifying public
Indicators operation to the Utils-owned `StandardResponse[T]` contract. It does not
register operations as AI tools. Tool registration remains a separate allow-list.

Before editing, the coding agent must read `AGENTS.md`, the repository authorities,
the current Indicators feature registry, all affected feature READMEs, and the
current Utils response/error contracts. It must refresh this inventory, issue the
required implementation dry run, identify any plan delta, and wait for a standalone
owner message whose complete trimmed content is `APPROVED: EXECUTE`.

Approval used to create this document does not authorize implementation.

## 2. Governing Rules

Authority order:

1. Owner instructions.
2. `AGENTS.md`.
3. `docs/PROJECT.md`.
4. `docs/ARCHITECTURE.md`.
5. `docs/CHANGELOG.md`.
6. `app/services/indicators/README.md` for the domain feature registry.

The governing migration principle is:

> Every HaruQuantAI-owned public operation that accepts one bounded request and
> produces one completed outcome must return `StandardResponse[T]`, whether or not
> it is registered as an AI tool.

Current `StandardResponse[T]` has exactly:

```text
status
message
data
error
metadata
```

The implemented contract uses `message`, not `content`. `data` contains the exact raw
successful result. Do not wrap it in `{"result": ...}`, `{"payload": ...}`, or a
domain envelope. `metadata.extensions` is only for non-payload evidence formerly
returned beside that raw result. On error, `data` is `None`; `StandardError` contains
exactly `code` and `details`.

Use `build_response_metadata`, `success_response`, `error_response`, and
`exception_response` from `app.utils`. Timing must begin immediately inside the
public boundary, use `time.perf_counter()`, and be emitted in milliseconds rounded to
three decimals by the shared helper.

## 3. Current Domain Shape

The feature registry contains:

- `FEAT-INDI-01`: Core contracts, validation, registry, and result handling.
- `FEAT-INDI-02`: Candle-pattern indicators.
- `FEAT-INDI-03`: Trend indicators.
- `FEAT-INDI-04`: Momentum indicators.
- `FEAT-INDI-05`: Volatility indicators.
- `FEAT-INDI-06`: Volume indicators.

The package root is the only documented stable import surface. Leaf modules remain
implementation details even when they have local exports.

The successful formula result is normally `IndicatorResult`, which must remain the
object in `StandardResponse.data`. Its frame, warmup evidence, manifest evidence, and
other business fields must not be split into extensions. `IndicatorResult.join_to`
must place its raw `pandas.DataFrame` result directly in `data`.

## 4. Public Operation Inventory

The baseline contains 28 qualifying operations.

### 4.1 Core registry and validation

| Operation | Current raw result | Required `data` |
|---|---|---|
| `get_capability_matrix` | Capability mapping | The same mapping |
| `get_indicator` | Registered indicator callable/specification | The same returned object |
| `get_warmup_requirement` | `WarmupRequirement` | The same object |
| `list_indicators` | Registered indicator collection | The same collection |
| `validate_indicator` | Validated indicator evidence | The same result |
| `IndicatorProtocol.calculate` | `IndicatorResult` | The same `IndicatorResult` |
| `IndicatorResult.join_to` | `pandas.DataFrame` | The same `DataFrame` |

Protocol annotations, registry-held callables, concrete functions, test doubles, and
consumer annotations must agree on `StandardResponse[IndicatorResult]`.

### 4.2 Candle patterns

- `doji`
- `engulfing`
- `inside_bar`
- `pinbar`

Each successful response contains the complete `IndicatorResult` in `data`.

### 4.3 Trend

- `adx`
- `bollinger_bands`
- `ema`
- `hull_ma`
- `sma`
- `wma`
- `zigzag`

### 4.4 Momentum

- `rsi`
- `williams_r`

### 4.5 Volatility

- `adr`
- `atr`
- `rolling_volatility`
- `standard_deviation`

### 4.6 Volume

- `cmf`
- `mfi`
- `obv`
- `price_volume_distribution`

### 4.7 Explicit exclusions

- Exported data-model constructors are constructors, not completed public operations.
- Properties and field access are unchanged.
- `guard_public_boundary` is internal and is not exported.
- Internal validation, formula, and registry helpers are unchanged unless required
  to keep a migrated public boundary correct.

If the refreshed root export differs, stop and issue a plan delta before adding or
removing operations.

## 5. Error Migration

Indicators currently owns `IndicatorErrorCode`, `IndicatorError`, and the
`guard_public_boundary` decorator in `app/services/indicators/core/errors.py`.

Create one focused Indicators-owned immutable catalogue, preferably
`app/services/indicators/core/error_catalog.py`, using Utils `ErrorDefinition`.
Retain all current codes exactly:

- `IND_INVALID_CONFIG`
- `IND_INVALID_PARAMETER`
- `IND_UNSUPPORTED_INDICATOR`
- `IND_UNSUPPORTED_TIMEFRAME`
- `IND_UNSUPPORTED_DTYPE`
- `IND_INVALID_INPUT_SCHEMA`
- `IND_MISSING_REQUIRED_COLUMN`
- `IND_INVALID_OUTPUT_COLUMN`
- `IND_OUTPUT_COLUMN_CONFLICT`
- `IND_INVALID_OUTPUT_MODE`
- `IND_INPUT_MUTATION_DETECTED`
- `IND_DUPLICATE_TIMESTAMP`
- `IND_NON_MONOTONIC_TIME`
- `IND_AMBIGUOUS_TIMESTAMP`
- `IND_INVALID_TIMEZONE`
- `IND_INVALID_OHLC`
- `IND_INSUFFICIENT_DATA`
- `IND_LOOKAHEAD_RISK`
- `IND_FORMULA_VERSION_MISMATCH`
- `IND_RESOURCE_LIMIT_EXCEEDED`
- `IND_PARTIAL_RESULT`
- `IND_INTERNAL_ERROR`

For each definition, record a safe description, severity, retryability, and operator
action. Validate the detached catalogue with Utils catalogue validation.

The public-boundary decorator must be replaced or adapted so it returns a response:

- Successful formula execution becomes `success_response(raw_indicator_result, ...)`.
- Deliberate `IndicatorError` becomes an error response using its exact code.
- Its safe message becomes `StandardResponse.message`.
- Its bounded structured evidence becomes `error.details`.
- Unexpected `Exception` becomes `IND_INTERNAL_ERROR` with only safe exception class
  and operation identifiers.
- `KeyboardInterrupt`, `SystemExit`, and other `BaseException` subclasses continue to
  propagate.
- No raw pandas/NumPy exception message, frame values, credentials, or caller payload
  may enter logs or response details.

The migration must not retain a second generic response envelope.

## 6. Metadata Policy

Common values:

- `domain="indicators"`.
- `places_trade=False`.
- `modifies_database=False`.
- `writes_file=False`.
- `requires_network=False` for all pure registry/formula/result operations.
- Preserve supplied request/correlation IDs; otherwise use shared canonical ID
  generation.

| Operation family | Risk | Read only | Extensions |
|---|---|---:|---|
| Registry discovery | `none` | Yes | Registry or formula version only if already returned |
| Validation/warmup | `low` | Yes | Existing validation version/evidence only |
| Indicator calculations | `low` | Yes | Existing non-result execution evidence only |
| `IndicatorResult.join_to` | `low` | Yes | Join/output-mode evidence only if previously returned |

Do not duplicate indicator values, columns, frames, manifests, or warmup objects in
extensions. They remain part of the raw result.

## 7. Dependency and Consumer Coordination

Phase 3 Data is an upstream prerequisite. Any Indicators caller of migrated Data
operations must inspect `response.status`, handle `response.error`, and consume
`response.data`; it must not pass a `StandardResponse` where a frame or dataset is
expected.

Known downstream domains include Strategy, Simulation, Research, and any tests or
examples importing the root Indicators port. Update them only where required to keep
Indicators integration tests passing. Broad downstream migrations belong to their
own phases.

Registry contracts need special care: if `get_indicator` returns a callable, that
callable's annotation and behavior must match the migrated calculation contract.

## 8. Implementation Work Packages

### INDI-WP1 — Refresh and freeze the boundary

1. Reconcile root `__all__`, README public API, feature registries, tests, and usage.
2. Record every current return type and all non-payload evidence.
3. Add failing boundary tests proving all 28 operations return exactly five fields.
4. Confirm frame/object identity expectations before wrapping.

### INDI-WP2 — Catalogue and boundary adapter

1. Add the domain-owned Utils-shaped error catalogue.
2. Validate all enum values are present exactly once.
3. Adapt `guard_public_boundary` to construct metadata and response objects.
4. Preserve public signatures with `functools.wraps` and correct generic annotations.
5. Add success, known-error, unexpected-error, redaction, and timing tests.

### INDI-WP3 — Core operations

Migrate registry, validation, warmup, protocol, and result join operations first.
Update `app/services/indicators/core/README.md`, its `FR-*` entries, unit tests, and
`tests/indicators/usage/01_core.py`.

### INDI-WP4 — Formula families

Migrate in dependency order:

1. Candle patterns.
2. Trend.
3. Momentum.
4. Volatility.
5. Volume.

For every feature, update its README registry row, public signatures, unit tests, and
one numbered usage program. Do not alter formulas, warmup semantics, column names,
input mutation rules, or numerical tolerances.

### INDI-WP5 — Consumers and documentation

1. Update internal and required cross-domain consumers.
2. Update root exports only if the contract names change; do not broaden them.
3. Update `app/services/indicators/README.md` as the canonical current-state registry.
4. Update `docs/PROJECT.md` or `docs/ARCHITECTURE.md` only for actual cross-domain
   contract changes.
5. Add one concise `Changed` entry under `docs/CHANGELOG.md` `[Unreleased]`.

## 9. Tests and Usage Evidence

At minimum add or update:

- `tests/indicators/unit/test_public_api.py`
- `tests/indicators/unit/test_errors.py`
- `tests/indicators/unit/test_contracts.py`
- `tests/indicators/unit/test_results.py`
- `tests/indicators/integration/test_registry_workflow.py`
- `tests/indicators/integration/test_usage_scripts.py`
- All six numbered programs under `tests/indicators/usage/`

Assertions must cover exact top-level keys, raw result identity/type, metadata,
monotonic duration shape, catalogue completeness, known and unexpected failures,
redaction, JSON serialization, registry-held callable behavior, and no input
mutation.

Suggested final validation:

```powershell
uv run ruff check app/services/indicators tests/indicators
uv run ruff format --check app/services/indicators tests/indicators
uv run mypy app/services/indicators tests/indicators
uv run pytest tests/indicators
uv run python tests/indicators/usage/01_core.py
uv run python tests/indicators/usage/02_candles.py
uv run python tests/indicators/usage/03_trend.py
uv run python tests/indicators/usage/04_momentum.py
uv run python tests/indicators/usage/05_volatility.py
uv run python tests/indicators/usage/06_volume.py
```

Run targeted files during development. Preserve the existing numerical golden
fixtures and performance behavior.

## 10. Risks, Boundaries, and Rollback

Primary risks:

- Decorated functions may accidentally report their wrapper name or lose annotations.
- Registry callables may return nested responses if both registry and function wrap.
- DataFrame/Pydantic serialization may replace raw runtime identity.
- Formula changes could be introduced accidentally during mechanical migration.
- Downstream consumers may treat a response object as an `IndicatorResult`.

Explicitly excluded:

- Formula redesign or numerical optimization.
- New indicators.
- AI-tool registration.
- Broader package exports.
- Unrelated Data, Strategy, Simulation, or Research refactors.

Rollback the implementation by reverting only the affected Indicators source, tests,
usage programs, registry documentation, and required consumer edits; remove the new
catalogue/export if introduced; then rerun the pre-migration Indicators gate.

## 11. Completion Checklist

- [ ] All 28 refreshed public operations return `StandardResponse[T]`.
- [ ] Every successful raw result is directly in `data`.
- [ ] All 22 error codes use a validated Indicators-owned catalogue.
- [ ] Known and unexpected failures are safe error responses.
- [ ] Metadata is accurate and execution time is monotonic.
- [ ] Protocols, registry callables, consumers, mocks, and examples agree.
- [ ] All affected `FR-*` rows and usage evidence cite exact code paths and lines.
- [ ] Targeted and full Indicators validation passes.
- [ ] Scope, commands, decisions, dependencies, and rollback are reported.

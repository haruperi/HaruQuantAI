# Phase 5 Strategy StandardResponse Migration

> **Plan ID:** `STR-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/strategy`
> **Migration program:** HaruQuantAI standard public-operation responses
> **Intended reader:** A coding agent with no prior conversation context

## 1. Purpose and Approval Boundary

Migrate each qualifying Strategy public operation to Utils
`StandardResponse[T]`, preserving every raw result and every safe field currently
carried by `StrategyOutcome[T]` or `StrategyError`.

This document is a plan. The receiving coding agent must read `AGENTS.md`,
`docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`,
`app/services/strategy/README.md`, all affected feature READMEs, and the current
Utils response/error implementation. It must refresh the plan, issue a dry run, and
wait for a new standalone `APPROVED: EXECUTE`.

## 2. Standard Contract

The governing principle applies to bounded public operations whether or not they
become AI tools. The exact response fields are `status`, `message`, `data`, `error`,
and `metadata`.

Rules:

- Use the current Utils factories and metadata builder.
- Put the successful Strategy result directly in `data`.
- Do not put a `StrategyOutcome`, `result`, or `payload` wrapper in `data`.
- Use only `success` or `error` for response status.
- Keep business states such as `ACCEPTED`, `IDEMPOTENT`, and `REJECTED` inside the
  raw `StrategyMutationResult`; they are not response statuses.
- Preserve former non-payload envelope evidence in `metadata.extensions`.
- Preserve safe domain failure evidence in `error.details`.
- Use monotonic elapsed timing rounded to three decimals.

## 3. Feature and Public Boundaries

Feature order:

1. `FEAT-STR-01` contracts.
2. `FEAT-STR-02` diagnostics.
3. `FEAT-STR-03` registry.
4. `FEAT-STR-04` intents.
5. `FEAT-STR-05` replay.
6. `FEAT-STR-06` checkpoints.
7. `FEAT-STR-07` vectorized execution.
8. `FEAT-STR-08` event execution.
9. `FEAT-STR-09` signal boundary.
10. `FEAT-STR-10` concrete evaluator library.

The package root is the authoritative public port. Constructors, data model
properties, private helpers, migration definitions, and registry persistence
internals are excluded unless the refreshed feature registry explicitly classifies
them as public operations.

## 4. Public Operation Inventory

The baseline contains 23 operations.

### 4.1 Public functions

| Feature | Operations | Required raw `data` |
|---|---|---|
| Registry validation | `validate_strategy_ref`, `validate_strategy_config` | Existing validated reference/configuration |
| Registry queries/mutations | `list_strategy_versions`, `register_strategy_version`, `update_strategy_parameters` | Existing listing or `StrategyMutationResult` |
| Intents | `build_trade_intent` | Existing `TradeIntent` |
| Replay | `create_strategy_replay_manifest` | Existing `StrategyReplayManifest` |
| Checkpoints | `create_strategy_checkpoint`, `validate_strategy_checkpoint` | Existing checkpoint/validated checkpoint result |
| Vectorized | `run_vectorized_strategy_signals` | Existing `StrategyExecutionResult` |
| Event | `run_event_strategy_hook` | Existing event execution result |
| Signals | `evaluate_strategy_signals` | Existing decision/signal result |
| Diagnostics | `export_strategy_diagnostics` | Existing diagnostics/export result |

### 4.2 Public evaluator methods

Migrate the public method on each exported evaluator:

- `SignalEvaluator.evaluate_signals`
- `VectorizedStrategyEvaluator.evaluate_vectorized`
- `EventStrategyEvaluator.evaluate_event`
- `DecomposingTradeEvaluator.evaluate_signals`
- `HarrietHedgingEvaluator.evaluate_signals`
- `MarketStructureEvaluator.evaluate_signals`
- `NaiveMATrendEvaluator.evaluate_signals`
- `RandomWalkEvaluator.evaluate_signals`
- `SQXBreakoutAtrTrailingEvaluator.evaluate_signals`
- `WhiteFairyEvaluator.evaluate_signals`

All protocol and implementation annotations must return the same
`StandardResponse[raw-result-type]`. Do not wrap a response again when a runner calls
an evaluator; unwrap and propagate deliberately at each bounded public boundary.

## 5. Legacy Envelope Mapping

`app/services/strategy/contracts/outcomes.py` currently defines:

- `StrategyOutcome[T]`: `status`, `data`, `error`.
- `StrategyError`: `contract_version`, `schema_id`, `code`, `message`, `details`,
  `request_id`, `correlation_id`.
- `success`, `failure`, and `propagate_failure` helpers.

Migration mapping:

| Legacy evidence | Destination |
|---|---|
| `StrategyOutcome.data` | Directly `StandardResponse.data` |
| `StrategyOutcome.status` | Standard status; do not preserve duplicate `success/error` |
| `StrategyError.code` | `StandardError.code` |
| `StrategyError.message` | `StandardResponse.message` |
| `StrategyError.details` | `StandardError.details` |
| Error request/correlation IDs | Canonical `ResponseMetadata` identifiers |
| Error contract/schema identity | `metadata.extensions` only when needed for compatibility |
| Mutation business status | Remains in raw `StrategyMutationResult` |

Retire `StrategyOutcome[T]` as a generic public envelope after all producers and
consumers migrate. Do not remove it while reachable public annotations or consumers
still depend on it. A temporary internal compatibility adapter is allowed only if it
has an explicit removal step and cannot leak at the root API.

The helper functions in `outcomes.py` are not root public operations; replace their
internal use with focused Utils factory/adaptation helpers and then remove or
deprecate them according to the refreshed dependency graph.

## 6. Strategy Error Catalogue

Create one Strategy-owned immutable catalogue using Utils `ErrorDefinition`, while
preserving all approved codes:

- `STRATEGY_INVALID_CONFIG`
- `STRATEGY_NOT_FOUND`
- `STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE`
- `STRATEGY_DEPRECATED`
- `STRATEGY_UNAPPROVED_MODULE`
- `STRATEGY_SCHEMA_VALIDATION_FAILED`
- `STRATEGY_UNSUPPORTED_TIMING_POLICY`
- `STRATEGY_LOOKAHEAD_DETECTED`
- `STRATEGY_ARBITRARY_CODE_REJECTED`
- `STRATEGY_INTERNAL_ERROR`
- `STRATEGY_LIFECYCLE_NOT_APPROVED`
- `STRATEGY_ENVIRONMENT_NOT_PERMITTED`
- `STRATEGY_ARTIFACT_HASH_MISMATCH`
- `STRATEGY_DEPENDENCY_HASH_MISMATCH`
- `INDICATOR_MODULE_ERROR`
- `STRATEGY_CHECKPOINT_INVALID`
- `STRATEGY_CHECKPOINT_INCOMPATIBLE`
- `STRATEGY_DATA_NOT_READY`
- `STRATEGY_INDICATOR_NOT_READY`
- `STRATEGY_MISSING_REQUIRED_DATA`
- `STRATEGY_STALE_DATA`
- `STRATEGY_DUPLICATE_INTENT`
- `STRATEGY_RESOURCE_LIMIT_EXCEEDED`
- `STRATEGY_TIMEOUT`
- `STRATEGY_VALIDATION_ARTIFACT_REQUIRED`
- `STRATEGY_RISK_PROFILE_REQUIRED`
- `STRATEGY_POSITION_LIMIT_EXCEEDED`
- `STRATEGY_DATA_QUALITY_GATE_FAILED`
- `STRATEGY_HARD_KILLED`

`INDICATOR_MODULE_ERROR` remains Strategy-owned only if the current Strategy
contract deliberately exposes that exact translated code. Do not silently substitute
an Indicators code or duplicate Indicators catalogue policy.

Known Strategy failures become error responses. Unexpected exceptions must map to
`STRATEGY_INTERNAL_ERROR` with safe exception type/operation evidence only. Security,
arbitrary-code, lifecycle, environment, and hard-kill failures remain fail-closed.

## 7. Metadata Policy

Common declarations:

- `domain="strategy"`.
- `places_trade=False`; Strategy produces decisions/intents and does not execute.
- `requires_network=False` for deterministic validation/evaluation.
- File/database flags must reflect concrete registry, checkpoint, or diagnostic
  persistence behavior rather than function naming.

| Operation family | Risk | Read only | Possible side effects/extensions |
|---|---|---:|---|
| Validation/listing | `low` | Yes | Registry/version evidence |
| Evaluators/runners | `medium` | Yes | Evaluator/version/timing-policy evidence |
| Intent construction | `medium` | Yes | Strategy reference and decision evidence |
| Registry mutation | `high` | No | Mutation/audit/publication evidence; DB flag if persisted |
| Checkpoint creation | `medium` | No | Artifact/hash evidence; file/DB flag as implemented |
| Diagnostics export | `low` | Depends | Export reference/hash; `writes_file` if written |

Raw decisions, signals, intents, manifests, checkpoints, diagnostics, and mutation
results remain in `data`, not extensions.

## 8. Dependencies and Consumers

Prerequisites:

- Phase 3 Data response migration.
- Phase 4 Indicators response migration.

Strategy must unwrap upstream responses explicitly:

1. Check `status`.
2. Translate an approved upstream failure to a Strategy code without losing safe
   upstream code evidence.
3. Consume `data` only on success.
4. Never pass a response object to formula/evaluator logic expecting a frame or
   `IndicatorResult`.

Downstream consumers include Risk, Trading, Simulation, Optimization, Portfolio, and
Research handoffs. Update only direct consumers required for Strategy correctness;
their broad public migrations belong to later phases.

## 9. Implementation Order

### STR-WP1 — Baseline tests

Freeze raw result types, object equality/identity where relevant, error mappings,
side effects, and the root operation inventory. Add boundary tests that initially
fail for non-standard returns.

### STR-WP2 — Shared Strategy migration infrastructure

1. Add and validate the Strategy error catalogue.
2. Add focused private response construction/translation helpers only if repeated
   logic justifies them.
3. Update `StrategyError` use sites and trace propagation.
4. Define the staged retirement of `StrategyOutcome`, `success`, `failure`, and
   `propagate_failure`.

### STR-WP3 — Pure validation and diagnostics

Migrate validation, listing, and diagnostics operations first. Confirm exact raw
outputs and JSON serialization.

### STR-WP4 — Registry, replay, and checkpoints

Migrate mutations and persistence-aware operations transactionally. Preserve
idempotency, immutable versioning, hashes, publication status, and audit references.

### STR-WP5 — Evaluation boundaries

Migrate vectorized, event, signal, and all concrete evaluator methods. Update
protocols, runners, registry callables, mocks, and consumers together.

### STR-WP6 — Intent and downstream handoff

Migrate `build_trade_intent`, then update Risk/Trading/Simulation handoffs to consume
the raw intent from `response.data`.

### STR-WP7 — Documentation and envelope removal

Update the root and feature READMEs with exact `FR-*`, contracts, requirements,
public API, and usage paths. Remove the generic envelope only after repository-wide
search proves no live reference. Add an `[Unreleased]` changelog entry.

## 10. Test and Usage Plan

Required coverage includes:

- Exact five-field responses for all 23 operations.
- Direct raw result placement.
- All 29 Strategy error codes.
- Trace propagation and safe redaction.
- Mutation business statuses remaining unchanged.
- Registry/checkpoint idempotency.
- Protocol/concrete evaluator compatibility.
- Data/Indicators upstream success and failure translation.
- No arbitrary module/code execution regression.

Primary files:

- `tests/strategy/unit/test_outcomes.py`
- `tests/strategy/unit/test_errors.py`
- `tests/strategy/unit/test_public_api.py`
- `tests/strategy/unit/test_event_runner.py`
- `tests/strategy/unit/test_vectorized_runner.py`
- All concrete evaluator tests
- `tests/strategy/integration/test_contract_compatibility.py`
- `tests/strategy/integration/test_runtime_boundary.py`
- `tests/strategy/integration/test_usage_scripts.py`
- All ten numbered programs under `tests/strategy/usage/`

Suggested final commands:

```powershell
uv run ruff check app/services/strategy tests/strategy
uv run ruff format --check app/services/strategy tests/strategy
uv run mypy app/services/strategy tests/strategy
uv run pytest tests/strategy
uv run python tests/strategy/usage/01_contracts.py
uv run python tests/strategy/usage/02_diagnostics.py
uv run python tests/strategy/usage/03_registry.py
uv run python tests/strategy/usage/04_intents.py
uv run python tests/strategy/usage/05_replay.py
uv run python tests/strategy/usage/06_checkpoints.py
uv run python tests/strategy/usage/07_vectorized.py
uv run python tests/strategy/usage/08_event.py
uv run python tests/strategy/usage/09_signals.py
uv run python tests/strategy/usage/10_strategy_library.py
```

## 11. Risks, Exclusions, and Rollback

Risks:

- Nested responses between runners and evaluators.
- Loss of request/correlation identity during legacy-envelope removal.
- Confusing mutation status with response status.
- Breaking registry callable protocols.
- Changing signal timing, lookahead protections, or strategy decisions.

Excluded:

- New strategies or evaluator behavior.
- Changes to trading authorization.
- AI-tool registration.
- Arbitrary-code support.
- Broad downstream-domain refactors.

Rollback only the approved Strategy source, tests, usage programs, consumer
coordination, and authoritative documentation. Restore legacy exports only as a
coherent unit; then rerun the pre-migration Strategy gate.

## 12. Completion Checklist

- [ ] All 23 refreshed operations return `StandardResponse[T]`.
- [ ] Raw outputs remain directly in `data`.
- [ ] All 29 codes have validated Strategy-owned definitions.
- [ ] `StrategyOutcome[T]` no longer crosses the public boundary.
- [ ] Mutation and evaluation semantics are unchanged.
- [ ] Upstream and downstream consumers are coordinated.
- [ ] Exact `FR-*` and usage evidence paths/lines are updated.
- [ ] Quality, typing, tests, usage programs, and coverage pass.

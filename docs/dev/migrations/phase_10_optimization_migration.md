# Phase 10 Optimization StandardResponse Migration

> **Plan ID:** `OPT-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/optimization`
> **Migration program:** HaruQuantAI standard public-operation responses

## 1. Purpose and Approval Gate

Migrate the ten official Optimization operations to Utils
`StandardResponse[T]`, preserving exact advisory evidence, scores, rankings,
robustness results, walk-forward results, hashes, caveats, and handoffs.

The implementation agent must read all repository authorities, the Optimization
README and feature registries, `public_api/`, Utils responses/errors, and current
Simulation/Analytics/Strategy contracts. It must refresh the inventory, issue the
required dry run, and wait for a new standalone `APPROVED: EXECUTE`.

Optimization remains advisory. It must not mutate Strategy state, place trades, or
claim live readiness.

## 2. Standard Contract

The response top level is exactly `status`, `message`, `data`, `error`, and
`metadata`.

- The existing Optimization result/evidence object goes directly in `data`.
- Do not put it under `result` or `payload`.
- Keep business evidence such as pass rates, scores, ranks, overfit labels, caveats,
  or handoff state inside the raw result model.
- Put only former non-payload context in extensions.
- Domain/technical failure uses a catalogue-approved standard error.
- Use shared monotonic duration measurement.

## 3. Authoritative Public Boundary

The root `app.services.optimization` port intentionally exposes ten official
operations and the `OFFICIAL_OPTIMIZATION_TOOLS` name tuple.

Feature subpackages expose many implementation functions through local `__all__`
values, but the domain README defines the root public API as narrow and typed.
Therefore this phase migrates only the ten official operations. It does not convert
every internal search, scoring, persistence, validation, and evidence helper.

If the owning README or root registry is deliberately broadened before coding, issue
a plan delta with the additional operation inventory and consumer impact.

## 4. Public Operation Inventory

### 4.1 Search and validation orchestration

- `run_parameter_sweep`
- `run_walk_forward_optimization`
- `run_walk_forward_matrix`
- `run_robustness_analysis`

The existing `SearchSummary`, walk-forward result, matrix, or robustness result
remains raw `data`.

### 4.2 Comparison and scoring

- `compare_optimization_runs`
- `calculate_parameter_stability`
- `detect_overfit_parameters`
- `rank_parameter_sets`
- `calculate_robustness_score`

Preserve ordering, deterministic tie breaking, unavailable evidence, score
definitions, sample sufficiency, overfit caveats, and Decimal/float behavior exactly.

### 4.3 Handoff

- `build_optimization_handoff`

Return the existing advisory handoff directly in `data`. This operation must not
submit a Strategy parameter update or mutate a registry.

### 4.4 Explicit exclusions

- `OFFICIAL_OPTIMIZATION_TOOLS` is data, not an operation.
- `OptimizationError.to_payload` is not part of the package-root domain port.
- Local functions in `parameters/`, `scoring/`, `search/`, `execution/`,
  `robustness/`, `state/`, `evidence/`, and `validation/` remain internal call
  seams.
- Constructors, validators, stores, adapter protocols, migrations, and properties
  are unchanged unless required internally to consume migrated upstream responses.

Internal helpers continue returning their current raw types. The official public
operation wraps only once at its outer boundary.

## 5. Error Catalogue Migration

Replace `OPTIMIZATION_ERROR_CODES` with an immutable Optimization-owned catalogue
using Utils `ErrorDefinition`. Preserve all ten codes:

- `OPT_ADAPTER_INCOMPATIBLE`
- `OPT_CONSTRAINT_INVALID`
- `OPT_EVIDENCE_INCOMPLETE`
- `OPT_EXECUTION_FAILED`
- `OPT_INTERNAL_ERROR`
- `OPT_INVALID_REQUEST`
- `OPT_LEAKAGE_DETECTED`
- `OPT_LIMIT_EXCEEDED`
- `OPT_PERSISTENCE_FAILED`
- `OPT_STATE_CONFLICT`

Each definition records a safe description, severity, retryability, and operator
action. Validate completeness against every constructed `OptimizationError`.

At the official boundary:

- `OptimizationError.code` becomes `StandardError.code`.
- Symbolic `detail` and redacted `safe_details` become structured error details.
- The catalogue description supplies a stable response message.
- Unexpected exceptions become `OPT_INTERNAL_ERROR` with safe type/operation
  evidence only.
- Adapter failures use the most precise approved code and preserve safe upstream
  domain/code evidence.
- Leakage, limit, state conflict, and adapter incompatibility remain fail closed.

Do not move Optimization-specific policy into Utils.

## 6. Metadata Policy

Common:

- `domain="optimization"`.
- `places_trade=False`.
- `modifies_database=False` and `writes_file=False` for the ten current advisory
  operations unless refreshed implementation performs a direct persisted write.
- `requires_network` reflects the concrete injected Simulation/Analytics adapter;
  use a conservative true value if the public operation can invoke a remote adapter.

| Operations | Risk | Read only | Extensions |
|---|---|---:|---|
| Comparison/stability/scoring/ranking | `low` | Yes | Metric/catalog/version evidence not in raw result |
| Overfit/robustness assessment | `medium` | Yes | Seed/trial-policy evidence only when separate |
| Parameter sweep/walk-forward | `medium` | Yes | Adapter/run IDs and bounded execution summary outside raw result |
| Handoff construction | `high` | Yes | Strategy target/version and approval-required marker |

Raw candidates, scores, rankings, folds, robustness rows, and handoff objects are not
extensions.

## 7. Cross-Domain Coordination

Prerequisites:

- Simulation public response migration.
- Analytics public response migration.
- Strategy public contracts for handoff targets.

Official operations that call injected adapters must:

1. Verify the upstream response shape/status.
2. Translate errors into approved Optimization codes.
3. Consume raw data once.
4. Preserve safe upstream request/run identifiers.
5. Never score a failed candidate as zero.
6. Never treat missing evidence as successful evidence.

Downstream Portfolio or UI/API consumers must unwrap Optimization data explicitly and
must not interpret response success as approval to deploy parameters.

## 8. Implementation Work Packages

### OPT-WP1 — Freeze official behavior

Characterize all ten official signatures, raw results, deterministic ordering,
hashes, limits, failures, adapter calls, and non-side-effect guarantees.

### OPT-WP2 — Error catalogue and boundary helper

Create the validated catalogue and one focused private decorator/helper for the ten
operations if it avoids duplication while preserving signatures and typing.

### OPT-WP3 — Pure official calculations

Migrate comparison, stability, overfit detection, ranking, and robustness score.
Verify exact numeric and caveat parity.

### OPT-WP4 — Adapter-backed orchestration

Migrate sweep, walk-forward optimization, matrix, and robustness analysis. Update
Simulation/Analytics adapters and mocks to unwrap upstream responses.

### OPT-WP5 — Handoff

Migrate handoff construction and verify it remains advisory, immutable, versioned,
and unable to mutate Strategy.

### OPT-WP6 — Documentation

Update the root and all affected feature registry rows with exact `FR-*`, public
contract, usage evidence paths/lines, dependency changes, and `[Unreleased]`.
Preserve the narrow root API statement.

## 9. Tests and Usage

Required:

- Exact five-field response for all ten official operations.
- Direct raw result placement.
- All ten catalogue codes and redaction.
- Deterministic order/tie/hash/seed behavior.
- Bound enforcement and leakage rejection.
- Failed candidates never become zero scores.
- Upstream Simulation/Analytics error translation.
- No Strategy mutation, persistence, or trade side effect.

Primary suites:

- `tests/optimization/unit/test_public_api_operations.py`
- `tests/optimization/unit/test_public_api_validation.py`
- `tests/optimization/unit/test_errors.py`
- Scoring, robustness, walk-forward, and handoff unit suites
- `tests/optimization/integration/test_public_api_workflow.py`
- `test_bounded_sweep.py`
- `test_walk_forward.py`
- `test_robustness_workflow.py`
- `test_evidence_workflow.py`
- `test_usage_scripts.py`
- `tests/optimization/usage/09_public_api.py`

Final gate:

```powershell
uv run ruff check app/services/optimization tests/optimization
uv run ruff format --check app/services/optimization tests/optimization
uv run mypy app/services/optimization tests/optimization
uv run pytest tests/optimization
Get-ChildItem tests/optimization/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

## 10. Risks, Exclusions, and Rollback

Risks:

- Accidentally wrapping internal helpers and creating nested responses.
- Altering deterministic ranking or hashes.
- Losing candidate-level failure evidence.
- Treating advisory handoff success as deployment approval.

Excluded:

- Expanding the official API.
- New optimizers/objectives/robustness methods.
- Strategy mutation.
- Live trading.
- AI-tool registration decisions.

Rollback the ten public operations, catalogue, direct adapters/consumers, tests,
examples, and active documentation as a coherent unit. Internal raw helpers should
remain untouched wherever possible.

## 11. Completion Checklist

- [ ] All ten refreshed official operations return `StandardResponse[T]`.
- [ ] Internal helpers remain raw and the outer boundary wraps once.
- [ ] Raw official results are direct `data`.
- [ ] All ten errors use a validated Optimization catalogue.
- [ ] Determinism and advisory-only behavior remain intact.
- [ ] Upstream adapters and downstream consumers are coordinated.
- [ ] Exact `FR-*` and usage evidence are updated.
- [ ] Full validation passes.

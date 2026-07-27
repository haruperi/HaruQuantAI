# Phase 12 Research StandardResponse Migration

> **Plan ID:** `RES-001`
> **Document status:** Approved planning artifact; implementation not authorized
> **Prepared:** 2026-07-27
> **Target domain:** `app/services/research`
> **Migration program:** HaruQuantAI standard public-operation responses

## 1. Purpose and Gate

Migrate the currently classified stable Research operation,
`run_edge_lab_profile`, to Utils `StandardResponse[ResearchReport]`, preserving the
complete advisory report and every Research safety boundary.

The coding agent must read the repository authorities, the Research README and all
12 feature specifications, `PUBLIC_API_CLASSIFICATIONS`, current Utils contracts,
upstream Data/Indicators/Analytics contracts, source/tests/usage, and the
Research-to-Strategy system test. It must refresh this inventory, issue a dry run,
and wait for a new standalone `APPROVED: EXECUTE`.

Research remains advisory and must not submit Strategy changes, trade, schedule,
perform provider reads, or persist artifacts through this operation.

## 2. Standard Contract

`StandardResponse[T]` contains exactly `status`, `message`, `data`, `error`, and
`metadata`.

- The complete `ResearchReport` is directly in `data`.
- Do not split stages, warnings, scorecards, profiles, or evidence into extensions
  when they already belong to the report.
- Preserve only separate orchestration evidence in extensions.
- Known Research failures become catalogue-approved errors.
- Unexpected exceptions become a safe internal Research error selected during
  catalogue reconciliation.
- Timing uses the shared monotonic helper.

## 3. Public API Classification Boundary

`app/services/research/contracts/api.py` classifies every package-root `__all__` name
as stable. The root contains many contract classes but only one callable operation:

- `run_edge_lab_profile`

Feature module `__init__.py` files expose approved feature APIs for domain-internal
composition and direct feature usage, but they are not package-root domain
operations under the current classification contract. This phase therefore migrates
one operation.

It does not mechanically wrap the many functions in `data/`, `features/`,
`leakage/`, `metrics/`, `statistics/`, `studies/`, `seasonality/`,
`market_structure/`, `modeling/`, `profiles/`, and `artifacts/`.

If the owner intends those feature-module callables to become system-wide public
operations, that is a material API expansion requiring a new inventory and plan
delta before implementation.

## 4. Operation Mapping

Current contract:

```text
run_edge_lab_profile(
    dataset: MarketDataset,
    *,
    hypothesis: str,
    config: EdgeLabConfig,
    performance: PerformanceReport | None = None,
) -> ResearchReport
```

Required contract:

```text
run_edge_lab_profile(...) -> StandardResponse[ResearchReport]
```

Success:

- `data` is the exact final `ResearchReport`.
- `message` is a stable bounded completion summary.
- `metadata.operation` identifies `run_edge_lab_profile`.
- Extensions may include selected-stage names or an orchestration version only if
  not already represented in the report.

Failure:

- `data=None`.
- Preserve the exact approved Research code.
- Preserve only safe symbolic detail/evidence.
- Do not expose frame values, hypothesis text, feature values, model internals,
  artifact contents, credentials, or raw exception messages.

The internal stage functions keep raw returns. The root workflow wraps once after all
selected stages complete.

## 5. Error Catalogue Reconciliation

Research currently raises Utils exception classes with Research-specific codes
distributed across features. Create one Research-owned immutable catalogue using
Utils `ErrorDefinition`, then make every reachable code explicit.

The README currently documents:

Configuration:

- `RES_CONFIGURATION_INVALID`
- `RES_STAGE_DEPENDENCY_INVALID`

Validation:

- `RES_INPUT_INVALID`
- `RES_INSUFFICIENT_DATA`
- `RES_NONFINITE_DATA`
- `RES_RESOURCE_LIMIT_EXCEEDED`
- `RES_VERSION_INCOMPATIBLE`
- `RES_MODEL_FIT_FAILED`

Security:

- `RES_PERMISSION_DENIED`
- `RES_LEAKAGE_DETECTED`
- `RES_ARTIFACT_PATH_REJECTED`
- `RES_SENSITIVE_OUTPUT_REJECTED`

Artifact/system:

- `RES_ARTIFACT_CONFLICT`
- `RES_ARTIFACT_TOO_LARGE`
- `RES_ARTIFACT_ATOMICITY_UNAVAILABLE`
- `RES_ARTIFACT_WRITE_FAILED`
- `RES_AUDIT_PERSISTENCE_FAILED`

Current workflow code and `FR-RES-096` additionally reference:

- `RES_STAGE_UNAVAILABLE`

This is a specification discrepancy: the code is reachable but the README taxonomy
table does not include it. The implementation dry run must resolve it explicitly by
adding it to the authoritative Research catalogue/README or by replacing it with an
owner-approved existing code. Do not silently omit or rename it.

Also reconcile code-to-exception-class mismatches, such as configuration codes raised
through `ValidationError`. StandardResponse makes the external code stable, but
internal exception choice should remain semantically coherent.

The catalogue must provide safe descriptions, severity, retryability, and operator
actions. Research codes remain Research-owned; Utils supplies only the definition
shape and validation.

## 6. Metadata Policy

For `run_edge_lab_profile`:

- `domain="research"`.
- `risk_level="low"` because output is advisory analysis.
- `read_only=True`.
- `writes_file=False`.
- `modifies_database=False`.
- `places_trade=False`.
- `requires_network=False`.

These declarations match `FR-RES-096`: provider reads, cache, scheduling,
database/artifact writes, and Strategy submission remain external.

If refreshed implementation performs any such side effect, stop and issue a plan
delta rather than changing metadata to legitimize an architectural violation.

Extensions may contain:

- Selected stage tuple.
- Profile/workflow contract version.
- Safe upstream request/correlation IDs.
- A bounded list of stage names completed before an error, when safe and useful.

They must not contain raw datasets, feature frames, Analytics reports, stage result
objects, hypotheses, or model output duplicated from the report.

## 7. Upstream and Downstream Coordination

Inputs include:

- Data-owned `MarketDataset`.
- Optional Analytics `PerformanceReport`.
- Indicator calculations and Research feature functions used during selected stages.

If the workflow actively calls migrated upstream public operations, it must unwrap
their standard responses. If it receives already-constructed raw DTOs as arguments,
it must continue accepting those raw DTOs; do not require callers to pass a response
object.

Downstream:

- `tests/system/integration/test_research_to_strategy.py`
- UI/API orchestration that may build a Strategy proposal

Consumers must unwrap the report and treat it as advisory. Response success is not
permission to register, deploy, or trade a Strategy.

## 8. Implementation Work Packages

### RES-WP1 — Boundary and code reconciliation

1. Reconcile root `__all__` with `PUBLIC_API_CLASSIFICATIONS`.
2. Confirm one qualifying root operation.
3. Enumerate every error code reachable from selected stages.
4. Resolve `RES_STAGE_UNAVAILABLE` and exception-class mismatches through the
   authoritative README.
5. Characterize raw report equality and all stage configurations.

### RES-WP2 — Catalogue

Create the Research-owned Utils-shaped catalogue in a focused contracts/support file.
Validate completeness, descriptions, retryability, and all constructed codes.

### RES-WP3 — Workflow boundary

Wrap `run_edge_lab_profile` once:

1. Start timing immediately.
2. Validate inputs and dependencies using current logic.
3. Run raw internal stages in canonical order.
4. Translate known errors without losing code.
5. Map unexpected errors safely.
6. Return the exact `ResearchReport` in data.

Do not change stage algorithms or public feature-module return types.

### RES-WP4 — Upstream/downstream coordination

Update only actual calls to migrated Data/Indicators/Analytics public operations and
the Research-to-Strategy consumer. Avoid broad feature-module migrations.

### RES-WP5 — Documentation

Update:

- Root Research feature registry.
- Profiles feature specification.
- `FR-RES-026` only if classifications change.
- `FR-RES-096` signature, errors, and usage evidence.
- Error taxonomy and catalogue ownership.
- Cross-domain project/architecture documentation where needed.
- `[Unreleased]` with a concise response-contract change.

Every completed checklist item requires code path and line evidence.

## 9. Tests and Usage

Required:

- Exact five-field response.
- Direct `ResearchReport` placement and serialization.
- All selected-stage combinations.
- Invalid hypothesis/config/dependency/unavailable stage.
- Resource, nonfinite, insufficient-data, leakage, and sensitive-output failures.
- No raw exceptions or sensitive data.
- Accurate read-only/no-write/no-trade/no-network metadata.
- Advisory Research-to-Strategy handoff.
- Root API classifications remain exact.

Primary tests:

- `tests/research/unit/test_workflow.py`
- `tests/research/unit/test_contract_api.py`
- `tests/research/unit/test_contract_results.py`
- Selected-stage unit tests across all feature folders
- `tests/research/integration/test_usage_scripts.py`
- `tests/research/integration/test_unsupervised_research.py`
- `tests/research/integration/test_market_structure_profile.py`
- `tests/system/integration/test_research_to_strategy.py`
- `tests/research/usage/11_profiles.py`

Run all 12 usage programs because the root workflow composes the feature APIs:

```powershell
uv run ruff check app/services/research tests/research
uv run ruff format --check app/services/research tests/research
uv run mypy app/services/research tests/research
uv run pytest tests/research
uv run pytest tests/system/integration/test_research_to_strategy.py
Get-ChildItem tests/research/usage/[0-9][0-9]_*.py | ForEach-Object {
    uv run python $_.FullName
}
```

## 10. Risks, Exclusions, and Rollback

Risks:

- Treating feature-module helpers as root public operations and expanding scope.
- Nested responses if internal stages are wrapped.
- Losing advisory report evidence.
- Missing a distributed Research error code.
- Converting response success into Strategy deployment authority.

Excluded:

- Migration of all feature-module callables.
- Research algorithm/statistical/model redesign.
- Artifact persistence through `run_edge_lab_profile`.
- Provider reads, scheduling, cache, database writes, Strategy submission, or trade.
- AI-tool registration.

Rollback the root workflow response change, catalogue, focused consumers, tests,
usage evidence, and active docs. Internal stage functions should remain unchanged.
Rerun all Research and Research-to-Strategy tests.

## 11. Completion Checklist

- [ ] Root classification still identifies exactly the intended stable operation.
- [ ] `run_edge_lab_profile` returns `StandardResponse[ResearchReport]`.
- [ ] The complete raw report is directly in `data`.
- [ ] Every reachable Research code has a validated domain definition.
- [ ] `RES_STAGE_UNAVAILABLE` discrepancy is resolved authoritatively.
- [ ] Internal feature functions remain raw and wrap only once.
- [ ] Advisory/no-side-effect boundaries remain intact.
- [ ] Consumers, tests, examples, exact `FR-*`, and line evidence agree.
- [ ] Full Research and system validation passes.

# Implementation Plan — HaruQuantAI Spatiotemporal Composability (Phases 6–8)

Source documents: `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` v2 incl. §1.2.1 `R-01`–`R-07`; `IMPLEMENTATION_PLAN_P0-P2.md`; `IMPLEMENTATION_PLAN_P3-P5.md`
Repository state: assumes commits 1–25 (`P0-T01` … `P5-T04`) merged
Generated: 2026-08-20   |   Target executor: low-reasoning coding agent

> **Batch 3 of 5.** Phases 6 (composition, injection, generations), 7 (errors, health, profile readiness), 8 (provider state, migrations, golden fixtures). Commits 26–41.

---

## 0. EXECUTOR OPERATING RULES

```markdown
You are implementing ONE task from this plan. Follow these rules without exception.
1. Implement ONLY the current task. Do not start the next task.
2. Do not modify any file not listed in "Files to Create/Modify". If you believe another file
   must change, STOP and report it instead.
3. Use the exact names, signatures, types, paths and message strings given. Do not rename,
   reorder parameters, or "improve" the API.
4. Do not add features, options, parameters, abstractions, caching, or threading that the task
   does not explicitly request.
5. Do not add a new third-party dependency. If one seems required, STOP and report.
6. Read only the files listed in "Context to Read". Do not scan the repository.
7. Write the tests exactly as specified, then make them pass. Do not weaken, skip, xfail, or
   delete a test to make it pass.
8. Run every command in "Quality Gates" and paste the real output. Never claim a command passed
   without running it.
9. STOP CONDITIONS — stop and report instead of improvising if:
   - a gate still fails after 2 fix attempts;
   - the spec contradicts existing code;
   - a file you must modify does not exist, or already contains conflicting logic;
   - an existing signature differs from the one quoted in the task;
   - the task would require touching a file listed under "DO NOT";
   - you cannot satisfy the task without inventing an unspecified decision.
10. Finish with exactly one git commit using the message given in the task.
11. Report at the end: files changed, test results, gate output, and anything you could not do.
```

---

## 1. ENVIRONMENT & COMMANDS

| Purpose | Command |
|---|---|
| Format (write) | `uv run ruff format .` |
| Lint | `uv run ruff check .` |
| Type check | `uv run mypy .` |
| Targeted test | `uv run pytest <path> -q` |
| Full test + coverage | `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` |
| All gates | `uv run python scripts/ci_check.py` |
| Architecture sweep | `uv run python scripts/audit_check.py` |

`mypy --strict`, full ruff docstring rules (`D`, `ANN`, `DOC102`, `DOC201`, `DOC202`, `DOC501`), and the global 80% coverage floor all apply to `app/` — see Batch 2 §1. `scripts/*.py` direct children keep the `INP001, D100, D103, ANN, S603, S607, T201` ignores.

---

## 2. CURRENT-STATE INVENTORY

Existing after Batch 2:

| Path | Status | Surface |
|---|---|---|
| `app/capabilities/` | EXISTING | `CapabilitySpec`, `Requirement`, `check_conformance`, `qualified_id`, `parse_qualified_id`, `satisfies` |
| `app/kernel/` | EXISTING | `KernelError`, `ReasonCode`, `Unavailability`, `ProviderManifest`, `load_manifest`, `CapabilityRegistry`, `ResolutionReport`, `resolve`, `ComponentState`, `Effect`, `EffectScope`, `Component` |
| `app/kernel/discovery.py::discover_manifests` | EXISTING | Not re-exported at package root |
| `app/kernel/profiles.py::Profile, evaluate_readiness` | EXISTING | Not re-exported at package root |
| `tests/architecture/test_import_boundaries.py` | EXISTING | `FORBIDDEN_PREFIXES` for `app/capabilities` and `app/kernel` |
| `app/composition/` | CREATE | Declared by `P1-T04`, built here |

Existing symbols in `app/utils` referenced by Phase 7, verified from `app/runtime.py`:

```python
build_response_metadata(name=..., domain=..., risk_level=..., request_id=...,
                        start_time=..., read_only=..., writes_file=...,
                        modifies_database=..., places_trade=..., requires_network=...)
error_response(code=..., details={...}, message=..., metadata=..., catalog=...)
success_response(data, message=..., metadata=...)
generate_id("req") -> str
get_common_error_catalog()
```

### 2.1 UNVERIFIED — two items each task must confirm before relying on them

| Item | Why unverified | Handling |
|---|---|---|
| The error-catalog object shape returned by `get_common_error_catalog()`, and whether a caller-supplied catalog may register a new code | `app/utils/errors/__init__.py` was not read during planning | `P7-T01` step 1 reads it. If a caller-supplied catalog cannot carry `CAPABILITY_UNAVAILABLE`, the task **STOPS and reports** rather than editing `app/utils`, which is PROTECTED |
| The dataset-construction helper name in `tests/indicators/helpers.py` | Only lines 1–80 were read. Verified present: module docstring "Shared deterministic fixtures for Indicators tests"; `from app.services.data import build_ohlcv_record`; `from app.services.indicators import get_indicator_result_metadata, get_indicator_result_values, join_indicator_result`; `_START = datetime(2026, 1, 1, tzinfo=UTC)`; `_FixtureModel`; `MarketDataset = _FixtureModel`; `OHLCVRecord = build_ohlcv_record`; `unwrap_response`. The builder function name below line 80 is not known | `P8-T04` step 1 reads the whole file and uses whatever public helper it finds. If none constructs a dataset, the task **STOPS and reports** |

**Pre-existing failures:** whatever `docs/dev/plugin-decoupling/BASELINE.md` records.

---

## 3. SHARED CONTRACTS (INTERFACE FREEZE)

### 3.1 New file tree

| Path | Status | Purpose |
|---|---|---|
| `app/composition/__init__.py` | CREATE | Public surface |
| `app/composition/README.md` | CREATE | Non-feature declaration |
| `app/composition/generations.py` | CREATE | `ProviderGeneration` |
| `app/composition/loader.py` | CREATE | The **only** entry-point importer in the codebase |
| `app/composition/activation.py` | CREATE | Activation sequence |
| `app/composition/root.py` | CREATE | `CompositionRoot` |
| `app/composition/responses.py` | CREATE | `Unavailability` → `StandardResponse` |
| `app/composition/status.py` | CREATE | Capability-graph payload |
| `app/composition/policy.py` | CREATE | Profile policy table |
| `app/composition/retention.py` | CREATE | Uninstall-retention guard |
| `scripts/capture_golden.py` | CREATE | Golden fixture capture |
| `tests/fixtures/golden/` | CREATE | Captured baselines |
| `tests/golden/test_indicator_parity.py` | CREATE | Parity assertion |

### 3.2 Dependency direction — extended, enforced by `P6-T01`

```text
app.capabilities   →   stdlib only
app.kernel         →   app.capabilities, app.utils, stdlib
app.composition    →   app.kernel, app.capabilities, app.utils, stdlib
app.services.*     →   app.capabilities                        (Batch 4+)
```

`app.composition` may import `app.services.*` **only** through `loader.load_entry_point`, which resolves a manifest-declared dotted path at activation time. No `from app.services...` statement may appear anywhere under `app/composition/`.

### 3.3 `app/composition/generations.py` — CREATE

```python
@dataclass(frozen=True)
class ProviderGeneration:
    """One activated instance of a provider, with full provenance.

    Attributes:
        provider_id: Manifest provider id.
        provider_version: Manifest version.
        generation: Monotonic counter, starting at 1 for a provider's first activation.
        contract_versions: Sorted qualified capability ids this generation provides.
        config_digest: Hex SHA-256 of the canonical JSON of the activation config.
        dependency_generations: Sorted (provider_id, generation) pairs it was built against.
        scope_id: Identity of the EffectScope owning this generation's resources.
    """

    provider_id: str
    provider_version: int
    generation: int
    contract_versions: tuple[str, ...]
    config_digest: str
    dependency_generations: tuple[tuple[str, int], ...]
    scope_id: str


def config_digest(config: Mapping[str, object]) -> str: ...
def pin(generations: Iterable[ProviderGeneration]) -> tuple[tuple[str, int], ...]: ...
```

`config_digest` hashes `json.dumps(config, sort_keys=True, separators=(",", ":"))` with `hashlib.sha256` and returns `.hexdigest()`. An empty config digests to the SHA-256 of `"{}"`.
`pin` returns the sorted `(provider_id, generation)` set — **this is what a simulation run stores for reproducibility** (`REFACTOR_PLAN.md` Phase 6 reproducibility rule).

> No timestamp field. `Date.now()`-style values make a digest non-reproducible and would defeat run pinning. Activation time, if ever needed, is recorded by the caller.

### 3.4 `app/composition/loader.py` — CREATE

```python
def load_entry_point(entry_point: str) -> Callable[..., object]: ...
```

Splits on `:`, imports the module with `importlib.import_module`, and returns the named attribute.

Raises `KernelError` with these exact messages: `"entry_point must be module:callable, got {entry_point}"`; `"entry_point module not importable: {module}"`; `"entry_point attribute not found: {module}:{attr}"`; `"entry_point is not callable: {entry_point}"`.

> **This is the only module in the entire codebase permitted to import a provider.** Every other module — discovery, registry, resolver — treats `entry_point` as an inert string. `P6-T03` adds an architecture test asserting `importlib` appears nowhere else under `app/`.

### 3.5 `app/composition/activation.py` — CREATE

```python
@dataclass(frozen=True)
class ActivationOutcome:
    """Result of attempting to activate one provider."""

    provider_id: str
    state: ComponentState
    generation: ProviderGeneration | None
    unavailability: Unavailability | None


def activate(
    manifest: ProviderManifest,
    *,
    config: Mapping[str, object],
    dependencies: Mapping[str, object],
    generation_number: int,
    dependency_generations: tuple[tuple[str, int], ...],
) -> tuple[ActivationOutcome, Component]: ...
```

Frozen activation order (`REFACTOR_PLAN.md` Phase 5): validate config → allocate an isolated `EffectScope` → `load_entry_point` → call `setup(scope=..., config=..., **dependencies)` → mark `ACTIVE`.

Frozen failure rule: any exception from `setup` is caught, the scope is disposed immediately, and the outcome carries `state=ComponentState.FAILED` with `reason_code=ACTIVATION_FAILED`. **A partially-allocated scope is always unwound.**

### 3.6 `app/composition/root.py` — CREATE

```python
class CompositionRoot:
    """The only layer permitted to select providers and assemble components."""

    def __init__(self, registry: CapabilityRegistry,
                 specs: Mapping[str, CapabilitySpec]) -> None: ...
    def activate_all(self, config: Mapping[str, Mapping[str, object]]) -> tuple[ActivationOutcome, ...]: ...
    def component(self, provider_id: str) -> Component | None: ...
    def generation(self, provider_id: str) -> ProviderGeneration | None: ...
    def deactivate(self, provider_id: str) -> tuple[str, ...]: ...
    def pinned_graph(self) -> tuple[tuple[str, int], ...]: ...
```

Frozen rules:

1. `activate_all` resolves first, then activates strictly in `ResolutionReport.activation_order`.
2. Typed dependencies are passed to `setup` **at construction**. `CompositionRoot` exposes no `get(capability_id)` lookup, so business code cannot degenerate into a service locator (`D-10`).
3. `deactivate(provider_id)` deactivates every **dependent** first, in reverse `activation_order`, then the target. This is the reverse-order teardown that `P5-T04` deliberately excluded from `Component`.
4. A dependent that refuses quiesce aborts the whole cascade: the target is **not** deactivated, and already-drained dependents are returned to `ACTIVE`.
5. `pinned_graph()` returns `pin(...)` over every active generation.

### 3.7 `app/composition/responses.py` — CREATE

```python
def unavailability_response(
    unavailability: Unavailability,
    *,
    operation: str,
    domain: str,
) -> object: ...
```

Builds `build_response_metadata(...)` with `risk_level="none"`, `read_only=True`, and every side-effect flag `False`, then returns `error_response(code=unavailability.code, details={...}, message="Capability unavailable", metadata=metadata, catalog=<composition catalog>)`.

`details` carries exactly: `reason_code`, `capability`, `consumer`, `provider_id`, `dependency_chain` (as a list), `retryable`.

### 3.8 `app/composition/status.py` — CREATE

```python
def capability_graph_payload(
    report: ResolutionReport,
    registry: CapabilityRegistry,
    readiness: Mapping[Profile, ReadinessReport],
) -> dict[str, object]: ...
```

Returns a JSON-serialisable dict with `schema_version: 1`, `providers` (id, state, provides, unavailability-or-null), and `profiles` (name, ready, missing). Sorted by id and by profile name. This is the payload `app/ui` consumes over HTTP (`REFACTOR_PLAN.md` §6.2).

### 3.9 `app/composition/policy.py` — CREATE

```python
PROFILE_REQUIRED_CAPABILITIES: Final[dict[Profile, frozenset[str]]] = {
    Profile.RESEARCH: frozenset(),
    Profile.SIMULATION: frozenset(),
    Profile.DEMO: frozenset(),
    Profile.LIVE: frozenset(),
}
```

**All four start empty and are populated only as real capabilities ship.** Adding an id for a capability that does not yet exist would invent an artefact. Batch 4 populates `SIMULATION`; Batch 5 populates `DEMO` and `LIVE` once Risk and Trading have specs.

### 3.10 Manifest extension for stateful providers — MODIFY

`ProviderManifest` (Batch 2 §3.6) gains four optional fields, all defaulting so every existing manifest still parses:

```python
    state_schema_id: str | None = None
    state_schema_version: int | None = None
    uninstall_retention: str = "preserve"
    purge_requires_authorization: bool = True
```

TOML block:

```toml
[state]
schema_id = "indicators.snapshot.v1"
schema_version = 2
uninstall_retention = "preserve"
purge_requires_authorization = true
```

`uninstall_retention` must be `"preserve"` or `"quarantine"`; `"drop"` is **not a legal value** — `AGENTS.md` §5 as amended by `P1-T01` makes schema append-only.

### 3.11 `__all__`

| Module | `__all__` |
|---|---|
| `app/composition/__init__.py` | `["ActivationOutcome", "CompositionRoot", "ProviderGeneration", "capability_graph_payload", "load_entry_point", "unavailability_response"]` |

---

## 4. NAMING & LAYOUT CONVENTIONS

Inherited from Batch 2 §4 unchanged. Three reminders:

- **Logging.** `app/composition/` logs at `INFO` on activation and deactivation, at `WARNING` on activation failure and quiesce refusal. `app/capabilities/` still logs nothing.
- **CHANGELOG.** Every task here touches `app/` or `scripts/`, so **every task adds exactly one `## [Unreleased]` bullet** and includes `docs/CHANGELOG.md` in its `git add`.
- **README.** `app/composition/README.md` carries no `FEAT-*` id and no `### Feature Registry` section.

---

## 5. SCOPE & PROTECTED AREAS

**In scope:** source Phases 6, 7, 8, and the golden fixtures deferred from source Phase 0. Gates `G6`, `G7`, `G8`.

**Out of scope:** the RSI/Williams pilot and every provider migration (Phases 9+, Batch 4); deletion CI (Phase 11, Batch 4); the 21 cross-domain waves (Phase 12, Batch 5); enforcement CI and HMR (Phases 16–17, Batch 5); `D-11` generated registries (Batch 5).

**PROTECTED paths — no task in this plan may modify these:**

| Path | Reason |
|---|---|
| `app/services/` (entire tree) | No domain changes until Batch 4 |
| `app/agentic/` | Same |
| `app/utils/` | The eager-barrel split is source wave 12.1, Batch 5. **`P7-T01` must supply its own catalog rather than register a code here** |
| `app/runtime.py` | `P7-T04` reads it and adds a **separate** function; it does not modify `validate_runtime_configuration` |
| `app/kernel/`, `app/capabilities/` | Frozen by Batch 2 except the one manifest extension authorised in `P8-T01` |
| `app/services/risk/kill_switch/`, `app/services/trading/live/` | `AGENTS.md` §3 |
| `scripts/audit_check.py`, `scripts/ci_check.py` | Gate definitions |
| `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` | No dependency or tool-config change (§6) |
| `docs/CHANGELOG.md` released-version blocks | Only `## [Unreleased]` may be appended to |
| `tests/*/usage/` | `P1-T03` made relocation transitional; nothing moves until Batch 4 |

**Forbidden changes (repo-wide):** no unrelated refactoring; no public API change absent from §3; no new dependency; no weakening/skipping/xfailing/deleting an existing test; no `# noqa` or `# type: ignore` unless a task authorises that specific suppression; no placeholder, stub, `TODO` or `FIXME`; no secrets; no live-trading or live-broker operation from tests; **no `async def` under `app/kernel/`, `app/capabilities/`, or `app/composition/`** (`R-02`); **no `importlib` outside `app/composition/loader.py`**.

---

## 6. DEPENDENCY AUTHORIZATION

```text
No new dependencies are authorized by this plan.
```

`hashlib`, `importlib`, `json`, `tomllib`, `contextlib`, `dataclasses`, `enum`, `pathlib`, `typing`, `collections.abc` are stdlib on Python 3.14.

---

## 7. SOURCE CONFLICTS

```text
Conflict ID:   CF-05
Sources:       REFACTOR_PLAN.md Phase 7 (unavailability normalised into the shared
               five-field StandardResponse)  vs  Plan §5 (app/utils is PROTECTED)
Claim A:       Every boundary returns CAPABILITY_UNAVAILABLE through the standard
               response envelope, which requires the code to exist in an error catalog.
Claim B:       app/utils/errors owns the common catalog and may not be modified in
               this batch; its split is source wave 12.1.
Precedence:    Rule 5 (repository-wide instructions) for the protection, rule 4
               (approved design) for the requirement — both are satisfiable.
Decision:      app/composition/responses.py supplies its OWN catalog to the existing
               error_response(catalog=...) parameter, verified present in
               app/runtime.py. app/utils is not touched. If the catalog type turns out
               not to accept a caller-supplied code, P7-T01 STOPS and reports rather
               than editing a protected path.
Affected tasks: P7-T01
```

```text
Conflict ID:   CF-06
Sources:       REFACTOR_PLAN.md Phase 5 ("deactivate dependent consumers in reverse
               dependency order")  vs  IMPLEMENTATION_PLAN_P3-P5.md P5-T04 rule 8
               ("dependents are NOT deactivated by this method")
Claim A:       Deactivation cascades to dependents in reverse order.
Claim B:       Component.deactivate knows only itself.
Precedence:    Rule 4 (approved design) — both are true at different layers.
Decision:      The cascade is a composition-root concern, not a component concern. A
               Component owns its own scope; CompositionRoot.deactivate owns the
               ordering across components (§3.6 rule 3). This is not a contradiction
               but a layering, and it is why P5-T04 excluded it deliberately.
Affected tasks: P6-T06
```

---

## 8. OPEN QUESTIONS (BLOCKING)

```text
None blocking. Two UNVERIFIED items are recorded in §2.1, each with a first
implementation step that reads the file and an explicit STOP CONDITION if the
assumption does not hold. Neither requires an owner decision in advance.
```

---

## 9. PLANNER OBSERVATIONS (non-blocking)

1. **`loader.py` is a deliberate single point of danger.** Every other kernel module treats `entry_point` as inert text. Concentrating the import in one ~30-line module with an architecture test around it is what keeps discovery side-effect-free.
2. **`ProviderGeneration` carries no timestamp** — a wall-clock field would make `config_digest` non-reproducible and break simulation-run pinning.
3. **`PROFILE_REQUIRED_CAPABILITIES` ships empty on purpose.** Populating `LIVE` with `risk.kill_switch.v1` today would cite a capability that has no spec. It fills in as specs land.
4. **`uninstall_retention` has no `"drop"` value.** The amended `AGENTS.md` §5 makes schema append-only; a legal drop value would invite exactly the data loss `P1-T01` forbade.
5. **Golden fixtures cover Indicators only in this batch.** `tests/indicators/helpers.py` is the one deterministic construction path verified to exist. Analytics, Risk, Strategy, Simulator and Portfolio fixtures follow in Batch 4 alongside their pilots, where their own helpers can be read.
6. **`app/runtime.py` is extended, not modified.** `P7-T04` adds a sibling function and leaves `validate_runtime_configuration` and its four `FR-APP-*` requirements untouched.

---

## 10. PROGRESS DASHBOARD

- [ ] **Phase 6 — Composition, injection, generations**
  - [ ] `P6-T01` — Create composition package skeleton
  - [ ] `P6-T02` — Add provider generation identity
  - [ ] `P6-T03` — Add entry-point loader
  - [ ] `P6-T04` — Add component activation sequence
  - [ ] `P6-T05` — Add composition root orchestrator
  - [ ] `P6-T06` — Add reverse-order dependent teardown
- [ ] **Phase 7 — Errors, health, profile readiness**
  - [ ] `P7-T01` — Add unavailability response mapper
  - [ ] `P7-T02` — Add capability graph payload
  - [ ] `P7-T03` — Add profile policy table
  - [ ] `P7-T04` — Add runtime readiness entry point
- [ ] **Phase 8 — Provider state, migrations, golden fixtures**
  - [ ] `P8-T01` — Add state schema manifest fields
  - [ ] `P8-T02` — Add uninstall retention guard
  - [ ] `P8-T03` — Add migration tombstone reconciler
  - [ ] `P8-T04` — Add golden fixture capture harness
  - [ ] `P8-T05` — Capture indicator golden fixtures
  - [ ] `P8-T06` — Add golden fixture parity test

---

## 11. PHASES

### Phase 6 — Composition, injection, generations

**Goal.** Providers are assembled with typed dependencies injected at construction, each activation carries full provenance, and teardown cascades correctly across components.
**Why now.** Gate `G5` passed: the kernel resolves and components dispose. Composition is the layer that turns a resolution report into running software.
**Deliverable.** `app/composition/` with generations, the single entry-point loader, activation, the root orchestrator, and reverse-order teardown.

**Phase 6 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] No test failing that is not in `BASELINE.md`
- [ ] No PROTECTED path in `git diff --name-only <phase-start>..HEAD`
- [ ] `grep -rn "importlib" app/ --include=*.py | grep -v "app/composition/loader.py"` finds nothing
- [ ] `grep -rn "^from app\.services\|^import app\.services" app/composition/` finds nothing
- [ ] Functional proof: a two-provider fixture where `b` requires `a` activates in order `a, b`; `deactivate("a")` tears down `b` first, then `a`, and both scopes report zero live effects

---

#### - [ ] Task `P6-T01` — Create composition package skeleton

**Traces to:** `REFACTOR_PLAN.md` Phase 6; resolutions `R-03`, `R-06`; Gate `G6`
**Depends on:** `P5-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** `app/composition/` exists as a non-feature package, and the architecture test is extended so its import boundary is enforced from the first commit.

**Context to Read (and nothing else):**

- `app/kernel/__init__.py` and `app/kernel/README.md` — the pattern to mirror
- `tests/architecture/test_import_boundaries.py` — you add one mapping entry
- Shared Contracts §3.1, §3.2, §3.11

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/__init__.py` | CREATE | Package root, empty `__all__` |
| `app/composition/README.md` | CREATE | Non-feature declaration |
| `tests/architecture/test_import_boundaries.py` | MODIFY | Add the composition rule |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `tests/architecture/test_import_boundaries.py`, the existing `FORBIDDEN_PREFIXES` dict has two entries. Add a third; the two existing entries stay byte-identical:

```python
    "app/composition": ("app.services", "app.agentic"),
```

Then add a new test asserting no file under `app/composition` except `loader.py` contains the substring `importlib`.

**Specification (the contract — copy exactly):**

```python
# app/composition/__init__.py
"""The only layer permitted to select providers and assemble components.

Composition owns policy: which provider satisfies which capability, in what
order components activate, and how teardown cascades. The kernel owns the
mechanism. This package reaches ``app.services`` only through
``app.composition.loader.load_entry_point``.
"""

from __future__ import annotations

__all__: list[str] = []
```

**Behaviour Rules (numbered, testable):**

1. `import app.composition` succeeds and `__all__ == []`.
2. Importing it adds no `sys.modules` key beginning `app.services` or `app.agentic`.
3. `FORBIDDEN_PREFIXES` has exactly three entries after this task.
4. A new test `test_importlib_confined_to_loader` passes vacuously now and fails later if any module other than `loader.py` imports `importlib`.
5. `app/composition/README.md` contains no `FEAT-` substring and no `### Feature Registry` heading.

**Implementation Steps:**

1. Create `app/composition/__init__.py` with the exact content above.
2. Create `app/composition/README.md` stating purpose, the `R-06` rationale for a top-level package, the registry exclusion, and that `loader.py` is the only permitted importer.
3. Add the third `FORBIDDEN_PREFIXES` entry.
4. Add `test_importlib_confined_to_loader`, walking `app/composition/*.py` and asserting `"importlib" not in text` for every file whose name is not `loader.py`.
5. Add the CHANGELOG bullet.
6. Commit.

**DO NOT (anti-invention guardrails):**

- Do not create `loader.py`, `generations.py`, or any other module — those are later tasks.
- Do not add a `FEAT-*` id or a Feature Registry section.
- Do not modify the two existing `FORBIDDEN_PREFIXES` entries.
- Do not add `app.utils` to the composition forbidden list — composition legitimately uses the logger.
- Do not add `async def`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_package.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_package_imports_clean` | `import app.composition` | no exception |
| `test_all_is_empty` | `__all__` | `== []` |
| `test_no_domain_modules_loaded` | `sys.modules` | no `app.services` / `app.agentic` key |
| `test_readme_has_no_feature_ids` | README text | no `FEAT-`, no `### Feature Registry` |

Plus, in `tests/architecture/test_import_boundaries.py`: `test_composition_imports_no_domain`, `test_importlib_confined_to_loader`.

Run: `uv run pytest tests/unit/test_composition_package.py tests/architecture -q` → all pass, 0 skipped.

**Regression Tests**

The five existing `tests/architecture` tests must still pass unchanged:
`uv run pytest tests/architecture -q` → 7 passed.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_package.py tests/architecture
uv run ruff check app/composition tests/unit/test_composition_package.py tests/architecture
uv run mypy .
uv run pytest tests/unit/test_composition_package.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added app/composition package as the sole provider-selection layer.`

**Git Commit:**

```bash
git add app/composition tests/unit/test_composition_package.py tests/architecture docs/CHANGELOG.md
git commit -m "feat(composition): add composition root package" -m "Creates the only layer permitted to select providers, with its import
boundary enforced from the first commit.
Refs: REFACTOR_PLAN.md R-03, R-06, Gate G6"
```

**Re-run safety:** `Safe — one anchored dict insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] Six tests passing (four unit, two architecture)
- [ ] Existing architecture tests unchanged and green
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P6-T02` — Add provider generation identity

**Traces to:** `REFACTOR_PLAN.md` Phase 6 generation model and reproducibility rule; Gate `G6`
**Depends on:** `P6-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** Every activation carries a reproducible provenance record, and a simulation run can pin the exact provider-generation set it ran against.

**Context to Read (and nothing else):**

- Shared Contracts §3.3 — the complete contract
- Planner Observation §9.2 — why there is no timestamp

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/generations.py` | CREATE | Provenance |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Replace `__all__: list[str] = []` with an import of `ProviderGeneration` from `app.composition.generations` and `__all__ = ["ProviderGeneration"]`. Docstring and `__future__` line unchanged.

**Specification (the contract — copy exactly):** as Shared Contracts §3.3.

**Behaviour Rules (numbered, testable):**

1. `config_digest({})` equals `hashlib.sha256(b"{}").hexdigest()`.
2. `config_digest` is order-independent: `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` digest identically.
3. `config_digest` is separator-canonical: it uses `separators=(",", ":")`, so no whitespace affects the digest.
4. `ProviderGeneration.__post_init__` raises `ValueError` `"generation must be >= 1, got {generation}"` when `generation < 1`.
5. It raises `ValueError` `"contract_versions must be sorted"` when the tuple is not ascending.
6. `pin` returns `(provider_id, generation)` pairs sorted by `provider_id` ascending.
7. Two `ProviderGeneration` values with identical fields compare equal and hash equally — the dataclass is frozen with no mutable field.
8. The module contains no wall-clock call: no `datetime`, no `time`, no `Date`.

**Implementation Steps:**

1. Create `app/composition/generations.py` with a module docstring and `from __future__ import annotations`.
2. Import `hashlib`, `json`, `dataclass`, `Iterable`, `Mapping`.
3. Implement `config_digest` per rules 1–3.
4. Add the frozen `ProviderGeneration` dataclass with the seven fields and `__post_init__` per rules 4–5.
5. Implement `pin` per rule 6.
6. Give every member a Google docstring with `Attributes:` / `Raises:`.
7. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add an `activated_at` or any timestamp field** — it would make the digest non-reproducible and break run pinning.
- Do not add a random or UUID field; `scope_id` is supplied by the caller.
- Do not make `contract_versions` or `dependency_generations` a list or set; both are sorted tuples so the record stays hashable.
- Do not add a global generation counter here; the number is passed in.
- Do not import `app.kernel` — this module is pure data.
- Do not add logging.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_generations.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_empty_config_digest` | `{}` | equals `sha256(b"{}").hexdigest()` |
| `test_digest_key_order_independent` | two dicts, same pairs | identical digests |
| `test_generation_zero_rejected` | `generation=0` | `ValueError`, match `"generation must be >= 1"` |
| `test_unsorted_contract_versions_rejected` | `("b.v1", "a.v1")` | `ValueError`, match `"must be sorted"` |
| `test_pin_sorted` | generations `b`, `a` | `(("a.p", 1), ("b.p", 1))` |
| `test_no_clock_in_module` | module source text | no `datetime`, no `time.` |

Run: `uv run pytest tests/unit/test_composition_generations.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_generations.py
uv run ruff check app/composition tests/unit/test_composition_generations.py
uv run mypy .
uv run pytest tests/unit/test_composition_generations.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added provider generation identity with reproducible config digest and run pinning.`

**Git Commit:**

```bash
git add app/composition/generations.py app/composition/__init__.py tests/unit/test_composition_generations.py docs/CHANGELOG.md
git commit -m "feat(composition): add provider generation identity" -m "Records provider provenance with a canonical config digest and dependency
generations, so a simulation run can pin the exact graph it ran against.
No wall-clock field, which would defeat reproducibility.
Refs: REFACTOR_PLAN.md Phase 6, Gate G6"
```

**Re-run safety:** `Safe — one anchored replacement, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No timestamp, no randomness in the module
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P6-T03` — Add entry-point loader

**Traces to:** `REFACTOR_PLAN.md` Phase 6; resolution `R-05`; Gate `G6`
**Depends on:** `P6-T02`
**Estimated size:** S (<50 LOC)

**Goal.** One small module resolves a manifest's dotted `entry_point` to a callable — the only place in the codebase permitted to import provider code.

**Context to Read (and nothing else):**

- Shared Contracts §3.4 — the contract and the four exact error messages
- `app/kernel/errors.py` — `KernelError`
- Planner Observation §9.1 — why the import is deliberately concentrated here

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/loader.py` | CREATE | The only importer |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.composition.loader import load_entry_point` and insert `"load_entry_point",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.4.

**Behaviour Rules (numbered, testable):**

1. A string without exactly one `:` raises `KernelError` `"entry_point must be module:callable, got {entry_point}"`.
2. An unimportable module raises `KernelError` `"entry_point module not importable: {module}"`, chained from the original `ImportError` with `raise ... from`.
3. A missing attribute raises `KernelError` `"entry_point attribute not found: {module}:{attr}"`.
4. A non-callable attribute raises `KernelError` `"entry_point is not callable: {entry_point}"`.
5. A valid entry point returns the callable object itself, uncalled.
6. The module never catches a bare `Exception` around `import_module`; it catches `ImportError` only, so a provider whose import raises `ValueError` surfaces that error unchanged.
7. `load_entry_point` performs no caching — the same string imports through Python's own module cache, not a local one.

**Implementation Steps:**

1. Create `app/composition/loader.py` with a module docstring stating it is the only permitted importer.
2. Import `importlib`, `Callable`; import `KernelError` from `app.kernel.errors`.
3. Split on `:` with `partition` and validate per rule 1.
4. Call `importlib.import_module(module)` inside `try` / `except ImportError as error`, re-raising per rule 2.
5. Use `getattr(module_obj, attr, None)` and raise per rule 3 when `None`.
6. Check `callable(...)` and raise per rule 4.
7. Return the attribute.
8. Give the function a Google docstring including all four `Raises:` cases.
9. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add a cache, registry, or memoisation.** Python's module cache is the only cache.
- **Do not catch bare `Exception`** around the import — a provider's own error must not be disguised as an import failure. Ruff `BLE` forbids it anyway.
- Do not call the returned callable.
- Do not validate the callable's signature here; that is `check_conformance`'s job at activation.
- Do not add a `fallback`, `default`, or `optional` parameter — a missing entry point is an error, never a silent skip.
- Do not import `importlib` anywhere else in the codebase.
- Do not add logging; failures are exceptions.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_loader.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_loads_stdlib_callable` | `"json:dumps"` | returns `json.dumps`, uncalled |
| `test_missing_colon_rejected` | `"json.dumps"` | `KernelError`, match `"module:callable"` |
| `test_unimportable_module` | `"no_such_module_xyz:f"` | `KernelError`, match `"not importable"` |
| `test_missing_attribute` | `"json:no_such_attr"` | `KernelError`, match `"attribute not found"` |
| `test_non_callable_attribute` | `"json:__doc__"` | `KernelError`, match `"is not callable"` |
| `test_two_colons_rejected` | `"a:b:c"` | `KernelError`, match `"module:callable"` |

Run: `uv run pytest tests/unit/test_composition_loader.py -q` → all pass, 0 skipped.

**Regression Tests**

`test_importlib_confined_to_loader` from `P6-T01` must still pass now that `loader.py` exists and legitimately imports `importlib`:
`uv run pytest tests/architecture -q` → 7 passed.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_loader.py
uv run ruff check app/composition tests/unit/test_composition_loader.py
uv run mypy .
uv run pytest tests/unit/test_composition_loader.py tests/architecture -q
grep -rln "importlib" app/ --include=*.py | grep -v "app/composition/loader.py" ; test $? -eq 1
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added the single entry-point loader, the only module permitted to import provider code.`

**Git Commit:**

```bash
git add app/composition/loader.py app/composition/__init__.py tests/unit/test_composition_loader.py docs/CHANGELOG.md
git commit -m "feat(composition): add entry-point loader" -m "Resolves a manifest dotted entry_point to a callable. This is the only
module in the codebase permitted to import provider code, enforced by an
architecture test.
Refs: REFACTOR_PLAN.md R-05, Gate G6"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] `importlib` appears nowhere else under `app/`
- [ ] No cache, no bare except, no signature validation
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P6-T04` — Add component activation sequence

**Traces to:** `REFACTOR_PLAN.md` Phase 5 activation sequence; decision `D-10`; Gate `G6`
**Depends on:** `P6-T03`
**Estimated size:** L (120–200 LOC)

**Goal.** One provider activates with typed dependencies injected at construction, and a failure part-way through always unwinds the scope it had already allocated.

**Context to Read (and nothing else):**

- Shared Contracts §3.5 — the contract, the frozen order, and the frozen failure rule
- `app/kernel/scope.py`, `app/kernel/lifecycle.py`, `app/kernel/errors.py`
- `app/composition/loader.py`, `app/composition/generations.py`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/activation.py` | CREATE | Activation |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.composition.activation import ActivationOutcome` and insert `"ActivationOutcome",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.5.

**Behaviour Rules (numbered, testable):**

1. Activation order is exactly: allocate `EffectScope(owner_id=manifest.provider_id)` → `load_entry_point` → call `setup(scope=scope, config=config, **dependencies)` → build `ProviderGeneration` → transition the `Component` to `STARTING` then `ACTIVE`.
2. Dependencies are passed as keyword arguments to `setup`. **No lookup object, registry, or context is passed** — `D-10` forbids a service locator.
3. Any exception raised by `setup` is caught, `scope.dispose()` is called immediately, and the outcome is `state=ComponentState.FAILED` with an `Unavailability` whose `reason_code` is `ACTIVATION_FAILED` and whose `provider_id` is the manifest id.
4. A `KernelError` from `load_entry_point` produces the same `ACTIVATION_FAILED` outcome, not a propagated exception.
5. On failure the returned `Component` is in `FAILED` and its scope reports zero live effects, even when `setup` had already registered some.
6. On success `generation.config_digest` equals `config_digest(config)` and `generation.scope_id` equals the scope's `owner_id`.
7. `activate` logs one `INFO` on success — `"activated %s generation %d"` — and one `WARNING` on failure — `"activation failed for %s: %s"`.
8. `activate` never partially returns: it always yields both an `ActivationOutcome` and a `Component`.

**Implementation Steps:**

1. Create `app/composition/activation.py` with a module docstring and `from __future__ import annotations`.
2. Import `get_logger` from `app.utils`; `ComponentState`, `Component`, `EffectScope`, `ProviderManifest`, `ReasonCode`, `Unavailability` from `app.kernel`; `load_entry_point`; `ProviderGeneration`, `config_digest`.
3. Add the frozen `ActivationOutcome` dataclass.
4. Add a private `_failure(manifest, scope, component, detail)` that disposes the scope and returns a `FAILED` outcome per rules 3–5.
5. Implement `activate` following rule 1 exactly.
6. Wrap `load_entry_point` and the `setup` call in one `try` / `except Exception as error`, delegating to `_failure`.
7. Build `ProviderGeneration` per rule 6, with `contract_versions` sorted.
8. Emit the rule 7 logs.
9. Give every member a Google docstring.
10. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not pass a registry, container, context, or `get()` callable into `setup`.** Dependencies are plain keyword arguments resolved before the call (`D-10`).
- **Do not leave a scope allocated on failure.** Rule 5 is the whole point of this task.
- Do not retry activation; a failure is a returned outcome.
- Do not add a `timeout` or `async def`.
- Do not deactivate dependents here; that is `P6-T06`.
- Do not call `check_conformance` here — conformance is checked by the root in `P6-T05`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_activation.py` (CREATE)

Define fixture `setup` functions inline in the test module and point manifests at them via `"tests.unit.test_composition_activation:ok_setup"`.

| Test function | Input | Expected |
|---|---|---|
| `test_successful_activation` | `ok_setup` | `state is ACTIVE`, generation non-`None` |
| `test_dependencies_passed_as_kwargs` | setup recording its kwargs | recorded kwargs equal the `dependencies` mapping |
| `test_setup_exception_disposes_scope` | setup registering one effect then raising | `state is FAILED`; the effect's disposer ran |
| `test_failure_reason_code` | raising setup | `unavailability.reason_code is ACTIVATION_FAILED` |
| `test_bad_entry_point_is_activation_failed` | `"no_mod:f"` | `state is FAILED`, no exception propagates |
| `test_digest_matches_config` | config `{"a": 1}` | `generation.config_digest == config_digest({"a": 1})` |

Run: `uv run pytest tests/unit/test_composition_activation.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_activation.py
uv run ruff check app/composition tests/unit/test_composition_activation.py
uv run mypy .
uv run pytest tests/unit/test_composition_activation.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added component activation injecting typed dependencies and unwinding partial scopes on failure.`

**Git Commit:**

```bash
git add app/composition/activation.py app/composition/__init__.py tests/unit/test_composition_activation.py docs/CHANGELOG.md
git commit -m "feat(composition): add component activation sequence" -m "Activates one provider with dependencies injected as keyword arguments at
construction. A failure part-way through always disposes the scope already
allocated, so no partial activation leaks resources.
Refs: REFACTOR_PLAN.md Phase 5 activation, D-10, Gate G6"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No service-locator object reaches `setup`
- [ ] Partial-failure test proves zero leaked effects
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P6-T05` — Add composition root orchestrator

**Traces to:** `REFACTOR_PLAN.md` Phase 6; decisions `D-05`, `D-10`; resolution `R-06`; Gate `G6`
**Depends on:** `P6-T04`
**Estimated size:** L (120–200 LOC)

**Goal.** A single object turns a registry plus specs into running components in resolved order, holds their generations, and exposes the pinned graph — without ever offering a runtime capability lookup.

**Context to Read (and nothing else):**

- Shared Contracts §3.6 — the contract and rules 1, 2, 5 (rules 3 and 4 are `P6-T06`)
- `app/kernel/resolver.py`, `app/kernel/registry.py`
- `app/composition/activation.py`, `app/composition/generations.py`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/root.py` | CREATE | Orchestrator |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.composition.root import CompositionRoot` and insert `"CompositionRoot",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.6, **omitting `deactivate`**, which is `P6-T06`.

**Behaviour Rules (numbered, testable):**

1. `activate_all` calls `resolve` once, then activates strictly in `ResolutionReport.activation_order`.
2. A provider whose resolver entry is inactive is never activated; its `ActivationOutcome` carries the resolver's own `Unavailability` unchanged.
3. Dependencies passed to `activate` are the objects returned by each dependency's `setup`, keyed by the **requirement's capability id with dots replaced by underscores** — so `data.ohlcv` arrives as the keyword `data_ohlcv`.
4. `check_conformance` runs on each `setup` return value against its declared spec; a non-empty violation tuple turns the outcome into `FAILED` with `reason_code=ACTIVATION_FAILED` and disposes the scope.
5. `component(provider_id)` and `generation(provider_id)` return `None` for an unknown or inactive id.
6. Generation numbers start at 1 per provider and increment on each re-activation of the same id within one root.
7. `pinned_graph()` returns `pin(...)` over active generations only, sorted by provider id.
8. **`CompositionRoot` exposes no `get`, `lookup`, `resolve_capability`, or `__getitem__`.** `D-10` forbids a service locator.

**Implementation Steps:**

1. Create `app/composition/root.py` with a module docstring and `from __future__ import annotations`.
2. Import `get_logger`; `CapabilityRegistry`, `ResolutionReport`, `resolve`, `ComponentState`, `Component` from `app.kernel`; `check_conformance`, `CapabilitySpec` from `app.capabilities`; `activate`, `ActivationOutcome`; `ProviderGeneration`, `pin`.
3. `__init__` stores registry, specs, and empty dicts for components, generations and a per-provider generation counter.
4. Implement `activate_all` per rules 1–4, 6.
5. Implement the keyword-name transform of rule 3 as a private `_kwarg_name(capability_id)`.
6. Implement `component`, `generation`, `pinned_graph` per rules 5 and 7.
7. Give every member a Google docstring.
8. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add a `get(capability_id)` or any runtime lookup method** — rule 8 is the anti-service-locator rule from `D-10`.
- Do not implement `deactivate`; that is `P6-T06`.
- Do not activate a provider the resolver marked inactive.
- Do not swallow a conformance violation; rule 4 requires it to fail the activation.
- Do not make `CompositionRoot` a module-level singleton or add a global accessor.
- Do not add threading, locking, or `async def`.
- Do not import `app.services` directly; only `load_entry_point` reaches providers.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_root.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_activates_in_resolved_order` | `b` requires `a` | activation order `("a.p", "b.p")` |
| `test_inactive_provider_not_activated` | missing dependency | outcome `FAILED`, resolver unavailability preserved |
| `test_dependency_kwarg_name_transform` | requirement `data.ohlcv` | setup receives keyword `data_ohlcv` |
| `test_conformance_violation_fails_activation` | setup returning a wrong-shaped record | `state is FAILED`, `ACTIVATION_FAILED` |
| `test_generation_increments` | activate the same id twice | generations 1 then 2 |
| `test_no_service_locator_methods` | `dir(CompositionRoot)` | none of `get`, `lookup`, `resolve_capability`, `__getitem__` |

Run: `uv run pytest tests/unit/test_composition_root.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_root.py
uv run ruff check app/composition tests/unit/test_composition_root.py
uv run mypy .
uv run pytest tests/unit/test_composition_root.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added composition root activating providers in resolved order with construction-time injection.`

**Git Commit:**

```bash
git add app/composition/root.py app/composition/__init__.py tests/unit/test_composition_root.py docs/CHANGELOG.md
git commit -m "feat(composition): add composition root orchestrator" -m "Turns a registry and specs into running components in resolved order,
checking conformance and tracking generations. Exposes no runtime lookup,
so business code cannot degenerate into a service locator.
Refs: REFACTOR_PLAN.md D-05, D-10, R-06, Gate G6"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No lookup method exists on `CompositionRoot`
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P6-T06` — Add reverse-order dependent teardown

**Traces to:** `REFACTOR_PLAN.md` Phase 5 deactivation ordering; conflict `CF-06`; Gate `G6`
**Depends on:** `P6-T05`
**Estimated size:** M (50–120 LOC)

**Goal.** Deactivating a provider tears down everything that depends on it first, in reverse activation order, and a single quiesce refusal aborts the whole cascade without leaving the graph half-dismantled.

**Context to Read (and nothing else):**

- Shared Contracts §3.6 rules 3 and 4 — the cascade and the abort rule
- Conflict `CF-06` in §7 — why the cascade lives here and not in `Component`
- `app/composition/root.py` — created by `P6-T05`; you add one method
- `app/kernel/lifecycle.py` — `Component.deactivate`, `Component.can_dispose`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/root.py` | MODIFY | Add `deactivate` |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Insert `deactivate` as the last method of `CompositionRoot`, immediately after `pinned_graph`. Every existing member stays byte-identical.

**Specification (the contract — copy exactly):**

```python
    def deactivate(self, provider_id: str) -> tuple[str, ...]:
        """Tear down a provider and everything depending on it.

        Dependents are deactivated first, in reverse activation order, then the
        target. A dependent that refuses quiesce aborts the whole cascade: the
        target is left running and every already-drained dependent is returned
        to ACTIVE.

        Args:
            provider_id: The provider to deactivate.

        Returns:
            The names of effects whose disposers failed, across every component
            torn down. Empty on a clean cascade or on an aborted one.

        Raises:
            KernelError: If provider_id is not an active component.
        """
```

**Behaviour Rules (numbered, testable):**

1. An unknown or inactive `provider_id` raises `KernelError` `"not an active component: {provider_id}"`.
2. Dependents are computed transitively from the manifests' `requires`, then ordered as the reverse of `activation_order`.
3. Each dependent is checked with `can_dispose()` **before** any component is disposed. A single refusal aborts before anything is torn down.
4. On abort, every component moved to `DRAINING` during the pre-check is transitioned back to `ACTIVE`, the method logs one `WARNING` — `"cascade aborted, %s refused disposal"` — and returns `()`.
5. On success, components are deactivated dependents-first, then the target, and the returned tuple is the concatenation of every component's failure names in teardown order.
6. A component whose disposal fails does **not** abort the cascade; teardown continues and its failures are collected.
7. Deactivated components are removed from the root's component and generation maps, so `component(id)` and `generation(id)` return `None` afterwards.
8. One `INFO` line per component torn down: `"deactivated %s"`.

**Implementation Steps:**

1. Open `app/composition/root.py` and locate the end of `pinned_graph`.
2. Add a private `_dependents(provider_id)` computing the transitive dependent set from manifests.
3. Add `deactivate` with the exact signature and docstring above.
4. Implement rule 1.
5. Build the ordered teardown list per rule 2 (dependents reverse-ordered, then the target).
6. Run the rule 3 pre-check across the whole list, transitioning each to `DRAINING`.
7. Implement the rule 4 abort path.
8. Implement rules 5–8 on the success path.
9. Add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not dispose anything before the full pre-check completes.** A refusal discovered halfway would leave the graph half-dismantled — rule 3 exists to prevent exactly that.
- **Do not force past a refusal**, and do not add a `force` parameter.
- Do not place, cancel, or compensate any external action.
- Do not modify `Component.deactivate` or `Component.can_dispose`.
- Do not deactivate a provider's **dependencies** — only its dependents. Tearing down `a` must not touch what `a` itself needed.
- Do not add `async def`, a timeout, or a retry.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_root.py` (MODIFY — append; do not alter the six `P6-T05` tests)

| Test function | Input | Expected |
|---|---|---|
| `test_dependents_torn_down_first` | `c` → `b` → `a`; deactivate `a` | teardown order `("c.p", "b.p", "a.p")` |
| `test_dependencies_untouched` | deactivate `c` | `a` and `b` remain `ACTIVE` |
| `test_refusal_aborts_whole_cascade` | `c` holds an irreversible effect | nothing disposed; all three back to `ACTIVE`; returns `()` |
| `test_disposal_failure_does_not_abort` | `b`'s disposer raises | all three torn down; returns `("b_effect",)` |
| `test_unknown_id_raises` | `"absent.p"` | `KernelError`, match `"not an active component"` |
| `test_maps_cleared_after_teardown` | deactivate `a` | `component("a.p") is None`, `generation("a.p") is None` |

Run: `uv run pytest tests/unit/test_composition_root.py -q` → all twelve pass, 0 skipped.

**Regression Tests**

The six `P6-T05` tests in the same file must still pass unchanged:
`uv run pytest tests/unit/test_composition_root.py -q` → 12 passed, the six original names present.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_root.py
uv run ruff check app/composition tests/unit/test_composition_root.py
uv run mypy .
uv run pytest tests/unit/test_composition_root.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Changed`:
  `- Composition root now tears down dependents in reverse order and aborts cleanly on a quiesce refusal.`

**Git Commit:**

```bash
git add app/composition/root.py tests/unit/test_composition_root.py docs/CHANGELOG.md
git commit -m "feat(composition): add reverse-order dependent teardown" -m "Deactivating a provider tears down its dependents first, in reverse
activation order. A single quiesce refusal aborts the cascade before
anything is disposed, so the graph is never left half-dismantled.
Refs: REFACTOR_PLAN.md Phase 5 deactivation, CF-06, Gate G6"
```

**Re-run safety:** `Safe — one anchored method insertion; git revert + re-run is clean`

**Definition of Done:**

- [ ] Two files modified, no others
- [ ] Six new tests added; the six existing tests still pass unchanged
- [ ] Pre-check completes before any disposal
- [ ] Dependencies untouched; only dependents cascade
- [ ] Exactly one commit with the message above

---
### Phase 7 — Errors, health, profile readiness

**Goal.** Capability absence becomes a structured response at every boundary, the active capability graph is publishable to the UI, and runtime profiles fail closed.
**Why now.** Gate `G6` passed: components activate and tear down. Now the outside world can be told what is and is not available.
**Deliverable.** `app/composition/` gains `responses.py`, `status.py`, `policy.py`, and `app/runtime.py` gains a sibling readiness entry point.

**Phase 7 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] No test failing that is not in `BASELINE.md`
- [ ] No PROTECTED path in `git diff --name-only <phase-start>..HEAD`
- [ ] `git diff <phase-start>..HEAD -- app/utils/` is empty
- [ ] `validate_runtime_configuration` in `app/runtime.py` is byte-identical to its pre-phase text
- [ ] Functional proof: a fixture graph with one missing dependency yields an error response whose `details.dependency_chain` has more than one element, and a `capability_graph_payload` that round-trips through `json.dumps`

---

#### - [ ] Task `P7-T01` — Add unavailability response mapper

**Traces to:** `REFACTOR_PLAN.md` Phase 7 evidence payload; decision `D-06`; conflict `CF-05`; Gate `G7`
**Depends on:** `P6-T06`
**Estimated size:** M (50–120 LOC)

**Goal.** An `Unavailability` becomes the project's standard five-field error response, using a catalog this package owns, so `app/utils` is never touched.

**Context to Read (and nothing else):**

- `app/utils/errors/__init__.py` — **step 1 reads this** to learn the catalog type returned by `get_common_error_catalog()` and whether a caller may supply one carrying a new code
- `app/runtime.py` — the verified call shape for `build_response_metadata` and `error_response`
- Shared Contracts §3.7; conflict `CF-05` in §7
- `app/kernel/errors.py` — `Unavailability`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/responses.py` | CREATE | Mapper and catalog |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.composition.responses import unavailability_response` and insert `"unavailability_response",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.7, plus a module-level `get_composition_error_catalog()` returning a catalog that registers `CAPABILITY_UNAVAILABLE`, built with whatever constructor `app/utils/errors` exposes.

**Behaviour Rules (numbered, testable):**

1. `details` carries exactly six keys: `reason_code`, `capability`, `consumer`, `provider_id`, `dependency_chain`, `retryable`. No more, no fewer.
2. `dependency_chain` is serialised as a `list`, not a tuple, so the payload is JSON-clean.
3. `reason_code` is the string value, not the enum member.
4. Metadata is built with `risk_level="none"`, `read_only=True`, and `writes_file`, `modifies_database`, `places_trade`, `requires_network` all `False`.
5. `request_id` comes from `generate_id("req")`; `start_time` from `time.perf_counter_ns()` captured at function entry.
6. `message` is the fixed string `"Capability unavailable"`; the specific reason lives in `details`, never in free text.
7. The returned response's `code` equals `"CAPABILITY_UNAVAILABLE"` for every reason code.
8. No submitted configuration value, credential, or provider payload appears anywhere in the response — `AGENTS.md` §3 and the `FR-APP-004` precedent in `app/runtime.py`.

**Implementation Steps:**

1. **Read `app/utils/errors/__init__.py`.** Identify the catalog type and its registration API. **STOP and report** if a caller-supplied catalog cannot carry a new code — do not modify `app/utils`, which is PROTECTED.
2. Create `app/composition/responses.py` with a module docstring and `from __future__ import annotations`.
3. Import `time`; `build_response_metadata`, `error_response`, `generate_id` from `app.utils`; `Unavailability` from `app.kernel`.
4. Implement `get_composition_error_catalog()` registering `CAPABILITY_UNAVAILABLE` using the API found in step 1.
5. Implement `unavailability_response` per rules 1–7.
6. Give every member a Google docstring.
7. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not modify `app/utils/` in any way**, including registering a code in the common catalog. Supply your own catalog through the existing `catalog=` parameter.
- Do not put the reason, the provider id, or any detail into `message`; the message is fixed.
- Do not add a seventh `details` key.
- Do not include configuration values, credentials, or provider payloads in the response.
- Do not raise; this function always returns a response.
- Do not add an `async def` or a success path — it maps failure only.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `app/runtime.py`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_responses.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_code_is_capability_unavailable` | any `Unavailability` | response code `"CAPABILITY_UNAVAILABLE"` |
| `test_details_has_exactly_six_keys` | any | `set(details)` equals the six names |
| `test_chain_is_a_list` | chain of two | `isinstance(details["dependency_chain"], list)` |
| `test_reason_code_is_string` | `NOT_INSTALLED` | `details["reason_code"] == "NOT_INSTALLED"` |
| `test_message_is_fixed` | two different reason codes | both messages equal `"Capability unavailable"` |
| `test_payload_is_json_serialisable` | any | `json.dumps(details)` succeeds |

Run: `uv run pytest tests/unit/test_composition_responses.py -q` → all pass, 0 skipped.

**Regression Tests**

`app/utils` must be untouched and its own tests unaffected:
`git diff --name-only HEAD -- app/utils/` → empty.
`uv run pytest tests/utils -q` → same counts as `BASELINE.md`.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_responses.py
uv run ruff check app/composition tests/unit/test_composition_responses.py
uv run mypy .
uv run pytest tests/unit/test_composition_responses.py tests/utils -q
git diff --name-only HEAD -- app/utils/ | wc -l
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The `wc -l` must print `0`.

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added capability unavailability mapping to the standard response envelope.`

**Git Commit:**

```bash
git add app/composition/responses.py app/composition/__init__.py tests/unit/test_composition_responses.py docs/CHANGELOG.md
git commit -m "feat(composition): map unavailability to standard response" -m "Turns structured Unavailability evidence into the project error response
using a catalog this package owns, leaving app/utils untouched.
Refs: REFACTOR_PLAN.md D-06, CF-05, Gate G7"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] `app/utils/` diff is empty
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P7-T02` — Add capability graph payload

**Traces to:** `REFACTOR_PLAN.md` §6.2 (UI consumes the capability graph over HTTP); Phase 7 status concepts; Gate `G7`
**Depends on:** `P7-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** The active capability graph and per-profile readiness serialise to one JSON-clean dict, so `app/ui` can render degraded widgets instead of handling 5xx.

**Context to Read (and nothing else):**

- Shared Contracts §3.8 — the contract
- `app/kernel/resolver.py`, `app/kernel/registry.py`, `app/kernel/profiles.py`
- `REFACTOR_PLAN.md` §6.2 — why the UI needs this

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/status.py` | CREATE | Payload builder |
| `app/composition/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.composition.status import capability_graph_payload` and insert `"capability_graph_payload",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):**

```python
{
  "schema_version": 1,
  "providers": [
    {"provider_id": "indicator.rsi.default", "state": "ACTIVE",
     "provides": ["indicator.rsi.v1"], "unavailability": None}
  ],
  "profiles": [
    {"profile": "research", "ready": True, "missing": []}
  ]
}
```

**Behaviour Rules (numbered, testable):**

1. `providers` is sorted by `provider_id` ascending; `profiles` by `profile` ascending.
2. `provides` is the sorted qualified capability ids the manifest declares.
3. `unavailability` is `None` for an active provider, otherwise the same six-key details mapping `P7-T01` produces.
4. `missing` is a list of those same detail mappings, one per unsatisfied profile requirement.
5. The whole payload survives `json.dumps` without a custom encoder — no enum member, tuple, `Path`, or dataclass instance leaks through.
6. `schema_version` is the integer `1`.
7. A provider that is registered but disabled appears with `state` `"DISABLED"`, not omitted — the UI must be able to distinguish "not installed" from "switched off".
8. The function is pure: no logging, no I/O, no mutation of its arguments.

**Implementation Steps:**

1. Create `app/composition/status.py` with a module docstring and `from __future__ import annotations`.
2. Import `Mapping`; `CapabilityRegistry`, `ResolutionReport` from `app.kernel`; `Profile`, `ReadinessReport` from `app.kernel.profiles`.
3. Add a private `_details(unavailability)` producing the same six-key mapping as `P7-T01`, with the chain as a list.
4. Build the `providers` list per rules 1–3 and 7.
5. Build the `profiles` list per rules 1 and 4.
6. Return the dict per rules 5–6.
7. Give every member a Google docstring.
8. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add a FastAPI route, router, or endpoint — wiring this into the API is source wave 12.19, Batch 5.
- Do not leak an enum member, tuple, dataclass, or `Path` into the payload.
- Do not omit disabled providers; rule 7 requires them present.
- Do not add caching or a `since`/`etag` parameter.
- Do not import `app.services` or `app.ui`.
- Do not add logging or `async def`.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_status.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_schema_version_is_one` | any payload | `payload["schema_version"] == 1` |
| `test_providers_sorted` | ids `b.p`, `a.p` | `a.p` first |
| `test_disabled_provider_present` | one disabled provider | appears with `state == "DISABLED"` |
| `test_active_has_null_unavailability` | active provider | `unavailability is None` |
| `test_profile_missing_details` | one unready profile | `missing[0]` has the six keys |
| `test_json_round_trip` | full payload | `json.loads(json.dumps(payload)) == payload` |

Run: `uv run pytest tests/unit/test_composition_status.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_status.py
uv run ruff check app/composition tests/unit/test_composition_status.py
uv run mypy .
uv run pytest tests/unit/test_composition_status.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added capability graph payload publishing provider states and profile readiness.`

**Git Commit:**

```bash
git add app/composition/status.py app/composition/__init__.py tests/unit/test_composition_status.py docs/CHANGELOG.md
git commit -m "feat(composition): add capability graph payload" -m "Serialises provider states and per-profile readiness to one JSON-clean
dict, so the TypeScript UI can render degraded states instead of handling
5xx responses.
Refs: REFACTOR_PLAN.md section 6.2, Gate G7"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] Payload JSON round-trips with no custom encoder
- [ ] No FastAPI route added
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P7-T03` — Add profile policy table

**Traces to:** `REFACTOR_PLAN.md` §1.5 profile readiness; decision `D-01`; Gate `G7`
**Depends on:** `P7-T02`
**Estimated size:** S (<50 LOC)

**Goal.** The policy table that says which capabilities each runtime profile requires lives in composition, empty until real capabilities exist, so the kernel stays business-neutral and no capability id is invented.

**Context to Read (and nothing else):**

- Shared Contracts §3.9 — the table and why it ships empty
- `app/kernel/profiles.py` — `Profile`, `evaluate_readiness`
- Planner Observation §9.3

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/policy.py` | CREATE | Policy table |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.9, plus:

```python
def required_capabilities(profile: Profile) -> frozenset[str]:
    """Return the qualified capability ids a profile requires.

    Args:
        profile: The runtime profile.

    Returns:
        A frozenset of qualified capability ids, empty when the profile has
        no declared requirements yet.
    """
```

**Behaviour Rules (numbered, testable):**

1. `PROFILE_REQUIRED_CAPABILITIES` has exactly four keys, one per `Profile` member.
2. All four values are empty frozensets at this commit.
3. `required_capabilities` returns the frozenset for a known profile.
4. Every id ever added must be a qualified id parseable by `parse_qualified_id`; a module-level assertion enforces this at import time and raises `ValueError` otherwise.
5. The module imports nothing from `app.services`.

**Implementation Steps:**

1. Create `app/composition/policy.py` with a module docstring stating the table fills in as specs land.
2. Import `Final`; `Profile` from `app.kernel.profiles`; `parse_qualified_id` from `app.capabilities`.
3. Add `PROFILE_REQUIRED_CAPABILITIES` with the four empty entries.
4. Add the module-level validation loop of rule 4.
5. Implement `required_capabilities`.
6. Add the CHANGELOG bullet.
7. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not populate any profile with a capability id.** No capability exists yet beyond `indicator.rsi.v1`, and `LIVE` requiring `risk.kill_switch.v1` would cite an artefact that does not exist. Batch 4 populates `SIMULATION`; Batch 5 populates `DEMO` and `LIVE`.
- Do not move this table into `app/kernel/` — `D-01` forbids the kernel knowing capability policy.
- Do not add a fifth profile.
- Do not read the table from a config file or environment variable.
- Do not add logging or `async def`.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_policy.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_four_profiles_present` | table keys | equals `set(Profile)` |
| `test_all_empty_at_this_commit` | all values | every one is empty |
| `test_required_capabilities_returns_frozenset` | `Profile.LIVE` | `isinstance(..., frozenset)` |
| `test_ids_are_qualified` | every id in the table | `parse_qualified_id` accepts each |
| `test_no_service_import` | module source | no `app.services` substring |

Run: `uv run pytest tests/unit/test_composition_policy.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_policy.py
uv run ruff check app/composition tests/unit/test_composition_policy.py
uv run mypy .
uv run pytest tests/unit/test_composition_policy.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added profile capability policy table, empty until real capabilities ship.`

**Git Commit:**

```bash
git add app/composition/policy.py tests/unit/test_composition_policy.py docs/CHANGELOG.md
git commit -m "feat(composition): add profile capability policy table" -m "Holds which capabilities each runtime profile requires, in composition
rather than the kernel. Ships empty; entries are added only as the
capabilities they name actually exist.
Refs: REFACTOR_PLAN.md section 1.5, D-01, Gate G7"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All five tests written and passing
- [ ] No capability id populated
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P7-T04` — Add runtime readiness entry point

**Traces to:** `REFACTOR_PLAN.md` §1.5; Phase 7 six status concepts; Gate `G7`
**Depends on:** `P7-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** A system-level function answers "may this profile operate", extending `app/runtime.py` alongside the existing route-compatibility check without altering it.

**Context to Read (and nothing else):**

- `app/runtime.py` — read it in full. `validate_runtime_configuration(*, runtime_profile: str, execution_route: str)`, `_EXECUTION_ROUTE_BY_PROFILE`, `_ERROR_CODE`, and the `FR-APP-001`…`FR-APP-004` requirements it satisfies. **You add a sibling; you change nothing.**
- `app/composition/policy.py`, `app/composition/responses.py`
- `app/kernel/profiles.py` — `evaluate_readiness`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/runtime.py` | MODIFY | Add one function |
| `app/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `app/runtime.py`, append the new function after the closing line of `validate_runtime_configuration`. That function, its four module constants (`_EXECUTION_ROUTE_BY_PROFILE`, `_ERROR_CODE`, `_ERROR_DETAIL`, `_ERROR_MESSAGE`, `_SUCCESS_MESSAGE`), the module docstring and every existing import must remain **byte-identical**.

**Specification (the contract — copy exactly):**

```python
def validate_profile_readiness(
    *,
    runtime_profile: str,
    report: object,
    registry: object,
) -> object:
    """Validate that a runtime profile has every capability it requires.

    Args:
        runtime_profile: Runtime profile selected by Utils-owned configuration.
        report: The kernel ResolutionReport for the active graph.
        registry: The kernel CapabilityRegistry backing that report.

    Returns:
        A successful response containing raw ``None`` when the profile is
        ready, or a value-free structured error response otherwise.
    """
```

**Behaviour Rules (numbered, testable):**

1. An unknown `runtime_profile` returns the existing `SYSTEM_RUNTIME_ROUTE_INCOMPATIBLE`-style failure shape with detail `"RUNTIME_PROFILE_UNKNOWN"`, reusing `error_response` — it does not raise.
2. A ready profile returns `success_response(None, ...)` with the message `"Runtime profile capability requirements are satisfied"`.
3. An unready profile returns the `unavailability_response` for the **first** entry of `ReadinessReport.missing`, which is sorted, so the result is deterministic.
4. Metadata identifies `app.runtime.validate_profile_readiness`, domain `"app"`, `risk_level="none"`, read-only, with every side-effect flag `False` — matching the existing function's pattern.
5. Submitted values never appear in the response or the logs, matching the `FR-APP-004` precedent.
6. `validate_runtime_configuration` is not called, wrapped, or modified by this function.
7. One `WARNING` is logged when unready: `"profile %s is not ready"`. Nothing is logged when ready.

**Implementation Steps:**

1. Read `app/runtime.py` in full and confirm the existing function's exact closing line.
2. Add imports for `Profile`, `evaluate_readiness`, `required_capabilities`, `unavailability_response`, grouped with the existing local import block.
3. Append `validate_profile_readiness` with the exact signature and docstring above.
4. Implement rule 1 using the existing `error_response` + `build_response_metadata` pattern already in the file.
5. Build the policy mapping from `required_capabilities` and call `evaluate_readiness`.
6. Implement rules 2–4 and 7.
7. Add the export to `app/__init__.py`, keeping `__all__` sorted.
8. Add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not modify `validate_runtime_configuration`, its constants, or its docstring.** It satisfies `FR-APP-001` through `FR-APP-004` and its tests must pass unchanged.
- Do not merge the two checks into one function or have one call the other.
- Do not add a fifth profile or change `_EXECUTION_ROUTE_BY_PROFILE`.
- Do not raise for an unready profile; unreadiness is a returned response.
- Do not include the submitted profile string in the error details.
- Do not add `async def`.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/system/unit/test_runtime_readiness.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_ready_profile_succeeds` | empty policy | `status == "success"`, `data is None` |
| `test_unknown_profile_fails` | `"other"` | error response, detail `"RUNTIME_PROFILE_UNKNOWN"` |
| `test_unready_returns_first_missing` | two missing, sorted | details capability equals the first |
| `test_metadata_identity` | any | metadata name `app.runtime.validate_profile_readiness` |
| `test_no_submitted_values_leak` | odd profile string | that string appears nowhere in the response |
| `test_existing_function_untouched` | import both | `validate_runtime_configuration` still callable with its documented signature |

Run: `uv run pytest tests/system/unit/test_runtime_readiness.py -q` → all pass, 0 skipped.

**Regression Tests**

The existing runtime tests named in `app/README.md` must pass unchanged:
`uv run pytest tests/system/unit/test_runtime.py tests/system/integration/test_runtime_initialization.py tests/unit/test_runtime_coverage.py -q` → same counts as `BASELINE.md`.

**Usage Example**

None — `app/` root is outside `app/services/<domain>` and its README already records that the numbered-usage rule does not apply.

**Quality Gates:**

```bash
uv run ruff format app/runtime.py app/__init__.py tests/system/unit/test_runtime_readiness.py
uv run ruff check app/runtime.py app/__init__.py tests/system/unit/test_runtime_readiness.py
uv run mypy .
uv run pytest tests/system tests/unit/test_runtime_coverage.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `app/README.md` — add `validate_profile_readiness` to the Public Contract section. **Do not add a Feature Registry row**; this is composition plumbing, not a new `FEAT-APP-*` feature.
- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added runtime profile readiness validation alongside the existing route compatibility check.`

**Git Commit:**

```bash
git add app/runtime.py app/__init__.py app/README.md tests/system/unit/test_runtime_readiness.py docs/CHANGELOG.md
git commit -m "feat(runtime): add profile capability readiness check" -m "Adds a sibling to validate_runtime_configuration answering whether a
profile has every capability it requires. The existing function and its
FR-APP requirements are untouched.
Refs: REFACTOR_PLAN.md section 1.5, Gate G7"
```

**Re-run safety:** `Safe — one anchored append to an existing module; git revert + re-run is clean`

**Definition of Done:**

- [ ] Five files modified/created, no others
- [ ] All six tests written and passing
- [ ] Existing runtime tests pass with unchanged counts
- [ ] `validate_runtime_configuration` byte-identical
- [ ] Exactly one commit with the message above

---

### Phase 8 — Provider state, migrations, golden fixtures

**Goal.** Removing a stateful provider preserves its data, and a captured financial baseline makes every later refactor provably behaviour-preserving.
**Why now.** Gate `G7` passed. Phase 9's pilot physically removes a provider, so the retention rules and the golden baseline must both exist first.
**Deliverable.** Manifest state fields, a retention guard, a tombstone reconciler, and captured Indicators fixtures with a parity test.

**Phase 8 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] No test failing that is not in `BASELINE.md`
- [ ] No PROTECTED path in `git diff --name-only <phase-start>..HEAD`
- [ ] `tests/fixtures/golden/indicators.json` exists and is tracked by git
- [ ] `uv run pytest tests/golden -q` green
- [ ] Functional proof: a manifest with `uninstall_retention = "drop"` is rejected at parse time; a manifest declaring `state_schema_id` round-trips through parse with its four fields intact

---

#### - [ ] Task `P8-T01` — Add state schema manifest fields

**Traces to:** `REFACTOR_PLAN.md` Phase 8 manifest additions; decision `D-09`; `AGENTS.md` §5 as amended by `P1-T01`; Gate `G8`
**Depends on:** `P7-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** A stateful provider declares its state-schema identity and retention policy in its manifest, and no manifest can declare a destructive one.

**Context to Read (and nothing else):**

- Shared Contracts §3.10 — the four new fields and the TOML block
- `app/kernel/manifests.py` — the existing `ProviderManifest` and `parse_manifest`
- `AGENTS.md` §5 — the `Owner-Absent Tombstones` and `Uninstall Is Not Purge` bullets added by `P1-T01`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/manifests.py` | MODIFY | Add four optional fields |
| `tests/unit/test_kernel_manifests.py` | MODIFY | Append four tests |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `ProviderManifest`, add the four fields **after** `source_path`, each with the default from §3.10, so every existing construction site still works. `parse_manifest`'s existing validation order is unchanged; the `[state]` block is parsed last.

**Specification (the contract — copy exactly):** as Shared Contracts §3.10.

**Behaviour Rules (numbered, testable):**

1. A manifest without a `[state]` block parses with `state_schema_id is None`, `state_schema_version is None`, `uninstall_retention == "preserve"`, `purge_requires_authorization is True`.
2. `uninstall_retention` accepts only `"preserve"` or `"quarantine"`; anything else raises `KernelError` with detail `"unknown uninstall_retention: {value}"`.
3. **`"drop"` is explicitly rejected** by rule 2, with the same message.
4. Declaring `schema_id` without `schema_version` raises `KernelError` detail `"state schema_id requires schema_version"`, and the converse raises `"state schema_version requires schema_id"`.
5. `schema_version` must be an `int >= 1`; detail `"state schema_version must be >= 1"`.
6. `purge_requires_authorization` defaults to `True`; a manifest may set it `False` only when `state_schema_id is None`, else detail `"purge authorization cannot be waived for a stateful provider"`.
7. Every existing `P4-T03` test still passes unchanged.

**Implementation Steps:**

1. Open `app/kernel/manifests.py` and locate `ProviderManifest`.
2. Add `RETENTION_POLICIES: Final[frozenset[str]] = frozenset({"preserve", "quarantine"})` near `EFFECT_CLASSES`.
3. Add the four fields with their defaults after `source_path`.
4. In `parse_manifest`, read the optional `[state]` table after the existing `effects` handling.
5. Implement rules 2–6 using the existing `_fail` helper.
6. Update the `ProviderManifest` docstring `Attributes:` block with the four fields.
7. Append the four new tests to `tests/unit/test_kernel_manifests.py`.
8. Add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add a `"drop"` retention value, now or ever.** `AGENTS.md` §5 as amended makes schema append-only; a legal drop value invites the data loss `P1-T01` forbade.
- Do not make any of the four fields required — every existing manifest must still parse.
- Do not implement migration execution, ledger reconciliation, or purge here; this task is schema declaration only.
- Do not reorder or alter the existing validation of `provider`, `provides`, `requires`, or `effects`.
- Do not alter the six existing tests in the test file.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/composition/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_manifests.py` (MODIFY — append; the six `P4-T03` tests stay unchanged)

| Test function | Input | Expected |
|---|---|---|
| `test_state_block_absent_defaults` | `MINIMAL` | the four defaults from rule 1 |
| `test_drop_retention_rejected` | `uninstall_retention = "drop"` | `KernelError`, match `"unknown uninstall_retention: drop"` |
| `test_schema_id_requires_version` | `schema_id` alone | `KernelError`, match `"requires schema_version"` |
| `test_purge_waiver_rejected_for_stateful` | `schema_id` set, `purge_requires_authorization = false` | `KernelError`, match `"cannot be waived"` |

Run: `uv run pytest tests/unit/test_kernel_manifests.py -q` → all ten pass, 0 skipped.

**Regression Tests**

`uv run pytest tests/unit/test_kernel_manifests.py tests/unit/test_kernel_discovery.py tests/unit/test_kernel_registry.py tests/unit/test_kernel_resolver.py -q` → all pass; the six original manifest test names present.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_manifests.py
uv run ruff check app/kernel tests/unit/test_kernel_manifests.py
uv run mypy .
uv run pytest tests/unit -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added state schema and retention declarations to the provider manifest.`

**Git Commit:**

```bash
git add app/kernel/manifests.py tests/unit/test_kernel_manifests.py docs/CHANGELOG.md
git commit -m "feat(kernel): add state schema manifest fields" -m "Stateful providers declare a state schema id, version and retention policy.
Retention accepts preserve or quarantine only; drop is rejected, keeping
schema append-only per AGENTS.md section 5.
Refs: REFACTOR_PLAN.md D-09, Phase 8, Gate G8"
```

**Re-run safety:** `Safe — additive fields with defaults; git revert + re-run is clean`

**Definition of Done:**

- [ ] Three files modified, no others
- [ ] Four new tests added; the six existing tests pass unchanged
- [ ] `"drop"` is rejected
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P8-T02` — Add uninstall retention guard

**Traces to:** `REFACTOR_PLAN.md` Phase 8 ("uninstall is not purge"); decision `D-09`; Gate `G8`
**Depends on:** `P8-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** A function decides what happens to a removed provider's data, and there is no code path by which removal destroys it.

**Context to Read (and nothing else):**

- Shared Contracts §3.10 — the retention fields
- `app/kernel/manifests.py` — `ProviderManifest` as extended by `P8-T01`
- `AGENTS.md` §5 `Uninstall Is Not Purge`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/retention.py` | CREATE | Retention decision |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
@dataclass(frozen=True)
class RetentionDecision:
    """What happens to a removed provider's persisted state.

    Attributes:
        provider_id: The provider being removed.
        state_schema_id: Its declared schema id, or None when stateless.
        action: "none" for a stateless provider, otherwise "preserve" or
            "quarantine". Never "drop".
        purge_authorized: Always False. Purge is a separate operator action.
        rationale: One short sentence for the operator log.
    """

    provider_id: str
    state_schema_id: str | None
    action: str
    purge_authorized: bool
    rationale: str


def decide_retention(manifest: ProviderManifest) -> RetentionDecision: ...
```

**Behaviour Rules (numbered, testable):**

1. A stateless provider (`state_schema_id is None`) yields `action == "none"` and rationale `"provider declares no persisted state"`.
2. A stateful provider yields `action` equal to its `uninstall_retention`, so `"preserve"` or `"quarantine"`.
3. `purge_authorized` is **always** `False`, for every input, with no parameter able to change it.
4. `"drop"` is unreachable: `decide_retention` has no branch producing it, and a manifest cannot declare it (`P8-T01` rule 3).
5. The function performs no I/O: it touches no database, drops no table, deletes no file.
6. The module exposes no `purge`, `drop`, `delete`, or `truncate` function.
7. `rationale` never contains a table name, a credential, or a submitted value.

**Implementation Steps:**

1. Create `app/composition/retention.py` with a module docstring quoting the `AGENTS.md` §5 rule.
2. Import `dataclass`; `ProviderManifest` from `app.kernel`.
3. Add the frozen `RetentionDecision` dataclass.
4. Implement `decide_retention` per rules 1–3.
5. Give every member a Google docstring.
6. Add the CHANGELOG bullet.
7. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add a purge, drop, delete, or truncate function to this module or anywhere in this batch.** Purge is a separate, explicitly authorised operator action outside this plan.
- **Do not let `purge_authorized` ever be `True`**, and do not add a parameter that could set it.
- Do not touch a database, execute SQL, or delete a file.
- Do not add a `force` or `confirm` parameter.
- Do not import `app.services.data` or any persistence module.
- Do not add `async def`.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_retention.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_stateless_is_none_action` | manifest without state | `action == "none"` |
| `test_preserve_passthrough` | `uninstall_retention = "preserve"` | `action == "preserve"` |
| `test_quarantine_passthrough` | `"quarantine"` | `action == "quarantine"` |
| `test_purge_never_authorized` | both stateful and stateless | `purge_authorized is False` both times |
| `test_no_destructive_symbols` | module source | no `purge`, `drop`, `delete`, `truncate` identifier |
| `test_rationale_leaks_nothing` | stateful manifest | rationale contains no schema id or path |

Run: `uv run pytest tests/unit/test_composition_retention.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_retention.py
uv run ruff check app/composition tests/unit/test_composition_retention.py
uv run mypy .
uv run pytest tests/unit/test_composition_retention.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added uninstall retention guard; removing a provider never purges its data.`

**Git Commit:**

```bash
git add app/composition/retention.py tests/unit/test_composition_retention.py docs/CHANGELOG.md
git commit -m "feat(composition): add uninstall retention guard" -m "Decides preserve or quarantine for a removed provider's state. There is no
code path producing drop, and purge is never authorized here.
Refs: REFACTOR_PLAN.md D-09, AGENTS.md section 5, Gate G8"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests written and passing
- [ ] No destructive function exists in the module
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P8-T03` — Add migration tombstone reconciler

**Traces to:** `REFACTOR_PLAN.md` Phase 8 tombstones; decision `D-09`; `AGENTS.md` §5 `Owner-Absent Tombstones`; Gate `G8`
**Depends on:** `P8-T02`
**Estimated size:** M (50–120 LOC)

**Goal.** A pure function classifies each applied migration step as owned, tombstoned, or unknown, so an absent owner is never mistaken for a checksum mismatch.

**Context to Read (and nothing else):**

- `AGENTS.md` §5, the `Owner-Absent Tombstones` bullet added by `P1-T01` — the rule this implements
- `app/kernel/manifests.py` — `ProviderManifest.owns_migrations`, `state_schema_id`
- Shared Contracts §3.1

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/tombstones.py` | CREATE | Reconciler |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
@dataclass(frozen=True)
class LedgerEntry:
    """One applied migration step as recorded in the ledger.

    Attributes:
        step_id: Ledger step identifier.
        owner_capability: Qualified capability id that applied the step.
        checksum: Recorded step checksum.
    """

    step_id: str
    owner_capability: str
    checksum: str


@dataclass(frozen=True)
class Reconciliation:
    """Classification of every applied step against the installed set."""

    owned: tuple[str, ...]
    tombstoned: tuple[str, ...]
    unknown: tuple[str, ...]

    def blocks_database_access(self) -> bool: ...


def reconcile(
    entries: Iterable[LedgerEntry],
    installed_capabilities: frozenset[str],
) -> Reconciliation: ...
```

**Behaviour Rules (numbered, testable):**

1. A step whose `owner_capability` is in `installed_capabilities` is `owned`.
2. A step whose `owner_capability` is a well-formed qualified id but absent from the installed set is `tombstoned` — **not** an error.
3. A step whose `owner_capability` is not a parseable qualified id is `unknown`.
4. `blocks_database_access()` returns `True` only when `unknown` is non-empty. **A tombstoned step never blocks access** — this is the whole point of `D-09`.
5. All three tuples are sorted by `step_id` ascending.
6. The function performs no I/O: it reads no ledger, opens no database, verifies no checksum. Checksum verification stays where it already lives, in the Data domain.
7. An empty `entries` yields three empty tuples and `blocks_database_access() is False`.

**Implementation Steps:**

1. Create `app/composition/tombstones.py` with a module docstring quoting the `AGENTS.md` §5 tombstone rule.
2. Import `dataclass`, `Iterable`; `parse_qualified_id` from `app.capabilities`.
3. Add the two frozen dataclasses.
4. Implement `reconcile` per rules 1–3 and 5, catching `ValueError` from `parse_qualified_id` to classify `unknown`.
5. Implement `blocks_database_access` per rule 4.
6. Give every member a Google docstring.
7. Add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not treat a tombstoned step as an error or a mismatch.** Rule 4 is the fix for the single largest blocker identified in the refactor plan.
- Do not read a ledger, connect to a database, or execute SQL — this is a pure classifier.
- Do not verify or recompute a checksum; that authority stays in the Data domain.
- Do not drop, alter, or rename any table.
- Do not import `app.services.data` or any persistence module.
- Do not add `async def`.
- Do not modify any PROTECTED path: `app/utils/`, `app/services/`, `app/agentic/`, `app/kernel/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_composition_tombstones.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_installed_owner_is_owned` | owner in the set | classified `owned` |
| `test_absent_owner_is_tombstoned` | owner not in the set | classified `tombstoned` |
| `test_tombstone_does_not_block` | one tombstoned step | `blocks_database_access() is False` |
| `test_unparseable_owner_is_unknown` | owner `"garbage"` | classified `unknown` |
| `test_unknown_blocks` | one unknown step | `blocks_database_access() is True` |
| `test_results_sorted` | steps `s2`, `s1` | `("s1", "s2")` |

Run: `uv run pytest tests/unit/test_composition_tombstones.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_tombstones.py
uv run ruff check app/composition tests/unit/test_composition_tombstones.py
uv run mypy .
uv run pytest tests/unit/test_composition_tombstones.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added migration tombstone reconciler; an absent owner no longer blocks database access.`

**Git Commit:**

```bash
git add app/composition/tombstones.py tests/unit/test_composition_tombstones.py docs/CHANGELOG.md
git commit -m "feat(composition): add migration tombstone reconciler" -m "Classifies applied steps as owned, tombstoned or unknown. Only an unknown
owner blocks database access, so removing a migration-owning feature
degrades rather than bricking the database.
Refs: REFACTOR_PLAN.md D-09, AGENTS.md section 5, Gate G8"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests written and passing
- [ ] A tombstoned step never blocks access
- [ ] No I/O, no checksum recomputation
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P8-T04` — Add golden fixture capture harness

**Traces to:** `REFACTOR_PLAN.md` Phase 0 golden fixtures; resolved `OQ-01`; Gate `G8`
**Depends on:** `P8-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** A script captures deterministic Indicators outputs to a JSON baseline, so every later refactor can be proven behaviour-preserving.

**Context to Read (and nothing else):**

- `tests/indicators/helpers.py` — **read this file in full first.** Verified present: `build_ohlcv_record` imported from `app.services.data`; `get_indicator_result_values` from `app.services.indicators`; `_START = datetime(2026, 1, 1, tzinfo=UTC)`; `_FixtureModel`; `MarketDataset = _FixtureModel`; `OHLCVRecord = build_ohlcv_record`; `unwrap_response`. **STOP and report** if it exposes no helper that constructs a dataset.
- Plan §2.1 — why this file is UNVERIFIED below line 80
- Batch 1 §2.3 — the `rsi` signature
- Batch 2 §1 — the `scripts/*.py` ignore set, which permits `print`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/capture_golden.py` | CREATE | Capture harness |
| `tests/fixtures/golden/.gitkeep` | CREATE | Tracked output directory |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
#!/usr/bin/env python
"""Capture deterministic financial outputs as a golden baseline.

Usage:
    uv run python scripts/capture_golden.py
"""

GOLDEN_DIR: Final[Path] = REPO_ROOT / "tests" / "fixtures" / "golden"
SCHEMA_VERSION: Final[int] = 1
BAR_COUNT: Final[int] = 120
RSI_PERIODS: Final[tuple[int, ...]] = (2, 14, 30)
ROUNDING: Final[int] = 10


def capture_indicators() -> dict[str, object]: ...
def main() -> int: ...
```

Output shape, written to `tests/fixtures/golden/indicators.json`:

```json
{
  "schema_version": 1,
  "bar_count": 120,
  "cases": [
    {"indicator": "rsi", "period": 14, "source": "close",
     "values": [null, null, 55.1234567891]}
  ]
}
```

**Behaviour Rules (numbered, testable):**

1. The dataset is built exclusively through `tests/indicators/helpers.py`, using only symbols that file already exposes.
2. The bar series is generated deterministically from a fixed arithmetic formula seeded by bar index — **no `random`, no `Math.random`, no wall clock**. The timestamps derive from `helpers._START`.
3. `values` are rounded to `ROUNDING` decimal places; `NaN` serialises as JSON `null`.
4. `cases` is sorted by `(indicator, period, source)`.
5. Re-running the script produces a byte-identical file.
6. `main()` prints exactly one line: `wrote <n> cases to <path>` and returns 0; it returns 1 with `missing output directory: <path>` when `GOLDEN_DIR` is absent.
7. The script calls `rsi` only through the public `app.services.indicators` boundary — never a deep submodule import.
8. No broker, network, or database is touched; `ENVIRONMENT` is not read.

**Implementation Steps:**

1. **Read `tests/indicators/helpers.py` in full.** Identify the public dataset-construction helper. STOP and report if none exists.
2. Create `scripts/capture_golden.py` with the shebang, docstring and constants above.
3. Import `json`, `math`, `Path`, `Final`; import the helper module by path using `importlib.util.spec_from_file_location`, since `tests` is importable but the helper is not a package export.
4. Generate `BAR_COUNT` bars per rule 2.
5. For each period in `RSI_PERIODS`, call `rsi` through `app.services.indicators` and extract values with `get_indicator_result_values`.
6. Convert `NaN` to `None` and round per rule 3.
7. Assemble the payload, sort per rule 4, write with `json.dumps(payload, indent=2)` plus a trailing newline.
8. Print the rule 6 summary and return 0.
9. Create `tests/fixtures/golden/.gitkeep` as a zero-byte file.
10. Add the CHANGELOG bullet.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not use `tests/indicators/usage/_support.py` or any usage program as a data source.** It calls `get_market_data` and `_resolve_mt5_usage_config`, requires `ENVIRONMENT=dev` plus persisted MT5 credentials, and raises `SystemExit(3)` without them — a harness built on it would be non-deterministic and would fail closed in CI.
- Do not use `random`, `secrets`, `time`, or `datetime.now()` — rule 5 requires byte-identical reruns.
- Do not deep-import `app.services.indicators.momentum.rsi`; use the domain public boundary.
- Do not modify `app/services/indicators/` or any indicator formula.
- Do not capture Analytics, Risk, Strategy, Simulator, or Portfolio here — their construction helpers are unverified and are Batch 4.
- Do not commit the generated `indicators.json` in this task; `P8-T05` does that.
- Do not modify any PROTECTED path: `app/`, `scripts/audit_check.py`, `scripts/ci_check.py`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_capture_golden.py` (CREATE)

Load the script with the `load_script` helper from Batch 1 §3.6.

| Test function | Input | Expected |
|---|---|---|
| `test_constants_frozen` | module | `BAR_COUNT == 120`, `RSI_PERIODS == (2, 14, 30)`, `ROUNDING == 10` |
| `test_capture_is_deterministic` | `capture_indicators()` twice | two identical dicts |
| `test_cases_sorted` | payload | `cases` ordered by `(indicator, period, source)` |
| `test_nan_becomes_null` | payload | warm-up entries are `None`, not a float `nan` |
| `test_no_randomness_in_source` | module source | no `random`, `secrets`, `datetime.now`, `time.time` |
| `test_no_usage_support_import` | module source | no `_support` substring |

Run: `uv run pytest tests/unit/test_capture_golden.py -q` → all pass, 0 skipped.

**Usage Example**

Run: `uv run python scripts/capture_golden.py`

Expected output shape:

```
wrote 3 cases to tests/fixtures/golden/indicators.json
```

Exit code 0.

**Quality Gates:**

```bash
uv run ruff format scripts/capture_golden.py tests/unit/test_capture_golden.py
uv run ruff check scripts/capture_golden.py tests/unit/test_capture_golden.py
uv run mypy .
uv run pytest tests/unit/test_capture_golden.py -q
uv run python scripts/capture_golden.py
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added deterministic golden fixture capture harness for indicator outputs.`

**Git Commit:**

```bash
git add scripts/capture_golden.py tests/fixtures/golden/.gitkeep tests/unit/test_capture_golden.py docs/CHANGELOG.md
git commit -m "feat(architecture): add golden fixture capture harness" -m "Captures deterministic indicator outputs through the domain public boundary
using the existing test fixture helpers. No broker, no network, no clock,
so reruns are byte-identical.
Refs: REFACTOR_PLAN.md Phase 0 fixtures, OQ-01, Gate G8"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Three files created, one modified, no others
- [ ] All six tests written and passing
- [ ] Script runs twice producing identical output
- [ ] No usage program or broker touched
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P8-T05` — Capture indicator golden fixtures

**Traces to:** `REFACTOR_PLAN.md` Phase 0 golden fixtures; Gate `G8`
**Depends on:** `P8-T04`
**Estimated size:** S (<50 LOC, generated data)

**Goal.** The baseline file exists in the repository, so every later phase has something to compare against.

**Context to Read (and nothing else):**

- `scripts/capture_golden.py` — created by `P8-T04`; you run it, you do not modify it

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/fixtures/golden/indicators.json` | CREATE | The baseline |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** the file is the verbatim output of `uv run python scripts/capture_golden.py`. It is not hand-edited.

**Behaviour Rules (numbered, testable):**

1. `tests/fixtures/golden/indicators.json` exists and is tracked by git.
2. It parses as JSON with `schema_version == 1` and `bar_count == 120`.
3. It contains exactly three cases, one per entry of `RSI_PERIODS`.
4. Re-running the capture script leaves the file byte-identical — `git diff` is empty afterwards.
5. No value in the file is a string; every numeric entry is a number or `null`.

**Implementation Steps:**

1. Run `uv run python scripts/capture_golden.py`.
2. Confirm `tests/fixtures/golden/indicators.json` was written.
3. Run the script a second time and confirm `git diff --stat tests/fixtures/golden/indicators.json` is empty.
4. Add the CHANGELOG bullet.
5. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not hand-edit the JSON.** It is generated output; an edited baseline is a false baseline.
- Do not adjust `RSI_PERIODS`, `BAR_COUNT`, or `ROUNDING` to make the numbers look nicer.
- Do not add fixtures for other domains.
- Do not modify `scripts/capture_golden.py`.
- Do not add the file to `.gitignore`.
- Do not modify any PROTECTED path: `app/`, `scripts/audit_check.py`, `scripts/ci_check.py`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_golden_fixture_file.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_file_exists` | path | exists |
| `test_schema_version` | parsed | `== 1` |
| `test_three_cases` | parsed | `len(cases) == 3` |
| `test_periods_match_script` | parsed | periods `{2, 14, 30}` |
| `test_values_are_numbers_or_null` | every value | `isinstance(v, (int, float)) or v is None` |

Run: `uv run pytest tests/unit/test_golden_fixture_file.py -q` → all pass, 0 skipped.

**Usage Example**

None — this task produces data, not code.

**Quality Gates:**

```bash
test -f tests/fixtures/golden/indicators.json
uv run python scripts/capture_golden.py && git diff --stat tests/fixtures/golden/indicators.json | wc -l
uv run pytest tests/unit/test_golden_fixture_file.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The second command's `wc -l` must print `0`.

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Captured indicator golden baseline for refactor parity checking.`

**Git Commit:**

```bash
git add tests/fixtures/golden/indicators.json tests/unit/test_golden_fixture_file.py docs/CHANGELOG.md
git commit -m "test(architecture): capture indicator golden baseline" -m "Records deterministic RSI outputs at three periods so later refactors can
be proven behaviour-preserving.
Refs: REFACTOR_PLAN.md Phase 0 fixtures, Gate G8"
```

**Re-run safety:** `Safe — regenerating produces an identical file`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All five tests written and passing
- [ ] Regenerating leaves `git diff` empty
- [ ] File not hand-edited
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P8-T06` — Add golden fixture parity test

**Traces to:** `REFACTOR_PLAN.md` Phase 0 output-parity requirement; per-provider recipe step H; Gate `G8`
**Depends on:** `P8-T05`
**Estimated size:** M (50–120 LOC)

**Goal.** A test fails the build the moment an indicator's numeric output drifts from the captured baseline — turning "behaviour preserved" from a claim into a gate.

**Context to Read (and nothing else):**

- `scripts/capture_golden.py` — you reuse `capture_indicators`, you do not reimplement it
- `tests/fixtures/golden/indicators.json` — the baseline
- Batch 1 §3.6 — the `load_script` helper

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/golden/__init__.py` | CREATE | Package marker |
| `tests/golden/test_indicator_parity.py` | CREATE | Parity gate |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
TOLERANCE: float = 1e-9
```

The test loads the baseline, calls `capture_indicators()` live, and compares case by case.

**Behaviour Rules (numbered, testable):**

1. Case sets must match exactly: a missing or extra case fails with `"case set drift: expected {expected}, got {actual}"`.
2. For each case, value lists must be the same length, failing with `"length drift on {indicator} period {period}"`.
3. `None` must align with `None`; a `None` opposite a number fails with `"warmup drift at index {i} on {indicator} period {period}"`.
4. Numeric values must agree within `TOLERANCE`, failing with `"value drift at index {i} on {indicator} period {period}: {expected} vs {actual}"`.
5. The test never regenerates or overwrites the baseline.
6. `TOLERANCE` is `1e-9`, tighter than the baseline's ten-decimal rounding, so rounding noise cannot mask a real change.
7. The suite runs without a broker, network, or database.

**Implementation Steps:**

1. Create `tests/golden/__init__.py` with a one-line docstring.
2. Create `tests/golden/test_indicator_parity.py`.
3. Add the `load_script` helper from Batch 1 §3.6 and load `capture_golden`.
4. Load the baseline JSON with `encoding="utf-8"`.
5. Add `test_case_sets_match` per rule 1.
6. Add `test_value_lengths_match` per rule 2.
7. Add `test_warmup_alignment` per rule 3.
8. Add `test_values_within_tolerance` per rule 4.
9. Add `test_baseline_not_rewritten`, asserting the file's bytes are unchanged after the suite runs.
10. Add the CHANGELOG bullet.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not regenerate or overwrite the baseline from a test.** A self-healing parity test proves nothing.
- Do not loosen `TOLERANCE` to make a comparison pass; a real drift is a finding, and the correct response is to STOP and report.
- Do not `xfail`, `skip`, or mark any parity test conditional.
- Do not reimplement `capture_indicators`; import it from the script.
- Do not add a `--update-baseline` flag anywhere.
- Do not touch a broker, network, or database.
- Do not modify any PROTECTED path: `app/`, `scripts/`, `pyproject.toml`.

**Unit Tests**

The file created by this task **is** the test. Its five test functions are listed in the implementation steps above and must all be present:

| Test function | Input | Expected |
|---|---|---|
| `test_case_sets_match` | baseline vs live | identical case sets |
| `test_value_lengths_match` | each case | equal lengths |
| `test_warmup_alignment` | each case | `None` positions align |
| `test_values_within_tolerance` | each numeric pair | difference `< 1e-9` |
| `test_baseline_not_rewritten` | file bytes before and after | identical |

Run: `uv run pytest tests/golden -q` → all pass, 0 skipped.

**Quality Gates:**

```bash
uv run ruff format tests/golden
uv run ruff check tests/golden
uv run mypy .
uv run pytest tests/golden -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
git diff --stat tests/fixtures/golden/indicators.json | wc -l
```

The final `wc -l` must print `0`.

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`:
  `- Added golden parity test failing the build on any indicator output drift.`

**Git Commit:**

```bash
git add tests/golden docs/CHANGELOG.md
git commit -m "test(architecture): add golden output parity gate" -m "Compares live indicator output against the captured baseline within 1e-9
and never rewrites the baseline, so behaviour preservation is a gate rather
than a claim.
Refs: REFACTOR_PLAN.md Phase 0 parity, recipe step H, Gate G8"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Three files created/modified, no others
- [ ] All five tests written and passing
- [ ] Baseline unchanged after the suite runs
- [ ] No update-baseline path exists
- [ ] Exactly one commit with the message above

---

## 12. TRACEABILITY MAP

| Source identifier | Source location | Task IDs | Status |
|---|---|---|---|
| Phase 6 — composition, injection, generations | `REFACTOR_PLAN.md` Part I | `P6-T01` … `P6-T06` | PLANNED |
| Gate `G6` | `REFACTOR_PLAN.md` §1.2 | `P6-T01` … `P6-T06` | PLANNED |
| `D-10` Access mechanism (no service locator) | `REFACTOR_PLAN.md` §1.2 | `P6-T04`, `P6-T05` | PLANNED |
| `R-06` Composition root location | `REFACTOR_PLAN.md` §1.2.1 | `P6-T01` | PLANNED |
| `R-05` Manifest format (entry-point loading) | `REFACTOR_PLAN.md` §1.2.1 | `P6-T03` | PLANNED |
| Phase 6 reproducibility rule (run pinning) | `REFACTOR_PLAN.md` Phase 6 | `P6-T02` | PLANNED |
| Phase 5 deactivation ordering | `REFACTOR_PLAN.md` Phase 5 | `P6-T06` | PLANNED |
| Phase 7 — errors, health, profile readiness | `REFACTOR_PLAN.md` Part I | `P7-T01` … `P7-T04` | PLANNED |
| Gate `G7` | `REFACTOR_PLAN.md` §1.2 | `P7-T01` … `P7-T04` | PLANNED |
| `D-06` Error model | `REFACTOR_PLAN.md` §1.2 | `P7-T01` | PLANNED |
| §6.2 UI second runtime | `REFACTOR_PLAN.md` §6.2 | `P7-T02` (payload); UI client is Batch 5 | PARTIAL |
| §1.5 Profile readiness | `REFACTOR_PLAN.md` §1.5 | `P7-T03`, `P7-T04` | PLANNED |
| Phase 8 — provider state and migrations | `REFACTOR_PLAN.md` Part I | `P8-T01` … `P8-T03` | PLANNED |
| Gate `G8` | `REFACTOR_PLAN.md` §1.2 | `P8-T01` … `P8-T06` | PLANNED |
| `D-09` Migration/schema | `REFACTOR_PLAN.md` §1.2 | `P8-T01`, `P8-T02`, `P8-T03` | PLANNED |
| Phase 0 — golden output fixtures | `REFACTOR_PLAN.md` Part I | `P8-T04`, `P8-T05`, `P8-T06` | PLANNED (Indicators only; other domains Batch 4) |
| `OQ-01` | Batch 1 §8 | `P8-T04` | RESOLVED and consumed |
| Install→disable→reinstall test cycle | `REFACTOR_PLAN.md` Phase 8 | none | DEFERRED to `P11` (Batch 4) — needs a real provider |
| Phases 9–17, Gates `G9`–`G11` | `REFACTOR_PLAN.md` Parts II–VI | none | OUT OF SCOPE (§5) |

---

## 13. COMMIT SEQUENCE

| Order | Task ID | Commit message |
|---|---|---|
| 26 | `P6-T01` | `feat(composition): add composition root package` |
| 27 | `P6-T02` | `feat(composition): add provider generation identity` |
| 28 | `P6-T03` | `feat(composition): add entry-point loader` |
| 29 | `P6-T04` | `feat(composition): add component activation sequence` |
| 30 | `P6-T05` | `feat(composition): add composition root orchestrator` |
| 31 | `P6-T06` | `feat(composition): add reverse-order dependent teardown` |
| 32 | `P7-T01` | `feat(composition): map unavailability to standard response` |
| 33 | `P7-T02` | `feat(composition): add capability graph payload` |
| 34 | `P7-T03` | `feat(composition): add profile capability policy table` |
| 35 | `P7-T04` | `feat(runtime): add profile capability readiness check` |
| 36 | `P8-T01` | `feat(kernel): add state schema manifest fields` |
| 37 | `P8-T02` | `feat(composition): add uninstall retention guard` |
| 38 | `P8-T03` | `feat(composition): add migration tombstone reconciler` |
| 39 | `P8-T04` | `feat(architecture): add golden fixture capture harness` |
| 40 | `P8-T05` | `test(architecture): capture indicator golden baseline` |
| 41 | `P8-T06` | `test(architecture): add golden output parity gate` |

Continues from order 25 (`P5-T04`) in Batch 2 §13.

---

## 14. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation | Mitigating task |
|---|---|---|---|---|
| `importlib` spreads beyond `loader.py`, making discovery execute provider code | High | High | Architecture test asserts `importlib` appears in no other file under `app/`; a phase-exit `grep` repeats the check | `P6-T01`, `P6-T03` |
| `CompositionRoot` grows a `get()` and becomes a service locator | High | High | `D-10`; §3.6 rule 8; a test asserts the method names are absent | `P6-T05` |
| A failed activation leaks a half-allocated scope | High | High | §3.5 frozen failure rule; a dedicated test registers an effect then raises | `P6-T04` |
| A quiesce refusal leaves the graph half-dismantled | Medium | High | Full pre-check before any disposal; abort restores every drained component | `P6-T06` |
| Registering `CAPABILITY_UNAVAILABLE` forces an edit to protected `app/utils` | Medium | Medium | `CF-05`: supply a caller-owned catalog; STOP condition rather than a protected-path edit | `P7-T01` |
| A capability id is invented for a profile that has no spec | Medium | High | `PROFILE_REQUIRED_CAPABILITIES` ships empty; a test asserts it | `P7-T03` |
| `validate_runtime_configuration` is modified, breaking `FR-APP-001`…`004` | Medium | High | Sibling function only; byte-identity is a phase-exit gate; existing tests are a regression gate | `P7-T04` |
| A retention path drops data | Low | Critical | `"drop"` rejected at parse; `purge_authorized` hardwired `False`; a test asserts no destructive identifier exists | `P8-T01`, `P8-T02` |
| A tombstoned migration is misread as a checksum mismatch and blocks the DB | High | Critical | `blocks_database_access()` returns `True` only for `unknown`; dedicated test | `P8-T03` |
| Golden fixtures built on a usage program, hence non-deterministic and broker-dependent | High | High | Explicit `DO NOT`; `_support.py`'s `SystemExit(3)` behaviour documented; a test asserts the module never imports `_support` | `P8-T04` |
| A parity test is "fixed" by regenerating the baseline | Medium | High | No update path; `test_baseline_not_rewritten`; phase-exit `git diff` check | `P8-T06` |

---

## SELF-VERIFICATION REPORT

Checks 1–16: **PASS with notes**

1. **PASS** — all sixteen tasks carry every mandatory field. `Regression Tests` present on `P6-T01`, `P6-T03`, `P6-T06`, `P7-T01`, `P7-T04`, `P8-T01` (each modifies or depends on existing behaviour) and omitted elsewhere. `Logging` omitted throughout: logging requirements are stated in §4 once and inside the relevant Behaviour Rules, and no task's logging differs from that. `Rollback` omitted: `P8-T01`–`P8-T03` touch schema *declaration* and pure classification only — no migration runs, no table changes, so `git revert` is sufficient.
2. **PASS** — every symbol is defined in its task or frozen in §3.
3. **PASS** — no banned verb in any implementation step.
4. **PASS** — single chain `P6-T01 → … → P8-T06`, no forward reference; `P6-T01` depends on Batch 2's `P5-T04`.
5. **PASS** — paths spelled identically across §3, task tables, gates and `git add` lines.
6. **PASS** — every Phase 6–8 source identifier appears in §12 with an explicit status; the install→reinstall cycle is marked DEFERRED with its reason rather than dropped.
7. **PASS** — every cited identifier appears verbatim in `REFACTOR_PLAN.md` or is defined here. `FR-APP-001`–`FR-APP-004` are cited only as **existing** requirements of the untouched `validate_runtime_configuration`, verified in `app/README.md`. Unconfirmed requirement IDs: **none**.
8. **PASS** — largest tasks are `P6-T04` and `P6-T05` at size L, 3 files plus test, ≤11 steps. No title contains "and".
9. **PASS** — all sixteen commit messages are Conventional Commits with a scope; each `git add` names only files in that task's table.
10. **PASS** — §8 is empty of blockers. The two UNVERIFIED items in §2.1 each have a first-step read and an explicit STOP CONDITION, so neither routes a decision to the executor at runtime.
11. **N/A** — walking skeleton discharged in Batch 1 (`CF-02`). Phases 6–8 are vertical slices: composition runs components, Phase 7 publishes status, Phase 8 gates behaviour preservation.
12. **PASS** — `EXISTING`/`MODIFY` artefacts are backed by evidence: the `app/utils` response helpers and `app/runtime.py` structure were read in full; `tests/indicators/helpers.py` is explicitly marked UNVERIFIED below line 80 in §2.1 with a reading step.
13. **PASS** — no task file table contains a PROTECTED path. `app/runtime.py` is listed PROTECTED against *modification of the existing function*; `P7-T04` appends a sibling, and byte-identity of the original is a phase-exit gate.
14. **PASS** — every command traces to §1.
15. **PASS** — two material conflicts (`CF-05`, `CF-06`), both resolved with a single stated approach.
16. **PASS** — no dependency used that is not stdlib or already present.

Tasks: **16** across **3** complete phases
Requirements covered: **17** source identifiers PLANNED or PARTIAL; **1** DEFERRED with reason; **1** OUT OF SCOPE group
Unconfirmed requirement IDs: **none**
Material conflicts resolved: **2**   |   Blocking open questions: **0**
New dependencies authorized: **0**

**Batch 3 is complete.** Batch 4 continues at Phase 9.

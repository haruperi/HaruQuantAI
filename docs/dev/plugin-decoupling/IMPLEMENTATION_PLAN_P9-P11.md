# Implementation Plan — HaruQuantAI Spatiotemporal Composability (Phases 9–11)

Source documents: `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` v2 incl. §1.2.1 `R-01`–`R-07`; Batches 1–3
Repository state: assumes commits 1–41 (`P0-T01` … `P8-T06`) merged
Generated: 2026-08-20   |   Target executor: low-reasoning coding agent

> **Batch 4 of 5.** Phases 9 (pure pilot: RSI and Williams %R), 10 (effectful pilot: Notifications, then a data stream), 11 (deletion, reinstall and enforcement CI). Commits 42–58.
>
> **This is the first batch that modifies existing domain code.** Every task that does so begins by reading the file and carries an explicit STOP CONDITION.

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
| Golden parity | `uv run pytest tests/golden -q` |

`mypy --strict`, full ruff docstring rules, and the global 80% coverage floor apply to `app/`. `scripts/*.py` direct children keep the `INP001, D100, D103, ANN, S603, S607, T201` ignores — **`S603`/`S607` ignored there is why the deletion-proof runner in `P11-T03` lives in `scripts/`, not in `tests/`**.

---

## 2. CURRENT-STATE INVENTORY

Existing after Batch 3: `app/capabilities/` (spec vocabulary + `indicator.rsi.v1`), `app/kernel/` (errors, manifests, discovery, registry, resolver, profiles, states, scope, lifecycle), `app/composition/` (generations, loader, activation, root, responses, status, policy, retention, tombstones), `tests/architecture/`, `tests/golden/`, `scripts/capture_golden.py`, `scripts/composability_*.py`.

Verified domain facts this batch depends on:

| Fact | Evidence |
|---|---|
| `app/services/indicators/momentum/` contains exactly `__init__.py` (200 B), `README.md` (570 B), `rsi.py` (6326 B), `williams_r.py` (6179 B) | directory listing |
| `momentum/__init__.py` is eager and reads exactly: docstring, `from app.services.indicators.momentum.rsi import rsi`, `from app.services.indicators.momentum.williams_r import williams_r`, `__all__ = ["rsi", "williams_r"]` | full file read |
| `rsi(data, *, period, source="close", config=None) -> IndicatorResult`, decorated `@guard_public_boundary`, module `__all__ = ["rsi"]` | full file read |
| `rsi.py` imports `app.services.indicators.core.{contracts,errors,results,validation}` and `app.utils.get_logger` | full file read |
| `app/utils/__init__.py` is a fully eager barrel importing `contracts`, `errors`, `idempotency`, `identity`, `logging`, `notifications`, and further blocks | first 45 lines read |
| `app/services/indicators/` has a `migrations/` directory | directory listing |

### 2.1 UNVERIFIED — read before relying on, STOP if the assumption fails

| Item | Why unverified | First step that resolves it |
|---|---|---|
| `app/services/indicators/__init__.py` (19 942 B) — whether it is lazy `_EXPORTS` or eager, and how it exports `rsi` / `williams_r` | not read during planning | `P9-T04` step 1 |
| `williams_r(...)` signature | `williams_r.py` not read | `P9-T01` step 1 |
| `app/utils/__init__.py` below line 45; the full export list and whether a lazy barrel is mechanically safe | only 45 lines read | `P10-T02` step 1 |
| `app/utils/notifications/` public surface | not read | `P10-T01` step 1 |
| Whether any consumer deep-imports `app.services.indicators.momentum` | not searched | `P9-T04` step 2 (a repo grep, authorised for that task only) |

**Pre-existing failures:** whatever `docs/dev/plugin-decoupling/BASELINE.md` records.

---

## 3. SHARED CONTRACTS (INTERFACE FREEZE)

### 3.1 Provider package layout — frozen for every provider in this batch and all later ones

```text
app/services/<domain>/<provider_name>/
├── manifest.toml
├── __init__.py          # docstring + __all__ = []; no imports
├── plugin.py            # setup(*, scope, config, **dependencies) -> object
├── implementation.py    # the behaviour; no import-time side effects
├── example.py           # executable evidence; prints bounded results
├── README.md            # no FEAT-* id until the domain registry is regenerated
└── tests/
    ├── __init__.py
    ├── test_contract.py
    ├── test_unit.py
    └── test_removability.py
```

`plugin.py` defines exactly one public callable:

```python
def setup(*, scope: EffectScope, config: Mapping[str, object]) -> object:
    """Build this provider's capability record.

    Args:
        scope: Lifecycle owner for any resource this provider allocates.
        config: Provider configuration; empty for a pure provider.

    Returns:
        The capability record or provider object the spec declares.
    """
```

A **pure** provider registers no effect and ignores `scope`. An **effectful** provider registers every resource on `scope`.

### 3.2 `app/capabilities/indicator/williams_r/v1.py` — CREATE

Mirrors `indicator.rsi.v1` exactly in shape: `CAPABILITY_ID = "indicator.williams_r"`, `VERSION = 1`, a `WilliamsRCalculator` Protocol, a frozen `WilliamsRRecord` with one `compute` field, `SPEC` with `cardinality="many"` and `kind="callable_record"`, `REQUIRES = ()`.

### 3.3 Loader configuration — CREATE

`config/providers.toml` at the repository root:

```toml
schema_version = 1

[providers."indicator.rsi.default"]
enabled = true

[providers."indicator.williams_r.default"]
enabled = true
```

```python
# app/composition/config.py
DEFAULT_CONFIG_PATH: Final[Path] = REPO_ROOT / "config" / "providers.toml"


@dataclass(frozen=True)
class LoaderConfig:
    schema_version: int
    enabled: frozenset[str]
    disabled: frozenset[str]

    def is_enabled(self, provider_id: str) -> bool: ...


def load_loader_config(path: Path = DEFAULT_CONFIG_PATH) -> LoaderConfig: ...
```

Frozen rules: a provider absent from the file is **enabled by default**; an explicit `enabled = false` disables it; an unknown key raises `KernelError`. Disabling is the mechanism the deletion matrix uses, and it is equivalent to deletion **only because** the import-time-side-effect lint guarantees the loader is the sole activation path.

### 3.4 `scripts/deletion_matrix.py` — CREATE

```python
def run_matrix(provider_ids: Sequence[str]) -> list[dict[str, object]]: ...
def main() -> int: ...
```

For each id: write a temporary config disabling it, boot the composition root in a **subprocess**, and record `{provider_id, boot_ok, capability_state, dependents_ok}`. Exit 1 if any `boot_ok` is `False` for a Tier A/B provider, or if any provider listed in `REQUIRED_PROVIDER_IDS` boots successfully while disabled.

`REQUIRED_PROVIDER_IDS: Final[frozenset[str]] = frozenset()` — **ships empty**; ids are added only as genuinely required providers exist.

### 3.5 `scripts/deletion_proof.py` — CREATE

```python
def prove_deletion(provider_path: str, repo_root: Path, work_root: Path) -> dict[str, object]: ...
def main() -> int: ...
```

Copies the tree to `work_root`, deletes `provider_path`, then runs in a **fresh interpreter subprocess**: import the kernel → import the app → resolve → call the affected capability → assert no stale `sys.modules` entry names the deleted package. Returns a record per step. Never mutates the source tree.

### 3.6 `__all__` additions

| Module | Added |
|---|---|
| `app/composition/__init__.py` | `"LoaderConfig"`, `"load_loader_config"` |

---

## 4. NAMING & LAYOUT CONVENTIONS

Inherited from Batches 2–3. Four additions for provider packages:

- Provider directory name is `<capability_leaf>_<variant>`, e.g. `rsi_default`, `williams_r_default`. Provider **id** is the dotted `<capability_id>.<variant>`, e.g. `indicator.rsi.default`.
- `example.py` may use `print` — extend the existing `AGENTS.md` §2 standalone-script exception, already amended by `P1-T03`.
- Provider-local `tests/` is collected because `testpaths = ["tests"]` does **not** restrict `python_files` matching elsewhere; `P9-T02` adds `app` to `testpaths` **only if** the executor confirms provider tests are otherwise uncollected. **If adding to `testpaths` would require editing `pyproject.toml`, the task STOPS and reports** — `pyproject.toml` is PROTECTED.
- **CHANGELOG:** every task in this batch adds exactly one `## [Unreleased]` bullet.

---

## 5. SCOPE & PROTECTED AREAS

**In scope:** source Phases 9, 10, 11. Gates `G9`, `G10`, `G11`.

**Deliberately unprotected for this batch only, and only for the named paths:**

| Path | Unprotected for | Rule |
|---|---|---|
| `app/services/indicators/momentum/` | `P9-T02`, `P9-T03`, `P9-T04` | Formulae are copied verbatim; the golden parity gate proves it |
| `app/services/indicators/__init__.py` | `P9-T04` | Re-export path only; the exported names must not change |
| `app/utils/__init__.py` | `P10-T02` | Lazification only; the exported names must not change |
| `app/utils/notifications/` | `P10-T03` | Extraction only; behaviour unchanged |

**PROTECTED paths — no task in this plan may modify these:**

| Path | Reason |
|---|---|
| Every `app/services/*` domain except `indicators` | Domain migration is Batch 5 |
| `app/services/indicators/core/`, `migrations/`, and every non-`momentum` family | Only the pilot families move |
| `app/agentic/` | Batch 5 |
| Every `app/utils/*` subpackage except `notifications/` | wave 12.1, Batch 5 |
| `app/kernel/`, `app/capabilities/`, `app/composition/` except the additions in §3.3 | Frozen by Batches 2–3 |
| `app/services/risk/kill_switch/`, `app/services/trading/live/` | `AGENTS.md` §3 |
| `app/runtime.py` | Extended in Batch 3; unchanged here |
| `scripts/audit_check.py`, `scripts/ci_check.py`, `scripts/capture_golden.py` | Gate definitions and the baseline producer |
| `tests/fixtures/golden/indicators.json` | The baseline; regenerating it to pass a test is forbidden |
| `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` | No dependency or tool-config change (§6) |
| `docs/CHANGELOG.md` released-version blocks | Only `## [Unreleased]` may be appended to |

**Forbidden changes (repo-wide):** no unrelated refactoring; no public API change absent from §3; no new dependency; no weakening/skipping/xfailing/deleting an existing test; no `# noqa` or `# type: ignore` unless a task authorises it specifically; no placeholder, stub, `TODO` or `FIXME`; no secrets; no live-trading or live-broker operation from tests or examples; **no `async def` under `app/kernel/`, `app/capabilities/`, `app/composition/`**; **no `importlib` outside `app/composition/loader.py` and the two `scripts/` runners**; **no change to any indicator formula**.

---

## 6. DEPENDENCY AUTHORIZATION

```text
No new dependencies are authorized by this plan.
```

`subprocess`, `shutil`, `tempfile`, `tomllib`, `json`, `pathlib` are stdlib. `subprocess` is used only in `scripts/*.py`, where ruff `S603`/`S607` are ignored.

---

## 7. SOURCE CONFLICTS

```text
Conflict ID:   CF-07
Sources:       REFACTOR_PLAN.md Phase 9 (RSI and Williams %R become separate
               provider folders)  vs  AGENTS.md section 1 Feature-group namespace
               exception  vs  scripts/audit_check.py check REG
Claim A:       momentum/ becomes an organizational namespace containing only
               README.md and __init__.py, with two sibling provider folders.
Claim B:       AGENTS.md permits a documented non-feature namespace containing only
               README.md, __init__.py and registered feature folders; audit_check REG
               reconciles README-registered feature ids against module folders.
Precedence:    Rules 4 and 5 agree — the namespace exception already permits exactly
               this shape.
Decision:      momentum/ is declared a feature-group namespace. The two providers are
               siblings under indicators/, not children of momentum/, because a
               provider folder must be independently deletable and a child of a
               namespace that also holds README ownership is not. The indicators
               README feature rows for RSI and Williams are updated in the same task
               that moves them, so REG never goes red.
Affected tasks: P9-T02, P9-T03, P9-T04
```

```text
Conflict ID:   CF-08
Sources:       REFACTOR_PLAN.md Phase 11 (config-disable is equivalent to deletion)
               vs REFACTOR_PLAN.md Phase 11 proof 2 (fresh-process physical deletion)
Claim A:       Disabling a provider in loader config is equivalent to deleting it.
Claim B:       Only a fresh-process physical deletion proves removability, because a
               stale sys.modules entry can mask an import coupling.
Precedence:    Rule 2 — both are approved acceptance criteria at different costs.
Decision:      Both are implemented and neither substitutes for the other. The
               config-disable matrix (P11-T02) gates every merge because it is fast.
               The physical deletion proof (P11-T03) runs nightly and is the only
               thing that can catch a stale-module mask. The equivalence claim holds
               only while the import-time-side-effect lint passes, which P11-T06
               makes a mandatory gate.
Affected tasks: P11-T02, P11-T03, P11-T06
```

---

## 8. OPEN QUESTIONS (BLOCKING)

```text
None. Five UNVERIFIED items are recorded in §2.1, each with a named first step and a
STOP CONDITION. None requires an owner decision in advance; each is answerable by
reading one file in the repository.
```

---

## 9. PLANNER OBSERVATIONS (non-blocking)

1. **The pilot deliberately does not delete the old code path in the same commit.** `P9-T02` and `P9-T03` create providers that call the existing functions; `P9-T04` switches the barrel. If parity fails at any point, one `git revert` restores the working system.
2. **Formulae are copied, never rewritten.** `_wilder_rsi` and its constants move verbatim. The golden parity gate from `P8-T06` is what makes this provable rather than asserted.
3. **`REQUIRED_PROVIDER_IDS` ships empty**, exactly like `PROFILE_REQUIRED_CAPABILITIES`. `risk.kill_switch` has no provider yet, so listing it would cite an artefact that does not exist.
4. **`app/utils` lazification is the highest-risk task in the batch.** Every domain imports from it. It is placed immediately before the notification extraction so that a failure reverts one commit, and its regression gate is the entire test suite, not a subset.
5. **Provider test collection is an unverified mechanic.** `testpaths = ["tests"]` may exclude `app/**/tests/`. If it does, the fix is a `pyproject.toml` edit, which is PROTECTED — so `P9-T02` STOPS and reports rather than making it. The fallback is a thin re-export under `tests/indicators/providers/`.
6. **Phase 10's data-stream pilot is scoped to the simulated stream**, not a live broker. `AGENTS.md` §3 forbids live operation from tests, and a live MT5 stream would make the pilot non-deterministic.

---

## 10. PROGRESS DASHBOARD

- [ ] **Phase 9 — Pure pilot: RSI and Williams %R**
  - [ ] `P9-T01` — Add Williams %R capability specification
  - [ ] `P9-T02` — Create RSI provider package
  - [ ] `P9-T03` — Create Williams %R provider package
  - [ ] `P9-T04` — Convert momentum to a namespace
  - [ ] `P9-T05` — Add cross-feature removability proof
- [ ] **Phase 10 — Effectful pilot: Notifications, then a data stream**
  - [ ] `P10-T01` — Add notification capability specification
  - [ ] `P10-T02` — Make the utils barrel lazy
  - [ ] `P10-T03` — Create notification provider package
  - [ ] `P10-T04` — Add notification disposal proof
  - [ ] `P10-T05` — Create simulated stream provider package
  - [ ] `P10-T06` — Add stream replacement proof
- [ ] **Phase 11 — Deletion, reinstall and enforcement CI**
  - [ ] `P11-T01` — Add loader configuration
  - [ ] `P11-T02` — Add config-disable matrix runner
  - [ ] `P11-T03` — Add fresh-process deletion proof
  - [ ] `P11-T04` — Add reinstall cycle proof
  - [ ] `P11-T05` — Add required-provider refusal assertion
  - [ ] `P11-T06` — Wire composability gates into CI

---

## 11. PHASES

### Phase 9 — Pure pilot: RSI and Williams %R

**Goal.** Two indicators become independently removable providers with no change to their numeric output.
**Why now.** Gates `G3`–`G8` passed: specs, kernel, composition, retention and the golden baseline all exist. Indicators are pure, so this pilot exercises the whole model at the lowest possible blast radius.
**Deliverable.** `indicator.williams_r.v1` spec; `rsi_default/` and `williams_r_default/` provider packages; `momentum/` reduced to a namespace; a consumer proof that deleting one does not affect the other.

**Phase 9 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] `uv run pytest tests/golden -q` green and `git diff tests/fixtures/golden/indicators.json` empty
- [ ] `uv run python scripts/audit_check.py` exits 0 with `REG` unchanged
- [ ] No test failing that is not in `BASELINE.md`
- [ ] Functional proof: in a copied tree, deleting `app/services/indicators/williams_r_default/` leaves the app importable and `rsi` working; deleting `rsi_default/` leaves `williams_r` working and reports `CAPABILITY_UNAVAILABLE` with `reason_code=NOT_INSTALLED` for `indicator.rsi.v1`
- [ ] `from app.services.indicators import rsi, williams_r` still resolves

---

#### - [ ] Task `P9-T01` — Add Williams %R capability specification

**Traces to:** `REFACTOR_PLAN.md` Phase 9; resolution `R-04`; Gate `G9`
**Depends on:** `P8-T06`
**Estimated size:** S (<50 LOC)

**Goal.** The second capability spec exists, mirroring `indicator.rsi.v1`, so the pilot has two independent capabilities to prove removability against.

**Context to Read (and nothing else):**

- `app/services/indicators/momentum/williams_r.py` — **step 1 reads this** for the exact public signature. STOP and report if its public function is not named `williams_r` or is not decorated `@guard_public_boundary`.
- `app/capabilities/indicator/rsi/v1.py` — the exact template to mirror
- Shared Contracts §3.2

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/indicator/williams_r/__init__.py` | CREATE | Namespace |
| `app/capabilities/indicator/williams_r/v1.py` | CREATE | Specification |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** identical in shape to `app/capabilities/indicator/rsi/v1.py`, substituting `CAPABILITY_ID = "indicator.williams_r"`, `WilliamsRCalculator`, `WilliamsRRecord`, and a `compute` signature whose keyword parameters match the ones found in step 1.

**Behaviour Rules (numbered, testable):**

1. `SPEC.capability_id == "indicator.williams_r"`, `SPEC.version == 1`.
2. `SPEC.kind == "callable_record"`, `SPEC.cardinality == "many"`.
3. `qualified_id(...) == "indicator.williams_r.v1"`.
4. `check_conformance(SPEC, WilliamsRRecord(compute=lambda **_: None))` returns `()`.
5. Importing the module loads no `app.services` module.
6. `WilliamsRCalculator.compute`'s keyword parameter names match the real `williams_r` signature found in step 1, excluding `config`.
7. `REQUIRES == ()`.

**Implementation Steps:**

1. Read `app/services/indicators/momentum/williams_r.py` and record its public signature. STOP if it differs in shape from `rsi`.
2. Create `app/capabilities/indicator/williams_r/__init__.py` with a docstring and `__all__: list[str] = []`.
3. Create `v1.py` mirroring the RSI spec with the substitutions above.
4. Use `Any` for the dataset and result types, exactly as the RSI spec does.
5. Add the CHANGELOG bullet.
6. Commit.

**DO NOT (anti-invention guardrails):**

- Do not import, call, or modify `williams_r`.
- Do not narrow `Any` to a private Indicators type — that would break the `app/capabilities` import boundary.
- Do not add a `config` parameter to the Protocol; configuration is a provider concern.
- Do not add a `v2.py`.
- Do not re-export the spec from `app/capabilities/__init__.py`.
- Do not modify the RSI spec.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_capability_indicator_williams_r_v1.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_spec_identity` | `SPEC` | id and version correct |
| `test_kind_and_cardinality` | `SPEC` | `callable_record`, `many` |
| `test_qualified_id` | `SPEC` | `"indicator.williams_r.v1"` |
| `test_conforming_record` | valid record | `()` |
| `test_non_callable_reported` | `compute=5` | `("not callable: compute",)` |
| `test_no_domain_import` | `sys.modules` | no `app.services` key |

Run: `uv run pytest tests/unit/test_capability_indicator_williams_r_v1.py -q` → all pass, 0 skipped.

**Usage Example** — none; non-feature infrastructure per `P1-T04`.

**Quality Gates:**

```bash
uv run ruff format app/capabilities tests/unit/test_capability_indicator_williams_r_v1.py
uv run ruff check app/capabilities tests/unit/test_capability_indicator_williams_r_v1.py
uv run mypy .
uv run pytest tests/unit/test_capability_indicator_williams_r_v1.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added indicator.williams_r.v1 capability specification.`

**Git Commit:**

```bash
git add app/capabilities/indicator/williams_r tests/unit/test_capability_indicator_williams_r_v1.py docs/CHANGELOG.md
git commit -m "feat(capabilities): add indicator.williams_r.v1 specification" -m "Second capability specification, giving the pilot two independent
capabilities to prove removability against.
Refs: REFACTOR_PLAN.md Phase 9, R-04, Gate G9"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Three files created/modified, no others
- [ ] All six tests passing
- [ ] `williams_r.py` untouched
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P9-T02` — Create RSI provider package

**Traces to:** `REFACTOR_PLAN.md` Phase 9 RSI tasks; per-provider recipe steps A–E, H; Gate `G9`
**Depends on:** `P9-T01`
**Estimated size:** L (120–200 LOC)

**Goal.** RSI exists as an independently deletable provider package whose numeric output is byte-identical to the current implementation.

**Context to Read (and nothing else):**

- `app/services/indicators/momentum/rsi.py` — the source. **Copy `_wilder_rsi`, `_build_config`, `_FORMULA_VERSION`, `_INDICATOR_VERSION`, `_FLAT_RSI` verbatim.**
- Shared Contracts §3.1 — the provider layout and the `setup` signature
- `app/capabilities/indicator/rsi/v1.py` — `SPEC`, `RsiRecord`
- Shared Contracts §3.6 (Batch 2) — the manifest TOML schema

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/rsi_default/` | CREATE | Provider package per §3.1 |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

The package contains `manifest.toml`, `__init__.py`, `plugin.py`, `implementation.py`, `example.py`, `README.md`, and `tests/` with `__init__.py`, `test_contract.py`, `test_unit.py`, `test_removability.py`.

**Specification (the contract — copy exactly):**

```toml
# manifest.toml
[provider]
id = "indicator.rsi.default"
version = 1
entry_point = "app.services.indicators.rsi_default.plugin:setup"

[[provides]]
capability_id = "indicator.rsi"
version = 1
```

```python
# plugin.py
def setup(*, scope: EffectScope, config: Mapping[str, object]) -> RsiRecord:
    """Build the RSI capability record.

    Args:
        scope: Lifecycle owner. RSI is pure and registers no effect.
        config: Ignored; RSI takes all parameters per call.

    Returns:
        An RsiRecord bound to this provider's compute function.
    """
```

**Behaviour Rules (numbered, testable):**

1. `implementation.py` contains `_wilder_rsi` copied **character for character** from `momentum/rsi.py`, including its constants and comments.
2. The public `compute(data, *, period, source="close", config=None)` produces values identical to the current `rsi` for every input.
3. `setup` registers **no** effect on `scope`; `scope.effect_names() == ()` after activation.
4. Importing `plugin.py` or `implementation.py` triggers no registration, no I/O, and no logging — all behaviour happens inside `setup` or `compute`.
5. `__init__.py` contains only a docstring and `__all__: list[str] = []`; it imports nothing.
6. `check_conformance(SPEC, setup(scope=..., config={}))` returns `()`.
7. `example.py` runs standalone with exit code 0 and prints at most 10 bounded lines.
8. The existing `momentum/rsi.py` is **not modified or deleted** by this task.

**Implementation Steps:**

1. Create the package directories and the eight files of §3.1.
2. Copy `_wilder_rsi`, `_build_config` and the three module constants verbatim into `implementation.py`.
3. Move the body of the public `rsi` function into `implementation.compute`, keeping every line, including the logger call and the `build_indicator_result` call.
4. Write `plugin.py` with the exact `setup` above, returning `RsiRecord(compute=compute)`.
5. Write `manifest.toml` exactly as specified.
6. Write `example.py`: build a small deterministic dataset via `tests/indicators/helpers.py`, call `compute` at period 14, print the last five values.
7. Write `README.md` describing the provider, its capability, and that it registers no effect. **No `FEAT-*` id.**
8. Write the three test files per the table below.
9. Confirm provider tests are collected by `uv run pytest app/services/indicators/rsi_default/tests -q`. **If they are not collected and the fix requires editing `pyproject.toml`, STOP and report** — that file is PROTECTED.
10. Add the CHANGELOG bullet.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not modify, simplify, optimise, or re-derive the RSI formula.** Copy it verbatim; the golden parity gate will catch any drift.
- **Do not delete or edit `momentum/rsi.py` in this task.** The barrel switch is `P9-T04`, so a failure here reverts cleanly.
- Do not register any effect on `scope`; RSI is pure.
- Do not add caching, vectorisation, or a `fillna` option.
- Do not import `williams_r` or any other indicator.
- Do not add a `FEAT-*` id to the provider README.
- Do not edit `pyproject.toml` to make tests collect.
- Do not modify any PROTECTED path.

**Unit Tests**

Files: `app/services/indicators/rsi_default/tests/test_contract.py`, `test_unit.py`, `test_removability.py` (CREATE)

| Test function | File | Expected |
|---|---|---|
| `test_setup_returns_conforming_record` | `test_contract.py` | `check_conformance` returns `()` |
| `test_setup_registers_no_effect` | `test_contract.py` | `scope.effect_names() == ()` |
| `test_import_has_no_side_effects` | `test_contract.py` | importing `plugin` adds no `sys.modules` key outside `app.services.indicators` |
| `test_matches_legacy_output` | `test_unit.py` | `compute(...)` values equal `app.services.indicators.rsi(...)` values within `1e-12` |
| `test_warmup_is_nan` | `test_unit.py` | first `period` values are `NaN` |
| `test_manifest_parses_and_declares_capability` | `test_removability.py` | `load_manifest` yields `provides == (("indicator.rsi", 1),)` |

Run: `uv run pytest app/services/indicators/rsi_default/tests -q` → all pass, 0 skipped.

**Regression Tests**

`uv run pytest tests/golden tests/indicators -q` → all pass; `git diff --stat tests/fixtures/golden/indicators.json` empty.

**Usage Example**

File: `app/services/indicators/rsi_default/example.py` (CREATE)
Run: `uv run python app/services/indicators/rsi_default/example.py`

```
rsi_default period=14 last 5 values
2026-01-05  55.1234567891
… (5 lines, exit code 0)
```

**Quality Gates:**

```bash
uv run ruff format app/services/indicators/rsi_default
uv run ruff check app/services/indicators/rsi_default
uv run mypy .
uv run pytest app/services/indicators/rsi_default/tests -q
uv run python app/services/indicators/rsi_default/example.py
uv run pytest tests/golden -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added RSI as an independently removable provider package.`

**Git Commit:**

```bash
git add app/services/indicators/rsi_default docs/CHANGELOG.md
git commit -m "feat(indicators): add RSI provider package" -m "RSI becomes a self-contained provider with manifest, plugin, example and
its own tests. The formula is copied verbatim and the golden parity gate
proves output is unchanged. The legacy path is untouched until the barrel
switch.
Refs: REFACTOR_PLAN.md Phase 9, Gate G9"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Provider package created with all eight files
- [ ] All six tests passing; example exits 0
- [ ] Golden parity green, baseline unchanged
- [ ] `momentum/rsi.py` untouched
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P9-T03` — Create Williams %R provider package

**Traces to:** `REFACTOR_PLAN.md` Phase 9 Williams tasks; Gate `G9`
**Depends on:** `P9-T02`
**Estimated size:** L (120–200 LOC)

**Goal.** Williams %R becomes an independently deletable provider, identical in structure to `rsi_default`, with unchanged numeric output.

**Context to Read (and nothing else):**

- `app/services/indicators/momentum/williams_r.py` — the source; copy its formula verbatim
- `app/services/indicators/rsi_default/` — the exact template, created by `P9-T02`
- `app/capabilities/indicator/williams_r/v1.py`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/williams_r_default/` | CREATE | Provider package per §3.1 |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** the `rsi_default` package structure with `id = "indicator.williams_r.default"`, `capability_id = "indicator.williams_r"`, `entry_point = "app.services.indicators.williams_r_default.plugin:setup"`, returning `WilliamsRRecord`.

**Behaviour Rules (numbered, testable):**

1. The formula is copied verbatim from `momentum/williams_r.py`.
2. Output equals the current `williams_r` for every input, within `1e-12`.
3. `setup` registers no effect.
4. Importing the modules has no side effect.
5. The package imports nothing from `rsi_default` — the two providers are independent.
6. `momentum/williams_r.py` is not modified or deleted by this task.
7. `example.py` runs with exit code 0.

**Implementation Steps:**

1. Copy the `rsi_default` package structure.
2. Copy the Williams formula verbatim into `implementation.py`.
3. Write `plugin.py` returning `WilliamsRRecord(compute=compute)`.
4. Write `manifest.toml` with the ids above.
5. Write `example.py`, `README.md` and the three test files, mirroring `rsi_default`.
6. Add the CHANGELOG bullet.
7. Commit.

**DO NOT (anti-invention guardrails):**

- Do not modify, simplify, or re-derive the Williams %R formula.
- Do not import anything from `rsi_default`; independence is the property being proven.
- Do not delete or edit `momentum/williams_r.py` in this task.
- Do not register an effect.
- Do not add a `FEAT-*` id.
- Do not edit `pyproject.toml`.
- Do not modify any PROTECTED path.

**Unit Tests**

Files: `app/services/indicators/williams_r_default/tests/{test_contract,test_unit,test_removability}.py` (CREATE)

| Test function | File | Expected |
|---|---|---|
| `test_setup_returns_conforming_record` | `test_contract.py` | `()` |
| `test_setup_registers_no_effect` | `test_contract.py` | `effect_names() == ()` |
| `test_import_has_no_side_effects` | `test_contract.py` | no foreign `sys.modules` key |
| `test_matches_legacy_output` | `test_unit.py` | equals `app.services.indicators.williams_r` within `1e-12` |
| `test_no_rsi_import` | `test_removability.py` | module source contains no `rsi_default` |
| `test_manifest_declares_capability` | `test_removability.py` | `provides == (("indicator.williams_r", 1),)` |

Run: `uv run pytest app/services/indicators/williams_r_default/tests -q` → all pass, 0 skipped.

**Regression Tests**

`uv run pytest tests/golden tests/indicators app/services/indicators/rsi_default/tests -q` → all pass, baseline unchanged.

**Usage Example**

File: `app/services/indicators/williams_r_default/example.py` (CREATE)
Run: `uv run python app/services/indicators/williams_r_default/example.py` → 5 bounded lines, exit code 0.

**Quality Gates:**

```bash
uv run ruff format app/services/indicators/williams_r_default
uv run ruff check app/services/indicators/williams_r_default
uv run mypy .
uv run pytest app/services/indicators/williams_r_default/tests -q
uv run python app/services/indicators/williams_r_default/example.py
uv run pytest tests/golden -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added Williams %R as an independently removable provider package.`

**Git Commit:**

```bash
git add app/services/indicators/williams_r_default docs/CHANGELOG.md
git commit -m "feat(indicators): add Williams R provider package" -m "Second pilot provider, structurally identical to rsi_default and importing
nothing from it, so the two can be removed independently.
Refs: REFACTOR_PLAN.md Phase 9, Gate G9"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Provider package created with all eight files
- [ ] All six tests passing; example exits 0
- [ ] No import of `rsi_default`
- [ ] `momentum/williams_r.py` untouched
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P9-T04` — Convert momentum to a namespace

**Traces to:** `REFACTOR_PLAN.md` Phase 9 target structure; conflict `CF-07`; `AGENTS.md` §1 feature-group namespace exception; Gate `G9`
**Depends on:** `P9-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** The domain barrel resolves `rsi` and `williams_r` through the new providers, `momentum/` becomes an organizational namespace, and the two legacy modules are removed — with the public export names unchanged.

**Context to Read (and nothing else):**

- `app/services/indicators/__init__.py` — **step 1 reads this in full.** STOP and report if `rsi` or `williams_r` is exported in a way the specification below cannot preserve.
- `app/services/indicators/momentum/__init__.py` — the four-line eager barrel
- `app/services/indicators/README.md` §Feature Registry — the RSI and Williams rows to update
- Conflict `CF-07` in §7

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/__init__.py` | MODIFY | Re-point two exports |
| `app/services/indicators/momentum/__init__.py` | MODIFY | Reduce to a namespace |
| `app/services/indicators/README.md` | MODIFY | Update two registry rows |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

`app/services/indicators/momentum/rsi.py` and `williams_r.py` are **DELETE**.

**Anchor text (MODIFY).** `momentum/__init__.py` currently reads exactly:

```python
"""Approved public momentum-indicator API."""

from app.services.indicators.momentum.rsi import rsi
from app.services.indicators.momentum.williams_r import williams_r

__all__ = ["rsi", "williams_r"]
```

Replace its body entirely with a docstring declaring it a documented feature-group namespace and `__all__: list[str] = []`.

**Behaviour Rules (numbered, testable):**

1. `from app.services.indicators import rsi, williams_r` continues to work and returns callables.
2. `rsi(...)` and `williams_r(...)` produce values identical to before, proven by the golden gate.
3. `app/services/indicators/__init__.py`'s `__all__` is unchanged — the same names in the same order.
4. `momentum/` contains only `__init__.py` and `README.md` afterwards, satisfying the `AGENTS.md` §1 feature-group namespace exception.
5. `momentum/rsi.py` and `momentum/williams_r.py` no longer exist.
6. A repo grep finds no remaining reference to `app.services.indicators.momentum.rsi` or `.williams_r`.
7. The README feature rows for RSI and Williams name the new owning module folders, so `audit_check.py` `REG` stays green.

**Implementation Steps:**

1. Read `app/services/indicators/__init__.py` in full and record how `rsi` and `williams_r` are exported. STOP if the shape is not one the steps below can preserve.
2. Grep the repository for `momentum.rsi` and `momentum.williams_r`. **This is the only task authorised to grep beyond its Context to Read.** Record every hit.
3. Re-point the two exports in the domain barrel to the new provider `implementation` modules, preserving the export names and `__all__` order exactly.
4. Replace `momentum/__init__.py` with the namespace form.
5. Delete `momentum/rsi.py` and `momentum/williams_r.py`.
6. Update `momentum/README.md` to state it is a documented non-feature namespace.
7. Update the two `README.md` feature-registry rows to the new module folders.
8. Update any hit from step 2 that lies outside `tests/` — if a hit lies inside a PROTECTED path, STOP and report.
9. Add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not change any exported name, the `__all__` ordering, or any function signature.** Consumers must not notice.
- Do not alter a formula while moving the export.
- Do not delete `momentum/README.md` or `momentum/__init__.py`; the namespace exception requires both.
- Do not add a `FEAT-*` id for the namespace — a namespace owns no feature.
- Do not regenerate the golden baseline to make parity pass. If parity fails, STOP and report.
- Do not touch any other indicator family.
- Do not modify any PROTECTED path: `app/services/indicators/core/`, `migrations/`, or any non-momentum family.

**Unit Tests**

File: `tests/indicators/structural/test_momentum_namespace.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_public_exports_unchanged` | `app.services.indicators.__all__` | contains `rsi` and `williams_r` |
| `test_legacy_modules_gone` | filesystem | `momentum/rsi.py` and `momentum/williams_r.py` absent |
| `test_namespace_contents` | `momentum/` listing | only `__init__.py`, `README.md`, `__pycache__` |
| `test_namespace_all_is_empty` | `momentum.__all__` | `== []` |
| `test_no_legacy_references` | repo grep | no `momentum.rsi`, no `momentum.williams_r` |
| `test_rsi_still_callable` | `rsi(dataset, period=14)` | returns a result |

Run: `uv run pytest tests/indicators/structural/test_momentum_namespace.py -q` → all pass, 0 skipped.

**Regression Tests**

`uv run pytest tests/golden tests/indicators app/services/indicators -q` → all pass; `git diff --stat tests/fixtures/golden/indicators.json` empty.
`uv run python scripts/audit_check.py` → exit 0, `REG` unchanged.

**Usage Example** — the two provider `example.py` files continue to run:
`uv run python app/services/indicators/rsi_default/example.py` and the Williams equivalent, both exit 0.

**Quality Gates:**

```bash
uv run ruff format app/services/indicators
uv run ruff check app/services/indicators
uv run mypy .
uv run pytest tests/indicators tests/golden app/services/indicators -q
uv run python scripts/audit_check.py
git diff --stat tests/fixtures/golden/indicators.json | wc -l
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `app/services/indicators/README.md` — update the RSI and Williams feature rows to the new owning module folders.
- `app/services/indicators/momentum/README.md` — declare it a documented non-feature namespace.
- `docs/CHANGELOG.md` — `### Changed`: `- RSI and Williams %R now resolve through provider packages; momentum is a namespace.`

**Git Commit:**

```bash
git add app/services/indicators docs/CHANGELOG.md tests/indicators/structural/test_momentum_namespace.py
git commit -m "refactor(indicators): convert momentum to a namespace" -m "Re-points the domain barrel at the two provider packages and reduces
momentum to a documented feature-group namespace. Public export names and
numeric output are unchanged.
Refs: REFACTOR_PLAN.md Phase 9, CF-07, Gate G9"
```

**Re-run safety:** `Not safe — this task deletes two modules. Revert with git revert of this single commit, which restores both files and the previous barrel; then re-run.`

**Definition of Done:**

- [ ] Four files modified, two deleted, one test file created
- [ ] All six tests passing
- [ ] Golden parity green, baseline unchanged
- [ ] `audit_check.py` `REG` unchanged
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P9-T05` — Add cross-feature removability proof

**Traces to:** `REFACTOR_PLAN.md` Phase 9 cross-feature proof; Gate `G9`
**Depends on:** `P9-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** A test consumer requiring RSI but not Williams proves the four pilot properties: deleting Williams does not affect it, deleting RSI deactivates it, reinstalling RSI reactivates it, and the domain survives both.

**Context to Read (and nothing else):**

- `app/composition/root.py` — `CompositionRoot`, `activate_all`, `deactivate`
- `app/composition/config.py` — **does not exist yet**; this task uses `CapabilityRegistry` directly and `P11-T01` adds config-driven disabling
- The two provider `manifest.toml` files

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/__init__.py` | CREATE | Package marker |
| `tests/removability/test_indicator_pilot.py` | CREATE | The four proofs |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** the test module defines a consumer provider inline whose manifest requires `indicator.rsi` at `min_version=1, max_version=1` with `on_missing="fail_closed"`, and does not mention `indicator.williams_r`.

**Behaviour Rules (numbered, testable):**

1. With both providers registered, the consumer activates and the resolution order places `indicator.rsi.default` before it.
2. With `indicator.williams_r.default` absent, the consumer still activates — proving no hidden coupling.
3. With `indicator.rsi.default` absent, the consumer does **not** activate and its entry carries `reason_code=DEPENDENCY_UNAVAILABLE` with `"indicator.rsi.v1"` in the chain.
4. Re-registering `indicator.rsi.default` and re-resolving reactivates the consumer — proving reinstatement, not just removal.
5. With RSI absent, `williams_r` remains callable through the domain barrel.
6. No test regenerates the golden baseline or mutates the repository.
7. `tests/removability/` lives **outside** any provider folder, so deleting a provider never deletes the tests proving the rest of the app survives.

**Implementation Steps:**

1. Create `tests/removability/__init__.py` with a one-line docstring.
2. Create the test module and load both provider manifests with `load_manifest`.
3. Define the consumer manifest inline, pointing its `entry_point` at a `setup` defined in the same test module.
4. Add `test_consumer_activates_with_both`.
5. Add `test_williams_absence_is_harmless`.
6. Add `test_rsi_absence_deactivates_consumer`.
7. Add `test_rsi_reinstall_reactivates_consumer`.
8. Add `test_williams_still_callable_without_rsi`.
9. Add `test_baseline_untouched`.
10. Add the CHANGELOG bullet.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not place these tests inside either provider's `tests/` folder.** Rule 7 is the reason; a provider must not own the proof that the app survives without it.
- Do not physically delete files in this test; absence is modelled by not registering the manifest. Physical deletion is `P11-T03`.
- Do not mark any test `skip` or `xfail`.
- Do not regenerate `tests/fixtures/golden/indicators.json`.
- Do not modify either provider package.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/removability/test_indicator_pilot.py` (CREATE) — the six functions listed in the steps above.

| Test function | Expected |
|---|---|
| `test_consumer_activates_with_both` | consumer `ACTIVE`; RSI ordered first |
| `test_williams_absence_is_harmless` | consumer `ACTIVE` |
| `test_rsi_absence_deactivates_consumer` | inactive; `DEPENDENCY_UNAVAILABLE`; chain contains `indicator.rsi.v1` |
| `test_rsi_reinstall_reactivates_consumer` | consumer `ACTIVE` again |
| `test_williams_still_callable_without_rsi` | `williams_r(...)` returns a result |
| `test_baseline_untouched` | baseline bytes unchanged |

Run: `uv run pytest tests/removability -q` → all pass, 0 skipped.

**Usage Example** — none; this is a test artefact.

**Quality Gates:**

```bash
uv run ruff format tests/removability
uv run ruff check tests/removability
uv run mypy .
uv run pytest tests/removability tests/golden -q
git diff --stat tests/fixtures/golden/indicators.json | wc -l
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added cross-feature removability proof for the indicator pilot.`

**Git Commit:**

```bash
git add tests/removability docs/CHANGELOG.md
git commit -m "test(architecture): prove indicator pilot removability" -m "A consumer requiring RSI but not Williams proves independent removal,
correct deactivation, and reactivation on reinstall. The proofs live
outside both provider folders by design.
Refs: REFACTOR_PLAN.md Phase 9 cross-feature proof, Gate G9"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests passing
- [ ] Tests live outside both provider folders
- [ ] Baseline untouched
- [ ] Exactly one commit with the message above

---
### Phase 10 — Effectful pilot: Notifications, then a data stream

**Goal.** Prove the effectful half of the model: a provider that owns clients and queues releases every one of them on teardown, and a stream provider can be replaced without duplicating events.
**Why now.** Gate `G9` passed on the pure case. Notifications own real resources but carry no trading authority, making them the safest first effectful subject. This phase also fixes a live fragility: `app/utils/__init__.py` is fully eager today, so importing `get_logger` drags in `notifications`, `security` and every other subpackage.
**Deliverable.** Notification capability spec, a lazy utils barrel, a notification provider, a simulated stream provider, and disposal and replacement proofs.

**Phase 10 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] `uv run pytest tests/golden -q` green; baseline unchanged
- [ ] No test failing that is not in `BASELINE.md`
- [ ] `uv run python scripts/composability_barrels.py` reports `app.utils` as `lazy`
- [ ] Functional proof: importing `app.utils.get_logger` in a fresh interpreter loads **no** `app.utils.notifications` module
- [ ] Functional proof: a notification provider registering a client, a queue and a timer returns all three resource counts to zero after `deactivate()`, and its sent-notification effect is classified `irreversible_external` and is never disposed

---

#### - [ ] Task `P10-T01` — Add notification capability specification

**Traces to:** `REFACTOR_PLAN.md` Phase 10 Pilot A; resolutions `R-01`, `R-04`; Gate `G10`
**Depends on:** `P9-T05`
**Estimated size:** M (50–120 LOC)

**Goal.** A notification capability exists as a `Protocol` — the first effectful contract, exercising the other half of the `R-01` hybrid.

**Context to Read (and nothing else):**

- `app/utils/notifications/__init__.py` — **step 1 reads this** for the current public surface. STOP and report if it exposes no send-shaped function.
- `app/capabilities/indicator/rsi/v1.py` — the spec template
- Shared Contracts §3.3 (Batch 2) — `CapabilitySpec`, and `R-01`: effectful capabilities use `kind="protocol"`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/notification/__init__.py` | CREATE | Domain namespace |
| `app/capabilities/notification/channel/__init__.py` | CREATE | Capability namespace |
| `app/capabilities/notification/channel/v1.py` | CREATE | Specification |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
CAPABILITY_ID: Final[str] = "notification.channel"
VERSION: Final[int] = 1


class NotificationChannel(Protocol):
    """Structural contract for a notification transport."""

    def send(self, *, subject: str, body: str) -> bool:
        """Deliver one bounded notification.

        Args:
            subject: Short subject line.
            body: Message body; must contain no credential or account number.

        Returns:
            True when the transport accepted the message.
        """
        ...

    def channel_name(self) -> str:
        """Return the transport's stable name.

        Returns:
            A lowercase identifier such as "desktop" or "telegram".
        """
        ...


SPEC: Final[CapabilitySpec] = CapabilitySpec(
    capability_id=CAPABILITY_ID,
    version=VERSION,
    cardinality="one_of_several",
    kind="protocol",
    contract=NotificationChannel,
)

REQUIRES: Final[tuple[Requirement, ...]] = ()
```

**Behaviour Rules (numbered, testable):**

1. `SPEC.kind == "protocol"` — this is the effectful half of `R-01`.
2. `SPEC.cardinality == "one_of_several"`: many transports may exist, one is selected.
3. `check_conformance(SPEC, <object with both methods>)` returns `()`.
4. An object missing `channel_name` yields `("missing attribute: channel_name",)`.
5. An object whose `send` takes `(self, subject, message)` yields a `"parameter mismatch on send"` violation.
6. Importing the module loads no `app.services` and no `app.utils` module.
7. `REQUIRES == ()`.

**Implementation Steps:**

1. Read `app/utils/notifications/__init__.py` and record its public send-shaped function's parameters. STOP if none exists.
2. Create the two namespace `__init__.py` files with a docstring and empty `__all__`.
3. Create `v1.py` with the exact content above.
4. Add the CHANGELOG bullet.
5. Commit.

**DO NOT (anti-invention guardrails):**

- Do not import `app.utils.notifications` from the spec — `app/capabilities` imports nothing from `app.utils` (Batch 2 §3.2, `CF-04`).
- Do not use `kind="callable_record"`; a transport owns a client and a lifetime.
- Do not add `@runtime_checkable`.
- Do not add a `send_async` method; `R-02` keeps this synchronous.
- Do not add credential, token, or account parameters to `send`.
- Do not re-export from `app/capabilities/__init__.py`.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_capability_notification_channel_v1.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_spec_identity` | id `"notification.channel"`, version 1 |
| `test_kind_is_protocol` | `kind == "protocol"` |
| `test_cardinality_one_of_several` | `cardinality == "one_of_several"` |
| `test_conforming_object` | `()` |
| `test_missing_channel_name` | `("missing attribute: channel_name",)` |
| `test_parameter_mismatch_on_send` | one `"parameter mismatch on send"` violation |

Run: `uv run pytest tests/unit/test_capability_notification_channel_v1.py -q` → all pass, 0 skipped.

**Usage Example** — none; non-feature infrastructure.

**Quality Gates:**

```bash
uv run ruff format app/capabilities tests/unit/test_capability_notification_channel_v1.py
uv run ruff check app/capabilities tests/unit/test_capability_notification_channel_v1.py
uv run mypy .
uv run pytest tests/unit/test_capability_notification_channel_v1.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added notification.channel.v1 protocol capability specification.`

**Git Commit:**

```bash
git add app/capabilities/notification tests/unit/test_capability_notification_channel_v1.py docs/CHANGELOG.md
git commit -m "feat(capabilities): add notification channel specification" -m "First protocol-kind capability, exercising the effectful half of the R-01
hybrid contract model.
Refs: REFACTOR_PLAN.md Phase 10, R-01, Gate G10"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests passing
- [ ] No import of `app.utils` from the spec
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P10-T02` — Make the utils barrel lazy

**Traces to:** `REFACTOR_PLAN.md` §0.3 verified counter-example; Phase 10 Pilot A; wave 12.1 preparation; Gate `G10`
**Depends on:** `P10-T01`
**Estimated size:** L (120–200 LOC)

**Goal.** `from app.utils import get_logger` stops loading `notifications`, `security` and every other subpackage, with the exported name set unchanged.

**Context to Read (and nothing else):**

- `app/utils/__init__.py` — **step 1 reads this in full.** Verified for the first 45 lines: unconditional module-level `from app.utils.contracts import (...)`, `from app.utils.errors import (...)`, `from app.utils.idempotency import (...)`, `from app.utils.identity import ...`, `from app.utils.logging import ...`, `from app.utils.notifications import (...)`, and further blocks. STOP and report if the file contains executable logic beyond imports and `__all__`.
- `app/services/portfolio/__init__.py` — the proven lazy `_EXPORTS` + `__getattr__` pattern in this repository. **Copy its structure.**
- `scripts/composability_barrels.py` — the classifier that must report `lazy` afterwards

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/utils/__init__.py` | MODIFY | Convert to lazy `_EXPORTS` |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** the `app/services/portfolio/__init__.py` structure — `import typing`; an `if typing.TYPE_CHECKING:` block holding every current import verbatim; a module-level `_EXPORTS: dict[str, tuple[str, str]]` mapping each exported name to `(module_path, attribute)`; a module-level `__getattr__(name: str) -> object` resolving through `importlib` on first access; `__all__` listing the same names.

**Behaviour Rules (numbered, testable):**

1. `app.utils.__all__` is **exactly** the same set of names, in the same order, as before the change.
2. Every name in `__all__` has an `_EXPORTS` entry, and every `_EXPORTS` key is in `__all__`.
3. `from app.utils import get_logger` in a fresh interpreter loads `app.utils.logging` but **not** `app.utils.notifications`.
4. Accessing an unknown attribute raises `AttributeError` with the standard message shape.
5. `scripts/composability_barrels.py` classifies `app.utils` as `"lazy"` afterwards.
6. Every existing test in the repository passes with unchanged counts.
7. No behaviour, signature, or return value of any exported symbol changes.
8. `mypy --strict` still resolves every export, because the `TYPE_CHECKING` block keeps them statically visible.

**Implementation Steps:**

1. Read `app/utils/__init__.py` in full. Record every imported name and the module it comes from. STOP if the file contains logic beyond imports and `__all__`.
2. Record the current `__all__` verbatim; it must be reproduced exactly.
3. Rewrite the file following the `portfolio` template: `import typing`, the `TYPE_CHECKING` block, `_EXPORTS`, `__getattr__`, `__all__`.
4. Build `_EXPORTS` mechanically from step 1 — one entry per name, no name added or removed.
5. Run the full suite and compare counts against `BASELINE.md`.
6. Run `scripts/composability_barrels.py` and confirm `"lazy"`.
7. Add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add, remove, rename, or reorder a single exported name.** This is a mechanical lazification; any surface change makes a failure impossible to attribute.
- Do not move a symbol between subpackages.
- Do not change any subpackage's own code — only `app/utils/__init__.py`.
- Do not delete the `TYPE_CHECKING` block; `mypy --strict` needs it.
- Do not add caching beyond what `importlib` already does.
- Do not add `__dir__`, `__getattr__` fallbacks, or a deprecation shim.
- Do not modify any PROTECTED path: every `app/utils/*` subpackage.

**Unit Tests**

File: `tests/utils/test_utils_barrel_lazy.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_all_names_unchanged` | `__all__` equals a hard-coded snapshot captured in step 2 |
| `test_exports_and_all_agree` | `set(_EXPORTS) == set(__all__)` |
| `test_get_logger_does_not_load_notifications` | subprocess-free `sys.modules` check after a fresh import |
| `test_unknown_attribute_raises` | `AttributeError` |
| `test_every_export_resolves` | `getattr(app.utils, name)` succeeds for every name in `__all__` |
| `test_barrel_classified_lazy` | `classify_barrel(source)[0] == "lazy"` |

Run: `uv run pytest tests/utils/test_utils_barrel_lazy.py -q` → all pass, 0 skipped.

**Regression Tests**

**The regression gate for this task is the entire suite**, because every domain imports from `app.utils`:
`uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` → collected / passed / failed / skipped counts identical to `docs/dev/plugin-decoupling/BASELINE.md`.
`uv run pytest tests/golden -q` → green, baseline unchanged.

**Usage Example** — none; `app/utils` carries no numbered usage program change.

**Quality Gates:**

```bash
uv run ruff format app/utils/__init__.py tests/utils/test_utils_barrel_lazy.py
uv run ruff check app/utils tests/utils
uv run mypy .
uv run pytest tests/utils -q
uv run python scripts/composability_barrels.py
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Changed`: `- app.utils barrel is now lazy; importing one utility no longer loads every subpackage.`

**Git Commit:**

```bash
git add app/utils/__init__.py tests/utils/test_utils_barrel_lazy.py docs/CHANGELOG.md
git commit -m "refactor(utils): make the utils barrel lazy" -m "Converts the eager barrel to the lazy _EXPORTS pattern already proven in
portfolio. Importing get_logger no longer loads notifications, security or
serialization. Export names are unchanged.
Refs: REFACTOR_PLAN.md section 0.3, Phase 10, Gate G10"
```

**Re-run safety:** `Not safe to re-apply on top of itself — the file is rewritten. Revert this single commit to restore the eager barrel, then re-run.`

**Definition of Done:**

- [ ] One file modified, one test file created, one CHANGELOG line
- [ ] All six tests passing
- [ ] Full suite counts identical to baseline
- [ ] `app.utils` classified `lazy`
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P10-T03` — Create notification provider package

**Traces to:** `REFACTOR_PLAN.md` Phase 10 Pilot A; decisions `D-06`, `D-07`; Gate `G10`
**Depends on:** `P10-T02`
**Estimated size:** L (120–200 LOC)

**Goal.** A notification transport becomes a provider that owns its client on an `EffectScope`, and records a sent message as an irreversible effect.

**Context to Read (and nothing else):**

- `app/utils/notifications/__init__.py` — the existing transport behaviour to wrap
- `app/capabilities/notification/channel/v1.py` — the Protocol to satisfy
- `app/services/indicators/rsi_default/` — the provider layout template
- Shared Contracts §3.1 and Batch 2 §3.9 — `Effect`, `EffectScope`, the three effect classes

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/notifications/desktop_default/` | CREATE | Provider package per §3.1 |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```toml
[provider]
id = "notification.channel.desktop"
version = 1
entry_point = "app.services.notifications.desktop_default.plugin:setup"

[[provides]]
capability_id = "notification.channel"
version = 1

[[effects]]
name = "client"
effect_class = "reversible_ephemeral"

[[effects]]
name = "delivered_messages"
effect_class = "irreversible_external"
```

`setup` returns an object satisfying `NotificationChannel`, and registers on `scope`: a `reversible_ephemeral` effect named `client` whose disposer closes the transport, and an `irreversible_external` effect named `delivered_messages` whose disposer is never called.

**Behaviour Rules (numbered, testable):**

1. `check_conformance(SPEC, setup(...))` returns `()`.
2. `scope.effect_names()` after `setup` equals `("client", "delivered_messages")`, in registration order.
3. `scope.has_irreversible()` is `True`.
4. `scope.dispose()` calls the `client` disposer and **never** the `delivered_messages` disposer.
5. `send` returns `True` on acceptance and `False` on transport refusal; it never raises for a refusal.
6. `send` never writes a credential, token, account number, or full payload to the log — `AGENTS.md` §2 and §3.
7. Importing `plugin.py` opens no transport and registers nothing; everything happens inside `setup`.
8. `channel_name()` returns `"desktop"`.

**Implementation Steps:**

1. Create the package with the eight files of §3.1.
2. Wrap the existing `app.utils.notifications` transport in `implementation.py` as a class satisfying `NotificationChannel`.
3. In `plugin.setup`, construct the transport, register the two effects per the manifest, and return the object.
4. Write `manifest.toml` exactly as specified.
5. Write `example.py` sending one bounded message to a stubbed transport and printing the result. **It must not send a real notification.**
6. Write `README.md`; no `FEAT-*` id.
7. Write the three test files per the table below.
8. Add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not dispose the `delivered_messages` effect, and do not add any recall, unsend, or retraction path.** A sent message is irreversible; the lifecycle records it and stops.
- Do not send a real notification from `example.py` or any test — `AGENTS.md` §3 forbids real sends outside verified non-production targets.
- Do not log a credential, token, account number, or full payload.
- Do not open the transport at import time.
- Do not raise from `send` on a refusal; return `False`.
- Do not modify `app/utils/notifications/` behaviour; wrap it.
- Do not add `async def`.
- Do not modify any PROTECTED path.

**Unit Tests**

Files: `app/services/notifications/desktop_default/tests/{test_contract,test_unit,test_lifecycle}.py` (CREATE)

| Test function | File | Expected |
|---|---|---|
| `test_conforms_to_protocol` | `test_contract.py` | `()` |
| `test_registers_two_effects` | `test_contract.py` | `("client", "delivered_messages")` |
| `test_import_opens_no_transport` | `test_contract.py` | no transport constructed on import |
| `test_send_refusal_returns_false` | `test_unit.py` | `False`, no exception |
| `test_dispose_closes_client_only` | `test_lifecycle.py` | client closed; irreversible disposer never called |
| `test_no_secrets_logged` | `test_lifecycle.py` | caplog text contains no token or account substring |

Run: `uv run pytest app/services/notifications/desktop_default/tests -q` → all pass, 0 skipped.

**Usage Example**

File: `app/services/notifications/desktop_default/example.py` (CREATE)
Run: `uv run python app/services/notifications/desktop_default/example.py` → prints channel name and a stubbed send result, exit code 0, no real notification sent.

**Quality Gates:**

```bash
uv run ruff format app/services/notifications
uv run ruff check app/services/notifications
uv run mypy .
uv run pytest app/services/notifications/desktop_default/tests -q
uv run python app/services/notifications/desktop_default/example.py
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added desktop notification provider owning its client on an effect scope.`

**Git Commit:**

```bash
git add app/services/notifications docs/CHANGELOG.md
git commit -m "feat(notifications): add desktop channel provider" -m "First effectful provider. Owns its transport client as a reversible effect
and records delivered messages as irreversible, so teardown closes the
client and never attempts to unsend.
Refs: REFACTOR_PLAN.md Phase 10, D-06, D-07, Gate G10"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Provider package created with all eight files
- [ ] All six tests passing; example exits 0 with no real send
- [ ] Irreversible effect never disposed
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P10-T04` — Add notification disposal proof

**Traces to:** `REFACTOR_PLAN.md` Phase 5 exit gate (resource counts return to zero); Phase 10 Pilot A; Gate `G10`
**Depends on:** `P10-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** An end-to-end proof that activating and deactivating an effectful provider leaves zero live resources and refuses teardown while an irreversible effect is in flight.

**Context to Read (and nothing else):**

- `app/composition/root.py` — `activate_all`, `deactivate`
- `app/kernel/lifecycle.py` — `can_dispose`, `deactivate`
- The notification provider `manifest.toml`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_notification_lifecycle.py` | CREATE | The proof |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Behaviour Rules (numbered, testable):**

1. After `activate_all`, the provider's scope reports two effects.
2. After a clean `deactivate`, the reversible client disposer has run exactly once.
3. The irreversible disposer has run zero times, always.
4. The component's final state is `STOPPED` when the client disposer succeeds.
5. When the client disposer raises, the final state is `FAILED_CLEANUP` and the failure name is returned.
6. A component whose scope still holds an in-flight irreversible effect refuses `can_dispose`, and `CompositionRoot.deactivate` aborts the cascade rather than forcing it.
7. No test sends a real notification.
8. The test lives outside the provider package.

**Implementation Steps:**

1. Create the test module in `tests/removability/`.
2. Register the notification manifest with a `CapabilityRegistry` and activate through `CompositionRoot`.
3. Add `test_two_effects_registered`.
4. Add `test_clean_deactivate_disposes_client_once`.
5. Add `test_irreversible_never_disposed`.
6. Add `test_failing_client_disposer_reaches_failed_cleanup`.
7. Add `test_in_flight_irreversible_refuses_teardown`.
8. Add `test_no_real_send`.
9. Add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not place this test inside the provider package; deleting the provider must not delete the proof.
- Do not send a real notification.
- Do not force teardown past a refusal, and do not assert that forcing works.
- Do not mark any test `skip` or `xfail`.
- Do not modify the provider package.
- Do not modify any PROTECTED path.

**Unit Tests** — the six functions above, in `tests/removability/test_notification_lifecycle.py`.

Run: `uv run pytest tests/removability -q` → all twelve pass (six from `P9-T05`), 0 skipped.

**Usage Example** — none; test artefact.

**Quality Gates:**

```bash
uv run ruff format tests/removability
uv run ruff check tests/removability
uv run mypy .
uv run pytest tests/removability -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added notification lifecycle proof covering disposal and quiesce refusal.`

**Git Commit:**

```bash
git add tests/removability/test_notification_lifecycle.py docs/CHANGELOG.md
git commit -m "test(architecture): prove notification effect disposal" -m "End-to-end proof that an effectful provider returns every reversible
resource on teardown, never disposes an irreversible effect, and refuses
teardown while one is in flight.
Refs: REFACTOR_PLAN.md Phase 5 exit gate, Phase 10, Gate G10"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] One file created, one modified, no others
- [ ] All six tests passing alongside the six from `P9-T05`
- [ ] No real notification sent
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P10-T05` — Create simulated stream provider package

**Traces to:** `REFACTOR_PLAN.md` Phase 10 Pilot B; Gate `G10`
**Depends on:** `P10-T04`
**Estimated size:** L (120–200 LOC)

**Goal.** A bounded simulated market-data stream becomes a provider owning a subscription, a buffer and a task, so replacement and reconnection can be tested without a broker.

**Context to Read (and nothing else):**

- `app/services/notifications/desktop_default/` — the effectful provider template
- `app/kernel/scope.py` — `Effect`, `EffectScope`
- Shared Contracts §3.1
- Planner Observation §9.6 — why this is the simulated stream, not a live one

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/market/stream/__init__.py`, `v1.py` and its parent namespace | CREATE | `market.stream.v1` protocol spec |
| `app/services/data/simulated_stream/` | CREATE | Provider package per §3.1 |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
class MarketStream(Protocol):
    def subscribe(self, *, symbol: str) -> str: ...
    def poll(self, *, subscription_id: str, limit: int) -> tuple[object, ...]: ...
    def unsubscribe(self, *, subscription_id: str) -> None: ...
```

`SPEC` uses `cardinality="one_of_several"`, `kind="protocol"`. The provider manifest declares three `reversible_ephemeral` effects: `subscription`, `buffer`, `poller`.

**Behaviour Rules (numbered, testable):**

1. The stream is deterministic: the same symbol and sequence position always yields the same tick. **No `random`, no wall clock.**
2. `subscribe` registers the `subscription` effect; `poll` never registers a new effect.
3. `poll` returns at most `limit` items and never blocks.
4. `unsubscribe` is idempotent: a second call is a no-op, not an error.
5. `scope.dispose()` releases all three effects in reverse registration order.
6. No effect is `irreversible_external`; a simulated stream sends nothing externally.
7. The provider touches no broker, no network, and no database, and never reads `ENVIRONMENT`.
8. Importing the modules starts no task and opens no subscription.

**Implementation Steps:**

1. Create the `market.stream.v1` capability namespaces and spec, mirroring `notification/channel/v1.py`.
2. Create the provider package with the eight files of §3.1.
3. Implement a deterministic tick generator seeded by `(symbol, index)`.
4. Register the three effects in `setup`.
5. Implement `subscribe`, `poll`, `unsubscribe` per rules 2–4.
6. Write `manifest.toml`, `example.py`, `README.md` and the three test files.
7. Add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not connect to a live broker, a socket, or the network.** `AGENTS.md` §3 forbids live operation from tests, and a live stream would make the pilot non-deterministic.
- Do not use `random`, `secrets`, `time.time`, or `datetime.now`.
- Do not add an `irreversible_external` effect; nothing leaves the process.
- Do not add `async def`; `R-02` keeps this synchronous.
- Do not read `ENVIRONMENT` or any credential.
- Do not modify `app/services/data/` outside the new package directory.
- Do not modify any PROTECTED path.

**Unit Tests**

Files: `app/services/data/simulated_stream/tests/{test_contract,test_unit,test_lifecycle}.py` (CREATE)

| Test function | File | Expected |
|---|---|---|
| `test_conforms_to_protocol` | `test_contract.py` | `()` |
| `test_deterministic_ticks` | `test_unit.py` | two runs yield identical sequences |
| `test_poll_respects_limit` | `test_unit.py` | `len(result) <= limit` |
| `test_unsubscribe_idempotent` | `test_unit.py` | second call is a no-op |
| `test_three_effects_disposed_in_reverse` | `test_lifecycle.py` | reverse order confirmed |
| `test_no_network_symbols` | `test_lifecycle.py` | module source has no `socket`, `requests`, `urllib` |

Run: `uv run pytest app/services/data/simulated_stream/tests -q` → all pass, 0 skipped.

**Usage Example**

File: `app/services/data/simulated_stream/example.py` (CREATE) → subscribes, polls five ticks, unsubscribes, prints five bounded lines, exit code 0.

**Quality Gates:**

```bash
uv run ruff format app/capabilities/market app/services/data/simulated_stream
uv run ruff check app/capabilities/market app/services/data/simulated_stream
uv run mypy .
uv run pytest app/services/data/simulated_stream/tests tests/architecture -q
uv run python app/services/data/simulated_stream/example.py
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added deterministic simulated market stream provider.`

**Git Commit:**

```bash
git add app/capabilities/market app/services/data/simulated_stream docs/CHANGELOG.md
git commit -m "feat(data): add simulated market stream provider" -m "A deterministic bounded stream owning a subscription, buffer and poller as
reversible effects, so replacement and reconnection can be proven without a
broker or the network.
Refs: REFACTOR_PLAN.md Phase 10 Pilot B, Gate G10"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Capability spec and provider package created
- [ ] All six tests passing; example exits 0
- [ ] No network, no randomness, no clock
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P10-T06` — Add stream replacement proof

**Traces to:** `REFACTOR_PLAN.md` Phase 10 Pilot B (draining with active leases, reconnection as a new generation, no duplicate events); Gate `G10`
**Depends on:** `P10-T05`
**Estimated size:** M (50–120 LOC)

**Goal.** Replacing a stream provider produces a new generation, drains the old one cleanly while a consumer holds a lease, and emits no duplicate events.

**Context to Read (and nothing else):**

- `app/composition/root.py` — `activate_all`, `deactivate`, `generation`, `pinned_graph`
- `app/composition/generations.py` — `ProviderGeneration`, `pin`
- The simulated stream provider package

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_stream_replacement.py` | CREATE | The proof |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Behaviour Rules (numbered, testable):**

1. Re-activating the stream provider yields generation 2 with a different `generation` number and the same `provider_id`.
2. A consumer holding a subscription across the replacement observes **no duplicate tick**: the concatenated sequence is strictly increasing in sequence position.
3. The old generation's three effects are all disposed exactly once.
4. `pinned_graph()` changes between generations, so a simulation run pinned to generation 1 is distinguishable from one pinned to generation 2.
5. Draining while a lease is active does not raise; the lease is released by the scope disposer.
6. `config_digest` is unchanged when the config is unchanged, so a replacement with identical config is detectable as such.
7. The test uses no broker, no network, and no clock.

**Implementation Steps:**

1. Create the test module in `tests/removability/`.
2. Activate the stream provider through `CompositionRoot` and record generation 1 and `pinned_graph()`.
3. Subscribe and poll a few ticks.
4. Deactivate, re-activate, record generation 2.
5. Add the six tests per the rules above.
6. Add the CHANGELOG bullet.
7. Commit.

**DO NOT (anti-invention guardrails):**

- Do not place this test inside the provider package.
- Do not connect to a broker or the network.
- Do not assert on wall-clock timing or add a `sleep`.
- Do not mark any test `skip` or `xfail`.
- Do not modify the provider package or `app/composition/`.
- Do not modify any PROTECTED path.

**Unit Tests** — six functions in `tests/removability/test_stream_replacement.py` matching rules 1–6.

Run: `uv run pytest tests/removability -q` → all eighteen pass, 0 skipped.

**Usage Example** — none; test artefact.

**Quality Gates:**

```bash
uv run ruff format tests/removability
uv run ruff check tests/removability
uv run mypy .
uv run pytest tests/removability -q
uv run python scripts/composability_barrels.py
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added stream replacement proof covering generations, draining and duplicate suppression.`

**Git Commit:**

```bash
git add tests/removability/test_stream_replacement.py docs/CHANGELOG.md
git commit -m "test(architecture): prove stream generational replacement" -m "Replacing a stream yields a new generation, drains the old one with a lease
held, emits no duplicate ticks, and changes the pinned graph.
Refs: REFACTOR_PLAN.md Phase 10 Pilot B, Gate G10"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] One file created, one modified, no others
- [ ] All six tests passing alongside the twelve existing removability tests
- [ ] No broker, network, clock or sleep
- [ ] Exactly one commit with the message above

---

### Phase 11 — Deletion, reinstall and enforcement CI

**Goal.** Removability stops being an aspiration and becomes a gate that runs on every merge.
**Why now.** Gates `G9` and `G10` passed: pure and effectful providers both work. There are now real providers to remove.
**Deliverable.** Loader configuration, a config-disable matrix, a fresh-process deletion proof, a reinstall cycle, a required-provider refusal assertion, and CI wiring.

**Phase 11 Exit Gate:**

- [ ] Every task checked off
- [ ] `uv run ruff check .`, `uv run mypy .` clean; full coverage gate green
- [ ] `uv run python scripts/deletion_matrix.py` exits 0
- [ ] `uv run python scripts/deletion_proof.py --provider app/services/indicators/williams_r_default` exits 0
- [ ] `uv run pytest tests/removability -q` green
- [ ] No test failing that is not in `BASELINE.md`
- [ ] The composability gates are wired into `.github/` and fail the build on regression

---

#### - [ ] Task `P11-T01` — Add loader configuration

**Traces to:** `REFACTOR_PLAN.md` Phase 2 loader config; Phase 11 proof 1; Gate `G11`
**Depends on:** `P10-T06`
**Estimated size:** M (50–120 LOC)

**Goal.** A declarative file decides which providers are enabled, giving the deletion matrix its mechanism.

**Context to Read (and nothing else):**

- Shared Contracts §3.3 — the TOML shape and the frozen rules
- `app/kernel/manifests.py` — the `tomllib` parsing pattern to mirror
- `app/kernel/registry.py` — `CapabilityRegistry.register(..., enabled=...)`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `config/providers.toml` | CREATE | The configuration |
| `app/composition/config.py` | CREATE | The reader |
| `app/composition/__init__.py` | MODIFY | Add two exports |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.3.

**Behaviour Rules (numbered, testable):**

1. A provider absent from the file is **enabled**; absence is not disablement.
2. `enabled = false` disables; `enabled = true` is explicit and equivalent to absence.
3. An unknown top-level key raises `KernelError` `"invalid loader config at {path}: unknown key {key}"`.
4. A missing `schema_version` raises `KernelError` with detail `"missing schema_version"`.
5. A `schema_version` other than `1` raises `"unsupported schema_version: {n}"`.
6. A missing config file raises `KernelError` `"loader config not found: {path}"` — it does not silently default, because silently enabling everything would make a disabled-provider test pass for the wrong reason.
7. `LoaderConfig.is_enabled` applies rules 1–2.
8. The reader performs no import and no activation.

**Implementation Steps:**

1. Create `config/providers.toml` with `schema_version = 1` and explicit entries for the four providers built so far.
2. Create `app/composition/config.py` with a module docstring and `from __future__ import annotations`.
3. Import `tomllib`, `dataclass`, `Path`, `Final`; import `KernelError` from `app.kernel`.
4. Add `DEFAULT_CONFIG_PATH` and the frozen `LoaderConfig` dataclass.
5. Implement `load_loader_config` per rules 3–6.
6. Implement `is_enabled` per rules 1–2.
7. Update `app/composition/__init__.py`; add the CHANGELOG bullet.
8. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not default to an empty config when the file is missing** — rule 6 exists so a broken path cannot silently make every deletion test pass.
- Do not read environment variables to override the file.
- Do not import or activate anything from the reader.
- Do not add a `[settings]` or per-provider config block; provider configuration is separate and out of scope here.
- Do not add a YAML or JSON alternative.
- Do not add `async def`.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_composition_config.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_absent_provider_is_enabled` | `is_enabled("unlisted.p") is True` |
| `test_explicit_false_disables` | `is_enabled(...) is False` |
| `test_missing_schema_version_rejected` | `KernelError`, `"missing schema_version"` |
| `test_unsupported_version_rejected` | `KernelError`, `"unsupported schema_version: 2"` |
| `test_unknown_key_rejected` | `KernelError`, `"unknown key"` |
| `test_missing_file_raises` | `KernelError`, `"loader config not found"` |

Run: `uv run pytest tests/unit/test_composition_config.py -q` → all pass, 0 skipped.

**Usage Example** — none; non-feature infrastructure.

**Quality Gates:**

```bash
uv run ruff format app/composition tests/unit/test_composition_config.py
uv run ruff check app/composition tests/unit/test_composition_config.py
uv run mypy .
uv run pytest tests/unit/test_composition_config.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added declarative loader configuration controlling which providers are enabled.`

**Git Commit:**

```bash
git add config/providers.toml app/composition/config.py app/composition/__init__.py tests/unit/test_composition_config.py docs/CHANGELOG.md
git commit -m "feat(composition): add loader configuration" -m "Declarative per-provider enablement, the mechanism the deletion matrix uses.
A missing config file is an error rather than a silent enable-all.
Refs: REFACTOR_PLAN.md Phase 2 loader, Phase 11, Gate G11"
```

**Re-run safety:** `Safe — CREATE-only apart from one anchored export insertion and one CHANGELOG line`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests passing
- [ ] Missing file raises rather than defaulting
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P11-T02` — Add config-disable matrix runner

**Traces to:** `REFACTOR_PLAN.md` Phase 11 proof 1; conflict `CF-08`; Gate `G11`
**Depends on:** `P11-T01`
**Estimated size:** L (120–200 LOC)

**Goal.** For every optional provider, disable it, boot, and assert the app starts and the capability reports unavailable — fast enough to gate every merge.

**Context to Read (and nothing else):**

- Shared Contracts §3.4 — the contract and `REQUIRED_PROVIDER_IDS`
- `app/composition/config.py`, `app/composition/root.py`
- Batch 1 §1 — why this lives in `scripts/` (the `S603`/`S607` ignores)
- Conflict `CF-08` in §7

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/deletion_matrix.py` | CREATE | The matrix runner |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.4.

**Behaviour Rules (numbered, testable):**

1. For each provider id, a temporary config is written disabling exactly that one; every other provider stays enabled.
2. The boot happens in a **subprocess** with a fresh interpreter, so a stale `sys.modules` entry in the runner cannot mask a coupling.
3. A record is produced per provider: `provider_id`, `boot_ok`, `capability_state`, `dependents_ok`.
4. `boot_ok` is `False` when the subprocess exits non-zero.
5. `capability_state` is the resolver state string reported for the disabled provider's capability; the expected value is `"NOT_INSTALLED"`.
6. `main()` exits 1 if any optional provider has `boot_ok is False`, and exits 1 if any id in `REQUIRED_PROVIDER_IDS` **succeeds** in booting while disabled — the inverse assertion.
7. `REQUIRED_PROVIDER_IDS` is empty at this commit, so the inverse assertion passes vacuously.
8. The runner never modifies `config/providers.toml` in place; it writes to a temporary directory.
9. `main()` prints one line per provider and one summary line.

**Implementation Steps:**

1. Create `scripts/deletion_matrix.py` with the shebang, docstring and constants.
2. Add `REQUIRED_PROVIDER_IDS` as an empty `frozenset` with a comment naming Batch 5 as where it fills in.
3. Discover provider ids by walking manifests with `discover_manifests`.
4. For each id, write a temporary config per rule 1 with `tempfile.TemporaryDirectory`.
5. Boot in a subprocess per rule 2, passing the config path by argument.
6. Collect records per rule 3 and evaluate rules 4–6.
7. Print per rule 9 and return the exit code.
8. Add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not boot in-process.** Rule 2 exists because an already-imported module can hide the very coupling this matrix is meant to find.
- **Do not modify `config/providers.toml`.** Write to a temp directory.
- Do not populate `REQUIRED_PROVIDER_IDS` — no genuinely required provider exists yet, and listing one would cite an artefact that does not exist.
- Do not run combinatorial removals; N=1 only.
- Do not silently skip a provider whose subprocess times out; record it as `boot_ok = False`.
- Do not import `app` at module scope in the runner.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_deletion_matrix.py` (CREATE) — load the script with the Batch 1 §3.6 helper.

| Test function | Expected |
|---|---|
| `test_required_ids_empty` | `REQUIRED_PROVIDER_IDS == frozenset()` |
| `test_record_shape` | each record has the four keys |
| `test_temp_config_disables_one` | generated config disables exactly one id |
| `test_source_config_untouched` | `config/providers.toml` bytes unchanged after a run |
| `test_uses_subprocess` | module source contains `subprocess` |
| `test_no_module_scope_app_import` | module source has no top-level `import app` |

Run: `uv run pytest tests/unit/test_deletion_matrix.py -q` → all pass, 0 skipped.

**Usage Example**

Run: `uv run python scripts/deletion_matrix.py`

```
indicator.rsi.default        boot=ok  capability=NOT_INSTALLED  dependents=ok
indicator.williams_r.default boot=ok  capability=NOT_INSTALLED  dependents=ok
4 providers checked, 0 failures
```

Exit code 0.

**Quality Gates:**

```bash
uv run ruff format scripts/deletion_matrix.py tests/unit/test_deletion_matrix.py
uv run ruff check scripts/deletion_matrix.py tests/unit/test_deletion_matrix.py
uv run mypy .
uv run pytest tests/unit/test_deletion_matrix.py -q
uv run python scripts/deletion_matrix.py
git diff --stat config/providers.toml | wc -l
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The `wc -l` must print `0`.

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added config-disable deletion matrix booting each provider-disabled configuration.`

**Git Commit:**

```bash
git add scripts/deletion_matrix.py tests/unit/test_deletion_matrix.py docs/CHANGELOG.md
git commit -m "feat(architecture): add config-disable deletion matrix" -m "Disables each optional provider in turn, boots in a fresh subprocess, and
asserts the app starts with the capability reporting NOT_INSTALLED. Carries
the inverse assertion for required providers.
Refs: REFACTOR_PLAN.md Phase 11 proof 1, CF-08, Gate G11"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests passing; runner exits 0
- [ ] Source config untouched
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P11-T03` — Add fresh-process deletion proof

**Traces to:** `REFACTOR_PLAN.md` Phase 11 proof 2; conflict `CF-08`; Gate `G11`
**Depends on:** `P11-T02`
**Estimated size:** L (120–200 LOC)

**Goal.** Physically delete a provider folder in a copied tree and prove the app still boots — the only check that can catch a coupling masked by an already-imported module.

**Context to Read (and nothing else):**

- Shared Contracts §3.5 — the contract
- `scripts/deletion_matrix.py` — the subprocess pattern to mirror
- Conflict `CF-08` in §7 — why this exists alongside the matrix

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/deletion_proof.py` | CREATE | The proof runner |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.5, with a `--provider <repo-relative-path>` argument and an optional `--keep` flag that leaves the work tree for inspection.

**Behaviour Rules (numbered, testable):**

1. The source tree is **never mutated**; the copy happens into a `tempfile` directory unless `--keep` is given.
2. The copy excludes `.git`, `.venv`, `node_modules`, `__pycache__`, and every cache directory, so it is fast.
3. The named provider directory is deleted from the copy.
4. Every check runs in one **fresh interpreter subprocess** with the copy as `cwd`: import the kernel, import the app, resolve, call the affected capability.
5. The subprocess asserts that no `sys.modules` key names the deleted package — a stale entry means the check is invalid, and the step is recorded as failed rather than passed.
6. A record is returned per step with `ok` and a short reason.
7. `main()` exits 0 only when every step is `ok`, and prints one line per step.
8. An unreadable or absent `--provider` path exits 1 with `provider path not found: {path}`.

**Implementation Steps:**

1. Create `scripts/deletion_proof.py` with the shebang, docstring and `argparse` setup.
2. Implement the filtered copy per rules 1–2 using `shutil.copytree` with an `ignore` callable.
3. Delete the provider directory from the copy per rule 3.
4. Write the check body as a small Python program string and run it with `subprocess.run([sys.executable, "-c", ...], cwd=work_root)`.
5. Include the `sys.modules` assertion of rule 5 inside that program.
6. Parse the subprocess output into step records per rule 6.
7. Implement `main()` per rules 7–8.
8. Add the CHANGELOG bullet.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not delete anything in the source tree.** Every deletion happens in the copy.
- **Do not run the checks in-process.** Rule 4 is the entire reason this task exists separately from `P11-T02`.
- Do not treat a stale `sys.modules` entry as a pass; rule 5 makes it a failure.
- Do not copy `.git` — it makes the run slow enough to be skipped, and a skipped gate is no gate.
- Do not add a `--fix` or auto-repair mode.
- Do not modify `scripts/deletion_matrix.py`.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_deletion_proof.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_source_tree_untouched` | after a run, `git status --porcelain` is empty |
| `test_copy_excludes_git` | the work tree has no `.git` |
| `test_missing_provider_path_exits_one` | exit code 1, message matches |
| `test_step_records_have_ok_flag` | every record has `ok` and `reason` |
| `test_uses_fresh_subprocess` | module source contains `sys.executable` |
| `test_stale_module_is_a_failure` | a simulated stale entry yields `ok is False` |

Run: `uv run pytest tests/unit/test_deletion_proof.py -q` → all pass, 0 skipped.

**Usage Example**

Run: `uv run python scripts/deletion_proof.py --provider app/services/indicators/williams_r_default`

```
copy tree            ok
delete provider      ok
import kernel        ok
import app           ok
resolve              ok
capability status    ok  NOT_INSTALLED
stale module check   ok
```

Exit code 0.

**Quality Gates:**

```bash
uv run ruff format scripts/deletion_proof.py tests/unit/test_deletion_proof.py
uv run ruff check scripts/deletion_proof.py tests/unit/test_deletion_proof.py
uv run mypy .
uv run pytest tests/unit/test_deletion_proof.py -q
uv run python scripts/deletion_proof.py --provider app/services/indicators/williams_r_default
git status --porcelain | wc -l
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The `wc -l` must print `0` apart from the files this task itself added before commit.

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added fresh-process physical deletion proof with stale-module detection.`

**Git Commit:**

```bash
git add scripts/deletion_proof.py tests/unit/test_deletion_proof.py docs/CHANGELOG.md
git commit -m "feat(architecture): add fresh-process deletion proof" -m "Copies the tree, deletes a provider, and runs every check in a fresh
interpreter, failing when a stale sys.modules entry would mask the
deletion. Complements rather than replaces the config-disable matrix.
Refs: REFACTOR_PLAN.md Phase 11 proof 2, CF-08, Gate G11"
```

**Re-run safety:** `Safe — operates on a temporary copy; the source tree is never mutated`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests passing; the proof exits 0 for Williams
- [ ] Source tree unmutated
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P11-T04` — Add reinstall cycle proof

**Traces to:** `REFACTOR_PLAN.md` Phase 11 proof 3 and Phase 8 install→disable→reinstall cycle; decision `D-09`; Gate `G11`
**Depends on:** `P11-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** Remove, restart, reinstall — and prove consumers reactivate and declared state is preserved, closing the loop that the Phase 8 tasks could only declare.

**Context to Read (and nothing else):**

- `app/composition/retention.py` — `decide_retention`
- `app/composition/tombstones.py` — `reconcile`, `blocks_database_access`
- `app/composition/root.py` — `activate_all`, `deactivate`
- The two indicator provider manifests

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_reinstall_cycle.py` | CREATE | The cycle proof |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Behaviour Rules (numbered, testable):**

1. Activate → deactivate → re-register → activate again returns the consumer to `ACTIVE`.
2. The reinstalled provider receives a **new generation number**, not a reuse of the old.
3. `decide_retention` for a stateful manifest returns `"preserve"` and `purge_authorized is False` across the whole cycle.
4. A ledger entry whose owner is absent during the removed window classifies as `tombstoned`, and `blocks_database_access()` is `False` throughout.
5. When the owner returns, the same entry classifies as `owned` again.
6. No step of the cycle drops, alters, or renames anything; the test asserts no destructive call is made.
7. The cycle runs without a database, a broker, or the network.

**Implementation Steps:**

1. Create the test module in `tests/removability/`.
2. Build a stateful manifest fixture declaring `state_schema_id` and `uninstall_retention = "preserve"`.
3. Add `test_consumer_reactivates_after_reinstall`.
4. Add `test_reinstall_gets_new_generation`.
5. Add `test_retention_preserved_across_cycle`.
6. Add `test_tombstone_does_not_block_during_removal`.
7. Add `test_owner_returns_reclassifies_as_owned`.
8. Add `test_no_destructive_call`.
9. Add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not connect to a real database or run a real migration; `reconcile` is a pure classifier and the test supplies ledger entries directly.
- Do not drop or alter a table anywhere in the cycle.
- Do not assert that purge is possible; `purge_authorized` is always `False`.
- Do not place this test inside a provider package.
- Do not mark any test `skip` or `xfail`.
- Do not modify any PROTECTED path.

**Unit Tests** — the six functions above, in `tests/removability/test_reinstall_cycle.py`.

Run: `uv run pytest tests/removability -q` → all twenty-four pass, 0 skipped.

**Usage Example** — none; test artefact.

**Quality Gates:**

```bash
uv run ruff format tests/removability
uv run ruff check tests/removability
uv run mypy .
uv run pytest tests/removability -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added remove-restart-reinstall cycle proof covering reactivation and state retention.`

**Git Commit:**

```bash
git add tests/removability/test_reinstall_cycle.py docs/CHANGELOG.md
git commit -m "test(architecture): prove remove and reinstall cycle" -m "Closes the temporal loop: a removed provider's consumers reactivate on
reinstall, its state is preserved, and an owner-absent ledger entry never
blocks database access.
Refs: REFACTOR_PLAN.md Phase 11 proof 3, D-09, Gate G11"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] One file created, one modified, no others
- [ ] All six tests passing alongside the eighteen existing removability tests
- [ ] No destructive operation anywhere in the cycle
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P11-T05` — Add required-provider refusal assertion

**Traces to:** `REFACTOR_PLAN.md` Phase 11 inverse assertion; `AGENTS.md` §3 fail-closed; Gate `G11`
**Depends on:** `P11-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** Prove that a provider declared required makes the system refuse to boot when absent — so fail-closed is tested as deliberately as degradation.

**Context to Read (and nothing else):**

- `app/composition/policy.py` — `PROFILE_REQUIRED_CAPABILITIES`, currently empty
- `app/kernel/profiles.py` — `evaluate_readiness`
- `app/runtime.py` — `validate_profile_readiness`, added by `P7-T04`
- `scripts/deletion_matrix.py` — `REQUIRED_PROVIDER_IDS`, currently empty

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_required_refusal.py` | CREATE | The inverse assertion |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Behaviour Rules (numbered, testable):**

1. With a **synthetic** policy table requiring a capability that has no provider, `validate_profile_readiness` returns an error response, never a success.
2. The error carries `reason_code=PROFILE_REQUIREMENT_UNSATISFIED`.
3. A `DEGRADED` provider does not satisfy the requirement — degraded is not ready.
4. With the requirement satisfied, the same call returns success.
5. The test uses a synthetic policy passed in, and does **not** mutate `PROFILE_REQUIREMENT_CAPABILITIES` or add a real capability id to it.
6. `REQUIRED_PROVIDER_IDS` in the matrix runner is asserted empty, with a comment naming Batch 5 as where real ids arrive.
7. No test asserts that a required capability can be bypassed, forced, or defaulted.

**Implementation Steps:**

1. Create the test module in `tests/removability/`.
2. Build a synthetic policy mapping requiring one fabricated qualified id that no provider supplies.
3. Add `test_missing_required_capability_refuses`.
4. Add `test_reason_code_is_profile_requirement_unsatisfied`.
5. Add `test_degraded_does_not_satisfy`.
6. Add `test_satisfied_requirement_succeeds`.
7. Add `test_real_policy_table_untouched`.
8. Add `test_matrix_required_ids_still_empty`.
9. Add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not add a real capability id to `PROFILE_REQUIRED_CAPABILITIES`.** `risk.kill_switch` has no spec and no provider; citing it would invent an artefact. Batch 5 populates the table.
- **Do not add any id to `REQUIRED_PROVIDER_IDS`** for the same reason.
- Do not write a test that proves a required capability can be bypassed.
- Do not modify `app/composition/policy.py` or `scripts/deletion_matrix.py`.
- Do not mark any test `skip` or `xfail`.
- Do not modify any PROTECTED path.

**Unit Tests** — the six functions above, in `tests/removability/test_required_refusal.py`.

Run: `uv run pytest tests/removability -q` → all thirty pass, 0 skipped.

**Usage Example** — none; test artefact.

**Quality Gates:**

```bash
uv run ruff format tests/removability
uv run ruff check tests/removability
uv run mypy .
uv run pytest tests/removability -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added inverse assertion proving a missing required capability fails closed.`

**Git Commit:**

```bash
git add tests/removability/test_required_refusal.py docs/CHANGELOG.md
git commit -m "test(architecture): prove required capabilities fail closed" -m "A profile missing a required capability refuses rather than degrading, and
a degraded provider does not satisfy a requirement. Uses a synthetic policy
so no capability id is invented.
Refs: REFACTOR_PLAN.md Phase 11 inverse assertion, AGENTS.md section 3, Gate G11"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] One file created, one modified, no others
- [ ] All six tests passing alongside the twenty-four existing
- [ ] No real capability id added to any policy table
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P11-T06` — Wire composability gates into CI

**Traces to:** `REFACTOR_PLAN.md` Phase 11 ("green and required to merge"); Phase 16 preparation; conflict `CF-08`; Gate `G11`
**Depends on:** `P11-T05`
**Estimated size:** M (50–120 LOC)

**Goal.** The composability gates run automatically, so removability is enforced rather than remembered.

**Context to Read (and nothing else):**

- `.github/` — **step 1 lists this directory** to find the existing workflow file. STOP and report if no workflow exists, and add the gates to `scripts/ci_check.py` instead — but note `ci_check.py` is PROTECTED, so a STOP is the correct outcome and the owner decides.
- `scripts/ci_check.py` — the existing four-step gate sequence, for reference only
- `scripts/deletion_matrix.py`, `scripts/deletion_proof.py`
- Conflict `CF-08` — why the matrix gates every merge and the proof runs nightly

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `.github/workflows/composability.yml` | CREATE | Gate workflow |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** a workflow with two jobs.

`merge-gate`, on `pull_request` and `push`:

1. `uv run ruff format --check .`
2. `uv run ruff check .`
3. `uv run mypy .`
4. `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80`
5. `uv run pytest tests/architecture tests/removability tests/golden -q`
6. `uv run python scripts/deletion_matrix.py`

`nightly-proof`, on `schedule` at `0 3 * * *` and `workflow_dispatch`:

1. `uv run python scripts/deletion_proof.py --provider app/services/indicators/rsi_default`
2. `uv run python scripts/deletion_proof.py --provider app/services/indicators/williams_r_default`
3. `uv run python scripts/composability_graph.py`
4. `uv run python scripts/composability_barrels.py`
5. `uv run python scripts/composability_matrix.py`

**Behaviour Rules (numbered, testable):**

1. `merge-gate` fails the build if any of its six steps exits non-zero.
2. `nightly-proof` does not gate merges; it reports.
3. Neither job uses `continue-on-error` on any step.
4. No step regenerates `tests/fixtures/golden/indicators.json` or commits anything.
5. The workflow adds no secret, no credential, and no live-broker environment variable.
6. The workflow does not modify `scripts/ci_check.py`.

**Implementation Steps:**

1. List `.github/` and locate the existing workflow. **STOP and report** if none exists — the fallback would require editing PROTECTED `scripts/ci_check.py`, which is the owner's decision.
2. Create `.github/workflows/composability.yml` with the two jobs above.
3. Use the same Python and `uv` setup steps as the existing workflow found in step 1.
4. Confirm no step carries `continue-on-error`.
5. Confirm no secret is referenced.
6. Add the CHANGELOG bullet.
7. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not modify `scripts/ci_check.py`** — it is PROTECTED and changing it changes every task's definition of done.
- Do not add `continue-on-error` to any step; a gate that cannot fail is not a gate.
- Do not add a step that regenerates the golden baseline or commits a generated artefact.
- Do not reference a secret, credential, or live-broker variable.
- Do not put the nightly proof in the merge gate; `CF-08` separates them by cost.
- Do not add a matrix over Python versions; the project pins `>=3.14`.
- Do not modify any PROTECTED path.

**Unit Tests**

File: `tests/unit/test_composability_workflow.py` (CREATE) — parses the YAML as text, since `pyyaml` parsing of a workflow adds no value here.

| Test function | Expected |
|---|---|
| `test_workflow_exists` | file present |
| `test_merge_gate_has_six_steps` | six command lines under `merge-gate` |
| `test_no_continue_on_error` | substring absent |
| `test_no_secrets_referenced` | no `secrets.` substring |
| `test_nightly_not_on_pull_request` | `nightly-proof` triggers are `schedule` and `workflow_dispatch` only |
| `test_ci_check_untouched` | `scripts/ci_check.py` unchanged in this commit |

Run: `uv run pytest tests/unit/test_composability_workflow.py -q` → all pass, 0 skipped.

**Usage Example** — none; CI configuration.

**Quality Gates:**

```bash
uv run ruff format tests/unit/test_composability_workflow.py
uv run ruff check tests/unit/test_composability_workflow.py
uv run mypy .
uv run pytest tests/unit/test_composability_workflow.py -q
uv run python scripts/deletion_matrix.py
uv run pytest tests/architecture tests/removability tests/golden -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — `### Added`: `- Added CI workflow gating architecture, removability, golden parity and the deletion matrix.`

**Git Commit:**

```bash
git add .github/workflows/composability.yml tests/unit/test_composability_workflow.py docs/CHANGELOG.md
git commit -m "ci(architecture): gate composability on every merge" -m "Runs the architecture, removability, golden parity and deletion-matrix
checks on every pull request, with the slower physical deletion proof on a
nightly schedule.
Refs: REFACTOR_PLAN.md Phase 11, CF-08, Gate G11"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] One workflow created, one test file, one CHANGELOG line
- [ ] All six tests passing
- [ ] `scripts/ci_check.py` untouched
- [ ] No `continue-on-error`, no secret
- [ ] Exactly one commit with the message above

---

## 12. TRACEABILITY MAP

| Source identifier | Source location | Task IDs | Status |
|---|---|---|---|
| Phase 9 — pure pilot | `REFACTOR_PLAN.md` Part II | `P9-T01` … `P9-T05` | PLANNED |
| Gate `G9` | `REFACTOR_PLAN.md` §1.2 | `P9-T01` … `P9-T05` | PLANNED |
| `R-04` spec layout | `REFACTOR_PLAN.md` §1.2.1 | `P9-T01`, `P10-T01`, `P10-T05` | PLANNED |
| Phase 9 cross-feature proof | `REFACTOR_PLAN.md` Phase 9 | `P9-T05` | PLANNED |
| §1.1 granularity guard (bundle by default) | `REFACTOR_PLAN.md` §1.1 | `P9-T02`, `P9-T03` (split on demonstrated need) | PLANNED |
| Phase 10 — effectful pilot A | `REFACTOR_PLAN.md` Part II | `P10-T01` … `P10-T04` | PLANNED |
| Phase 10 — effectful pilot B | `REFACTOR_PLAN.md` Part II | `P10-T05`, `P10-T06` | PLANNED |
| §0.3 eager `app.utils` counter-example | `REFACTOR_PLAN.md` §0.3 | `P10-T02` | PLANNED |
| `R-01` hybrid contract shape | `REFACTOR_PLAN.md` §1.2.1 | `P10-T01` (protocol side) | PLANNED |
| `D-07` effect classes | `REFACTOR_PLAN.md` §1.2 | `P10-T03` | PLANNED |
| Gate `G10` | `REFACTOR_PLAN.md` §1.2 | `P10-T01` … `P10-T06` | PLANNED |
| Phase 11 proof 1 — config-disable | `REFACTOR_PLAN.md` Phase 11 | `P11-T01`, `P11-T02` | PLANNED |
| Phase 11 proof 2 — physical deletion | `REFACTOR_PLAN.md` Phase 11 | `P11-T03` | PLANNED |
| Phase 11 proof 3 — reinstall cycle | `REFACTOR_PLAN.md` Phase 11 | `P11-T04` | PLANNED |
| Phase 11 inverse assertion | `REFACTOR_PLAN.md` Phase 11 | `P11-T05` | PLANNED |
| Phase 8 install→disable→reinstall cycle | `REFACTOR_PLAN.md` Phase 8 | `P11-T04` | PLANNED (deferred here from Batch 3) |
| `D-09` migration/schema | `REFACTOR_PLAN.md` §1.2 | `P11-T04` | PLANNED |
| Gate `G11` | `REFACTOR_PLAN.md` §1.2 | `P11-T01` … `P11-T06` | PLANNED |
| Golden fixtures for Analytics, Risk, Strategy, Simulator, Portfolio | `REFACTOR_PLAN.md` Phase 0 | none | DEFERRED to Batch 5 — construction helpers unverified per Batch 3 §9.5 |
| Wave 12.1 `app/utils` full split | `REFACTOR_PLAN.md` wave 12.1 | `P10-T02` (lazification only) | PARTIAL — capability extraction is Batch 5 |
| Phases 12, 16, 17 | `REFACTOR_PLAN.md` Parts IV–VI | none | OUT OF SCOPE (§5) |

---

## 13. COMMIT SEQUENCE

| Order | Task ID | Commit message |
|---|---|---|
| 42 | `P9-T01` | `feat(capabilities): add indicator.williams_r.v1 specification` |
| 43 | `P9-T02` | `feat(indicators): add RSI provider package` |
| 44 | `P9-T03` | `feat(indicators): add Williams R provider package` |
| 45 | `P9-T04` | `refactor(indicators): convert momentum to a namespace` |
| 46 | `P9-T05` | `test(architecture): prove indicator pilot removability` |
| 47 | `P10-T01` | `feat(capabilities): add notification channel specification` |
| 48 | `P10-T02` | `refactor(utils): make the utils barrel lazy` |
| 49 | `P10-T03` | `feat(notifications): add desktop channel provider` |
| 50 | `P10-T04` | `test(architecture): prove notification effect disposal` |
| 51 | `P10-T05` | `feat(data): add simulated market stream provider` |
| 52 | `P10-T06` | `test(architecture): prove stream generational replacement` |
| 53 | `P11-T01` | `feat(composition): add loader configuration` |
| 54 | `P11-T02` | `feat(architecture): add config-disable deletion matrix` |
| 55 | `P11-T03` | `feat(architecture): add fresh-process deletion proof` |
| 56 | `P11-T04` | `test(architecture): prove remove and reinstall cycle` |
| 57 | `P11-T05` | `test(architecture): prove required capabilities fail closed` |
| 58 | `P11-T06` | `ci(architecture): gate composability on every merge` |

Continues from order 41 (`P8-T06`) in Batch 3 §13.

---

## 14. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation | Mitigating task |
|---|---|---|---|---|
| An indicator formula changes while being moved | High | Critical | Verbatim copy required; golden parity gate runs in every Phase 9 task's Quality Gates; baseline regeneration explicitly forbidden | `P9-T02`, `P9-T03`, `P9-T04` |
| The barrel switch breaks a consumer that deep-imported `momentum.rsi` | High | High | `P9-T04` step 2 is an authorised repo grep recording every hit before the switch; a hit inside a PROTECTED path is a STOP | `P9-T04` |
| Lazifying `app/utils` silently drops an export | High | Critical | `__all__` snapshot test; `_EXPORTS`/`__all__` agreement test; the regression gate is the **entire** suite with baseline-matching counts | `P10-T02` |
| A sent notification is "rolled back" by disposal | Medium | High | Irreversible effects are never disposed; a test asserts the disposer is called zero times; no unsend path exists | `P10-T03`, `P10-T04` |
| Config-disable passes because a module was already imported | High | High | `CF-08`: the physical deletion proof runs in a fresh interpreter and treats a stale `sys.modules` entry as a failure | `P11-T03` |
| A missing loader config silently enables everything, making deletion tests pass falsely | Medium | High | A missing file raises rather than defaulting | `P11-T01` |
| A capability id is invented for a required provider that does not exist | Medium | High | `REQUIRED_PROVIDER_IDS` and `PROFILE_REQUIRED_CAPABILITIES` both stay empty; `P11-T05` uses a synthetic policy and asserts the real tables are untouched | `P11-T05` |
| The pilot deletes the legacy path in the same commit that adds the provider, making failure hard to revert | Medium | High | `P9-T02`/`P9-T03` are additive; only `P9-T04` deletes, and its re-run safety notes the single-commit revert | `P9-T04` |
| A live broker or network call sneaks into the stream pilot | Medium | High | Simulated stream only; a test asserts no `socket`, `requests` or `urllib` symbol appears in the module | `P10-T05` |
| A CI gate is added with `continue-on-error` and silently never fails | Medium | High | A test asserts the substring is absent from the workflow | `P11-T06` |

---

## SELF-VERIFICATION REPORT

Checks 1–16: **PASS with notes**

1. **PASS** — all seventeen tasks carry every mandatory field. `Regression Tests` present on `P9-T02`, `P9-T03`, `P9-T04`, `P10-T02`, `P10-T04` — every task that modifies or shadows existing behaviour. `Logging` omitted: logging rules are stated once in §4 and inside the relevant Behaviour Rules. `Rollback` present in substance on `P9-T04` and `P10-T02` via explicit `Re-run safety` entries marking them **Not safe** with the exact revert path; no task touches persistence or the trading runtime, so no schema downgrade exists to document.
2. **PASS** — every symbol is defined in its task or frozen in §3.
3. **PASS** — no banned verb in any implementation step.
4. **PASS** — single chain `P9-T01 → … → P11-T06`; `P9-T01` depends on Batch 3's `P8-T06`.
5. **PASS** — paths spelled identically throughout.
6. **PASS** — every Phase 9–11 source identifier is in §12 with an explicit status; the remaining golden fixtures and the full utils split are marked DEFERRED/PARTIAL with reasons rather than dropped.
7. **PASS** — every cited identifier appears verbatim in `REFACTOR_PLAN.md` or is defined here. No `FEAT-*` id is invented; `P9-T04` updates **existing** README rows rather than creating ids. Unconfirmed requirement IDs: **none**.
8. **PASS** — largest tasks are size L at 3 directories-or-files plus tests, ≤11 steps. No title contains "and".
9. **PASS** — all seventeen commit messages are Conventional Commits with a scope; each `git add` names only files in that task's table.
10. **PASS** — §8 has no blockers. Five UNVERIFIED items in §2.1 each have a named first step and a STOP CONDITION.
11. **N/A** — walking skeleton discharged in Batch 1 (`CF-02`). Each phase here is a vertical slice ending in an executable proof.
12. **PASS** — every `EXISTING`/`MODIFY` artefact is backed by evidence, and the five items read only partially are listed explicitly in §2.1 rather than assumed.
13. **PASS** — no task file table contains a PROTECTED path. Four paths are explicitly unprotected in §5 for named tasks only, each with a stated constraint.
14. **PASS** — every command traces to §1.
15. **PASS** — two material conflicts (`CF-07`, `CF-08`), both resolved with a single stated approach.
16. **PASS** — no dependency used that is not stdlib or already present.

Tasks: **17** across **3** complete phases
Requirements covered: **18** source identifiers PLANNED or PARTIAL; **1** DEFERRED with reason; **1** OUT OF SCOPE group
Unconfirmed requirement IDs: **none**
Material conflicts resolved: **2**   |   Blocking open questions: **0**
New dependencies authorized: **0**

**Batch 4 is complete.** Batch 5 continues at Phase 12.

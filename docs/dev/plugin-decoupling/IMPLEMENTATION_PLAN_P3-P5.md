# Implementation Plan — HaruQuantAI Spatiotemporal Composability (Phases 3–5)

Source documents: `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` v2 incl. §1.2.1 resolutions `R-01`–`R-07`; `docs/dev/plugin-decoupling/IMPLEMENTATION_PLAN_P0-P2.md`; `AGENTS.md` (as amended by `P1-T01`–`P1-T04`); `pyproject.toml` (v2.2.11)
Repository state: `C:\Users\rharu\AppDev\HaruquantAI` — assumes `P0-T01` … `P2-T03` merged
Generated: 2026-08-20   |   Target executor: low-reasoning coding agent

> **Batch 2 of 5 — COMPLETE.** 16 tasks, commits 10–25. Batch 1 = Phases 0–2. This document = Phases 3–5. Batch 3 = Phases 6–8 + golden fixtures. Batch 4 = Phases 9–11. Batch 5 = Phases 12, 16, 17.

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

Identical to Batch 1 §1. Verified against `pyproject.toml`, `.pre-commit-config.yaml`, `scripts/ci_check.py`, `AGENTS.md` §7.

| Purpose | Command |
|---|---|
| Format (write) | `uv run ruff format .` |
| Lint | `uv run ruff check .` |
| Type check | `uv run mypy .` |
| Targeted test | `uv run pytest <path> -q` |
| Full test + coverage | `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` |
| All gates | `uv run python scripts/ci_check.py` |
| Architecture sweep | `uv run python scripts/audit_check.py` |

**Three constraints that apply to every task in this batch and did not apply in Batch 1**, because this batch writes code into `app/` for the first time:

1. **`mypy --strict` applies.** `pyproject.toml` sets `strict = true`, `files = ["app", "tests"]`, `warn_unreachable`, `disallow_untyped_defs`, `disallow_incomplete_defs`, `warn_return_any`. Every function, parameter and return in `app/capabilities/` and `app/kernel/` needs a complete annotation.
2. **Full ruff docstring rules apply.** The `scripts/*.py` per-file ignores (`D100`, `D103`, `ANN`, `T201`) do **not** cover `app/`. Every module, class and public function needs a Google-style docstring with `Args:`, `Returns:` and `Raises:` sections. `DOC102` rejects a documented parameter absent from the signature; `DOC201` requires `Returns:` when a value is returned; `DOC202` rejects `Returns:` when none is; `DOC501` requires every explicitly raised exception to be documented.
3. **Coverage is global.** `--cov=app --cov-fail-under=80` measures the whole of `app/`. New kernel code lands inside that scope, so a task that adds production code without tests can fail the gate for the entire repository. Every task below carries its own tests for this reason.

**No `print` in `app/`.** `AGENTS.md` §2 and ruff `T201`. Use `from app.utils import get_logger`. See §4 for where logging is required and where it is forbidden.

---

## 2. CURRENT-STATE INVENTORY

**Greenfield for the target paths.** `app/capabilities/` and `app/kernel/` do not exist. This plan creates them from nothing. `app/composition/` is declared by `P1-T04` but is **not** built in this batch — it is Phase 6, Batch 3.

Existing artefacts this batch depends on, all verified in Batch 1 §2:

| Symbol / path | Status | Note |
|---|---|---|
| `app/utils/get_logger` | EXISTING | Imported from the package root `app.utils`; the eager barrel means this pulls the whole of `app/utils` — accepted for now, resolved at source wave 12.1 |
| `app/services/indicators/momentum/rsi.py::rsi` | EXISTING, UNCHANGED | Signature `rsi(data: MarketDataset, *, period: int, source: str = "close", config: IndicatorConfig | None = None) -> IndicatorResult`. Referenced by `P3-T04` as the shape the first spec describes. **No task in this batch modifies it.** |
| `tests/architecture/` | CREATE | Named by the `P1-T04` policy text; first created by `P3-T05` |
| `AGENTS.md` §1 "Non-Feature Infrastructure Packages" | EXISTING after `P1-T04` | The rule that exempts these packages from `FEAT-*` registration |
| `scripts/audit_check.py` | EXISTING, PROTECTED | Its `REG` check counts README-registered feature dirs; the `P1-T04` exemption keeps the new packages out of that count |

`tomllib` is standard library on Python 3.14 (`requires-python = ">=3.14"`). No dependency is added by `R-05`.

**Pre-existing failures:** whatever `docs/dev/plugin-decoupling/BASELINE.md` records. Every exit gate in this batch compares against that file.

---

## 3. SHARED CONTRACTS (INTERFACE FREEZE)

### 3.1 Package tree

| Path | Status | Purpose |
|---|---|---|
| `app/capabilities/__init__.py` | CREATE | Re-exports the spec vocabulary; nothing else |
| `app/capabilities/README.md` | CREATE | Non-feature infrastructure declaration |
| `app/capabilities/spec.py` | CREATE | `CapabilitySpec`, `Requirement`, ID helpers |
| `app/capabilities/conformance.py` | CREATE | Contract conformance checking for both kinds |
| `app/capabilities/indicator/__init__.py` | CREATE | Domain namespace, empty |
| `app/capabilities/indicator/rsi/__init__.py` | CREATE | Capability namespace, empty |
| `app/capabilities/indicator/rsi/v1.py` | CREATE | First real specification |
| `app/kernel/__init__.py` | CREATE | Re-exports the kernel public surface |
| `app/kernel/README.md` | CREATE | Non-feature infrastructure declaration |
| `app/kernel/errors.py` | CREATE | Reason codes and `KernelError` |
| `app/kernel/manifests.py` | CREATE | `ProviderManifest` and TOML parsing |
| `app/kernel/discovery.py` | CREATE | Filesystem walk for `manifest.toml` |
| `app/kernel/registry.py` | CREATE | Capability → provider inventory |
| `app/kernel/resolver.py` | CREATE | Requirement resolution and reporting |
| `app/kernel/profiles.py` | CREATE | Profile readiness evaluation |
| `app/kernel/states.py` | CREATE | `ComponentState` enum and legal transitions |
| `app/kernel/scope.py` | CREATE | `Effect`, `EffectScope` |
| `app/kernel/lifecycle.py` | CREATE | Activation, deactivation, quiesce |
| `tests/architecture/__init__.py` | CREATE | Package marker |
| `tests/architecture/test_import_boundaries.py` | CREATE | Enforces the dependency direction in §3.2 |
| `tests/unit/test_capability_spec.py` … | CREATE | One per production module, named in each task |

### 3.2 Dependency direction — frozen, enforced by `P3-T05`

```text
app.capabilities   →   (stdlib only)
app.kernel         →   app.capabilities, app.utils, stdlib
app.composition    →   app.kernel, app.capabilities        (Batch 3)
app.services.*     →   app.capabilities                    (Batch 4+)
```

`app.capabilities` imports **nothing** from `app.kernel`, `app.services.*`, `app.agentic`, or `app.utils`. It must be importable with zero providers installed and zero application configuration.
`app.kernel` imports **nothing** from `app.services.*` or `app.agentic`.

> The primitives live in `app.capabilities`, not `app.kernel`, precisely so this arrow points one way. Kernel consumes contract vocabulary; contract vocabulary never consumes machinery.

### 3.3 `app/capabilities/spec.py` — CREATE

```python
CARDINALITIES: Final[frozenset[str]] = frozenset(
    {"exactly_one", "zero_or_one", "one_of_several", "many"}
)
KINDS: Final[frozenset[str]] = frozenset({"protocol", "callable_record"})
ON_MISSING_POLICIES: Final[frozenset[str]] = frozenset(
    {"fail_closed", "degrade", "skip"}
)
DEFAULT_ON_MISSING: Final[str] = "fail_closed"


@dataclass(frozen=True)
class CapabilitySpec:
    """One versioned provider-neutral capability contract.

    Attributes:
        capability_id: Dotted identifier, lowercase, e.g. "indicator.rsi".
        version: Positive integer contract version.
        cardinality: One of CARDINALITIES.
        kind: One of KINDS. "protocol" for effectful capabilities that own a
            scope; "callable_record" for pure capabilities (R-01).
        contract: The Protocol class or frozen dataclass defining the surface.
    """

    capability_id: str
    version: int
    cardinality: str
    kind: str
    contract: type[object]


@dataclass(frozen=True)
class Requirement:
    """One declared dependency on a capability, with a version window.

    Attributes:
        capability_id: The required capability's dotted identifier.
        min_version: Lowest acceptable version, inclusive.
        max_version: Highest acceptable version, inclusive.
        on_missing: One of ON_MISSING_POLICIES. Defaults to fail_closed (D-04).
    """

    capability_id: str
    min_version: int
    max_version: int
    on_missing: str = DEFAULT_ON_MISSING


def qualified_id(capability_id: str, version: int) -> str: ...
def parse_qualified_id(text: str) -> tuple[str, int]: ...
def satisfies(spec: CapabilitySpec, requirement: Requirement) -> bool: ...
```

**Frozen decisions inside this contract, so no task re-litigates them:**

- Version windows are **explicit inclusive integers**, not a range string. There is no range parser anywhere in this plan.
- `qualified_id("indicator.rsi", 1)` returns `"indicator.rsi.v1"`. `parse_qualified_id` is its exact inverse.
- Validation happens in `__post_init__` on both dataclasses and raises `ValueError`.

### 3.4 `app/capabilities/conformance.py` — CREATE

```python
def check_conformance(spec: CapabilitySpec, candidate: object) -> tuple[str, ...]:
    """Report every way a candidate fails its capability contract.

    Args:
        spec: The capability specification to check against.
        candidate: A provider object (kind "protocol") or a record instance
            (kind "callable_record").

    Returns:
        A tuple of human-readable violation strings, empty when conformant.

    Raises:
        ValueError: If spec.kind is not a member of KINDS.
    """
```

Checking rules, frozen:

- `kind == "protocol"` — for every public attribute of `spec.contract` that is a function, the candidate must have a callable attribute of the same name whose positional-or-keyword parameter names match exactly, ignoring `self`.
- `kind == "callable_record"` — the candidate must be an instance of `spec.contract`, and every field of that frozen dataclass must be callable on the instance.
- Violation strings use exactly these formats: `"missing attribute: {name}"`, `"not callable: {name}"`, `"parameter mismatch on {name}: expected {expected}, got {actual}"`, `"wrong record type: expected {expected}, got {actual}"`.

### 3.5 `app/kernel/errors.py` — CREATE

```python
class ReasonCode(StrEnum):
    """Why a capability is unavailable. Values are the wire strings."""

    NOT_INSTALLED = "NOT_INSTALLED"
    DISABLED = "DISABLED"
    VERSION_INCOMPATIBLE = "VERSION_INCOMPATIBLE"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    PROVIDER_AMBIGUOUS = "PROVIDER_AMBIGUOUS"
    CONFIG_INVALID = "CONFIG_INVALID"
    ACTIVATION_FAILED = "ACTIVATION_FAILED"
    UNHEALTHY = "UNHEALTHY"
    DRAINING = "DRAINING"
    LOST_DURING_OPERATION = "LOST_DURING_OPERATION"
    PROFILE_REQUIREMENT_UNSATISFIED = "PROFILE_REQUIREMENT_UNSATISFIED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    CLEANUP_FAILED = "CLEANUP_FAILED"


CAPABILITY_UNAVAILABLE: Final[str] = "CAPABILITY_UNAVAILABLE"


@dataclass(frozen=True)
class Unavailability:
    """Structured evidence that one capability is not usable.

    Attributes:
        code: Always CAPABILITY_UNAVAILABLE.
        reason_code: The specific ReasonCode.
        capability: Qualified capability id, e.g. "indicator.rsi.v1".
        consumer: Qualified id of the requesting component, or None.
        provider_id: Provider that failed, or None when nothing was installed.
        dependency_chain: Ordered qualified ids from consumer to root cause.
        retryable: True only for UNHEALTHY and DRAINING.
    """

    reason_code: ReasonCode
    capability: str
    consumer: str | None
    provider_id: str | None
    dependency_chain: tuple[str, ...]
    retryable: bool
    code: str = CAPABILITY_UNAVAILABLE


class KernelError(Exception):
    """Raised only for kernel misuse, never for capability absence."""
```

> **The distinction that must not blur:** capability absence returns an `Unavailability` value. `KernelError` is raised only when the *kernel itself* is used incorrectly — a malformed manifest, a duplicate provider id, an illegal state transition. Absence is never an exception.

The thirteen reason codes are quoted verbatim from `REFACTOR_PLAN.md` Phase 7. `retryable` is `True` for exactly `UNHEALTHY` and `DRAINING`, `False` for the other eleven.

### 3.6 `app/kernel/manifests.py` — CREATE

`manifest.toml` schema, frozen (`R-05`):

```toml
[provider]
id = "indicator.rsi.default"
version = 1
entry_point = "app.services.indicators.rsi_default.plugin:setup"
owns_migrations = false
owns_persistence = false

[[provides]]
capability_id = "indicator.rsi"
version = 1

[[requires]]
capability_id = "data.ohlcv"
min_version = 1
max_version = 1
on_missing = "fail_closed"

[[effects]]
name = "none"
effect_class = "reversible_ephemeral"
```

```python
EFFECT_CLASSES: Final[frozenset[str]] = frozenset(
    {"reversible_ephemeral", "durable_compensatable", "irreversible_external"}
)


@dataclass(frozen=True)
class EffectDeclaration:
    name: str
    effect_class: str


@dataclass(frozen=True)
class ProviderManifest:
    provider_id: str
    version: int
    entry_point: str
    owns_migrations: bool
    owns_persistence: bool
    provides: tuple[tuple[str, int], ...]
    requires: tuple[Requirement, ...]
    effects: tuple[EffectDeclaration, ...]
    source_path: Path


def parse_manifest(text: str, source_path: Path) -> ProviderManifest: ...
def load_manifest(path: Path) -> ProviderManifest: ...
```

`parse_manifest` raises `KernelError` with message `"invalid manifest at {source_path}: {detail}"` for every schema violation. `entry_point` is stored as a string and **never imported** at parse or discovery time — that is the whole point of TOML (`R-05`).

### 3.7 `app/kernel/registry.py` and `app/kernel/resolver.py` — CREATE

```python
@dataclass(frozen=True)
class ProviderRecord:
    manifest: ProviderManifest
    enabled: bool


class CapabilityRegistry:
    """Inventory of installed providers keyed by capability."""

    def register(self, manifest: ProviderManifest, *, enabled: bool = True) -> None: ...
    def providers_for(self, capability_id: str, version: int) -> tuple[ProviderRecord, ...]: ...
    def provider_ids(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class ResolutionEntry:
    provider_id: str
    state: str
    unavailability: Unavailability | None
    resolved_requires: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ResolutionReport:
    activation_order: tuple[str, ...]
    entries: tuple[ResolutionEntry, ...]

    def is_active(self, provider_id: str) -> bool: ...


def resolve(
    registry: CapabilityRegistry,
    specs: Mapping[str, CapabilitySpec],
) -> ResolutionReport: ...
```

Frozen resolver rules:

1. `register` raises `KernelError` `"duplicate provider id: {id}"` on a repeated `provider_id`.
2. Resolution is a topological sort over `requires`. A cycle among **required** edges (`on_missing == "fail_closed"`) raises `KernelError` `"dependency cycle: {a} -> {b} -> ... -> {a}"`. A cycle that passes through any `degrade` or `skip` edge is permitted and broken at that edge.
3. Cardinality `exactly_one` with zero matches yields `NOT_INSTALLED`; with more than one match yields `PROVIDER_AMBIGUOUS`.
4. `zero_or_one` with more than one match yields `PROVIDER_AMBIGUOUS`; with zero it resolves to no provider without error.
5. A requirement whose capability exists at an out-of-window version yields `VERSION_INCOMPATIBLE`, never `NOT_INSTALLED`.
6. A provider whose dependency is unavailable yields `DEPENDENCY_UNAVAILABLE` with the full `dependency_chain`, and its own dependents inherit that chain with their id prepended.
7. `on_missing == "skip"` drops the requirement and keeps the provider active. `degrade` keeps it active in state `DEGRADED`. `fail_closed` makes it inactive.
8. `activation_order` lists only active providers, dependencies first. It is deterministic: ties break on `provider_id` ascending.

### 3.8 `app/kernel/states.py` — CREATE

```python
class ComponentState(StrEnum):
    DISCOVERED = "DISCOVERED"
    DISABLED = "DISABLED"
    RESOLVING = "RESOLVING"
    WAITING_FOR_DEPENDENCY = "WAITING_FOR_DEPENDENCY"
    STARTING = "STARTING"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    DRAINING = "DRAINING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    FAILED_CLEANUP = "FAILED_CLEANUP"
    QUARANTINED = "QUARANTINED"
    VERSION_INCOMPATIBLE = "VERSION_INCOMPATIBLE"


TERMINAL_STATES: Final[frozenset[ComponentState]] = frozenset(
    {ComponentState.STOPPED, ComponentState.FAILED,
     ComponentState.FAILED_CLEANUP, ComponentState.QUARANTINED,
     ComponentState.VERSION_INCOMPATIBLE}
)

LEGAL_TRANSITIONS: Final[Mapping[ComponentState, frozenset[ComponentState]]] = ...


def assert_transition(current: ComponentState, target: ComponentState) -> None: ...
```

`LEGAL_TRANSITIONS` is given in full in `P5-T01`. `assert_transition` raises `KernelError` `"illegal transition: {current} -> {target}"`.

### 3.9 `app/kernel/scope.py` — CREATE

Per `R-02` this is **synchronous**, built on `contextlib.ExitStack`.

```python
@dataclass(frozen=True)
class Effect:
    """One registered resource with a declared reversibility class.

    Attributes:
        name: Operator-facing label, unique within a scope.
        effect_class: One of EFFECT_CLASSES.
        dispose: Zero-argument callable that releases the resource.
    """

    name: str
    effect_class: str
    dispose: Callable[[], None]


class EffectScope:
    """Lifecycle owner for one component generation's resources."""

    def __init__(self, owner_id: str) -> None: ...
    def register(self, effect: Effect) -> None: ...
    def effect_names(self) -> tuple[str, ...]: ...
    def has_irreversible(self) -> bool: ...
    def dispose(self) -> tuple[str, ...]: ...
```

Frozen scope rules:

1. `register` raises `KernelError` `"duplicate effect: {name}"` on a repeated name within one scope.
2. `dispose` runs disposers in **reverse registration order**.
3. A disposer that raises does not stop the sweep. `dispose` continues and returns the tuple of failed effect names.
4. `dispose` is idempotent: a second call returns an empty tuple and disposes nothing.
5. `register` after `dispose` raises `KernelError` `"scope already disposed: {owner_id}"`.
6. Effects of class `irreversible_external` are **never disposed** — they are recorded, reported by `has_irreversible`, and skipped by the sweep. `dispose` never places a compensating action.

### 3.10 `app/kernel/lifecycle.py` — CREATE

```python
@dataclass(frozen=True)
class QuiesceVerdict:
    can_dispose: bool
    reason: str | None


class Component:
    def __init__(self, manifest: ProviderManifest, scope: EffectScope) -> None: ...
    @property
    def state(self) -> ComponentState: ...
    def transition(self, target: ComponentState) -> None: ...
    def can_dispose(self) -> QuiesceVerdict: ...
    def deactivate(self) -> tuple[str, ...]: ...
```

`deactivate` performs, in order: `assert_transition` to `DRAINING` → `can_dispose()` check → `STOPPING` → `scope.dispose()` → `STOPPED` when no failures, `FAILED_CLEANUP` when any. A refused quiesce leaves the component in `DRAINING` and returns without disposing.

### 3.11 `__all__` contents

| Module | `__all__` |
|---|---|
| `app/capabilities/__init__.py` | `["CapabilitySpec", "Requirement", "check_conformance", "parse_qualified_id", "qualified_id", "satisfies"]` |
| `app/kernel/__init__.py` | `["CapabilityRegistry", "Component", "ComponentState", "Effect", "EffectScope", "KernelError", "ProviderManifest", "ReasonCode", "ResolutionReport", "Unavailability", "load_manifest", "resolve"]` |

Both are sorted ascending. Per the `P1-T02` amendment these packages may export types; per `P1-T04` they carry no `FEAT-*` identifiers.

### 3.12 `app/kernel/discovery.py` — CREATE

```python
MANIFEST_FILENAME: Final[str] = "manifest.toml"
DISCOVERY_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {"__pycache__", ".venv", "build", "dist", "node_modules", ".git"}
)


def discover_manifests(root: Path) -> tuple[ProviderManifest, ...]: ...
```

Walks `root` recursively for files named `manifest.toml`, parses each with `load_manifest`, and returns them sorted by `provider_id` ascending. Skips any path containing a directory in `DISCOVERY_SKIP_DIRS`. **Never imports `entry_point`.** A malformed manifest propagates the `KernelError` from `parse_manifest` — discovery does not swallow it.

### 3.13 `app/kernel/profiles.py` — CREATE

```python
class Profile(StrEnum):
    RESEARCH = "research"
    SIMULATION = "simulation"
    DEMO = "demo"
    LIVE = "live"


@dataclass(frozen=True)
class ReadinessReport:
    """Whether one runtime profile may operate.

    Attributes:
        profile: The evaluated profile.
        ready: True only when every required capability resolved active.
        missing: Unavailability evidence, one entry per unsatisfied requirement.
    """

    profile: Profile
    ready: bool
    missing: tuple[Unavailability, ...]


def evaluate_readiness(
    profile: Profile,
    required: Mapping[Profile, frozenset[str]],
    report: ResolutionReport,
    registry: CapabilityRegistry,
) -> ReadinessReport: ...
```

> **The policy table is a parameter, not a constant.** `required` is supplied by the composition root (Batch 3), never hardcoded in the kernel. `D-01` forbids the kernel from knowing which capabilities Risk or Trading need; it owns the *mechanism* of readiness, not the *policy*. This also means no task in this batch invents a capability ID for a domain that has none yet.

Each unsatisfied requirement produces an `Unavailability` with `reason_code=PROFILE_REQUIREMENT_UNSATISFIED`, `capability` set to the qualified id, `consumer=None`, and `dependency_chain` copied from the resolver entry when one exists.

---

## 4. NAMING & LAYOUT CONVENTIONS

Inherited from Batch 1 §4, with three additions for `app/` code.

- Production code under `app/capabilities/` and `app/kernel/`; tests under `tests/unit/test_<module>.py`; architecture tests under `tests/architecture/`.
- **Logging.** `AGENTS.md` §2 requires the project logger at workflow boundaries, public entry points, state transitions, side-effect boundaries and failures — and explicitly exempts "pure helpers, trivial accessors, deterministic transformations". Applied here: `app/capabilities/` is pure and logs **nothing**; it must not import `app.utils` at all (§3.2). In `app/kernel/`, log at `INFO` on component state transitions and resolution completion, at `WARNING` on unavailability and on a disposer failure. Nowhere else. No `print` anywhere in `app/`.
- **Docstrings.** Google style on every module, class and function including private ones — ruff `D` is fully enabled outside `scripts/`. Document `Raises:` for every exception raised explicitly (`DOC501`).
- **`from __future__ import annotations`** at the top of every new module, matching `rsi.py` and `audit_check.py`.
- **CHANGELOG policy.** Unchanged from Batch 1 §4: every task whose file table contains a path outside `docs/dev/` adds exactly one concise single-line bullet under `## [Unreleased]` and includes `docs/CHANGELOG.md` in its `git add`. Every task in this batch touches `app/`, so **every task adds a bullet**.
- **README policy.** Per the `P1-T04` amendment, `app/capabilities/README.md` and `app/kernel/README.md` state purpose, public surface and registry exclusion. They carry **no** `### Feature Registry` section and **no** `FEAT-*` identifiers.

---

## 5. SCOPE & PROTECTED AREAS

**In scope:** source Phase 3 (capability specification layer), Phase 4 (protected microkernel), Phase 5 (lifecycle and effect ownership). Gates `G3`, `G4`, `G5`.

**Out of scope, with the source identifiers they map to:**

- `app/composition/`, injection, provider generations, shadow activation, atomic lease switch — source Phase 6, gate `G6`. Declared by `P1-T04`, built in Batch 3.
- `Unavailability` → `StandardResponse` synthesis at service, API, CLI and agent-tool boundaries — source Phase 7, gate `G7`. This batch produces the value; Batch 3 wires it to the response envelope.
- Migration tombstoning implementation and the install→disable→reinstall test cycle — source Phase 8, gate `G8`. Policy landed in `P1-T01`; code is Batch 3.
- Golden financial fixtures — source Phase 0. `OQ-01` resolved; scheduled for Batch 3.
- Every provider migration, including the RSI/Williams pilot — source Phases 9+, Batches 4–5.
- `D-11` (generated registries) and `D-13` (HMR) — source Phases 16 and 17, Batch 5.

**PROTECTED paths — no task in this plan may modify these:**

| Path | Reason |
|---|---|
| `app/services/` (entire tree) | This batch adds new packages only; no domain changes until Batch 4 |
| `app/agentic/` | Same |
| `app/utils/` | The eager-barrel split is source wave 12.1, Batch 5 |
| `app/services/risk/kill_switch/` | `AGENTS.md` §3 forbids any bypass |
| `app/services/trading/live/` | Live execution path |
| `scripts/audit_check.py`, `scripts/ci_check.py` | Gate definitions |
| `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml` | No dependency or tool-config change is authorized (§6) |
| `docs/CHANGELOG.md` released-version blocks | `AGENTS.md` §4: only `## [Unreleased]` may be appended to |
| `tests/*/usage/` (entire tree) | `P1-T03` declared the relocation transitional; nothing moves until Batch 4 |

**Forbidden changes (repo-wide, apply to every task):**

- No unrelated refactoring or "cleanup" of nearby code.
- No public API change that is not written out in §3.
- No new dependency outside §6.
- No weakening, skipping, xfailing, or deleting an existing test.
- No lint or type-check suppression (`# noqa`, `# type: ignore`) unless a specific task authorises that specific suppression and states why.
- No placeholder or stub implementation; no new `TODO` / `FIXME` comments — ruff `TD` and `FIX` are enabled and will fail the lint gate.
- No credentials, secrets, or local config committed.
- No live-trading, live-broker, or production operation from tests or examples.
- **No `async def` anywhere in `app/kernel/` or `app/capabilities/`** — `R-02` makes the core synchronous.

---

## 6. DEPENDENCY AUTHORIZATION

```text
No new dependencies are authorized by this plan.
```

`tomllib`, `contextlib`, `dataclasses`, `enum`, `pathlib`, `typing`, `collections.abc`, `inspect` are standard library on Python 3.14. `pytest` is present per Batch 1 §2.7.

---

## 7. SOURCE CONFLICTS

```text
Conflict ID:   CF-03
Sources:       REFACTOR_PLAN.md Phase 5 ("AsyncExitStack + structured concurrency")
               vs REFACTOR_PLAN.md §1.2.1 R-02 ("sync core, async edge")
Claim A:       The lifecycle scope is built on AsyncExitStack.
Claim B:       The kernel, resolver, registry and lifecycle are synchronous;
               async is confined to an adapter at the streaming/broker/API edge.
Precedence:    Rule 1 (explicit instruction in the current request) — R-02 is an owner
               resolution dated 2026-08-20 and supersedes the earlier plan body text,
               which has been amended in place.
Decision:      EffectScope is synchronous, built on contextlib.ExitStack. No async
               appears in app/kernel/ or app/capabilities/. §5 makes this a repo-wide
               forbidden change so it cannot creep back in task by task.
Affected tasks: P5-T02, P5-T03, P5-T04, P5-T05
```

```text
Conflict ID:   CF-04
Sources:       AGENTS.md §2 ("use the system-wide logger at public service entry points")
               vs Plan §3.2 (app.capabilities imports nothing from app.utils)
Claim A:       Public entry points log via app.utils.get_logger.
Claim B:       app.capabilities must be importable with zero application
               configuration, and app/utils/__init__.py is a fully eager barrel that
               pulls notifications, security and serialization on import.
Precedence:    Rule 4 (approved design) — the source document's defining property of the
               spec layer is that it imports cleanly with nothing installed.
Decision:      app/capabilities/ logs nothing and imports nothing from app.utils. It
               qualifies under the existing AGENTS.md §2 exemption for "pure helpers,
               deterministic transformations". app/kernel/ does use get_logger.
Affected tasks: P3-T02, P3-T03, P3-T04
```

---

## 8. OPEN QUESTIONS (BLOCKING)

```text
None. R-01 through R-07 resolved every decision this batch depends on. OQ-03 from
Batch 1 (pre-existing red tests) remains conditional on the P0-T01 result and gates
Batch 1's Phase 0 exit, not this batch.
```

---

## 9. PLANNER OBSERVATIONS (non-blocking)

1. **`Requirement` lives in `app/capabilities/`, not `app/kernel/`.** It is contract vocabulary that both manifests and specs need. Putting it in the kernel would force `app.capabilities → app.kernel`, inverting §3.2 and breaking the "importable with zero providers" property.
2. **`Unavailability` is a value, not an exception.** Every reason code returns; `KernelError` is reserved for kernel misuse. This is the single most likely thing for an executor to get wrong, so it is restated in the `DO NOT` block of every task that touches `errors.py`.
3. **`entry_point` is a string that is never imported by this batch.** Discovery reads TOML; nothing resolves the dotted path until Phase 6 composition. An executor who "helpfully" adds `importlib.import_module` would defeat `R-05` and make discovery execute provider code.
4. **The first spec describes `rsi` but does not wrap it.** `P3-T04` writes a contract whose shape matches the verified `rsi` signature. It does not import, call, or modify `rsi`. Binding a provider to the spec is Batch 4.
5. **Cycle policy is asymmetric on purpose.** Cycles among `fail_closed` edges raise; cycles through `degrade`/`skip` are permitted and broken at that edge. This is the Cordis idiom from the source document and is easy to mis-implement as "all cycles forbidden".
6. **`app/capabilities/indicator/rsi/` needs two `__init__.py` files** because ruff `INP001` is enabled outside `scripts/` and implicit namespace packages would fail the lint gate.

---

## 10. PROGRESS DASHBOARD

- [ ] **Phase 3 — Capability specification layer**
  - [ ] `P3-T01` — Create capabilities package skeleton
  - [ ] `P3-T02` — Add capability specification primitives
  - [ ] `P3-T03` — Add capability conformance checker
  - [ ] `P3-T04` — Add first capability specification
  - [ ] `P3-T05` — Add import-boundary architecture test
- [ ] **Phase 4 — Protected microkernel**
  - [ ] `P4-T01` — Create kernel package skeleton
  - [ ] `P4-T02` — Add kernel reason codes
  - [ ] `P4-T03` — Add provider manifest parser
  - [ ] `P4-T04` — Add provider discovery walker
  - [ ] `P4-T05` — Add capability registry
  - [ ] `P4-T06` — Add dependency resolver
  - [ ] `P4-T07` — Add profile readiness evaluator
- [ ] **Phase 5 — Lifecycle and effect ownership**
  - [ ] `P5-T01` — Add component state machine
  - [ ] `P5-T02` — Add synchronous effect scope
  - [ ] `P5-T03` — Add component deactivation sequence
  - [ ] `P5-T04` — Add quiesce refusal protocol

---

## 11. PHASES

### Phase 3 — Capability specification layer

**Goal.** A package a consumer can import to name a contract when **no provider is installed**.
**Why now.** Gate `G1` is passed. Everything in Phase 4 consumes this vocabulary, and §3.2 makes the arrow point this way, so it must exist first.
**Deliverable.** `app/capabilities/` with spec primitives, a conformance checker, one real specification, and an architecture test that enforces the import direction.

**Phase 3 Exit Gate — all must be true before Phase 4 starts:**

- [ ] Every task in this phase is checked off
- [ ] `uv run ruff check .` and `uv run mypy .` clean across the repo
- [ ] `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` green
- [ ] No test failing that was not already recorded in `docs/dev/plugin-decoupling/BASELINE.md`
- [ ] No PROTECTED path appears in `git diff --name-only <phase-start>..HEAD`
- [ ] Functional proof: `uv run python -c "import app.capabilities; print(sorted(app.capabilities.__all__))"` succeeds and `uv run python -c "import app.capabilities, sys; assert not [m for m in sys.modules if m.startswith('app.services')]"` exits 0 — the spec layer loads no domain
- [ ] `uv run python scripts/audit_check.py` exits 0 and its `REG` feature count is unchanged versus the Phase 2 run

---

#### - [ ] Task `P3-T01` — Create capabilities package skeleton

**Traces to:** `REFACTOR_PLAN.md` Phase 3; resolutions `R-03`, `R-04`; Gate `G3`
**Depends on:** `P1-T04`
**Estimated size:** S (<50 LOC)

**Goal.** `app/capabilities/` exists as an importable, empty, non-feature package with a README that states its exclusion from the feature registry.

**Context to Read (and nothing else):**

- `AGENTS.md` §1, the sub-bullet `- **Non-Feature Infrastructure Packages**:` added by `P1-T04` — the rule this package relies on
- Shared Contracts §3.1, §3.2, §3.11

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/__init__.py` | CREATE | Package root, empty `__all__` until `P3-T02` |
| `app/capabilities/README.md` | CREATE | Non-feature declaration |
| `docs/CHANGELOG.md` | MODIFY | One bullet under `## [Unreleased]` |

**Specification (the contract — copy exactly):**

```python
# app/capabilities/__init__.py
"""Versioned provider-neutral capability specifications.

This package is importable with zero providers installed. It contains no
implementation, no provider selection, and no I/O, and it imports nothing from
``app.kernel``, ``app.services``, ``app.agentic``, or ``app.utils``.
"""

from __future__ import annotations

__all__: list[str] = []
```

`README.md` must state, in prose: the package purpose; that specifications live at `app/capabilities/<domain>/<capability>/vN.py`; that the package carries no `FEAT-*` identifiers and no `### Feature Registry` section per `AGENTS.md` §1 Non-Feature Infrastructure Packages; and that its boundary is verified by `tests/architecture/test_import_boundaries.py`.

**Behaviour Rules (numbered, testable):**

1. `import app.capabilities` succeeds in a fresh interpreter.
2. `app.capabilities.__all__ == []`.
3. Importing it adds no module beginning `app.services`, `app.agentic`, `app.kernel`, or `app.utils` to `sys.modules`.
4. `app/capabilities/README.md` contains no `FEAT-` substring and no `### Feature Registry` heading.

**Implementation Steps:**

1. Create `app/capabilities/__init__.py` with the exact content above.
2. Create `app/capabilities/README.md` covering the four points listed.
3. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
4. If `### Added` carries a count in its heading, increment it by one.
5. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add a `### Feature Registry` section or any `FEAT-*` identifier to the README.
- Do not create `spec.py`, `conformance.py`, or any domain subdirectory — those are later tasks.
- Do not import anything into `__init__.py` beyond `from __future__ import annotations`.
- Do not create `app/kernel/` or `app/composition/`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `scripts/audit_check.py`, `scripts/ci_check.py`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_capabilities_package.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_package_imports_clean` | `import app.capabilities` | no exception |
| `test_all_is_empty` | `app.capabilities.__all__` | `== []` |
| `test_no_domain_modules_loaded` | fresh `subprocess`-free check over `sys.modules` after import | no key starts with `app.services`, `app.agentic`, `app.kernel` |
| `test_readme_has_no_feature_ids` | `app/capabilities/README.md` text | `"FEAT-" not in text` and `"### Feature Registry" not in text` |

Run: `uv run pytest tests/unit/test_capabilities_package.py -q` → all pass, 0 skipped.

**Usage Example**

None. Per `P1-T04` this package carries no numbered usage program; its behaviour is proven by unit and architecture tests.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/capabilities tests/unit/test_capabilities_package.py
uv run ruff check app/capabilities tests/unit/test_capabilities_package.py
uv run mypy .
uv run pytest tests/unit/test_capabilities_package.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added app/capabilities package for versioned provider-neutral specifications.`

**Git Commit:**

```bash
git add app/capabilities/__init__.py app/capabilities/README.md tests/unit/test_capabilities_package.py docs/CHANGELOG.md
git commit -m "feat(capabilities): add capability specification package" -m "Creates the provider-neutral specification package as non-feature
infrastructure, importable with zero providers installed.
Refs: REFACTOR_PLAN.md Phase 3, R-03, R-04, Gate G3"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line; git revert + re-run is clean`

**Definition of Done:**

- [ ] Three files created/modified, no others
- [ ] All four tests written and passing
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] README free of `FEAT-` and of a Feature Registry section
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P3-T02` — Add capability specification primitives

**Traces to:** `REFACTOR_PLAN.md` Phase 3; decisions `D-02`, `D-03`, `D-04`; resolution `R-01`; conflict `CF-04`; Gate `G3`
**Depends on:** `P3-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** `CapabilitySpec` and `Requirement` exist as validated frozen dataclasses, with the qualified-id helpers and the version-window match, so every later module names capabilities the same way.

**Context to Read (and nothing else):**

- Shared Contracts §3.3 — the complete contract, copy it
- Shared Contracts §3.2 — the import ban this module must honour
- Conflict `CF-04` in §7 — why this module logs nothing

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/spec.py` | CREATE | Primitives |
| `app/capabilities/__init__.py` | MODIFY | Re-export four symbols |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `app/capabilities/__init__.py`, replace exactly this line:

```python
__all__: list[str] = []
```

with the import block and `__all__` given below. The module docstring and `from __future__ import annotations` line must remain unchanged.

**Specification (the contract — copy exactly):** as Shared Contracts §3.3, plus:

```python
# app/capabilities/__init__.py — replacing the empty __all__
from app.capabilities.spec import (
    CapabilitySpec,
    Requirement,
    parse_qualified_id,
    qualified_id,
    satisfies,
)

__all__ = [
    "CapabilitySpec",
    "Requirement",
    "parse_qualified_id",
    "qualified_id",
    "satisfies",
]
```

**Behaviour Rules (numbered, testable):**

1. `CapabilitySpec.__post_init__` raises `ValueError` `"version must be >= 1, got {version}"` when `version < 1`.
2. It raises `ValueError` `"unknown cardinality: {cardinality}"` when `cardinality not in CARDINALITIES`.
3. It raises `ValueError` `"unknown kind: {kind}"` when `kind not in KINDS`.
4. It raises `ValueError` `"capability_id must be lowercase dotted, got {capability_id}"` when the id does not match `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`.
5. `Requirement.__post_init__` raises `ValueError` `"unknown on_missing policy: {on_missing}"` when the policy is not in `ON_MISSING_POLICIES`, and `"min_version {min} exceeds max_version {max}"` when `min_version > max_version`.
6. `Requirement.on_missing` defaults to `"fail_closed"`.
7. `qualified_id("indicator.rsi", 1) == "indicator.rsi.v1"`.
8. `parse_qualified_id("indicator.rsi.v1") == ("indicator.rsi", 1)`; a string without a trailing `.v<int>` raises `ValueError` `"not a qualified capability id: {text}"`.
9. `satisfies` returns `True` when `spec.capability_id == requirement.capability_id` and `requirement.min_version <= spec.version <= requirement.max_version`, else `False`.
10. The module contains no `import` of `app.kernel`, `app.services`, `app.agentic`, or `app.utils`, and no logging call.

**Implementation Steps:**

1. Create `app/capabilities/spec.py` with a module docstring and `from __future__ import annotations`.
2. Add the four module constants from §3.3 as `Final`.
3. Add the compiled id pattern as a module-level `Final[re.Pattern[str]]`.
4. Add `CapabilitySpec` as a frozen dataclass with the five fields and `__post_init__` implementing rules 1–4.
5. Add `Requirement` as a frozen dataclass with the four fields and `__post_init__` implementing rule 5.
6. Implement `qualified_id`, `parse_qualified_id`, `satisfies` per rules 7–9.
7. Give every module member a Google docstring with `Args:`, `Returns:` and `Raises:` as applicable.
8. Replace the `__all__` line in `app/capabilities/__init__.py` with the block above.
9. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add a version-range **string** parser. Windows are explicit inclusive integers; there is no `">=1,<2"` syntax anywhere in this plan.
- Do not import `app.utils` or call any logger — see `CF-04`.
- Do not add `runtime_checkable`, `__slots__`, `Generic`, or a metaclass.
- Do not add a registry, cache, or global mutable state to this module.
- Do not create `conformance.py` — that is `P3-T03`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_capability_spec.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_qualified_id_roundtrip` | `("indicator.rsi", 1)` | `parse_qualified_id(qualified_id(...))` returns the input |
| `test_rejects_zero_version` | `CapabilitySpec(..., version=0, ...)` | `ValueError`, match `"version must be >= 1, got 0"` |
| `test_rejects_unknown_cardinality` | `cardinality="some"` | `ValueError`, match `"unknown cardinality: some"` |
| `test_rejects_bad_capability_id` | `capability_id="Indicator.RSI"` | `ValueError`, match `"lowercase dotted"` |
| `test_requirement_defaults_fail_closed` | `Requirement("data.ohlcv", 1, 1)` | `.on_missing == "fail_closed"` |
| `test_satisfies_version_window` | spec v2; requirements (1,1), (1,3), (3,4) | `False`, `True`, `False` |

Run: `uv run pytest tests/unit/test_capability_spec.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/capabilities tests/unit/test_capability_spec.py
uv run ruff check app/capabilities tests/unit/test_capability_spec.py
uv run mypy .
uv run pytest tests/unit/test_capability_spec.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added CapabilitySpec and Requirement primitives with explicit integer version windows.`

**Git Commit:**

```bash
git add app/capabilities/spec.py app/capabilities/__init__.py tests/unit/test_capability_spec.py docs/CHANGELOG.md
git commit -m "feat(capabilities): add specification primitives" -m "Adds validated CapabilitySpec and Requirement dataclasses, qualified-id
helpers and the version-window match. Windows are explicit inclusive
integers; no range-string parser exists.
Refs: REFACTOR_PLAN.md D-02, D-03, D-04, R-01, Gate G3"
```

**Re-run safety:** `Safe — one anchored replacement in __init__.py, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] No import of `app.utils`, `app.kernel`, `app.services`, `app.agentic` in `spec.py`
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P3-T03` — Add capability conformance checker

**Traces to:** `REFACTOR_PLAN.md` Phase 3 ("contract conformance helpers"); resolution `R-01`; Gate `G3`
**Depends on:** `P3-T02`
**Estimated size:** M (50–120 LOC)

**Goal.** A single function reports every way a candidate provider fails its capability contract, handling both the `protocol` and `callable_record` kinds from `R-01`.

**Context to Read (and nothing else):**

- Shared Contracts §3.4 — the complete contract and the four violation string formats
- `app/capabilities/spec.py` — created by `P3-T02`; you import `CapabilitySpec` and `KINDS` from it
- Conflict `CF-04` in §7 — why this module logs nothing

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/conformance.py` | CREATE | Checker |
| `app/capabilities/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `app/capabilities/__init__.py`, insert `from app.capabilities.conformance import check_conformance` immediately **before** the existing `from app.capabilities.spec import (` line, and insert `"check_conformance",` into `__all__` so the list stays sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.4.

**Behaviour Rules (numbered, testable):**

1. `check_conformance` returns an empty tuple when the candidate conforms.
2. `kind == "protocol"`: for each public attribute of `spec.contract` that `inspect.isfunction` accepts, the candidate must have that attribute, it must be callable, and its positional-or-keyword parameter names must match exactly after removing a leading `self`.
3. A missing attribute yields `"missing attribute: {name}"`; a present non-callable yields `"not callable: {name}"`; a name mismatch yields `"parameter mismatch on {name}: expected {expected}, got {actual}"` where both sides are comma-joined parameter names.
4. `kind == "callable_record"`: a candidate that is not an instance of `spec.contract` yields exactly one violation, `"wrong record type: expected {expected}, got {actual}"`, using `__name__` on both sides.
5. `kind == "callable_record"`: for a correct instance, every `dataclasses.fields` entry whose value is not callable yields `"not callable: {name}"`.
6. An unknown `spec.kind` raises `ValueError` `"unknown kind: {kind}"`.
7. Violations are returned in the order the contract declares its members, and the function never raises for a non-conforming candidate.
8. Attributes whose name starts with `_` are ignored on both paths.

**Implementation Steps:**

1. Create `app/capabilities/conformance.py` with a module docstring and `from __future__ import annotations`.
2. Import `dataclasses` and `inspect`; import `CapabilitySpec` and `KINDS` from `app.capabilities.spec`.
3. Add a private `_parameter_names(func) -> tuple[str, ...]` returning positional-or-keyword parameter names with a leading `self` removed.
4. Add a private `_check_protocol(spec, candidate) -> list[str]` implementing rules 2, 3 and 8.
5. Add a private `_check_record(spec, candidate) -> list[str]` implementing rules 4, 5 and 8.
6. Implement `check_conformance` dispatching on `spec.kind`, raising `ValueError` per rule 6, returning `tuple(...)`.
7. Give every member a Google docstring including `Raises:` where applicable.
8. Update `app/capabilities/__init__.py` per the anchor instructions.
9. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not use `isinstance` against a `Protocol` class, and do not add `@runtime_checkable` — structural checks here are explicit and by inspection.
- Do not compare parameter *types*, defaults, or annotations. Names only.
- Do not raise for a non-conforming candidate; non-conformance is a returned value.
- Do not import `app.utils` or call any logger.
- Do not import `app.kernel` — it does not exist yet and must never be a dependency of this package.
- Do not modify `app/capabilities/spec.py`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_capability_conformance.py` (CREATE)

Define inline in the test module: a `Protocol` named `_Greeter` with `def greet(self, name: str) -> str: ...`, a conforming class, a class missing `greet`, a class whose `greet` takes `who`, a frozen dataclass `_Record` with one field `compute`, and an unrelated frozen dataclass `_Other`.

| Test function | Input | Expected |
|---|---|---|
| `test_conforming_protocol_is_clean` | conforming instance | `() ` |
| `test_missing_attribute_reported` | class without `greet` | `("missing attribute: greet",)` |
| `test_parameter_mismatch_reported` | `greet(self, who)` | one violation matching `"parameter mismatch on greet: expected name, got who"` |
| `test_wrong_record_type_reported` | `_Other()` against `_Record` spec | one violation matching `"wrong record type: expected _Record, got _Other"` |
| `test_non_callable_field_reported` | `_Record(compute=5)` | `("not callable: compute",)` |
| `test_unknown_kind_raises` | spec with `kind` forced to `"other"` via `dataclasses.replace` | `ValueError`, match `"unknown kind: other"` |

Run: `uv run pytest tests/unit/test_capability_conformance.py -q` → all pass, 0 skipped.

> The last test needs a `CapabilitySpec` whose `kind` bypasses `__post_init__` validation. Construct it with `object.__setattr__` on a valid instance inside the test — this is permitted here because ruff `SLF001` is ignored in `test_*.py`.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/capabilities tests/unit/test_capability_conformance.py
uv run ruff check app/capabilities tests/unit/test_capability_conformance.py
uv run mypy .
uv run pytest tests/unit/test_capability_conformance.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added capability conformance checking for protocol and callable-record contracts.`

**Git Commit:**

```bash
git add app/capabilities/conformance.py app/capabilities/__init__.py tests/unit/test_capability_conformance.py docs/CHANGELOG.md
git commit -m "feat(capabilities): add contract conformance checker" -m "Reports every way a candidate fails its capability contract, covering both
the protocol and callable-record kinds. Non-conformance is a returned
value, never an exception.
Refs: REFACTOR_PLAN.md Phase 3, R-01, Gate G3"
```

**Re-run safety:** `Safe — one anchored insertion in __init__.py, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] No `@runtime_checkable`, no type comparison, no logger
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P3-T04` — Add first capability specification

**Traces to:** `REFACTOR_PLAN.md` Phase 3; resolution `R-04`; source Phase 9 pilot target
**Depends on:** `P3-T03`
**Estimated size:** S (<50 LOC)

**Goal.** One real specification exists at the frozen path, proving the `<domain>/<capability>/vN.py` layout and giving Phase 4 something concrete to resolve against.

**Context to Read (and nothing else):**

- Shared Contracts §3.3 — `CapabilitySpec`, `Requirement`
- Batch 1 §2.3 — the verified `rsi` signature this contract mirrors. **You will not import, call, or modify `rsi`.**
- Planner Observation §9.4 — the spec describes the shape; it does not wrap the function
- Planner Observation §9.6 — why two `__init__.py` files are needed

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/indicator/__init__.py` | CREATE | Domain namespace |
| `app/capabilities/indicator/rsi/__init__.py` | CREATE | Capability namespace |
| `app/capabilities/indicator/rsi/v1.py` | CREATE | The specification |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

Both namespace `__init__.py` files contain only a one-line module docstring and `__all__: list[str] = []`.

**Specification (the contract — copy exactly):**

```python
# app/capabilities/indicator/rsi/v1.py
"""Relative Strength Index capability, contract version 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Protocol

from app.capabilities.spec import CapabilitySpec, Requirement

CAPABILITY_ID: Final[str] = "indicator.rsi"
VERSION: Final[int] = 1


class RsiCalculator(Protocol):
    """Structural contract for a Relative Strength Index provider."""

    def compute(self, data: Any, *, period: int, source: str) -> Any:
        """Calculate RSI over one normalized market dataset.

        Args:
            data: One normalized immutable market dataset.
            period: Smoothing period of at least two.
            source: Selected OHLC source column name.

        Returns:
            A deterministic indicator result.
        """
        ...


@dataclass(frozen=True)
class RsiRecord:
    """Callable record binding one RSI implementation.

    Attributes:
        compute: The calculation entry point matching RsiCalculator.compute.
    """

    compute: Any


SPEC: Final[CapabilitySpec] = CapabilitySpec(
    capability_id=CAPABILITY_ID,
    version=VERSION,
    cardinality="many",
    kind="callable_record",
    contract=RsiRecord,
)

REQUIRES: Final[tuple[Requirement, ...]] = ()

__all__ = ["CAPABILITY_ID", "REQUIRES", "SPEC", "VERSION", "RsiCalculator", "RsiRecord"]
```

**Behaviour Rules (numbered, testable):**

1. `SPEC.capability_id == "indicator.rsi"` and `SPEC.version == 1`.
2. `SPEC.kind == "callable_record"` and `SPEC.cardinality == "many"` — RSI is pure, so `R-01` puts it on the record path, and many providers may offer it.
3. `qualified_id(SPEC.capability_id, SPEC.version) == "indicator.rsi.v1"`.
4. `check_conformance(SPEC, RsiRecord(compute=lambda **_: None))` returns `()`.
5. Importing `app.capabilities.indicator.rsi.v1` loads no module beginning `app.services`.
6. `REQUIRES` is empty: this contract version declares no dependency.

**Implementation Steps:**

1. Create `app/capabilities/indicator/__init__.py` with a docstring and empty `__all__`.
2. Create `app/capabilities/indicator/rsi/__init__.py` the same way.
3. Create `app/capabilities/indicator/rsi/v1.py` with the exact content above.
4. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
5. Commit.

**DO NOT (anti-invention guardrails):**

- Do not import, call, or reference `app.services.indicators` in any way.
- Do not modify `app/services/indicators/momentum/rsi.py`.
- Do not narrow `Any` to `MarketDataset` or `IndicatorResult` — those are private to the Indicators domain and importing them would break §3.2. Tightening them is a Batch 4 task once the Data contracts exist.
- Do not add a second version file (`v2.py`).
- Do not register this spec anywhere — the registry is `P4-T05`.
- Do not re-export it from `app/capabilities/__init__.py`; specs are imported by their full path.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_capability_indicator_rsi_v1.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_spec_identity` | `SPEC` | `capability_id == "indicator.rsi"`, `version == 1` |
| `test_spec_kind_and_cardinality` | `SPEC` | `kind == "callable_record"`, `cardinality == "many"` |
| `test_qualified_id` | `SPEC` | `qualified_id(...) == "indicator.rsi.v1"` |
| `test_conforming_record_is_clean` | `RsiRecord(compute=<lambda>)` | `check_conformance` returns `()` |
| `test_non_callable_compute_reported` | `RsiRecord(compute=5)` | `("not callable: compute",)` |
| `test_no_domain_import` | after importing the spec module | no `sys.modules` key starts with `app.services` |

Run: `uv run pytest tests/unit/test_capability_indicator_rsi_v1.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/capabilities tests/unit/test_capability_indicator_rsi_v1.py
uv run ruff check app/capabilities tests/unit/test_capability_indicator_rsi_v1.py
uv run mypy .
uv run pytest tests/unit/test_capability_indicator_rsi_v1.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added indicator.rsi.v1 capability specification.`

**Git Commit:**

```bash
git add app/capabilities/indicator docs/CHANGELOG.md tests/unit/test_capability_indicator_rsi_v1.py
git commit -m "feat(capabilities): add indicator.rsi.v1 specification" -m "First real capability specification, proving the domain/capability/vN
layout. Describes the RSI contract shape without importing, calling or
modifying the existing implementation.
Refs: REFACTOR_PLAN.md Phase 3, R-04, Gate G3"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] `app/services/indicators/` untouched
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P3-T05` — Add import-boundary architecture test

**Traces to:** `REFACTOR_PLAN.md` Phase 3 exit gate; Shared Contracts §3.2; `P1-T04` policy text
**Depends on:** `P3-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** A test suite fails the build if `app/capabilities/` ever imports the kernel, a domain, or `app.utils` — turning §3.2 from a convention into an enforced invariant.

**Context to Read (and nothing else):**

- Shared Contracts §3.2 — the frozen dependency direction this test enforces
- `scripts/composability_graph.py` — created by `P2-T01`; **do not import it**, but its `extract_edges` design is the reference for the AST walk you will write independently here
- `AGENTS.md` §1 `- **Non-Feature Infrastructure Packages**:` — the sentence naming `tests/architecture/`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/architecture/__init__.py` | CREATE | Package marker |
| `tests/architecture/test_import_boundaries.py` | CREATE | The invariant |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
FORBIDDEN_PREFIXES: dict[str, tuple[str, ...]] = {
    "app/capabilities": ("app.kernel", "app.services", "app.agentic", "app.utils"),
    "app/kernel": ("app.services", "app.agentic"),
}


def imported_modules(path: Path) -> set[str]: ...
```

`imported_modules` parses one file with `ast` and returns every dotted module name named by an `Import` or `ImportFrom` with `level == 0`, including those inside `if TYPE_CHECKING:` — a type-only import still creates a source dependency for this purpose.

**Behaviour Rules (numbered, testable):**

1. For every `.py` file under each key of `FORBIDDEN_PREFIXES`, no imported module may equal or start with any forbidden prefix followed by `.`.
2. A violation fails with a message naming the file, the offending module, and the rule: `"{path} imports {module}, forbidden for {package}"`.
3. `app/kernel` is checked even before it exists; a missing directory yields zero files and the test passes vacuously.
4. Relative imports (`level > 0`) are ignored.
5. `tests/architecture/` files are excluded from the walk.

**Implementation Steps:**

1. Create `tests/architecture/__init__.py` containing only a one-line docstring.
2. Create `tests/architecture/test_import_boundaries.py`.
3. Add `REPO_ROOT = Path(__file__).resolve().parents[2]` and the `FORBIDDEN_PREFIXES` mapping above.
4. Implement `imported_modules` per the contract, reading with `encoding="utf-8"`.
5. Add `test_capabilities_imports_nothing_forbidden`, walking `app/capabilities` with `Path.rglob("*.py")` and asserting rule 1 with the rule 2 message.
6. Add `test_kernel_imports_no_domain`, doing the same for `app/kernel` and honouring rule 3.
7. Add `test_capabilities_loads_no_domain_at_runtime`, importing `app.capabilities` and asserting no `sys.modules` key starts with `app.services` or `app.agentic`.
8. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
9. Commit.

**DO NOT (anti-invention guardrails):**

- Do not import `scripts/composability_graph.py`; `tests/architecture/` must not depend on tooling under `scripts/`.
- Do not exempt `TYPE_CHECKING` imports — a type-only import of a domain still couples the spec layer to it.
- Do not add a forbidden prefix for `app/composition` — it does not exist until Batch 3.
- Do not use `subprocess`; ruff `S603`/`S607` are not ignored under `tests/`.
- Do not mark any test `xfail` or `skip`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

The file created by this task **is** the test. Its own correctness is proven by these assertions, which must be present as separate test functions:

| Test function | Input | Expected |
|---|---|---|
| `test_capabilities_imports_nothing_forbidden` | all `.py` under `app/capabilities` | no violations |
| `test_kernel_imports_no_domain` | all `.py` under `app/kernel` (absent at this point) | passes vacuously |
| `test_capabilities_loads_no_domain_at_runtime` | `import app.capabilities` | no `app.services*` or `app.agentic*` in `sys.modules` |
| `test_imported_modules_finds_type_checking_import` | inline source with a `TYPE_CHECKING` block importing `app.services.data` | `"app.services.data"` in the returned set |
| `test_imported_modules_ignores_relative` | inline source `from . import x` | empty set |

Run: `uv run pytest tests/architecture -q` → all pass, 0 skipped.

**Usage Example**

None — this is a test artefact.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format tests/architecture
uv run ruff check tests/architecture
uv run mypy .
uv run pytest tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added architecture tests enforcing capability and kernel import boundaries.`

**Git Commit:**

```bash
git add tests/architecture docs/CHANGELOG.md
git commit -m "test(architecture): enforce capability import boundaries" -m "Fails the build if app/capabilities imports the kernel, a domain or
app.utils, and if app/kernel imports a domain. Type-only imports count.
Refs: REFACTOR_PLAN.md Phase 3 exit gate, Gate G3"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Three files created/modified, no others
- [ ] All five tests written and passing
- [ ] Test suite depends on nothing under `scripts/`
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

### Phase 4 — Protected microkernel

**Goal.** A business-neutral runtime that discovers, validates and resolves providers, and reports precisely why a capability is unusable — all without importing a single line of provider code.
**Why now.** Gate `G3` passed; the spec vocabulary exists. Every later phase composes against this surface.
**Deliverable.** `app/kernel/` with errors, manifests, discovery, registry, resolver and profile readiness.

**Phase 4 Exit Gate — all must be true before Phase 5 starts:**

- [ ] Every task in this phase is checked off
- [ ] `uv run ruff check .` and `uv run mypy .` clean across the repo
- [ ] `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` green
- [ ] No test failing that was not already recorded in `docs/dev/plugin-decoupling/BASELINE.md`
- [ ] No PROTECTED path appears in `git diff --name-only <phase-start>..HEAD`
- [ ] `uv run pytest tests/architecture -q` green — the kernel imports no domain
- [ ] Functional proof: in a copied tree with `app/services/` deleted, `uv run python -c "import app.kernel; print(len(app.kernel.__all__))"` succeeds and prints `12`
- [ ] No occurrence of `import_module`, `__import__`, or `async def` anywhere under `app/kernel/`

---

#### - [ ] Task `P4-T01` — Create kernel package skeleton

**Traces to:** `REFACTOR_PLAN.md` Phase 4; decision `D-01`; resolution `R-03`; Gate `G4`
**Depends on:** `P3-T05`
**Estimated size:** S (<50 LOC)

**Goal.** `app/kernel/` exists as an importable, empty, non-feature package whose boundary is already covered by the `P3-T05` architecture test.

**Context to Read (and nothing else):**

- `app/capabilities/__init__.py` and `app/capabilities/README.md` — the pattern to mirror
- Shared Contracts §3.1, §3.2, §3.11

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/__init__.py` | CREATE | Package root, empty `__all__` until `P4-T02` |
| `app/kernel/README.md` | CREATE | Non-feature declaration |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):**

```python
# app/kernel/__init__.py
"""Business-neutral runtime for capability discovery, resolution and lifecycle.

The kernel imports nothing from ``app.services`` or ``app.agentic``. It knows
no indicator formula, no broker API, no risk policy. It owns the mechanism of
composition, never the policy.
"""

from __future__ import annotations

__all__: list[str] = []
```

`README.md` states: the purpose above; that the kernel carries no `FEAT-*` identifiers and no `### Feature Registry` section per `AGENTS.md` §1 Non-Feature Infrastructure Packages; that its boundary is verified by `tests/architecture/test_import_boundaries.py`; and that it is synchronous per `R-02`.

**Behaviour Rules (numbered, testable):**

1. `import app.kernel` succeeds in a fresh interpreter.
2. `app.kernel.__all__ == []`.
3. Importing it adds no `sys.modules` key beginning `app.services` or `app.agentic`.
4. `app/kernel/README.md` contains no `FEAT-` substring and no `### Feature Registry` heading.

**Implementation Steps:**

1. Create `app/kernel/__init__.py` with the exact content above.
2. Create `app/kernel/README.md` covering the four points listed.
3. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
4. If `### Added` carries a count in its heading, increment it by one.
5. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add a `### Feature Registry` section or any `FEAT-*` identifier.
- Do not create `errors.py`, `manifests.py`, or any other kernel module — those are later tasks.
- Do not import anything into `__init__.py` beyond `from __future__ import annotations`.
- Do not create `app/composition/` — that is Batch 3.
- Do not add `async def` anywhere; `R-02` makes the kernel synchronous.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_package.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_package_imports_clean` | `import app.kernel` | no exception |
| `test_all_is_empty` | `app.kernel.__all__` | `== []` |
| `test_no_domain_modules_loaded` | `sys.modules` after import | no key starts with `app.services` or `app.agentic` |
| `test_readme_has_no_feature_ids` | `app/kernel/README.md` text | `"FEAT-" not in text`, `"### Feature Registry" not in text` |

Run: `uv run pytest tests/unit/test_kernel_package.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_package.py
uv run ruff check app/kernel tests/unit/test_kernel_package.py
uv run mypy .
uv run pytest tests/unit/test_kernel_package.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added app/kernel package for capability discovery, resolution and lifecycle.`

**Git Commit:**

```bash
git add app/kernel/__init__.py app/kernel/README.md tests/unit/test_kernel_package.py docs/CHANGELOG.md
git commit -m "feat(kernel): add protected microkernel package" -m "Creates the business-neutral runtime package as non-feature infrastructure.
Imports no domain; synchronous per R-02.
Refs: REFACTOR_PLAN.md Phase 4, D-01, R-03, Gate G4"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Three files created/modified, no others
- [ ] All four tests written and passing
- [ ] `ruff`, `mypy .`, architecture tests, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T02` — Add kernel reason codes

**Traces to:** `REFACTOR_PLAN.md` Phase 7 reason-code list; decision `D-06`; Gate `G4`
**Depends on:** `P4-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** The thirteen reason codes, the `Unavailability` evidence record and `KernelError` exist, establishing once and for all that capability absence is a returned value and never an exception.

**Context to Read (and nothing else):**

- Shared Contracts §3.5 — the complete contract, copy it
- Planner Observation §9.2 — the value-vs-exception distinction

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/errors.py` | CREATE | Reason codes, evidence, exception |
| `app/kernel/__init__.py` | MODIFY | Re-export four symbols |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `app/kernel/__init__.py`, replace exactly `__all__: list[str] = []` with an import of `KernelError`, `ReasonCode`, `Unavailability` from `app.kernel.errors` and `__all__ = ["KernelError", "ReasonCode", "Unavailability"]`. The docstring and `from __future__ import annotations` stay unchanged.

**Specification (the contract — copy exactly):** as Shared Contracts §3.5.

**Behaviour Rules (numbered, testable):**

1. `ReasonCode` is a `StrEnum` with exactly thirteen members whose values equal their names.
2. `CAPABILITY_UNAVAILABLE == "CAPABILITY_UNAVAILABLE"`.
3. `Unavailability.code` defaults to `CAPABILITY_UNAVAILABLE` and cannot be set to anything else — `__post_init__` raises `ValueError` `"code must be CAPABILITY_UNAVAILABLE, got {code}"`.
4. `Unavailability.__post_init__` raises `ValueError` `"retryable must be True only for UNHEALTHY and DRAINING, got {reason_code}"` when `retryable` is `True` and `reason_code` is neither.
5. `dependency_chain` is a tuple; a list raises `TypeError` `"dependency_chain must be a tuple"`.
6. `KernelError` subclasses `Exception` directly and adds no fields.
7. No function in this module raises for capability absence; absence is expressed only by constructing an `Unavailability`.

**Implementation Steps:**

1. Create `app/kernel/errors.py` with a module docstring and `from __future__ import annotations`.
2. Import `StrEnum` from `enum`, `dataclass` from `dataclasses`, `Final` from `typing`.
3. Add `ReasonCode` with the thirteen members from §3.5, in that exact order.
4. Add `CAPABILITY_UNAVAILABLE` as a `Final[str]`.
5. Add a module-level `RETRYABLE_REASONS: Final[frozenset[ReasonCode]]` containing exactly `UNHEALTHY` and `DRAINING`.
6. Add the frozen `Unavailability` dataclass with the seven fields and `__post_init__` implementing rules 3–5.
7. Add `KernelError` with a one-line docstring.
8. Give every member a Google docstring with `Attributes:` or `Raises:` as applicable.
9. Update `app/kernel/__init__.py` per the anchor instruction.
10. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
11. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not create an exception class per reason code.** Capability absence is a returned `Unavailability`; `KernelError` is raised only for kernel misuse — a malformed manifest, a duplicate provider id, an illegal state transition.
- Do not add a fourteenth reason code, rename one, or change a value.
- Do not add a `message` or `detail` free-text field — evidence is structured.
- Do not import `app.utils` or add logging to this module; it is a pure data module.
- Do not add serialisation to `StandardResponse` — that wiring is Phase 7, Batch 3.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_errors.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_thirteen_reason_codes` | `list(ReasonCode)` | length 13; every `.value == .name` |
| `test_code_defaults_and_is_fixed` | valid `Unavailability` | `.code == "CAPABILITY_UNAVAILABLE"` |
| `test_wrong_code_rejected` | `code="OTHER"` | `ValueError`, match `"code must be CAPABILITY_UNAVAILABLE"` |
| `test_retryable_only_for_two` | `NOT_INSTALLED` + `retryable=True` | `ValueError`, match `"retryable must be True only"` |
| `test_retryable_allowed_for_draining` | `DRAINING` + `retryable=True` | constructs cleanly |
| `test_dependency_chain_must_be_tuple` | a list | `TypeError`, match `"must be a tuple"` |

Run: `uv run pytest tests/unit/test_kernel_errors.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_errors.py
uv run ruff check app/kernel tests/unit/test_kernel_errors.py
uv run mypy .
uv run pytest tests/unit/test_kernel_errors.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added thirteen capability unavailability reason codes with structured evidence.`

**Git Commit:**

```bash
git add app/kernel/errors.py app/kernel/__init__.py tests/unit/test_kernel_errors.py docs/CHANGELOG.md
git commit -m "feat(kernel): add capability unavailability reason codes" -m "Thirteen reason codes plus structured Unavailability evidence carrying the
dependency chain. Absence is a returned value; KernelError is reserved for
kernel misuse.
Refs: REFACTOR_PLAN.md D-06, Phase 7 code list, Gate G4"
```

**Re-run safety:** `Safe — one anchored replacement, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] Exactly one exception class exists in the module
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T03` — Add provider manifest parser

**Traces to:** `REFACTOR_PLAN.md` §1.1 manifest schema; decision `D-07`; resolution `R-05`; Gate `G4`
**Depends on:** `P4-T02`
**Estimated size:** L (120–200 LOC)

**Goal.** A `manifest.toml` is parsed into a validated frozen `ProviderManifest` using stdlib `tomllib`, with `entry_point` stored as an inert string.

**Context to Read (and nothing else):**

- Shared Contracts §3.6 — the TOML schema and the complete Python contract
- `app/capabilities/spec.py` — you import `Requirement` from `app.capabilities`
- `app/kernel/errors.py` — you raise `KernelError`
- Planner Observation §9.3 — why `entry_point` is never imported

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/manifests.py` | CREATE | Schema and parser |
| `app/kernel/__init__.py` | MODIFY | Add two exports |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** In `app/kernel/__init__.py`, add `from app.kernel.manifests import ProviderManifest, load_manifest` and insert `"ProviderManifest",` and `"load_manifest",` into `__all__`, keeping it sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.6.

**Behaviour Rules (numbered, testable):**

1. Every schema violation raises `KernelError` with message `"invalid manifest at {source_path}: {detail}"`.
2. Missing `[provider]`, or a missing `id`, `version` or `entry_point` key, is a violation.
3. `provider_id` must match `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$`; detail `"provider id must be lowercase dotted"`.
4. `version` must be an `int >= 1`; detail `"version must be >= 1"`.
5. `entry_point` must contain exactly one `:`; detail `"entry_point must be module:callable"`. **It is stored, never imported.**
6. `provides` must be a non-empty array of tables each with `capability_id` and `version`; detail `"provides must declare at least one capability"`.
7. `requires` is optional and defaults to `()`. Each entry becomes a `Requirement`; a missing `on_missing` defaults to `"fail_closed"`. An unknown policy propagates the `ValueError` from `Requirement` re-raised as `KernelError` with the same message format.
8. `effects` is optional and defaults to `()`. Each `effect_class` must be in `EFFECT_CLASSES`; detail `"unknown effect class: {value}"`.
9. `owns_migrations` and `owns_persistence` are optional booleans defaulting to `False`.
10. `load_manifest(path)` reads the file with `encoding="utf-8"` and delegates to `parse_manifest`; a `tomllib.TOMLDecodeError` becomes `KernelError` with detail `"malformed TOML"`.
11. A valid manifest with only the mandatory keys parses successfully.

**Implementation Steps:**

1. Create `app/kernel/manifests.py` with a module docstring and `from __future__ import annotations`.
2. Import `tomllib`, `dataclass`, `Path`, `Final`; import `Requirement` from `app.capabilities`; import `KernelError` from `app.kernel.errors`.
3. Add `EFFECT_CLASSES` and the compiled provider-id pattern as `Final`.
4. Add the frozen `EffectDeclaration` dataclass.
5. Add the frozen `ProviderManifest` dataclass with the nine fields from §3.6.
6. Add a private `_fail(source_path, detail)` that raises `KernelError` with the rule 1 format.
7. Implement `parse_manifest`, validating in the order of rules 2–9.
8. Implement `load_manifest` per rule 10.
9. Give every member a Google docstring including `Raises:`.
10. Update `app/kernel/__init__.py` per the anchor instruction.
11. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
12. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not import, resolve, or validate the `entry_point` target.** No `importlib`, no `__import__`, no `pkgutil`. Discovery must never execute provider code — this is the whole reason the manifest is TOML (`R-05`).
- Do not add a YAML or JSON fallback format.
- Do not add a version-range string; `requires` carries explicit `min_version` and `max_version` integers.
- Do not silently default a missing mandatory key.
- Do not add a manifest cache or registry here — that is `P4-T05`.
- Do not add logging; parse failures are exceptions, not log lines.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_manifests.py` (CREATE)

Define `MINIMAL` inline as a TOML string with `[provider]` (`id`, `version`, `entry_point`) and one `[[provides]]` table.

| Test function | Input | Expected |
|---|---|---|
| `test_minimal_manifest_parses` | `MINIMAL` | `provider_id` set; `requires == ()`; `effects == ()`; `owns_migrations is False` |
| `test_requires_defaults_fail_closed` | `MINIMAL` + a `[[requires]]` without `on_missing` | `requires[0].on_missing == "fail_closed"` |
| `test_bad_provider_id_rejected` | `id = "Indicator.RSI"` | `KernelError`, match `"provider id must be lowercase dotted"` |
| `test_entry_point_shape_enforced` | `entry_point = "app.x.plugin"` | `KernelError`, match `"entry_point must be module:callable"` |
| `test_empty_provides_rejected` | `MINIMAL` without `[[provides]]` | `KernelError`, match `"at least one capability"` |
| `test_unknown_effect_class_rejected` | `effect_class = "magic"` | `KernelError`, match `"unknown effect class: magic"` |

Run: `uv run pytest tests/unit/test_kernel_manifests.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_manifests.py
uv run ruff check app/kernel tests/unit/test_kernel_manifests.py
uv run mypy .
uv run pytest tests/unit/test_kernel_manifests.py -q
grep -rn "import_module\|__import__" app/kernel/ ; test $? -eq 1
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

The `grep` must find nothing and therefore exit 1, which the `test` converts to success.

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added provider manifest.toml schema and parser using stdlib tomllib.`

**Git Commit:**

```bash
git add app/kernel/manifests.py app/kernel/__init__.py tests/unit/test_kernel_manifests.py docs/CHANGELOG.md
git commit -m "feat(kernel): add provider manifest parser" -m "Parses manifest.toml into a validated frozen ProviderManifest with stdlib
tomllib. entry_point is stored as an inert string so discovery never
executes provider code.
Refs: REFACTOR_PLAN.md R-05, D-07, Gate G4"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No `importlib` or `__import__` anywhere under `app/kernel/`
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T04` — Add provider discovery walker

**Traces to:** `REFACTOR_PLAN.md` Phase 4 ("discover providers without importing implementation code"); resolution `R-05`; Gate `G4`
**Depends on:** `P4-T03`
**Estimated size:** S (<50 LOC)

**Goal.** A filesystem walk finds every `manifest.toml` under a root and returns parsed manifests in deterministic order, executing no provider code.

**Context to Read (and nothing else):**

- Shared Contracts §3.12 — the complete contract
- `app/kernel/manifests.py` — you call `load_manifest`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/discovery.py` | CREATE | Walker |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.12.

**Behaviour Rules (numbered, testable):**

1. `discover_manifests` returns manifests sorted by `provider_id` ascending.
2. A path containing any directory named in `DISCOVERY_SKIP_DIRS` is skipped entirely.
3. A missing `root` returns an empty tuple and does not raise.
4. A malformed manifest propagates `KernelError` unchanged — discovery does not swallow, log-and-continue, or partially return.
5. Two manifests declaring the same `provider_id` are both returned; duplicate detection belongs to the registry (`P4-T05`), not to discovery.
6. No module is imported as a result of discovery.

**Implementation Steps:**

1. Create `app/kernel/discovery.py` with a module docstring and `from __future__ import annotations`.
2. Import `Path`, `Final`; import `ProviderManifest` and `load_manifest` from `app.kernel.manifests`.
3. Add `MANIFEST_FILENAME` and `DISCOVERY_SKIP_DIRS` as `Final`.
4. Implement `discover_manifests`: return `()` immediately when `not root.is_dir()`.
5. Walk with `root.rglob(MANIFEST_FILENAME)`, skipping any path whose `parts` intersect `DISCOVERY_SKIP_DIRS`.
6. Call `load_manifest` on each surviving path.
7. Return `tuple(sorted(manifests, key=lambda m: m.provider_id))`.
8. Give every member a Google docstring including `Raises:` for the propagated `KernelError`.
9. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
10. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not import any discovered module.** No `importlib`, no `__import__`, no `exec`.
- Do not catch `KernelError` to continue past a bad manifest — a malformed manifest is a hard stop.
- Do not deduplicate `provider_id`; that is the registry's job.
- Do not add a cache, a watcher, or a parallel walk.
- Do not add a `pattern` or `recursive` parameter; the signature is exactly `discover_manifests(root: Path)`.
- Do not add logging.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_discovery.py` (CREATE)

Use the pytest `tmp_path` fixture to build the trees. Every manifest body reuses the `MINIMAL` TOML shape from `P4-T03`.

| Test function | Input | Expected |
|---|---|---|
| `test_finds_nested_manifests` | two manifests at different depths | both returned |
| `test_sorted_by_provider_id` | ids `b.two` then `a.one` written in that order | returned `("a.one", "b.two")` |
| `test_skips_pycache` | a manifest under `__pycache__/` | not returned |
| `test_missing_root_is_empty` | `tmp_path / "absent"` | `()` |
| `test_malformed_propagates` | a manifest with `id = "BAD"` | `KernelError` raised |
| `test_no_modules_imported` | `sys.modules` snapshot before and after | no new key starting `app.services` |

Run: `uv run pytest tests/unit/test_kernel_discovery.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_discovery.py
uv run ruff check app/kernel tests/unit/test_kernel_discovery.py
uv run mypy .
uv run pytest tests/unit/test_kernel_discovery.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added provider discovery that reads manifests without importing provider code.`

**Git Commit:**

```bash
git add app/kernel/discovery.py tests/unit/test_kernel_discovery.py docs/CHANGELOG.md
git commit -m "feat(kernel): add provider discovery walker" -m "Finds every manifest.toml under a root and returns parsed manifests sorted
by provider id, importing nothing.
Refs: REFACTOR_PLAN.md Phase 4, R-05, Gate G4"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests written and passing
- [ ] No import machinery anywhere in the module
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T05` — Add capability registry

**Traces to:** `REFACTOR_PLAN.md` Phase 4 ("maintain provider and capability inventories"); decision `D-03`; Gate `G4`
**Depends on:** `P4-T04`
**Estimated size:** M (50–120 LOC)

**Goal.** An inventory maps capabilities to installed providers, rejects duplicate provider ids, and honours the enabled flag that makes config-disable equivalent to deletion.

**Context to Read (and nothing else):**

- Shared Contracts §3.7 — `ProviderRecord` and `CapabilityRegistry`
- `app/kernel/manifests.py` — `ProviderManifest`
- `app/kernel/errors.py` — `KernelError`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/registry.py` | CREATE | Inventory |
| `app/kernel/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.kernel.registry import CapabilityRegistry` and insert `"CapabilityRegistry",` into `__all__`, keeping it sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.7, `ProviderRecord` and `CapabilityRegistry` only.

**Behaviour Rules (numbered, testable):**

1. `register` raises `KernelError` `"duplicate provider id: {id}"` when the id is already present, whether or not the earlier record was enabled.
2. `providers_for(capability_id, version)` returns only records whose manifest declares exactly that `(capability_id, version)` pair **and** whose `enabled` is `True`.
3. Results are ordered by `provider_id` ascending.
4. A disabled provider is retained in the registry and returned by `provider_ids()`, but never by `providers_for`.
5. `provider_ids()` returns every registered id, enabled or not, sorted ascending.
6. Registering a manifest that declares the same capability at two versions makes it discoverable at both.
7. The registry holds no mutable state beyond its own mapping and performs no I/O.

**Implementation Steps:**

1. Create `app/kernel/registry.py` with a module docstring and `from __future__ import annotations`.
2. Import `dataclass`; import `ProviderManifest` from `app.kernel.manifests`; import `KernelError` from `app.kernel.errors`.
3. Add the frozen `ProviderRecord` dataclass with `manifest` and `enabled`.
4. Add `CapabilityRegistry` with a private `_records: dict[str, ProviderRecord]` built in `__init__`.
5. Implement `register` per rule 1.
6. Implement `providers_for` per rules 2, 3, 6.
7. Implement `provider_ids` per rule 5.
8. Give every member a Google docstring including `Raises:`.
9. Update `app/kernel/__init__.py` per the anchor instruction.
10. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
11. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add an `unregister`, `replace`, or `clear` method — provider replacement is Phase 6, Batch 3.
- Do not resolve requirements here; the registry is an inventory, not a resolver.
- Do not import or instantiate any provider from `entry_point`.
- Do not make the registry a module-level singleton or add a global accessor.
- Do not add persistence, caching, or thread locking.
- Do not add logging; the registry is a pure data structure.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_registry.py` (CREATE)

Build `ProviderManifest` instances directly in the test body; do not go through TOML.

| Test function | Input | Expected |
|---|---|---|
| `test_duplicate_id_rejected` | same id twice | `KernelError`, match `"duplicate provider id: a.one"` |
| `test_providers_for_exact_version` | provider at v1; query v2 | `()` |
| `test_disabled_excluded_from_lookup` | `enabled=False` | `providers_for` returns `()` |
| `test_disabled_retained_in_ids` | `enabled=False` | `provider_ids()` contains the id |
| `test_results_sorted` | ids `b.two`, `a.one` | `("a.one", "b.two")` order |
| `test_two_versions_of_one_capability` | manifest providing v1 and v2 | found at both |

Run: `uv run pytest tests/unit/test_kernel_registry.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_registry.py
uv run ruff check app/kernel tests/unit/test_kernel_registry.py
uv run mypy .
uv run pytest tests/unit/test_kernel_registry.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added capability registry mapping capabilities to enabled providers.`

**Git Commit:**

```bash
git add app/kernel/registry.py app/kernel/__init__.py tests/unit/test_kernel_registry.py docs/CHANGELOG.md
git commit -m "feat(kernel): add capability registry" -m "Inventories installed providers by capability and version, rejects duplicate
provider ids, and excludes disabled providers from lookup so config-disable
behaves as deletion.
Refs: REFACTOR_PLAN.md Phase 4, D-03, Gate G4"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No `unregister`, no singleton, no global accessor
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T06` — Add dependency resolver

**Traces to:** `REFACTOR_PLAN.md` Phase 4 resolver rules; decisions `D-04`, `D-05`; Gate `G4`
**Depends on:** `P4-T05`
**Estimated size:** L (120–200 LOC)

**Goal.** Requirements resolve to a deterministic activation order, and every unsatisfied requirement produces `Unavailability` evidence carrying the full dependency chain.

**Context to Read (and nothing else):**

- Shared Contracts §3.7 — `ResolutionEntry`, `ResolutionReport`, `resolve`, and the eight frozen resolver rules
- Shared Contracts §3.3 — `Requirement`, `satisfies`
- `app/kernel/errors.py`, `app/kernel/registry.py`
- Planner Observation §9.5 — the asymmetric cycle policy, which is easy to mis-implement

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/resolver.py` | CREATE | Resolution |
| `app/kernel/__init__.py` | MODIFY | Add two exports |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.kernel.resolver import ResolutionReport, resolve` and insert `"ResolutionReport",` and `"resolve",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.7, `ResolutionEntry`, `ResolutionReport` and `resolve`, together with resolver rules 1–8 stated there.

**Behaviour Rules (numbered, testable):** rules 1–8 of Shared Contracts §3.7 are the behaviour rules for this task, plus:

9. Every entry whose state is not `"ACTIVE"` or `"DEGRADED"` carries a non-`None` `unavailability`.
10. `resolved_requires` lists `(capability_qualified_id, provider_id)` pairs for every satisfied requirement, sorted by capability id.
11. `ResolutionReport.is_active(provider_id)` returns `True` only for `"ACTIVE"`; a `DEGRADED` provider is running, so a separate `is_running` is **not** added — callers test the entry state directly.
12. The function logs one `INFO` line on completion — `"resolved %d providers, %d active"` — and one `WARNING` per unavailability. No other logging.

**Implementation Steps:**

1. Create `app/kernel/resolver.py` with a module docstring and `from __future__ import annotations`.
2. Import `get_logger` from `app.utils`; create `logger = get_logger(__name__)`.
3. Import `CapabilitySpec`, `Requirement`, `qualified_id`, `satisfies` from `app.capabilities`; `KernelError`, `ReasonCode`, `Unavailability` from `app.kernel.errors`; `CapabilityRegistry` from `app.kernel.registry`.
4. Add the frozen `ResolutionEntry` and `ResolutionReport` dataclasses.
5. Add a private `_candidates(registry, specs, requirement)` returning matching enabled providers and the cardinality verdict per rules 3–5.
6. Add a private `_required_edges(registry)` yielding only edges whose `on_missing == "fail_closed"`.
7. Add a private `_detect_cycle(edges)` raising `KernelError` `"dependency cycle: {a} -> {b} -> ... -> {a}"` per rule 2.
8. Implement the topological pass, processing providers in `provider_id` order for determinism per rule 8.
9. Apply the `on_missing` behaviour of rule 7, building `Unavailability` with the chain of rule 6.
10. Emit the rule 12 log lines.
11. Update `app/kernel/__init__.py`; add the CHANGELOG bullet.
12. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not forbid all cycles.** Cycles through a `degrade` or `skip` edge are legal and are broken at that edge; only `fail_closed` cycles raise. This is the single most likely rule to get wrong.
- Do not raise for an unsatisfied requirement — that is an `Unavailability` in the report.
- Do not import or call any provider `entry_point`; resolution is static.
- Do not activate anything; activation is Phase 5, deactivation is `P5-T04`.
- Do not use import order, filesystem order, or dict insertion order for provider selection — rule 8 requires `provider_id` ascending.
- Do not add a `force` or `ignore_missing` parameter.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_resolver.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_linear_chain_order` | `c` requires `b` requires `a` | `activation_order == ("a.p", "b.p", "c.p")` |
| `test_missing_required_is_not_installed` | requirement with no provider | entry inactive, `reason_code == NOT_INSTALLED` |
| `test_out_of_window_is_version_incompatible` | provider v2, requirement window (1,1) | `reason_code == VERSION_INCOMPATIBLE` |
| `test_dependency_chain_propagates` | `c` → `b` → missing `a` | `c`'s chain is `("c.p", "b.p", "a")`, `reason_code == DEPENDENCY_UNAVAILABLE` |
| `test_skip_keeps_provider_active` | unsatisfied requirement with `on_missing="skip"` | entry state `"ACTIVE"` |
| `test_fail_closed_cycle_raises` | `a` and `b` require each other, both `fail_closed` | `KernelError`, match `"dependency cycle"` |

Run: `uv run pytest tests/unit/test_kernel_resolver.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_resolver.py
uv run ruff check app/kernel tests/unit/test_kernel_resolver.py
uv run mypy .
uv run pytest tests/unit/test_kernel_resolver.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added dependency resolver producing deterministic activation order and unavailability evidence.`

**Git Commit:**

```bash
git add app/kernel/resolver.py app/kernel/__init__.py tests/unit/test_kernel_resolver.py docs/CHANGELOG.md
git commit -m "feat(kernel): add dependency resolver" -m "Topologically orders providers by fail-closed edges, permits cycles only
through optional edges, and reports every unsatisfied requirement as
structured evidence carrying the dependency chain.
Refs: REFACTOR_PLAN.md D-04, D-05, Gate G4"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] Optional-edge cycles resolve; fail-closed cycles raise
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P4-T07` — Add profile readiness evaluator

**Traces to:** `REFACTOR_PLAN.md` §1.5 profile readiness; Phase 7 `PROFILE_REQUIREMENT_UNSATISFIED`; Gate `G4`
**Depends on:** `P4-T06`
**Estimated size:** M (50–120 LOC)

**Goal.** A profile reports ready or unready against a supplied policy table, so live and demo fail closed without inventing any capability identifier inside the kernel.

**Context to Read (and nothing else):**

- Shared Contracts §3.13 — the complete contract and the reason the policy table is a parameter
- `app/kernel/resolver.py` — `ResolutionReport`
- `app/runtime.py` — the existing `validate_runtime_configuration(runtime_profile, execution_route)`; read it to match the four profile names, **do not modify it**

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/profiles.py` | CREATE | Readiness |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Specification (the contract — copy exactly):** as Shared Contracts §3.13.

**Behaviour Rules (numbered, testable):**

1. `Profile` has exactly four members whose values are `"research"`, `"simulation"`, `"demo"`, `"live"`, matching the keys of `_EXECUTION_ROUTE_BY_PROFILE` in `app/runtime.py`.
2. A profile absent from `required` is treated as requiring nothing and evaluates ready.
3. `ready` is `True` only when every qualified capability id in `required[profile]` has an active provider in `report`.
4. Each unsatisfied entry yields an `Unavailability` with `reason_code=PROFILE_REQUIREMENT_UNSATISFIED`, `capability` set to the qualified id, `consumer=None`, `retryable=False`.
5. When the resolver already recorded an unavailability for that capability, its `dependency_chain` is copied; otherwise the chain is `(qualified_id,)`.
6. `missing` is sorted by `capability` ascending.
7. A `DEGRADED` provider does **not** satisfy a profile requirement — degraded is not ready.
8. One `WARNING` is logged per unready profile: `"profile %s unready, %d requirements unsatisfied"`. Nothing is logged when ready.

**Implementation Steps:**

1. Create `app/kernel/profiles.py` with a module docstring and `from __future__ import annotations`.
2. Import `StrEnum`, `dataclass`, `Mapping`; import `get_logger` from `app.utils`; import `Unavailability` and `ReasonCode` from `app.kernel.errors`; import `ResolutionReport` from `app.kernel.resolver`; import `CapabilityRegistry` from `app.kernel.registry`.
3. Add `Profile` per rule 1.
4. Add the frozen `ReadinessReport` dataclass.
5. Implement `evaluate_readiness` per rules 2–7.
6. Emit the rule 8 log line.
7. Give every member a Google docstring.
8. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
9. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not hardcode a capability list for any profile.** `required` is a parameter supplied by the composition root in Batch 3. Inventing `risk.kill_switch.v1` or any other identifier here would violate `D-01` and would invent an artefact that does not exist.
- Do not modify `app/runtime.py` or call `validate_runtime_configuration`; wiring the two is Phase 7, Batch 3.
- Do not treat `DEGRADED` as ready.
- Do not add a `strict` or `allow_degraded` flag.
- Do not raise when a profile is unready; unreadiness is a returned report.
- Do not add a fifth profile.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `app/runtime.py`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_profiles.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_four_profiles` | `list(Profile)` | length 4, values match `app/runtime.py` keys |
| `test_unlisted_profile_is_ready` | empty `required` | `ready is True`, `missing == ()` |
| `test_missing_capability_makes_unready` | one required id, no provider | `ready is False`, one `PROFILE_REQUIREMENT_UNSATISFIED` |
| `test_degraded_does_not_satisfy` | provider resolved `DEGRADED` | `ready is False` |
| `test_chain_copied_from_resolver` | resolver recorded a chain | `missing[0].dependency_chain` equals it |
| `test_missing_sorted_by_capability` | two unsatisfied ids out of order | sorted ascending |

Run: `uv run pytest tests/unit/test_kernel_profiles.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_profiles.py
uv run ruff check app/kernel tests/unit/test_kernel_profiles.py
uv run mypy .
uv run pytest tests/unit/test_kernel_profiles.py tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added runtime profile readiness evaluation against a supplied capability policy table.`

**Git Commit:**

```bash
git add app/kernel/profiles.py tests/unit/test_kernel_profiles.py docs/CHANGELOG.md
git commit -m "feat(kernel): add profile readiness evaluator" -m "Evaluates research, simulation, demo and live readiness against a policy
table supplied by the caller, keeping capability policy out of the kernel.
Degraded providers do not satisfy a requirement.
Refs: REFACTOR_PLAN.md section 1.5, Gate G4"
```

**Re-run safety:** `Safe — CREATE-only apart from one CHANGELOG line`

**Definition of Done:**

- [ ] Two files created, one modified, no others
- [ ] All six tests written and passing
- [ ] No capability identifier hardcoded anywhere in the module
- [ ] `app/runtime.py` untouched
- [ ] Exactly one commit with the message above

---

### Phase 5 — Lifecycle and effect ownership

**Goal.** Removing a component releases every reversible resource it created, in reverse order, and refuses to dispose while an irreversible effect is in flight.
**Why now.** Gate `G4` passed. This is the temporal half of the model; Phase 6 composition depends on it.
**Deliverable.** `app/kernel/` gains `states.py`, `scope.py` and `lifecycle.py`.

**Phase 5 Exit Gate — all must be true before Phase 6 starts:**

- [ ] Every task in this phase is checked off
- [ ] `uv run ruff check .` and `uv run mypy .` clean across the repo
- [ ] `uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80` green
- [ ] No test failing that was not already recorded in `docs/dev/plugin-decoupling/BASELINE.md`
- [ ] No PROTECTED path appears in `git diff --name-only <phase-start>..HEAD`
- [ ] Functional proof: a test component registering a timer, a listener and a mock client returns **zero** live resources after `deactivate()`, and the disposal order is the exact reverse of registration
- [ ] `grep -rn "async def" app/kernel/ app/capabilities/` finds nothing
- [ ] Full suite emits no new `ResourceWarning` or `RuntimeWarning` versus the `P0-T01` baseline

---

#### - [ ] Task `P5-T01` — Add component state machine

**Traces to:** `REFACTOR_PLAN.md` Phase 5 component states; Gate `G5`
**Depends on:** `P4-T07`
**Estimated size:** M (50–120 LOC)

**Goal.** The fourteen component states and their legal transitions exist as data, so no later module encodes a transition rule inline.

**Context to Read (and nothing else):**

- Shared Contracts §3.8 — the enum, `TERMINAL_STATES`, `assert_transition`
- `app/kernel/errors.py` — `KernelError`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/states.py` | CREATE | States and transitions |
| `app/kernel/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.kernel.states import ComponentState` and insert `"ComponentState",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.8, with `LEGAL_TRANSITIONS` given in full here:

```python
LEGAL_TRANSITIONS: Final[Mapping[ComponentState, frozenset[ComponentState]]] = {
    ComponentState.DISCOVERED: frozenset({S.DISABLED, S.RESOLVING, S.QUARANTINED}),
    ComponentState.DISABLED: frozenset({S.DISCOVERED}),
    ComponentState.RESOLVING: frozenset(
        {S.WAITING_FOR_DEPENDENCY, S.STARTING, S.FAILED, S.VERSION_INCOMPATIBLE}
    ),
    ComponentState.WAITING_FOR_DEPENDENCY: frozenset({S.RESOLVING, S.STOPPED}),
    ComponentState.STARTING: frozenset({S.ACTIVE, S.DEGRADED, S.FAILED}),
    ComponentState.ACTIVE: frozenset({S.DEGRADED, S.DRAINING, S.FAILED}),
    ComponentState.DEGRADED: frozenset({S.ACTIVE, S.DRAINING, S.FAILED}),
    ComponentState.DRAINING: frozenset({S.STOPPING, S.ACTIVE}),
    ComponentState.STOPPING: frozenset({S.STOPPED, S.FAILED_CLEANUP}),
    ComponentState.STOPPED: frozenset({S.DISCOVERED}),
    ComponentState.FAILED: frozenset({S.DISCOVERED}),
    ComponentState.FAILED_CLEANUP: frozenset({S.QUARANTINED}),
    ComponentState.QUARANTINED: frozenset(),
    ComponentState.VERSION_INCOMPATIBLE: frozenset({S.DISCOVERED}),
}
```

`S` is a module-local alias for `ComponentState` used only in this literal.

**Behaviour Rules (numbered, testable):**

1. `ComponentState` has exactly fourteen members whose values equal their names.
2. `LEGAL_TRANSITIONS` has one key per member; no member is absent.
3. `assert_transition(current, target)` raises `KernelError` `"illegal transition: {current} -> {target}"` when `target not in LEGAL_TRANSITIONS[current]`, and returns `None` otherwise.
4. `assert_transition(s, s)` raises for every state — a self-transition is never legal.
5. `QUARANTINED` has no legal successor; every transition out of it raises.
6. `DRAINING → ACTIVE` is legal: a refused quiesce returns the component to service.
7. `TERMINAL_STATES` contains exactly `STOPPED`, `FAILED`, `FAILED_CLEANUP`, `QUARANTINED`, `VERSION_INCOMPATIBLE`.

**Implementation Steps:**

1. Create `app/kernel/states.py` with a module docstring and `from __future__ import annotations`.
2. Import `StrEnum`, `Mapping`, `Final`; import `KernelError` from `app.kernel.errors`.
3. Add `ComponentState` with the fourteen members from §3.8, in that order.
4. Add the module-local alias `S = ComponentState` immediately before the transition table.
5. Add `LEGAL_TRANSITIONS` exactly as given above.
6. Add `TERMINAL_STATES` per rule 7.
7. Implement `assert_transition` per rules 3–5.
8. Give every member a Google docstring including `Raises:`.
9. Update `app/kernel/__init__.py`; add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not add a fifteenth state, rename one, or reorder the enum.
- Do not add an edge that is not in the table above — in particular, `ACTIVE → STOPPED` is illegal; a component must pass through `DRAINING` and `STOPPING`.
- Do not make `assert_transition` return a boolean; it raises or returns `None`.
- Do not add a state-machine class, a transition callback, or an observer hook.
- Do not add logging here; the transition is logged by `Component.transition` in `P5-T03`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_states.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_fourteen_states` | `list(ComponentState)` | length 14; every `.value == .name` |
| `test_every_state_has_a_row` | `LEGAL_TRANSITIONS.keys()` | equals `set(ComponentState)` |
| `test_self_transition_always_illegal` | every state to itself | `KernelError` each time |
| `test_active_to_stopped_illegal` | `ACTIVE → STOPPED` | `KernelError`, match `"illegal transition"` |
| `test_draining_back_to_active_legal` | `DRAINING → ACTIVE` | returns `None` |
| `test_quarantined_is_terminal` | `QUARANTINED` to every state | `KernelError` each time |

Run: `uv run pytest tests/unit/test_kernel_states.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_states.py
uv run ruff check app/kernel tests/unit/test_kernel_states.py
uv run mypy .
uv run pytest tests/unit/test_kernel_states.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added component state machine with fourteen states and an explicit transition table.`

**Git Commit:**

```bash
git add app/kernel/states.py app/kernel/__init__.py tests/unit/test_kernel_states.py docs/CHANGELOG.md
git commit -m "feat(kernel): add component state machine" -m "Fourteen component states with an explicit legal-transition table. A
component cannot reach STOPPED without passing through DRAINING and
STOPPING; a refused quiesce returns it to ACTIVE.
Refs: REFACTOR_PLAN.md Phase 5, Gate G5"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] Transition table matches the specification exactly
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P5-T02` — Add synchronous effect scope

**Traces to:** `REFACTOR_PLAN.md` Phase 5 activation scope; decisions `D-06`, `D-07`; resolution `R-02`; conflict `CF-03`; Gate `G5`
**Depends on:** `P5-T01`
**Estimated size:** M (50–120 LOC)

**Goal.** A component's resources are owned by one scope that unwinds them in reverse registration order, never disposes an irreversible effect, and never places a compensating action.

**Context to Read (and nothing else):**

- Shared Contracts §3.9 — the complete contract and the six frozen scope rules
- Conflict `CF-03` in §7 — why this is `ExitStack` and not `AsyncExitStack`
- `app/kernel/manifests.py` — `EFFECT_CLASSES`
- `app/kernel/errors.py` — `KernelError`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/scope.py` | CREATE | Effect ownership |
| `app/kernel/__init__.py` | MODIFY | Add two exports |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.kernel.scope import Effect, EffectScope` and insert `"Effect",` and `"EffectScope",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.9, including scope rules 1–6.

**Behaviour Rules (numbered, testable):** rules 1–6 of Shared Contracts §3.9 are the behaviour rules, plus:

7. `Effect.__post_init__` raises `ValueError` `"unknown effect class: {effect_class}"` when the class is not in `EFFECT_CLASSES`.
8. `effect_names()` returns names in registration order, including irreversible ones.
9. `dispose()` logs one `WARNING` per failing disposer: `"effect %s failed to dispose for %s"`. Successful disposal logs nothing.
10. `has_irreversible()` is `True` when any registered effect has class `irreversible_external`, regardless of disposal state.

**Implementation Steps:**

1. Create `app/kernel/scope.py` with a module docstring and `from __future__ import annotations`.
2. Import `dataclass`, `Callable`; import `get_logger` from `app.utils`; import `EFFECT_CLASSES` from `app.kernel.manifests`; import `KernelError` from `app.kernel.errors`.
3. Add the frozen `Effect` dataclass with `__post_init__` per rule 7.
4. Add `EffectScope.__init__` storing `owner_id`, an ordered `list[Effect]`, and a `_disposed` flag.
5. Implement `register` per scope rules 1 and 5.
6. Implement `effect_names` and `has_irreversible` per rules 8 and 10.
7. Implement `dispose`: return `()` immediately when already disposed; otherwise iterate `reversed(self._effects)`.
8. Skip any effect whose class is `irreversible_external` without calling its disposer.
9. Wrap each call in `try` / `except Exception`, collect the failing name, log per rule 9, and continue.
10. Set `_disposed = True` and return the failures tuple.
11. Update `app/kernel/__init__.py`; add the CHANGELOG bullet.
12. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not use `AsyncExitStack`, `async def`, `await`, or `asyncio`.** `R-02` and `CF-03` make this synchronous; §5 makes async a repo-wide forbidden change.
- **Do not dispose an `irreversible_external` effect, and never invoke a compensating action.** A filled order is recorded and reported, never reversed by the lifecycle.
- Do not stop the sweep when a disposer raises; every remaining effect must still be attempted.
- Do not use a bare `except:`; ruff `BLE` and `AGENTS.md` §2 forbid it. Catch `Exception`.
- Do not re-raise a disposal failure; failures are returned as names.
- Do not add a `force`, `timeout`, or `parallel` parameter to `dispose`.
- Do not add a context-manager protocol (`__enter__` / `__exit__`) to `EffectScope`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_scope.py` (CREATE)

Use a module-level `calls: list[str]` in each test to record disposal order.

| Test function | Input | Expected |
|---|---|---|
| `test_disposes_in_reverse_order` | effects `a`, `b`, `c` | `calls == ["c", "b", "a"]` |
| `test_duplicate_effect_rejected` | same name twice | `KernelError`, match `"duplicate effect: a"` |
| `test_dispose_is_idempotent` | `dispose()` twice | second returns `()`, `calls` length unchanged |
| `test_failing_disposer_does_not_stop_sweep` | middle effect raises | all three attempted, returns `("b",)` |
| `test_irreversible_never_disposed` | one `irreversible_external` effect | its disposer is never called; `has_irreversible() is True` |
| `test_register_after_dispose_raises` | register post-dispose | `KernelError`, match `"scope already disposed"` |

Run: `uv run pytest tests/unit/test_kernel_scope.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_scope.py
uv run ruff check app/kernel tests/unit/test_kernel_scope.py
uv run mypy .
uv run pytest tests/unit/test_kernel_scope.py -q
grep -rn "async def\|await \|asyncio" app/kernel/ ; test $? -eq 1
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added synchronous effect scope disposing reversible resources in reverse order.`

**Git Commit:**

```bash
git add app/kernel/scope.py app/kernel/__init__.py tests/unit/test_kernel_scope.py docs/CHANGELOG.md
git commit -m "feat(kernel): add synchronous effect scope" -m "Owns a component generation's resources and unwinds them in reverse
registration order. Irreversible effects are recorded and reported, never
disposed and never compensated.
Refs: REFACTOR_PLAN.md D-06, D-07, R-02, CF-03, Gate G5"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No async construct anywhere under `app/kernel/`
- [ ] No compensating action on any path
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P5-T03` — Add component quiesce verdict

**Traces to:** `REFACTOR_PLAN.md` decision `D-08` quiesce protocol; Gate `G5`
**Depends on:** `P5-T02`
**Estimated size:** M (50–120 LOC)

**Goal.** A component tracks its state and answers whether it may be disposed, so a refused teardown is a structured verdict rather than a forced unwind.

**Context to Read (and nothing else):**

- Shared Contracts §3.10 — `QuiesceVerdict` and `Component`
- `app/kernel/states.py` — `ComponentState`, `assert_transition`
- `app/kernel/scope.py` — `EffectScope`

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/lifecycle.py` | CREATE | `QuiesceVerdict`, `Component` |
| `app/kernel/__init__.py` | MODIFY | Add one export |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Add `from app.kernel.lifecycle import Component` and insert `"Component",` into `__all__`, sorted ascending.

**Specification (the contract — copy exactly):** as Shared Contracts §3.10, `QuiesceVerdict` and `Component` **without** `deactivate`, which is `P5-T04`.

**Behaviour Rules (numbered, testable):**

1. A new `Component` starts in `ComponentState.DISCOVERED`.
2. `transition(target)` calls `assert_transition` first, so an illegal move raises `KernelError` and leaves the state unchanged.
3. `transition` logs one `INFO` line per successful move: `"component %s %s -> %s"`.
4. `can_dispose()` returns `QuiesceVerdict(can_dispose=False, reason="irreversible effects in flight")` when `scope.has_irreversible()` is `True`.
5. It returns `QuiesceVerdict(can_dispose=False, reason="component not draining")` when the state is not `DRAINING`.
6. It returns `QuiesceVerdict(can_dispose=True, reason=None)` otherwise.
7. Rule 5 is checked before rule 4, so a component that is not draining reports that first.
8. `can_dispose()` performs no state change and no disposal.

**Implementation Steps:**

1. Create `app/kernel/lifecycle.py` with a module docstring and `from __future__ import annotations`.
2. Import `dataclass`; import `get_logger` from `app.utils`; import `ComponentState` and `assert_transition` from `app.kernel.states`; import `EffectScope` from `app.kernel.scope`; import `ProviderManifest` from `app.kernel.manifests`.
3. Add the frozen `QuiesceVerdict` dataclass with `can_dispose` and `reason`.
4. Add `Component.__init__` storing `manifest`, `scope` and `_state = ComponentState.DISCOVERED`.
5. Add the read-only `state` property.
6. Implement `transition` per rules 2 and 3.
7. Implement `can_dispose` per rules 4–8, checking the draining condition first.
8. Give every member a Google docstring including `Raises:`.
9. Update `app/kernel/__init__.py`; add the CHANGELOG bullet.
10. Commit.

**DO NOT (anti-invention guardrails):**

- Do not implement `deactivate` — that is `P5-T04`.
- Do not let `can_dispose` mutate state, dispose anything, or log.
- Do not add a `force_dispose` or `ignore_irreversible` path anywhere.
- Do not make `state` settable; the only way to change it is `transition`.
- Do not import or call the manifest's `entry_point`.
- Do not add `async def`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_lifecycle.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_starts_discovered` | new `Component` | `state is ComponentState.DISCOVERED` |
| `test_illegal_transition_leaves_state` | `DISCOVERED → ACTIVE` | `KernelError`; state still `DISCOVERED` |
| `test_not_draining_refuses` | `ACTIVE` component | `can_dispose is False`, reason `"component not draining"` |
| `test_irreversible_refuses_while_draining` | draining, one irreversible effect | `can_dispose is False`, reason `"irreversible effects in flight"` |
| `test_clean_draining_allows` | draining, only reversible effects | `can_dispose is True`, `reason is None` |
| `test_can_dispose_does_not_mutate` | call twice | state unchanged, no effect disposed |

Run: `uv run pytest tests/unit/test_kernel_lifecycle.py -q` → all pass, 0 skipped.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_lifecycle.py
uv run ruff check app/kernel tests/unit/test_kernel_lifecycle.py
uv run mypy .
uv run pytest tests/unit/test_kernel_lifecycle.py -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added component quiesce verdict refusing disposal while irreversible effects are in flight.`

**Git Commit:**

```bash
git add app/kernel/lifecycle.py app/kernel/__init__.py tests/unit/test_kernel_lifecycle.py docs/CHANGELOG.md
git commit -m "feat(kernel): add component quiesce verdict" -m "Components track state through the transition table and report whether they
may be disposed. A component holding an irreversible effect refuses
teardown rather than being forced.
Refs: REFACTOR_PLAN.md D-08, Gate G5"
```

**Re-run safety:** `Safe — one anchored insertion, rest CREATE-only`

**Definition of Done:**

- [ ] Four files created/modified, no others
- [ ] All six tests written and passing
- [ ] No force-dispose path exists
- [ ] `ruff`, `mypy .`, full coverage gate clean
- [ ] Exactly one commit with the message above

---

#### - [ ] Task `P5-T04` — Add component deactivation sequence

**Traces to:** `REFACTOR_PLAN.md` Phase 5 deactivation sequence; decision `D-08`; Gate `G5`
**Depends on:** `P5-T03`
**Estimated size:** M (50–120 LOC)

**Goal.** `deactivate()` walks quiesce, drain, dispose in order, lands the component in `STOPPED` or `FAILED_CLEANUP`, and leaves it in `DRAINING` when quiesce refuses.

**Context to Read (and nothing else):**

- Shared Contracts §3.10 — the `deactivate` ordering paragraph
- `app/kernel/lifecycle.py` — created by `P5-T03`; you add one method
- `app/kernel/states.py` — the transition table

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/lifecycle.py` | MODIFY | Add `deactivate` |
| `docs/CHANGELOG.md` | MODIFY | One bullet |

**Anchor text (MODIFY).** Insert `deactivate` as the last method of `Component`, immediately after `can_dispose`. `can_dispose` and every other existing member must remain byte-identical.

**Specification (the contract — copy exactly):**

```python
    def deactivate(self) -> tuple[str, ...]:
        """Drain and dispose this component, honouring a quiesce refusal.

        Returns:
            The names of effects whose disposers failed, empty on clean
            teardown. A refused quiesce also returns an empty tuple and
            leaves the component in DRAINING.

        Raises:
            KernelError: If the component's current state cannot transition
                to DRAINING.
        """
```

**Behaviour Rules (numbered, testable):**

1. `deactivate` first transitions to `DRAINING`; from `ACTIVE` or `DEGRADED` this is legal, from anything else `assert_transition` raises.
2. A component already in `DRAINING` is not re-transitioned and proceeds directly to the quiesce check.
3. When `can_dispose().can_dispose` is `False`, the method logs one `WARNING` — `"component %s refused disposal: %s"` — returns `()`, and leaves the state `DRAINING`. Nothing is disposed.
4. Otherwise it transitions to `STOPPING`, then calls `scope.dispose()`.
5. Empty failures → transition to `STOPPED` and return `()`.
6. Non-empty failures → transition to `FAILED_CLEANUP` and return the failure names.
7. `deactivate` on an already-`STOPPED` component raises `KernelError` from `assert_transition`; it is not silently idempotent.
8. Dependents are **not** deactivated by this method; reverse-order dependent teardown belongs to the composition root in Phase 6.

**Implementation Steps:**

1. Open `app/kernel/lifecycle.py` and locate the end of `can_dispose`.
2. Add `deactivate` with the exact signature and docstring above.
3. Implement rule 1, skipping the transition when already `DRAINING` per rule 2.
4. Call `self.can_dispose()`; implement rule 3 on refusal.
5. Implement rules 4–6.
6. Add the Documentation Updates bullet to `docs/CHANGELOG.md`.
7. Commit.

**DO NOT (anti-invention guardrails):**

- **Do not deactivate dependents.** Reverse-order dependent teardown is Phase 6, Batch 3. A component knows only itself.
- Do not make `deactivate` idempotent by swallowing the illegal transition — rule 7 requires it to raise.
- Do not add a `force` parameter or any path that disposes past a refusal.
- Do not place, cancel, or compensate any external action.
- Do not add a timeout, retry, or `async def`.
- Do not modify `can_dispose`, `transition`, `state`, or `QuiesceVerdict`.
- Do not modify any PROTECTED path: `app/services/`, `app/agentic/`, `app/utils/`, `pyproject.toml`.

**Unit Tests**

File: `tests/unit/test_kernel_lifecycle.py` (MODIFY — append; do not alter the six `P5-T03` tests)

| Test function | Input | Expected |
|---|---|---|
| `test_clean_deactivate_reaches_stopped` | `ACTIVE`, two reversible effects | returns `()`; state `STOPPED`; both disposed in reverse |
| `test_refusal_leaves_draining` | `ACTIVE`, one irreversible effect | returns `()`; state `DRAINING`; nothing disposed |
| `test_failed_disposer_reaches_failed_cleanup` | disposer raises | returns `("b",)`; state `FAILED_CLEANUP` |
| `test_deactivate_from_stopped_raises` | already `STOPPED` | `KernelError`, match `"illegal transition"` |
| `test_from_degraded_is_legal` | `DEGRADED` component | reaches `STOPPED` |
| `test_does_not_touch_dependents` | component with a mock dependent | the dependent's state is unchanged |

Run: `uv run pytest tests/unit/test_kernel_lifecycle.py -q` → all ten pass, 0 skipped.

**Regression Tests**

The six `P5-T03` tests in the same file must still pass unchanged:
`uv run pytest tests/unit/test_kernel_lifecycle.py -q` → 10 passed, same six names present.

**Usage Example**

None — non-feature infrastructure per `P1-T04`.

**Quality Gates (run in order, all must pass):**

```bash
uv run ruff format app/kernel tests/unit/test_kernel_lifecycle.py
uv run ruff check app/kernel tests/unit/test_kernel_lifecycle.py
uv run mypy .
uv run pytest tests/unit/test_kernel_lifecycle.py -q
uv run pytest tests/architecture -q
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

**Documentation Updates:**

- `docs/CHANGELOG.md` — under `## [Unreleased]` → `### Added`, exactly:
  `- Added component deactivation walking quiesce, drain and dispose in order.`

**Git Commit:**

```bash
git add app/kernel/lifecycle.py tests/unit/test_kernel_lifecycle.py docs/CHANGELOG.md
git commit -m "feat(kernel): add component deactivation sequence" -m "Walks DRAINING, quiesce check, STOPPING and disposal, landing in STOPPED or
FAILED_CLEANUP. A refused quiesce leaves the component draining rather than
forcing teardown.
Refs: REFACTOR_PLAN.md Phase 5, D-08, Gate G5"
```

**Re-run safety:** `Safe — one anchored method insertion; git revert + re-run is clean`

**Definition of Done:**

- [ ] Two files modified, no others
- [ ] Four new tests added; the six existing tests still pass unchanged
- [ ] No dependent is touched by `deactivate`
- [ ] No force path, no compensating action
- [ ] Exactly one commit with the message above

---

---

## 12. TRACEABILITY MAP

| Source identifier | Source location | Task IDs | Status |
|---|---|---|---|
| Phase 3 — capability specification layer | `REFACTOR_PLAN.md` Part I | `P3-T01` … `P3-T05` | PLANNED |
| Gate `G3` | `REFACTOR_PLAN.md` §1.2 | `P3-T01` … `P3-T05` | PLANNED |
| `D-02` Capability naming + version | `REFACTOR_PLAN.md` §1.2 | `P3-T02` | PLANNED |
| `D-03` Cardinality | `REFACTOR_PLAN.md` §1.2 | `P3-T02` | PLANNED |
| `D-04` `on_missing` policy | `REFACTOR_PLAN.md` §1.2 | `P3-T02` (vocabulary), `P4-T06` (behaviour) | PARTIAL |
| `R-01` Contract shape | `REFACTOR_PLAN.md` §1.2.1 | `P3-T02`, `P3-T03`, `P3-T04` | PLANNED |
| `R-04` Spec layout | `REFACTOR_PLAN.md` §1.2.1 | `P3-T01`, `P3-T04` | PLANNED |
| `R-03` Non-feature infrastructure | `REFACTOR_PLAN.md` §1.2.1 | `P3-T01` | PLANNED |
| Phase 4 — protected microkernel | `REFACTOR_PLAN.md` Part I | `P4-T01` … `P4-T07` | PLANNED |
| `D-01` Kernel membership | `REFACTOR_PLAN.md` §1.2 | `P4-T01` | PLANNED |
| `D-05` Resolution timing | `REFACTOR_PLAN.md` §1.2 | `P4-T06` | PLANNED |
| `D-06` Error model | `REFACTOR_PLAN.md` §1.2 | `P4-T02` | PLANNED |
| `R-05` Manifest format | `REFACTOR_PLAN.md` §1.2.1 | `P4-T03`, `P4-T04` | PLANNED |
| Gate `G4` | `REFACTOR_PLAN.md` §1.2 | `P4-T01` … `P4-T07` | PLANNED |
| Phase 5 — lifecycle and effect ownership | `REFACTOR_PLAN.md` Part I | `P5-T01` … `P5-T04` | PLANNED |
| `D-07` Effect classes | `REFACTOR_PLAN.md` §1.2 | `P4-T03` (declaration), `P5-T02` (behaviour) | PLANNED |
| `D-08` Quiesce protocol | `REFACTOR_PLAN.md` §1.2 | `P5-T04` | PLANNED |
| `R-02` Concurrency model | `REFACTOR_PLAN.md` §1.2.1 | `P5-T02` … `P5-T04`; §5 repo-wide ban | PLANNED |
| Gate `G5` | `REFACTOR_PLAN.md` §1.2 | `P5-T01` … `P5-T04` | PLANNED |
| `R-06` Composition root | `REFACTOR_PLAN.md` §1.2.1 | none | OUT OF SCOPE — Batch 3, Phase 6 |
| `R-07` Approval granularity | `REFACTOR_PLAN.md` §1.2.1 | process rule, all phases | APPLIED |
| Phases 6–17, Gates `G6`–`G11` | `REFACTOR_PLAN.md` Parts I–VI | none | OUT OF SCOPE (§5) |

---

## 13. COMMIT SEQUENCE

| Order | Task ID | Commit message |
|---|---|---|
| 10 | `P3-T01` | `feat(capabilities): add capability specification package` |
| 11 | `P3-T02` | `feat(capabilities): add specification primitives` |
| 12 | `P3-T03` | `feat(capabilities): add contract conformance checker` |
| 13 | `P3-T04` | `feat(capabilities): add indicator.rsi.v1 specification` |
| 14 | `P3-T05` | `test(architecture): enforce capability import boundaries` |
| 15 | `P4-T01` | `feat(kernel): add protected microkernel package` |
| 16 | `P4-T02` | `feat(kernel): add capability unavailability reason codes` |
| 17 | `P4-T03` | `feat(kernel): add provider manifest parser` |
| 18 | `P4-T04` | `feat(kernel): add provider discovery walker` |
| 19 | `P4-T05` | `feat(kernel): add capability registry` |
| 20 | `P4-T06` | `feat(kernel): add dependency resolver` |
| 21 | `P4-T07` | `feat(kernel): add profile readiness evaluator` |
| 22 | `P5-T01` | `feat(kernel): add component state machine` |
| 23 | `P5-T02` | `feat(kernel): add synchronous effect scope` |
| 24 | `P5-T03` | `feat(kernel): add component quiesce verdict` |
| 25 | `P5-T04` | `feat(kernel): add component deactivation sequence` |

Continues from order 9 (`P2-T03`) in Batch 1 §13.

---

## 14. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation | Mitigating task |
|---|---|---|---|---|
| `app/capabilities/` acquires a domain import and silently loses "importable with zero providers" | High | High | Architecture test fails the build on any forbidden prefix, counting `TYPE_CHECKING` imports; plus a runtime `sys.modules` assertion | `P3-T05` |
| Executor treats capability absence as an exception rather than a returned `Unavailability` | High | High | §3.5 states the distinction; §9.2 restates it; every `errors.py` task repeats it in `DO NOT` | `P4-T02` |
| Executor adds `importlib.import_module` to discovery, making discovery execute provider code | Medium | High | `R-05` and §9.3; `DO NOT` in `P4-T04` forbids resolving `entry_point` | `P4-T04` |
| `async def` creeps back in from the pre-`R-02` plan text | Medium | Medium | `CF-03` records the supersession; §5 makes it a repo-wide forbidden change, not a per-task rule | `P5-T02` |
| New kernel code drops global coverage below 80% and reddens the whole repo | High | Medium | Every task carries its own tests and runs the full coverage gate, not just its own file | all |
| Version windows drift toward a range-string syntax | Medium | Medium | Explicit inclusive integers frozen in §3.3; `P3-T02` `DO NOT` forbids a parser | `P3-T02` |
| `Any` in `indicator.rsi.v1` is prematurely narrowed to a private Indicators type | Medium | Medium | `P3-T04` `DO NOT` forbids it and names Batch 4 as the place it tightens | `P3-T04` |
| Cycle rule mis-implemented as "all cycles forbidden", blocking legitimate optional edges | Medium | High | §3.7 rule 2 states the asymmetry explicitly; §9.5 flags it as a known trap | `P4-T06` |

---

## SELF-VERIFICATION REPORT

Checks 1–16: **PASS with notes**

1. **PASS** — all sixteen tasks carry every mandatory field. `Regression Tests` omitted throughout: every task is CREATE-only against greenfield paths and changes no existing behaviour. `Logging` omitted throughout Phase 3 per `CF-04` — `app/capabilities/` is pure and logs nothing; it returns in Phase 4 where the kernel logs state transitions. `Rollback` omitted throughout: no task touches persistence, schemas, config contracts, or the trading runtime.
2. **PASS** — every symbol used is defined in its task or frozen in §3. `CapabilitySpec`, `Requirement`, `check_conformance`, `FORBIDDEN_PREFIXES` and all Phase 4–5 types are frozen ahead of use.
3. **PASS** — no banned verb in any implementation step.
4. **PASS** — order is `P3-T01 → … → P3-T05 → P4-T01 → … → P4-T07 → P5-T01 → … → P5-T04`, a single chain with no forward reference.
5. **PASS** — every path spelled identically across §3, task tables, gates, and `git add` lines.
6. **PASS** — every Phase 3–5 source identifier appears in §12 with an explicit status; none is dropped.
7. **PASS** — every cited identifier (`D-01`–`D-08`, `G3`–`G5`, `R-01`–`R-07`, `CF-03`, `CF-04`) appears verbatim in `REFACTOR_PLAN.md` or is defined here. Unconfirmed requirement IDs: **none**. No `FEAT-*` or `FR-*` ID is cited, and per `P1-T04` these packages have none.
8. **PASS** — largest tasks are `P4-T03` and `P4-T06` at size L, 3 files plus test, 12 steps. No task exceeds 3 files, 200 LOC, 12 steps. No title contains "and".
9. **PASS** — all sixteen commit messages are Conventional Commits (`feat`, `test`) with a scope; each `git add` names only files in that task's table.
10. **PASS** — §8 is empty by design; `R-01`–`R-07` closed every decision this batch needed.
11. **N/A here** — the walking-skeleton rule was discharged in Batch 1 by `P2-T01` per `CF-02`. Phase 3 is a vertical slice: it delivers an importable, tested, boundary-enforced spec layer.
12. **PASS** — the only `EXISTING` artefacts referenced are `app/utils/get_logger`, `rsi`, `scripts/audit_check.py` and the `P1-T04` amendment, all backed by Batch 1 §2 evidence. Everything else is `CREATE`.
13. **PASS** — no task file table contains a PROTECTED path. `app/services/indicators/momentum/rsi.py` is read as evidence in `P3-T04` but appears in no file table, and its `DO NOT` block forbids modifying it.
14. **PASS** — every command traces to §1, which traces to `pyproject.toml`, `.pre-commit-config.yaml`, `scripts/ci_check.py`, or `AGENTS.md` §7.
15. **PASS** — two material conflicts (`CF-03`, `CF-04`), both resolved with a single stated approach. Neither reaches the executor.
16. **PASS** — no dependency used that is not stdlib or already present. §6 authorizes none.

Tasks emitted: **16** across **3** complete phases
Requirements covered: **19** source identifiers PLANNED or PARTIAL; **2** OUT OF SCOPE by explicit §5 decision
Unconfirmed requirement IDs: **none**
Material conflicts resolved: **2**   |   Blocking open questions: **0**
New dependencies authorized: **0**

**Batch 2 is complete.** Phases 3, 4 and 5 are emitted in full. Batch 3 continues at Phase 6.

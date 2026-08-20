# Implementation Plan — Spatiotemporal Provider Decoupling

Source documents: `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` v2, SHA-256 `097A934193AFF5BB652B9D36743FCE129C3E93FBF8990AC0D8C0474D432DE89A`; owner resolutions R-01 through R-07 and the 2026-08-20 recommended-answer set recorded in §7
Repository state: `main` / `828de8cb9546d31f91af762d3ab8adc6b1640bbd`
Generated: 2026-08-20   |   Target executor: low-reasoning coding agent

## 0. EXECUTOR OPERATING RULES

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

Repository approval adds one rule: do not run a task until the owner has approved that task's phase with a standalone message whose trimmed complete content is `APPROVED: EXECUTE`. Approval does not authorize a commit. Run the task's `git commit` command only when the owner separately authorizes commits for that phase; otherwise stop after staging nothing and report `commit not authorized`.

## 1. ENVIRONMENT & COMMANDS

Run commands from `C:\Users\rharu\AppDev\HaruquantAI` in PowerShell. The inspected interpreter is Python 3.14.3 and the inspected package runner is uv 0.12.3. The repository has no documented virtual-environment activation command; use `uv run --locked`.

Verified repository commands:

```powershell
git log -1 --oneline
git status --short
git diff --check
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy app tests
$env:PYTHONDONTWRITEBYTECODE='1'; uv run --frozen pytest -q -p no:cacheprovider
uv run --locked pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80
uv run --locked python scripts/ci_check.py
```

Verified frontend commands, run from `app/ui`:

```powershell
npm.cmd test -- --run
npm.cmd run typecheck
npm.cmd run build
npm.cmd run e2e
```

Task-specific commands are printed with literal paths inside each work order.

Do not substitute `mypy .` for `mypy app tests`: the former currently includes an ignored, untracked workspace script under `tmp/` and fails outside the configured source trees.

## 2. CURRENT-STATE INVENTORY

**Branch/Commit:** `828de8cb fix(data): narrow MT5 server name return type for mypy`

**Baseline test output:** `$env:PYTHONDONTWRITEBYTECODE='1'; uv run --frozen pytest -q -p no:cacheprovider` exited 1 with `13 failed, 6405 passed, 21 skipped, 1 warning in 506.86s`.

**Package layout:**

```text
app/
├── __init__.py                         public export: validate_runtime_configuration
├── runtime.py                          existing runtime-profile/route validation
├── kernel/                             ABSENT; create in Phases 3–7
├── capabilities/                       ABSENT; create in Phase 3
├── composition/                        ABSENT; create in Phase 6
├── agentic/                            existing top-level orchestration domain
├── services/                           existing business domains
│   ├── analytics/                      Tier A wave 12.6
│   ├── api/                            Tier B wave 12.19; owns current composition
│   ├── brokers/                        Tier B waves 12.3 and 12.14
│   ├── data/                           Tier C/B waves 12.2 and 12.4
│   ├── indicators/                     Phase 9 pilot and Tier A wave 12.5
│   ├── optimization/                   Tier A wave 12.17
│   ├── portfolio/                      Tier B waves 12.8 and 12.10
│   ├── research/                       Tier A wave 12.16
│   ├── risk/                           Tier B/C wave 12.9
│   ├── simulator/                      Tier A wave 12.13
│   ├── strategy/                       Tier B wave 12.7
│   └── trading/                        Tier B waves 12.11, 12.12, and 12.15
└── utils/                              eager public barrel; wave 12.1
tests/
├── architecture/                       cross-provider architecture tests
├── composition/                        composition tests to create
├── removability/                       absence/deletion/reinstall tests to create
└── <domain>/providers/<provider_id>/   owner-approved provider-test location
```

The existing `app/services/api/composition/` remains API-owned until wave 12.19. It is not the target composition root.

**Existing public interfaces:**

```python
# app/runtime.py
def validate_runtime_configuration(
    *, runtime_profile: str, execution_route: str
) -> object: ...

# app/services/indicators/momentum/rsi.py
def rsi(
    data: MarketDataset,
    *,
    period: int,
    source: str = "close",
    config: IndicatorConfig | None = None,
) -> IndicatorResult: ...

# app/services/indicators/momentum/williams_r.py
def williams_r(
    data: MarketDataset,
    *,
    period: int,
    config: IndicatorConfig | None = None,
) -> IndicatorResult: ...
```

`app/__init__.py` has exact `__all__ = ("validate_runtime_configuration",)`. The Indicators root uses lazy `_EXPORTS` and exports 86 names. `rsi` and `williams_r` are both owned by registered feature `FEAT-INDI-03`; that feature ID is preserved throughout the pilot.

**Test conventions:** pytest collects `tests/test_*.py` and `tests/*_test.py` with importlib mode. Unit, component, integration, structural, usage, and end-to-end directories already exist. Provider unit/contract/lifecycle tests will live under `tests/<domain>/providers/<provider_id>/`; system absence tests remain under `tests/removability/`. A provider's only colocated executable evidence is `example.py`.

**Logging, errors, configuration, dependencies:** workflow and I/O boundaries import the system logger from `app.utils`; pure numerical functions do not log unless their existing contract already does. Public operations use domain errors and standard response envelopes. Configuration uses Pydantic settings and process environment. `tomllib` is available in Python 3.14 and is the only manifest parser authorized. Dependencies are declared in `pyproject.toml` and locked by `uv.lock`.

**Verified commands:** all commands in §1 were read from `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`, `scripts/ci_check.py`, or executed during grounding.

**Pre-existing failures:**

- Full Python suite: 13 failures. Twelve Data/Indicators failures passed when rerun in their grouped target files and are classified as order/resource-interference failures pending independent correction. `tests/ui/structural/test_feature_registry.py` fails deterministically because documentation expects 252 total/244 completed/96.83%, while the README registries contain 253 unique/245 completed/96.84%.
- Frontend unit tests: 82 files and 652 tests passed.
- Frontend typecheck and build: passed; build emitted warnings only.
- Frontend Playwright: 13 failures, all in `app/ui/e2e/workbench-journeys.spec.ts`; current Next routes deleted the workstation simulator and analytics pages still required by the journeys.
- Ruff format check: `2994 files already formatted`.
- Ruff lint: `All checks passed!`.
- `mypy app tests`: `Success: no issues found in 2939 source files`.
- `mypy .`: one failure in ignored workspace file `tmp/explore_sqx_dat.py:111`; this is outside configured `app` and `tests` source roots.

**External prerequisite EP-01:** G0 requires a green suite. Before P0-T04 can complete, a separately approved defect work order must restore the missing UI workstation routes, reconcile the feature count, and eliminate or formally fix the twelve order/resource-interference failures. This plan does not authorize those unrelated repairs.

**Behavior that must remain unchanged:**

- All deterministic financial values captured by the Phase 0 hash manifest.
- Existing domain-root callable signatures and return/error behavior until their explicit cutover task.
- Live and demo mutation remains fail-closed; no provider absence creates authorization.
- The kill switch cannot be disabled, bypassed, replaced by a weaker provider, or auto-cleared.
- Removing provider code never deletes historical data or causes a compensating trade.
- Existing API paths and OpenAPI operations remain stable; unavailable optional capabilities return the structured error frozen in §3.
- A simulation run pins one complete provider-generation graph.

## 3. SHARED CONTRACTS (INTERFACE FREEZE)

### 3.1 Target package tree

Status is `CREATE` unless marked otherwise.

```text
app/capabilities/
├── __init__.py                         empty infrastructure boundary
├── indicator/
│   ├── __init__.py                     empty namespace
│   ├── common/v1.py                    provider-neutral input/result protocols
│   ├── rsi/v1.py                       pure RSI callable record
│   └── williams_r/v1.py                pure Williams %R callable record
├── notification/delivery/v1.py         effectful notification Protocol
└── data/tick_stream/v1.py              effectful tick-stream Protocol
app/kernel/
├── __init__.py                         frozen public machinery exports
├── identifiers.py                      validated IDs and versions
├── manifests.py                        static TOML schema and parser
├── discovery.py                        filesystem discovery without provider import
├── registry.py                         immutable inventory
├── resolver.py                         deterministic dependency resolution
├── profiles.py                         readiness policy
├── states.py                           component states and transitions
├── errors.py                           CAPABILITY_UNAVAILABLE family
├── health.py                           health/readiness projections
├── diagnostics.py                      bounded secret-safe projections
├── effects.py                          synchronous effect scope
├── async_effects.py                    async edge adapter
└── lifecycle.py                        activation/deactivation coordinator
app/composition/
├── __init__.py                         frozen composition exports
├── generations.py                      generation identity and leases
├── runtime.py                          construction-time injection and activation
└── reconciliation.py                   installed-provider config reconciliation
```

`app/kernel/`, `app/capabilities/`, and `app/composition/` are non-feature infrastructure. They have no `FEAT-*` ID, Feature Registry, or usage program.

### 3.2 Kernel identifiers and manifest values

```python
# app/kernel/identifiers.py
@dataclass(frozen=True, slots=True, order=True)
class CapabilityId:
    domain: str
    capability: str
    major: int

    @classmethod
    def parse(cls, value: str) -> CapabilityId: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True, slots=True, order=True)
class ProviderId:
    domain: str
    capability: str
    implementation: str

    @classmethod
    def parse(cls, value: str) -> ProviderId: ...
    def __str__(self) -> str: ...

@dataclass(frozen=True, slots=True, order=True)
class SemanticVersion:
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> SemanticVersion: ...
    def __str__(self) -> str: ...
```

Accepted capability text is exactly `<domain>.<capability>.v<positive integer>`. Accepted provider text is exactly `<domain>.<capability>.<implementation>`. Segments match `[a-z][a-z0-9_]*`. Version text is exactly three non-negative decimal integers separated by dots. Invalid values raise `ValueError` with `invalid capability id: {value!r}`, `invalid provider id: {value!r}`, or `invalid semantic version: {value!r}`.

```python
# app/kernel/manifests.py
class Cardinality(StrEnum):
    EXACTLY_ONE = "exactly_one"
    ZERO_OR_ONE = "zero_or_one"
    ONE_OF_SEVERAL = "one_of_several"
    MANY = "many"

class OnMissing(StrEnum):
    FAIL_CLOSED = "fail_closed"
    DEGRADE = "degrade"
    SKIP = "skip"

class EffectClass(StrEnum):
    REVERSIBLE_EPHEMERAL = "reversible_ephemeral"
    DURABLE_COMPENSATABLE = "durable_compensatable"
    IRREVERSIBLE_EXTERNAL = "irreversible_external"

class LifecyclePolicy(StrEnum):
    PURE = "pure"
    SCOPED = "scoped"

class ReloadPolicy(StrEnum):
    CONFIG_RESTART = "config_restart"
    PROCESS_RESTART = "process_restart"

@dataclass(frozen=True, slots=True)
class ProvidedCapability:
    capability_id: CapabilityId
    contract_version: SemanticVersion
    cardinality: Cardinality

@dataclass(frozen=True, slots=True)
class RequiredCapability:
    capability_id: CapabilityId
    supported_majors: tuple[int, ...]
    cardinality: Cardinality
    on_missing: OnMissing = OnMissing.FAIL_CLOSED

@dataclass(frozen=True, slots=True)
class ProviderManifest:
    provider_id: ProviderId
    provider_version: SemanticVersion
    entry_point: str
    provides: tuple[ProvidedCapability, ...]
    requires: tuple[RequiredCapability, ...]
    optional_requires: tuple[RequiredCapability, ...]
    profiles: tuple[RuntimeProfile, ...]
    scopes: tuple[str, ...]
    effect_classes: tuple[EffectClass, ...]
    lifecycle: LifecyclePolicy
    reload: ReloadPolicy
    config_schema: str | None
    state_schema_id: str | None
    state_schema_version: SemanticVersion | None
    migration_manifest: str | None
    compatible_state_majors: tuple[int, ...]
    uninstall_retention: str | None
    purge_requires_authorization: bool

def load_manifest(path: Path) -> ProviderManifest: ...
```

Manifest top-level TOML tables are exactly `[provider]`, `[[provides]]`, `[[requires]]`, `[[optional_requires]]`, `[runtime]`, and optional `[state]`. `entry_point` is `<module>:<factory>`. Unknown keys and duplicate capabilities raise `ManifestValidationError`. Discovery accepts only first-party manifests rooted under the configured repository `app/` path; Python entry points and third-party package entry points are out of scope.

### 3.3 States, errors, and reports

```python
# app/kernel/states.py
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

# app/kernel/errors.py
class CapabilityReasonCode(StrEnum):
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

@dataclass(frozen=True, slots=True)
class CapabilityUnavailable:
    code: Literal["CAPABILITY_UNAVAILABLE"]
    reason_code: CapabilityReasonCode
    capability: str
    consumer: str | None
    provider_id: str | None
    provider_state: str
    profile: str | None
    dependency_chain: tuple[str, ...]
    retryable: bool

class CapabilityUnavailableError(RuntimeError):
    detail: CapabilityUnavailable

class ManifestValidationError(ValueError): ...
class ResolutionError(RuntimeError): ...
class LifecycleError(RuntimeError): ...
```

`CapabilityUnavailable.code` is always `CAPABILITY_UNAVAILABLE`. `dependency_chain` starts with the direct consumer and ends with the unavailable leaf. Exception text is `CAPABILITY_UNAVAILABLE: {reason_code}: {capability}`. No exception field contains credentials, configuration values, or complete external payloads.

```python
# app/kernel/resolver.py
@dataclass(frozen=True, slots=True)
class ResolvedBinding:
    capability_id: CapabilityId
    provider_id: ProviderId
    provider_version: SemanticVersion

@dataclass(frozen=True, slots=True)
class InactiveCapability:
    capability_id: CapabilityId
    detail: CapabilityUnavailable

@dataclass(frozen=True, slots=True)
class ResolutionReport:
    bindings: tuple[ResolvedBinding, ...]
    inactive: tuple[InactiveCapability, ...]
    activation_order: tuple[ProviderId, ...]
    deactivation_order: tuple[ProviderId, ...]

def resolve_providers(
    manifests: tuple[ProviderManifest, ...],
    *,
    enabled_provider_ids: frozenset[ProviderId],
    selected_provider_ids: Mapping[CapabilityId, ProviderId],
) -> ResolutionReport: ...
```

Ordering is lexicographic by string provider ID whenever graph order permits more than one answer. Import order is never consulted.

### 3.4 Profiles and health

```python
class RuntimeProfile(StrEnum):
    RESEARCH = "research"
    SIMULATION = "simulation"
    DEMO = "demo"
    LIVE = "live"

@dataclass(frozen=True, slots=True)
class ProfileReadiness:
    profile: RuntimeProfile
    ready: bool
    missing: tuple[CapabilityUnavailable, ...]

@dataclass(frozen=True, slots=True)
class KernelHealth:
    live: bool
    ready: bool
    active_count: int
    inactive_count: int

def evaluate_profile_readiness(
    report: ResolutionReport,
    *,
    requirements: Mapping[RuntimeProfile, tuple[CapabilityId, ...]],
) -> tuple[ProfileReadiness, ...]: ...
```

Kernel boot succeeds with missing business providers and reports affected profiles unready. Demo/live mutation functions must reject an unready profile with `PROFILE_REQUIREMENT_UNSATISFIED`. The kernel itself, Data core, Risk kill switch, and the complete live safety set are required by construction for their governed operations; their absence never authorizes fallback or mutation.

### 3.5 Lifecycle and generations

```python
# app/kernel/effects.py
class EffectScope:
    def callback(self, disposer: Callable[[], object]) -> None: ...
    def enter_context(self, resource: ContextManager[T]) -> T: ...
    def can_dispose(self) -> bool: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...

# app/kernel/async_effects.py
class AsyncEffectScopeAdapter:
    def __init__(self, sync_scope: EffectScope) -> None: ...
    async def enter_async_context(self, resource: AsyncContextManager[T]) -> T: ...
    def callback(self, disposer: Callable[[], object]) -> None: ...
    async def aclose(self) -> None: ...

# app/kernel/lifecycle.py
class ProviderFactory(Protocol):
    def __call__(
        self,
        *,
        dependencies: Mapping[CapabilityId, object],
        config: Mapping[str, object],
        scope: EffectScope,
    ) -> object: ...

@dataclass(frozen=True, slots=True)
class ActiveComponent:
    provider_id: ProviderId
    generation_id: UUID
    state: ComponentState
    instance: object
    scope: EffectScope

def activate_component(...) -> ActiveComponent: ...
def deactivate_component(component: ActiveComponent, *, timeout_seconds: float) -> None: ...
```

The complete signatures elided above are frozen in tasks P5-T02 and P5-T03 before any consumer task uses them. No task may invent additional lifecycle parameters.

```python
# app/composition/generations.py
@dataclass(frozen=True, slots=True)
class ProviderGeneration:
    provider_id: ProviderId
    provider_version: SemanticVersion
    capability_versions: tuple[tuple[CapabilityId, SemanticVersion], ...]
    generation_id: UUID
    configuration_digest: str
    dependency_generation_ids: tuple[UUID, ...]
    activated_at: datetime
    effect_scope_id: UUID

@dataclass(frozen=True, slots=True)
class CapabilityLease(Generic[T]):
    capability_id: CapabilityId
    generation_id: UUID
    value: T

@dataclass(frozen=True, slots=True)
class PinnedCapabilityGraph:
    generations: tuple[ProviderGeneration, ...]
```

Configuration digests are lowercase SHA-256 over canonical JSON with keys sorted, UTF-8 encoding, and separators `(',', ':')`. Secret values are represented by their secret-reference identifier, never plaintext.

### 3.6 Provider IDs frozen for the pilots

| Provider | Provider ID | Capability | Contract | Cardinality | Lifecycle | Reload |
|---|---|---|---|---|---|---|
| RSI default | `indicator.rsi.default` | `indicator.rsi.v1` | `1.0.0` | `many` | `pure` | `config_restart` |
| Williams %R default | `indicator.williams_r.default` | `indicator.williams_r.v1` | `1.0.0` | `many` | `pure` | `config_restart` |
| Email notification | `notification.delivery.email` | `notification.delivery.v1` | `1.0.0` | `many` | `scoped` | `config_restart` |
| SMS notification | `notification.delivery.sms` | `notification.delivery.v1` | `1.0.0` | `many` | `scoped` | `config_restart` |
| Telegram notification | `notification.delivery.telegram` | `notification.delivery.v1` | `1.0.0` | `many` | `scoped` | `config_restart` |
| Desktop notification | `notification.delivery.desktop` | `notification.delivery.v1` | `1.0.0` | `many` | `scoped` | `config_restart` |
| MT5 tick stream | `data.tick_stream.metatrader` | `data.tick_stream.v1` | `1.0.0` | `one_of_several` | `scoped` | `process_restart` |
| Deterministic fake tick stream | `data.tick_stream.fake` | `data.tick_stream.v1` | `1.0.0` | `one_of_several` | `scoped` | `config_restart` |

RSI and Williams providers remain nested under `app/services/indicators/momentum/` so `FEAT-INDI-03` remains the single registered feature:

```text
app/services/indicators/momentum/
├── README.md
├── __init__.py
├── rsi_default/{manifest.toml,plugin.py,implementation.py,example.py,README.md}
└── williams_r_default/{manifest.toml,plugin.py,implementation.py,example.py,README.md}
```

Tests live at `tests/indicators/providers/indicator.rsi.default/` and `tests/indicators/providers/indicator.williams_r.default/`.

### 3.7 Public `__all__` values

- `app/capabilities/__init__.py`, every domain namespace `__init__.py`, and every capability namespace `__init__.py`: `__all__: tuple[str, ...] = ()`.
- `app/kernel/__init__.py`: `("CapabilityId", "ProviderId", "SemanticVersion", "ProviderManifest", "load_manifest", "discover_manifests", "resolve_providers", "ResolutionReport", "RuntimeProfile", "ProfileReadiness", "evaluate_profile_readiness", "ComponentState", "CapabilityReasonCode", "CapabilityUnavailable", "CapabilityUnavailableError", "KernelHealth", "EffectScope", "AsyncEffectScopeAdapter")`.
- `app/composition/__init__.py`: `("ProviderGeneration", "CapabilityLease", "PinnedCapabilityGraph", "CompositionRuntime", "reconcile_configuration")`.
- Provider `plugin.py`: `__all__ = ("create_provider",)`.
- Provider `implementation.py`: `__all__: tuple[str, ...] = ()`.

## 4. NAMING & LAYOUT CONVENTIONS

- Python modules and functions use `snake_case`; classes use `CapWords`; constants use `UPPER_SNAKE_CASE`; tests use `test_<behavior>`.
- Production uses absolute imports. Capability specs never import `app.services` or `app.agentic`. The kernel never imports those packages. Cross-domain consumers import capability specs, not concrete providers.
- Provider folders use implementation names such as `rsi_default`; provider IDs use dotted `<domain>.<capability>.<implementation>`.
- Each provider folder contains exactly `manifest.toml`, `plugin.py`, `implementation.py`, `example.py`, `README.md`, plus `__init__.py` when Python package import requires it. Tests do not live beside production.
- Module/class/function docstrings use Google style. Public symbols and workflow boundaries document Args, Returns, and Raises where the signature requires them.
- Provider README headings are `# <Provider display name>`, `## Identity`, `## Capabilities`, `## Dependencies`, `## Profiles`, `## Lifecycle`, `## State`, `## Removal behavior`, and `## Evidence`.
- The domain README remains the canonical Feature Registry until P16-T04. Manifests become authoritative only after the generator and cutover pass together.
- CHANGELOG policy: no task in this plan touches `docs/CHANGELOG.md`. Release aggregation is outside this refactor plan.

## 5. SCOPE & PROTECTED AREAS

**In scope:** G0–G11; waves 12.1–12.21; the repeatable provider procedure A–J; Phase 16 constraints; Phase 17 Tier 1 installed-provider configuration reconciliation.

**Out of scope:** Phase 17 Tier 2 logical source-code replacement; Phase 17 Tier 3 process-isolated replacement; third-party provider installation; entry-point discovery; automatic data purge; automatic financially compensating actions; live source-code HMR; provider implementations not selected by the Phase 2 audit and approved wave work order.

**PROTECTED paths — no task may modify unless that exact path appears in the task table:**

| Path | Reason |
|---|---|
| `app/services/risk/kill_switch/` | non-disableable live safety authority |
| `app/services/trading/live/` | irreversible external mutation path |
| `app/services/trading/protective_orders/` | live protective-order authority |
| `app/services/brokers/*/commands.py` | broker mutation; deferred to wave 12.14 |
| `app/services/data/migrations/*.py` | applied migration definitions are immutable |
| `data/` | persistent/runtime data; purge is outside scope |
| `.env*` except `.env.example` when explicitly listed | credentials and local configuration |
| `uv.lock` and `pyproject.toml` | no dependency change is authorized |
| `docs/CHANGELOG.md` | release aggregation is outside scope |

**Forbidden changes (apply to every task):**

- No unrelated refactoring or cleanup.
- No public API change not in §3.
- No new dependency outside §6.
- No weakening, skipping, xfailing, or deleting existing tests.
- No lint/type-check suppression unless a specific task authorizes it with reason.
- No placeholder or stub implementation; no new TODO/FIXME.
- No credentials, secrets, or local config committed.
- No live-trading, live-broker, or production operation from tests or examples.

## 6. DEPENDENCY AUTHORIZATION

No new dependencies are authorized by this plan.

Use standard-library `tomllib`, `contextlib.ExitStack`, `contextlib.AsyncExitStack`, `dataclasses`, `enum.StrEnum`, `hashlib`, `importlib`, `pathlib`, `typing`, and `uuid`, plus existing pinned project dependencies. Do not modify `pyproject.toml` or `uv.lock`.

## 7. SOURCE CONFLICTS

Conflict ID: CF-01
Sources: `REFACTOR_PLAN.md` Phase 5 former async-first wording vs R-02
Claim A: lifecycle uses `AsyncExitStack` in the kernel.
Claim B: kernel, resolver, registry, and lifecycle are synchronous; async exists only at streaming, broker, and API edges.
Precedence: owner resolution R-02.
Decision: `EffectScope` wraps `ExitStack`; `AsyncEffectScopeAdapter` wraps edge-only `AsyncExitStack` behavior.
Affected tasks: P5-T01, P5-T03, P10-T04, and generated async-edge tasks in waves 12.4, 12.14, and 12.19

Conflict ID: CF-02
Sources: `REFACTOR_PLAN.md` §1.4 vs owner recommended-answer set
Claim A: provider tests live inside each provider folder.
Claim B: provider tests live under root `tests/<domain>/providers/<provider_id>/`; only `example.py` is colocated.
Precedence: explicit owner answer.
Decision: use root tests and provider-local `example.py`.
Affected tasks: all provider migration tasks

Conflict ID: CF-03
Sources: `REFACTOR_PLAN.md` Phase 9 target vs owner recommended-answer set
Claim A: RSI and Williams providers are direct children of `app/services/indicators/`.
Claim B: preserve `FEAT-INDI-03` and nest two provider folders under `momentum/`.
Precedence: explicit owner answer.
Decision: use `momentum/rsi_default/` and `momentum/williams_r_default/`; do not create new feature IDs.
Affected tasks: P9-T01 through P9-T06

Conflict ID: CF-04
Sources: `REFACTOR_PLAN.md` D-11 vs current `AGENTS.md` Feature Registry Authority and owner recommended-answer set
Claim A: manifests become the source of truth.
Claim B: package README is the canonical registry today.
Precedence: owner-defined staged cutover.
Decision: README remains canonical through waves 12.1–12.21; P16-T04 adds the generator, compares both representations, then changes authority in the same phase.
Affected tasks: P1-T01, P16-T04

Conflict ID: CF-05
Sources: `REFACTOR_PLAN.md` Phase 11 inverse assertion vs owner recommended-answer set
Claim A: disabling any required provider refuses process boot.
Claim B: kernel/API may boot without a safety provider; demo/live become unready and all mutations are blocked.
Precedence: explicit owner answer plus stable API requirement.
Decision: absence of `app/kernel` or `app/capabilities` prevents boot; absence of a business safety provider permits kernel/API liveness but refuses demo/live readiness and mutation.
Affected tasks: P7-T02, P11-T03, and generated safety/readiness tasks in waves 12.9, 12.15, and 12.19

Conflict ID: CF-06
Sources: `REFACTOR_PLAN.md` Phase 17 vs owner recommended-answer set
Claim A: controlled runtime replacement includes three tiers.
Claim B: initial scope switches configuration among already-installed first-party providers; source reload is deferred.
Precedence: explicit owner answer.
Decision: P17 tasks implement Tier 1 only and never import newly written provider code into the running process.
Affected tasks: P6-T03, P17-T01, P17-T02

Conflict ID: CF-07
Sources: current request task template vs `AGENTS.md` Approval Gate
Claim A: every task ends with exactly one commit.
Claim B: phase approval does not authorize commits.
Precedence: `AGENTS.md` for repository execution; current request for plan content.
Decision: every task specifies one commit message, but executor runs it only after separate owner commit authorization.
Affected tasks: all tasks

Conflict ID: CF-08
Sources: `REFACTOR_PLAN.md` Gate G0 vs inspected repository baseline
Claim A: G0 requires a passing suite.
Claim B: current checkout has 13 Python and 13 Playwright failures.
Precedence: G0 remains mandatory; pre-existing failures are repository evidence.
Decision: record failures in P0-T01, then block G0 on external prerequisite EP-01; do not hide or waive failures.
Affected tasks: P0-T01 through P0-T04

Conflict ID: CF-09
Sources: `REFACTOR_PLAN.md` R-04 and Phase 3 shorthand
Claim A: R-04 requires `app/capabilities/<domain>/<capability>/vN.py`.
Claim B: Phase 3 abbreviates the path as `app/capabilities/<capability>/vN.py`.
Precedence: owner resolution R-04.
Decision: always include the domain segment.
Affected tasks: all capability-spec tasks

## 8. OPEN QUESTIONS (BLOCKING)

None. Phase 12 provider boundaries and file lists are produced by the deterministic G2 audit artifact and frozen by the mandatory per-wave expansion gate described in §11; that is an execution dependency, not an owner design question.

## 9. PLANNER OBSERVATIONS (non-blocking)

- The source contains architectural decision IDs (`D-*`), resolved answer IDs (`R-*`), gates (`G*`), wave numbers (`12.*`), and phase numbers, but no `FR-*` requirement IDs. Tasks cite only those verbatim identifiers; no new requirement ID is introduced.
- The source plan is untracked in the inspected checkout. Preserve its exact SHA-256 when reviewing this plan.
- Current Feature Registry totals are 253 unique features, 245 completed, and 8 pending; the current system documentation/test expectation is stale.
- Twelve full-suite Python failures disappear in grouped reruns, indicating shared-state, ordering, or resource-lifecycle interference. Phase 5 directly targets resource ownership, but G0 still requires an independent correction first.
- Existing usage programs under `tests/<domain>/usage/` remain until their owning provider migrates. Moving them is part of per-provider step H, not a bulk deletion.
- Each wave 12.1 through 12.21 requires a separate dry run and standalone approval. This is stricter than R-07's generic phase wording and follows the owner's later answer.
- The Data pilot is the existing MT5 tick stream, verified with a deterministic fake adapter. Real MT5 smoke is optional, dev-only, and never a quality gate.

## 10. PROGRESS DASHBOARD

| Task | Title | Depends On | Status |
|---|---|---|---|
| P0-T01 | Record protected baseline | — | [x] |
| P0-T02 | Freeze financial evidence hashes | P0-T01 | [x] |
| P0-T03 | Scaffold import deletion harness | P0-T01 | [x] |
| P0-T04 | Certify G0 baseline | P0-T02, P0-T03, EP-01 | [x] |
| P1-T01 | Amend builder governance | P0-T04 | [x] |
| P1-T02 | Freeze architecture policy | P1-T01 | [x] |
| P1-T03 | Update system relationships | P1-T02 | [x] |
| P1-T04 | Enforce G1 documentation | P1-T03 | [x] |
| P2-T01 | Extract static dependency graph | P1-T04 | [x] |
| P2-T02 | Extract runtime configuration graphs | P2-T01 | [x] |
| P2-T03 | Extract state frontend graphs | P2-T01 | [x] |
| P2-T04 | Build removability matrices | P2-T02, P2-T03 | [x] |
| P2-T05 | Freeze G2 classifications | P2-T04 | [x] |
| P3-T01 | Create capability package skeleton | P2-T05 | [ ] |
| P3-T02 | Add indicator common contract | P3-T01 | [ ] |
| P3-T03 | Add RSI capability contract | P3-T02 | [ ] |
| P3-T04 | Add Williams capability contract | P3-T02 | [ ] |
| P3-T05 | Enforce capability import isolation | P3-T03, P3-T04 | [ ] |
| P4-T01 | Add kernel identifiers | P3-T05 | [ ] |
| P4-T02 | Parse provider manifests | P4-T01 | [ ] |
| P4-T03 | Discover first-party manifests | P4-T02 | [ ] |
| P4-T04 | Register provider inventory | P4-T03 | [ ] |
| P4-T05 | Resolve provider graph | P4-T04 | [ ] |
| P4-T06 | Project kernel diagnostics | P4-T05 | [ ] |
| P5-T01 | Own synchronous effects | P4-T06 | [ ] |
| P5-T02 | Enforce component transitions | P5-T01 | [ ] |
| P5-T03 | Coordinate component lifecycle | P5-T02 | [ ] |
| P5-T04 | Adapt asynchronous edges | P5-T03 | [ ] |
| P6-T01 | Define provider generations | P5-T04 | [ ] |
| P6-T02 | Compose injected providers | P6-T01 | [ ] |
| P6-T03 | Reconcile installed configuration | P6-T02 | [ ] |
| P7-T01 | Normalize capability failures | P6-T03 | [ ] |
| P7-T02 | Compute profile readiness | P7-T01 | [ ] |
| P7-T03 | Extend runtime validation | P7-T02 | [ ] |
| P8-T01 | Define provider state metadata | P7-T03 | [ ] |
| P8-T02 | Accept migration tombstones | P8-T01 | [ ] |
| P8-T03 | Prove retained-state reinstall | P8-T02 | [ ] |
| P9-T01 | Create RSI provider package | P8-T03 | [ ] |
| P9-T02 | Activate RSI provider | P9-T01 | [ ] |
| P9-T03 | Create Williams provider package | P9-T02 | [ ] |
| P9-T04 | Activate Williams provider | P9-T03 | [ ] |
| P9-T05 | Preserve indicator façade | P9-T04 | [ ] |
| P9-T06 | Prove independent removal | P9-T05 | [ ] |
| P10-T01 | Make Utils boundary lazy | P9-T06 | [ ] |
| P10-T02 | Specify notification delivery | P10-T01 | [ ] |
| P10-T03a | Scope email transport | P10-T02 | [ ] |
| P10-T03b | Scope SMS transport | P10-T03a | [ ] |
| P10-T03c | Scope Telegram transport | P10-T03b | [ ] |
| P10-T03d | Scope desktop transport | P10-T03c | [ ] |
| P10-T04 | Inject notification manager | P10-T03d | [ ] |
| P10-T05 | Specify tick stream | P10-T04 | [ ] |
| P10-T06a | Add MT5 tick stream | P10-T05 | [ ] |
| P10-T06b | Add fake tick stream | P10-T06a | [ ] |
| P10-T07 | Prove effectful replacement | P10-T06b | [ ] |
| P11-T01 | Gate configuration disablement | P10-T07 | [ ] |
| P11-T02 | Prove physical deletion | P11-T01 | [ ] |
| P11-T03 | Prove reinstall and inverse safety | P11-T02 | [ ] |
| P12.1-T01 | Materialize Utils work orders | P11-T03 | [ ] |
| P12.2-T01 | Materialize Data foundation | 12.1 exit | [ ] |
| P12.3-T01 | Materialize Brokers read | 12.2 exit | [ ] |
| P12.4-T01 | Materialize Data live | 12.3 exit | [ ] |
| P12.5-T01 | Materialize Indicators | 12.4 exit | [ ] |
| P12.6-T01 | Materialize Analytics | 12.5 exit | [ ] |
| P12.7-T01 | Materialize Strategy | 12.6 exit | [ ] |
| P12.8-T01 | Materialize Portfolio reads | 12.7 exit | [ ] |
| P12.9-T01 | Materialize Risk | 12.8 exit | [ ] |
| P12.10-T01 | Materialize Portfolio actions | 12.9 exit | [ ] |
| P12.11-T01 | Materialize Trading state | 12.10 exit | [ ] |
| P12.12-T01 | Materialize Trading evaluation | 12.11 exit | [ ] |
| P12.13-T01 | Materialize Simulator | 12.12 exit | [ ] |
| P12.14-T01 | Materialize broker mutation | 12.13 exit | [ ] |
| P12.15-T01 | Materialize demo live composition | 12.14 exit | [ ] |
| P12.16-T01 | Materialize Research | 12.15 exit | [ ] |
| P12.17-T01 | Materialize Optimization | 12.16 exit | [ ] |
| P12.18-T01 | Materialize Agentic | 12.17 exit | [ ] |
| P12.19-T01 | Materialize API | 12.18 exit | [ ] |
| P12.20-T01 | Materialize UI | 12.19 exit | [ ] |
| P12.21-T01 | Materialize cutover | 12.20 exit | [ ] |
| P16-T01 | Enforce Python boundaries | P12.21–T01 | [ ] |
| P16-T02 | Enforce provider manifests | P16-T01 | [ ] |
| P16-T03 | Enforce removability evidence | P16-T02 | [ ] |
| P16-T04 | Generate feature registries | P16-T03 | [ ] |
| P17-T01 | Reconcile provider configuration | P16-T04 | [ ] |
| P17-T02 | Prove transactional rollback | P17-T01 | [ ] |

## 11. PHASES

### Phase 0 — Baseline & Foundations

**Goal:** create a reproducible, immutable record of pre-refactor behavior without modifying production code.
**Why now:** every later provider migration needs financial parity and clean-checkout evidence.
**Deliverable:** baseline report, financial hash manifest, and non-enforcing fresh-process harness.
**Phase Exit Gate:** G0 remains blocked until EP-01 is independently resolved.

#### - [x] Task `P0-T01` — Record protected baseline

**Traces to:** `Phase 0`, `G0`
**Depends on:** none
**Estimated size:** S (<50 LOC)

**Goal.** Record the exact inspected commit, tool versions, commands, exit codes, failure summaries, and working-tree state without changing application or test code.

**Context to Read (and nothing else):**
- `AGENTS.md` — approval and baseline rules.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Phase 0 and G0.
- `pyproject.toml` — Python quality commands.
- `app/ui/package.json` — frontend commands.
- `.github/workflows/ci.yml` — CI entry point.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `docs/dev/plugin-decoupling/evidence/baseline.md` | CREATE | immutable command transcript and failure classification |

**Specification (copy exactly):** the first heading is `# Plugin-Decoupling Baseline — 828de8cb`; include sections `Repository`, `Python`, `Frontend`, `Public Surface`, `Known Failures`, and `G0 Status`. Copy the §2 evidence values exactly. Set `G0 Status` to `BLOCKED — EP-01`.

**Behaviour Rules:**
1. Every command row contains command, working directory, exit code, and exact summary.
2. Distinguish deterministic failures from failures that pass in isolated/grouped reruns.
3. Do not label any failed command as passing.
4. Record source-plan SHA-256 exactly.

**Implementation Steps:**
1. Run `git log -1 --oneline` and `git status --short`.
2. Run each §1 baseline command once; do not rerun to replace a failure.
3. Create the evidence file with the required headings and outputs.
4. Add `EP-01` with the three required independent repairs.

**DO NOT (anti-invention guardrails):**
- Do not modify production, tests, configuration, or lockfiles.
- Do not repair a baseline failure.
- Do not omit stderr or warnings from summaries.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: none; this is evidence capture. Verify exact required headings with:
`rg -n '^# Plugin-Decoupling Baseline|^## (Repository|Python|Frontend|Public Surface|Known Failures|G0 Status)$' docs/dev/plugin-decoupling/evidence/baseline.md` → seven matches.

**Usage Example**
Run `Get-Content docs/dev/plugin-decoupling/evidence/baseline.md -TotalCount 20`; the first line is `# Plugin-Decoupling Baseline — 828de8cb`.

**Quality Gates (run in order, all must pass):**
```powershell
git diff --check
git status --short
```

**Documentation Updates:** the created evidence file is the only documentation update.

**Git Commit:** `test(architecture): record pre-composability baseline`

**Re-run safety:** Safe — replace no values; if the commit differs, stop instead of updating the evidence.

**Definition of Done:**
- [x] Evidence contains every required command and real exit code.
- [x] G0 is recorded as blocked by EP-01.
- [x] Only the listed file changed.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P0-T02` — Freeze financial evidence hashes

**Traces to:** `Phase 0`, `G0`, `Definition of done`
**Depends on:** P0-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Create a machine-checked SHA-256 manifest for existing deterministic indicator, analytics, risk, strategy, simulator, portfolio, and trading evidence.

**Context to Read (and nothing else):**
- `docs/dev/plugin-decoupling/evidence/baseline.md` — baseline identity.
- `tests/indicators/fixtures/momentum_golden.json` — indicator evidence.
- `tests/analytics/unit/test_performance_net_pnl.py` — analytics evidence.
- `tests/risk/unit/test_calculator.py` — risk evidence.
- `tests/simulator/fixtures/golden_run_report_v1.json` — simulator evidence.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/architecture/fixtures/plugin_financial_baseline.json` | CREATE | sorted path/hash ledger |
| `tests/architecture/test_plugin_financial_baseline.py` | CREATE | verify file presence and SHA-256 equality |

**Specification (copy exactly):** JSON object keys are `baseline_commit`, `algorithm`, and `artifacts`. `baseline_commit` is the full inspected hash. `algorithm` is `sha256`. `artifacts` is a list sorted by `path`; each item has only `path` and `sha256`. Include these exact 15 rows:

| Path | SHA-256 |
|---|---|
| `tests/analytics/fixtures/golden/max_drawdown.json` | `fc1d6c25c5d7bb51fcc863cb93450d8e15f704b5df1709d29b2ac40526203a8b` |
| `tests/analytics/fixtures/golden/net_pnl.json` | `64fd2403c3c0d47009fcaf36c74866c3c3a4454e86c97d87b0f19c5181000cd5` |
| `tests/indicators/fixtures/momentum_golden.json` | `c99792ecdc2ecd5f94b66a787726d8919078e2b9ceb1c412fc418ed33572d88f` |
| `tests/indicators/fixtures/trend_golden.json` | `8eee4b3d5b7e467d772a00b50948d0d67f46f7efd7ba24ae02af8ec7bc730b33` |
| `tests/indicators/fixtures/volatility_golden.json` | `868ab1c4425a1189966dd83ccd7bfe765fb3ac7d301433ff6b48719c287c22d6` |
| `tests/portfolio/unit/test_construction_service.py` | `2aee9f2f1f7901ce34c51e336134ca63c9096f0ddac3f8f0f8ade01865739416` |
| `tests/portfolio/unit/test_valuation_and_reconciliation.py` | `c264e91dc4bdf4219024b327082c88c1ec846eb217831ec00e76529a6b56f91c` |
| `tests/risk/unit/test_analysis.py` | `705f461ec98178650a249df5e8eacd2a9ca2fbaac9611b5de32fc1a912dee1cf` |
| `tests/risk/unit/test_calculator.py` | `a0e156a56b769ed197a726c00ec8abd31c64c39f1779e6dcc2213779484d6071` |
| `tests/simulator/fixtures/golden/report.md` | `a1cb33e4a2004fb34350bd08fc1374310ebf40f6bfd15ae092a970e80473c009` |
| `tests/simulator/unit/test_reports.py` | `3c819a66f3fd39aa29f14203cce907658c071404ecf893883194a0a50d43d769` |
| `tests/strategy/integration/test_concrete_signal_workflow.py` | `49fe7cd6d3354b042f90cff50e766fa3682607fb3f85a6be7873a3080e474e4d` |
| `tests/strategy/unit/test_naive_ma_trend_evaluator.py` | `d6fee8ae0b732999d7d8c92e74b93cf71e71ee5c5a01d1045d39198b353843e5` |
| `tests/trading/unit/contracts/test_order_policy_v2.py` | `535f979c284fa063933b211b93b50fbcd845c1764cd4fa9157e011c0f1845ead` |
| `tests/trading/unit/validation/test_plans.py` | `b0bd01f4616f8dd56c08323bddf6da8af0621dcff89ef3075679876fc2c882d9` |

**Behaviour Rules:**
1. Hash raw bytes without newline conversion.
2. Reject absolute paths, backslashes, duplicate paths, missing files, and non-lowercase 64-character hashes.
3. Test reports the first mismatched relative path.
4. Do not regenerate hashes inside the test.

**Implementation Steps:**
1. Recompute hashes with `Get-FileHash -Algorithm SHA256`.
2. Stop if any recomputed value differs from the grounded value.
3. Create sorted JSON with two-space indentation and one trailing newline.
4. Create one parametrized pytest test for shape and one for byte hashes.

**DO NOT:**
- Do not copy or alter golden financial artifacts.
- Do not add generated market values.
- Do not hash `data/`, logs, caches, or credentials.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_plugin_financial_baseline.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_financial_manifest_is_canonical` | JSON manifest | exact keys, sorted unique paths, lowercase hashes |
| `test_financial_artifacts_match_baseline` | every artifact | byte SHA-256 equals manifest |

Run: `uv run --locked pytest tests/architecture/test_plugin_financial_baseline.py -q` → 2 passed, 0 skipped.

**Usage Example**
Run the test file directly through pytest; its two passing tests are the executable parity proof.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/architecture/test_plugin_financial_baseline.py
uv run --locked ruff check tests/architecture/test_plugin_financial_baseline.py
uv run --locked mypy tests/architecture/test_plugin_financial_baseline.py
uv run --locked pytest tests/architecture/test_plugin_financial_baseline.py -q
git diff --check
```

**Documentation Updates:** none; evidence paths are self-describing and baseline.md already indexes the purpose.

**Git Commit:** `test(architecture): freeze financial baseline hashes`

**Re-run safety:** Safe — create-only; stop if either path exists.

**Definition of Done:**
- [x] Manifest includes all seven financial domains.
- [x] Two tests pass.
- [x] No golden artifact changed.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P0-T03` — Scaffold import deletion harness

**Traces to:** `Phase 0`, `Phase 11`
**Depends on:** P0-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Add a fresh-interpreter import smoke test and a copy-tree harness API without deleting any provider or enforcing future expectations.

**Context to Read (and nothing else):**
- `app/__init__.py` — current application import.
- `app/runtime.py` — runtime validation entry point.
- `tests/conftest.py` — repository fixtures.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Phase 0 and Phase 11 proof #2.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/architecture/test_application_import_smoke.py` | CREATE | clean subprocess application import |
| `tests/removability/__init__.py` | CREATE | test package marker |
| `tests/removability/harness.py` | CREATE | copied-tree subprocess result helper |

**Specification (copy exactly):**
```python
@dataclass(frozen=True, slots=True)
class FreshProcessResult:
    returncode: int
    stdout: str
    stderr: str

def run_in_fresh_process(
    *, repository_root: Path, script: str, timeout_seconds: float = 30.0
) -> FreshProcessResult: ...
```
Use `sys.executable`, `-I`, and `-c`; set subprocess cwd to `repository_root`; set `PYTHONDONTWRITEBYTECODE=1`; capture text; never use shell execution.

**Behaviour Rules:**
1. Smoke script imports `app`, imports `validate_runtime_configuration`, calls research/none, and prints only `IMPORT_OK`.
2. Timeout raises `AssertionError("fresh process exceeded {timeout_seconds:.3f}s")`.
3. Nonzero exit is returned, not raised by the helper.
4. This task does not copy or delete the repository.

**Implementation Steps:**
1. Create the removability package marker with empty `__all__`.
2. Implement immutable result and subprocess helper.
3. Add the application smoke test using the repository root.
4. Assert return code 0, stdout `IMPORT_OK`, and empty stderr.

**DO NOT:**
- Do not import a future kernel path.
- Do not delete or disable providers.
- Do not use a live broker or network.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_application_import_smoke.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_application_imports_in_fresh_process` | isolated Python | 0, `IMPORT_OK`, empty stderr |
| `test_fresh_process_reports_failure` | `raise SystemExit(7)` | returncode 7 |

**Usage Example**
Run `uv run --locked pytest tests/architecture/test_application_import_smoke.py -q`; two passes prove current import behavior.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/architecture/test_application_import_smoke.py tests/removability/__init__.py tests/removability/harness.py
uv run --locked ruff check tests/architecture/test_application_import_smoke.py tests/removability
uv run --locked mypy tests/architecture/test_application_import_smoke.py tests/removability
uv run --locked pytest tests/architecture/test_application_import_smoke.py -q
git diff --check
```

**Documentation Updates:** none; P0-T01 already records that the harness is scaffolded and non-enforcing.

**Git Commit:** `test(architecture): scaffold fresh-process deletion harness`

**Re-run safety:** Safe — create-only; stop if a target exists.

**Definition of Done:**
- [x] Fresh interpreter imports current app.
- [x] Helper exposes the exact frozen API.
- [x] No deletion occurs.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P0-T04` — Certify G0 baseline

**Traces to:** `G0`
**Depends on:** P0-T02, P0-T03, EP-01
**Estimated size:** S (<50 LOC)

**Goal.** Change the recorded G0 status from blocked to passed only after every baseline command is green from a clean checkout.

**Context to Read (and nothing else):**
- `docs/dev/plugin-decoupling/evidence/baseline.md` — anchor `## G0 Status`.
- `tests/architecture/test_plugin_financial_baseline.py` — parity gate.
- `tests/architecture/test_application_import_smoke.py` — import gate.
- `scripts/ci_check.py` — Python CI order.
- `app/ui/package.json` — frontend gate commands.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `docs/dev/plugin-decoupling/evidence/baseline.md` | MODIFY | replace only G0 status and append final command evidence |

Anchor text: `## G0 Status`. Preserve all earlier failed-run evidence; append, never overwrite, the successful clean-checkout run.

**Specification (copy exactly):** final status line is `PASSED — clean checkout verified at 828de8cb plus approved baseline repairs`. List the repair commit hashes between the baseline hash and status.

**Behaviour Rules:**
1. Stop unless Python CI, frontend unit/type/build/E2E, financial hashes, and import smoke all exit 0.
2. Do not mark G0 passed with skipped Playwright journeys.
3. Preserve the original 13+13 failure evidence.

**Implementation Steps:**
1. Confirm EP-01 repair commits exist.
2. Run all commands in Quality Gates without source changes between them.
3. Append output summaries.
4. Replace only the G0 status line.

**DO NOT:**
- Do not repair any failure in this task.
- Do not waive, skip, or xfail a gate.
- Do not change a test.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
Existing baseline tests must pass with the exact commands below.

**Usage Example**
Run `Select-String -Path docs/dev/plugin-decoupling/evidence/baseline.md -Pattern '^PASSED —'`; exactly one match.

**Quality Gates:**
```powershell
uv run --locked python scripts/ci_check.py
uv run --locked pytest tests/architecture/test_plugin_financial_baseline.py tests/architecture/test_application_import_smoke.py -q
Push-Location app/ui; npm.cmd test -- --run; npm.cmd run typecheck; npm.cmd run build; npm.cmd run e2e; Pop-Location
git diff --check
```

**Documentation Updates:** update only the baseline G0 section.

**Git Commit:** `test(architecture): certify composability baseline`

**Re-run safety:** Safe after G0; a second run must produce no file diff.

**Definition of Done:**
- [x] EP-01 is resolved by separate commits.
- [x] Every gate exits 0.
- [x] Original failure evidence remains.
- [x] Commit executed only with separate authorization.

**Phase 0 Exit Gate — all must be true before Phase 1 starts:**
- [x] Every task in this phase is checked off.
- [x] Full lint and type-check clean across repo.
- [x] Full test suite green; coverage remains at least 80%.
- [x] No test failing that was not in the original Phase 0 record.
- [x] No PROTECTED path appears in the phase diff.
- [x] All frontend checks exit 0.
- [x] Financial hash and fresh-process smoke tests pass.
- [x] G0 status is `PASSED`.

### Phase 1 — Governing Rules

**Goal:** make repository policy agree with the approved provider architecture before code is introduced.
**Why now:** current function-only, usage-location, registry-authority, and migration rules conflict with G1.
**Deliverable:** approved governance, architecture, system-index changes plus a structural policy test.
**Phase Exit Gate:** G1 policy changes merged; later decisions remain as frozen in §3 and §7.

#### - [x] Task `P1-T01` — Amend builder governance

**Traces to:** `D-09`, `D-10`, `D-12`, `D-01`, `R-03`, `R-04`, `R-07`, `G1`
**Depends on:** P0-T04
**Estimated size:** M (50–120 LOC)

**Goal.** Amend `AGENTS.md` so future tasks can create versioned specs, provider manifests, provider-local examples, root provider tests, and retained migration tombstones.

**Context to Read (and nothing else):**
- `AGENTS.md` — file to amend.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — §0.2, §1.1–§1.6.
- Shared Contracts §3 — exact package and test layout.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `AGENTS.md` | MODIFY | add provider architecture exceptions and tombstone policy |

Anchors: `**Reconciliation Exclusions**`, `**Function-Only Public API Surface**`, `**Usage Evidence**`, `**Immutable Historical Steps**`. Preserve every existing safety and feature-ownership rule.

**Specification (copy exactly):** add five named rules: `Provider Infrastructure Exception`, `Capability Boundary Export Exception`, `Provider Test and Example Placement`, `Manifest Authority Transition`, and `Migration Tombstones and Uninstall Retention`. State the decisions in §§3–4 without adding a feature prefix.

**Behaviour Rules:**
1. Business domain roots remain function-only transitional façades.
2. Capability specs may export immutable types and Protocols; providers may export only factories to composition.
3. `tests/<domain>/providers/<provider_id>/` replaces provider-local pytest.
4. Uninstall is not purge; applied owner-absent migrations remain checksum-verifiable.
5. Each 12.x wave receives separate approval.

**Implementation Steps:**
1. Insert infrastructure exception after Reconciliation Exclusions.
2. Insert boundary exception after Function-Only Public API Surface.
3. Replace only the provider-related usage-location rule; retain UI exception.
4. Add manifest transition to documentation authority.
5. Extend immutable migration policy with tombstones and explicit purge authority.

**DO NOT:**
- Do not weaken kill-switch, live-action, secret, or approval rules.
- Do not delete the package-root export gate.
- Do not make manifests canonical before P16-T04.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File is created in P1-T04. In this task run exact text checks for all five headings.

**Usage Example**
Run `rg -n 'Provider Infrastructure Exception|Migration Tombstones and Uninstall Retention' AGENTS.md`; both headings appear once.

**Quality Gates:**
```powershell
git diff --check
rg -n 'Provider Infrastructure Exception|Capability Boundary Export Exception|Provider Test and Example Placement|Manifest Authority Transition|Migration Tombstones and Uninstall Retention' AGENTS.md
```

**Documentation Updates:** `AGENTS.md` is the task deliverable.

**Rollback:** revert the task commit before any Phase 2+ code; after Phase 2 begins, revert all dependent commits first.

**Git Commit:** `docs(architecture): define provider builder rules`

**Re-run safety:** Not safe — anchored policy insertions would duplicate; verify headings are absent before execution.

**Definition of Done:**
- [x] Five exact rules are present once.
- [x] Existing safety text remains.
- [x] No other file changed.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P1-T02` — Freeze architecture policy

**Traces to:** `D-01`, `D-02`, `D-03`, `D-04`, `D-05`, `D-07`, `D-08`, `R-01`, `R-02`, `R-05`, `R-06`, `G1`
**Depends on:** P1-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Add one architecture section defining provider units, contracts, IDs, manifests, lifecycle, composition, readiness, state retention, and removability tiers.

**Context to Read (and nothing else):**
- `docs/ARCHITECTURE.md` — architecture authority.
- `AGENTS.md` — newly approved rules.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Parts I, IV, and V.
- Shared Contracts §3.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `docs/ARCHITECTURE.md` | MODIFY | add canonical spatiotemporal provider architecture |

Anchor: insert before `### Workspace Directory Layout (Target)`. Preserve all existing domain contracts and current-state claims.

**Specification (copy exactly):** heading `## Spatiotemporal Provider Architecture`; child headings `Units`, `Contract Shape`, `Identifiers`, `Manifest`, `Resolution`, `Lifecycle`, `Composition`, `Profiles`, `State Retention`, `Removability Tiers`, and `Frontend Boundary`. Copy the frozen values from §3.

**Behaviour Rules:**
1. Kernel and specs import no business domain.
2. Pure capabilities are frozen callable records; effectful capabilities are Protocols.
3. Core is sync; async is edge-only.
4. Provider selection is explicit and deterministic.
5. Stable API surfaces return `CAPABILITY_UNAVAILABLE`.

**Implementation Steps:**
1. Insert the section at the exact anchor.
2. Define all units and package paths.
3. Add manifest and lifecycle rules.
4. Add readiness and state-retention rules.
5. Add Tier A/B/C table and UI boundary.
6. Cross-reference, but do not duplicate, domain Feature Registries.

**DO NOT:**
- Do not rewrite existing domain sections.
- Do not describe Tier 2 or Tier 3 HMR as implemented.
- Do not move feature authority from README yet.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
P1-T04 adds structural checks. For this task verify the 11 child headings occur once.

**Usage Example**
Run `rg -n '^## Spatiotemporal Provider Architecture$' docs/ARCHITECTURE.md`; one match.

**Quality Gates:**
```powershell
git diff --check
rg -n '^## Spatiotemporal Provider Architecture$|^### (Units|Contract Shape|Identifiers|Manifest|Resolution|Lifecycle|Composition|Profiles|State Retention|Removability Tiers|Frontend Boundary)$' docs/ARCHITECTURE.md
```

**Documentation Updates:** `docs/ARCHITECTURE.md` only.

**Rollback:** revert before reverting P1-T01; later code depends on this contract.

**Git Commit:** `docs(architecture): freeze provider architecture`

**Re-run safety:** Not safe — stop if the top-level heading exists.

**Definition of Done:**
- [x] All frozen contracts are documented.
- [x] Current domain documentation remains intact.
- [x] One file changed.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P1-T03` — Update system relationships

**Traces to:** `R-03`, `R-06`, `G1`
**Depends on:** P1-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Index the three infrastructure packages and composition direction in `docs/PROJECT.md` without duplicating feature registries.

**Context to Read (and nothing else):**
- `docs/PROJECT.md` — system index.
- `docs/ARCHITECTURE.md` — new provider section.
- `AGENTS.md` — documentation ownership.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `docs/PROJECT.md` | MODIFY | index infrastructure and cross-domain direction |

Anchor: the existing system/domain index heading located by exact text before editing. Preserve all domain counts and feature rows.

**Specification (copy exactly):** add rows for `app/kernel/`, `app/capabilities/`, and `app/composition/`, each status `Planned until its gate passes`, owner `System infrastructure`, feature prefix `None`, registry `None`. Add relationship `composition → provider factory → injected capability; business consumer → capability spec; kernel ↛ business domain`.

**Behaviour Rules:**
1. Do not add feature IDs.
2. Do not copy provider lists into PROJECT.
3. Link architecture section by heading text.

**Implementation Steps:**
1. Locate the existing system index anchor.
2. Insert three infrastructure rows.
3. Insert one dependency-direction paragraph.
4. Verify no Feature Registry section was added.

**DO NOT:**
- Do not change feature totals.
- Do not resolve unrelated open decisions.
- Do not add an ADR.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
P1-T04 owns structural tests. Text check expects each infrastructure path once.

**Usage Example**
Run `rg -n 'app/kernel/|app/capabilities/|app/composition/' docs/PROJECT.md`; inspect exactly the inserted index/relationship references.

**Quality Gates:**
```powershell
git diff --check
rg -n 'app/kernel/|app/capabilities/|app/composition/' docs/PROJECT.md
```

**Documentation Updates:** `docs/PROJECT.md` only.

**Git Commit:** `docs(project): index provider infrastructure`

**Re-run safety:** Not safe — stop if all three index rows already exist.

**Definition of Done:**
- [x] Three non-feature packages indexed.
- [x] Dependency direction stated once.
- [x] No registry duplicated.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P1-T04` — Enforce G1 documentation

**Traces to:** `G1`
**Depends on:** P1-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Add a structural test that locks the approved G1 policy before implementation begins.

**Context to Read (and nothing else):**
- `AGENTS.md` — exact policy headings.
- `docs/ARCHITECTURE.md` — exact architecture heading.
- `docs/PROJECT.md` — infrastructure index rows.
- `tests/ui/structural/test_feature_registry.py` — structural-test style only.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/architecture/test_provider_governance.py` | CREATE | assert G1 policy text and non-feature status |

**Specification (copy exactly):** use `Path(__file__).resolve().parents[2]` as repository root. Read UTF-8. Define constants `REQUIRED_AGENT_HEADINGS`, `REQUIRED_ARCHITECTURE_HEADINGS`, and `INFRASTRUCTURE_PATHS`. Test exact occurrence count `== 1`. Assert no `FEAT-KRN`, `FEAT-CAP`, or `FEAT-CMP` text exists in the three documents.

**Behaviour Rules:**
1. Test content, not line numbers.
2. One failing assertion names the missing/duplicated string.
3. Do not scan production packages.

**Implementation Steps:**
1. Create constants with exact headings from P1-T01/P1-T02.
2. Add one test per authoritative document.
3. Add one no-invented-prefix test.
4. Run the complete test file.

**DO NOT:**
- Do not loosen an exact count to `>= 1`.
- Do not alter documentation in this task.
- Do not mark a test xfail.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_provider_governance.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_agents_contains_provider_rules_once` | five headings once |
| `test_architecture_contains_provider_section_once` | section and children once |
| `test_project_indexes_non_feature_infrastructure` | three paths and `None` ownership |
| `test_no_infrastructure_feature_prefix_was_invented` | forbidden prefixes absent |

**Usage Example**
Run the test file; four passes certify G1 documentation.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/architecture/test_provider_governance.py
uv run --locked ruff check tests/architecture/test_provider_governance.py
uv run --locked mypy tests/architecture/test_provider_governance.py
uv run --locked pytest tests/architecture/test_provider_governance.py -q
git diff --check
```

**Documentation Updates:** none; this task verifies P1-T01–P1-T03.

**Rollback:** revert the task commit before any Phase 2+ code; after Phase 2 begins, revert all dependent commits first.

**Git Commit:** `test(architecture): enforce provider governance`

**Re-run safety:** Safe — create-only; stop if file exists.

**Definition of Done:**
- [x] Four tests pass.
- [x] Test uses exact-count assertions.
- [x] No docs changed.
- [x] Commit executed only with separate authorization.

**Phase 1 Exit Gate — all must be true before Phase 2 starts:**
- [x] Every task in this phase is checked off.
- [x] Full lint and type-check clean across repo.
- [x] Full test suite green; coverage remains at least 80%.
- [x] No new failure exists beyond Phase 0 evidence.
- [x] No PROTECTED path appears in the phase diff.
- [x] G1 structural test passes.
- [x] Architecture and project docs contain no second Feature Registry.

### Phase 2 — Five-Graph Audit

**Goal:** produce the complete static, runtime, state, configuration, and frontend coupling inventory used to define every provider migration.
**Why now:** removal boundaries and wave file lists must come from evidence, not folder names.
**Deliverable:** deterministic JSON graphs, cycle report, and provider/domain removability matrices.
**Phase Exit Gate:** G2 classifies every registered feature and explains every dynamic import.

#### - [x] Task `P2-T01` — Extract static dependency graph

**Traces to:** `Phase 2`, `G2`
**Depends on:** P1-T04
**Estimated size:** L (120–200 LOC)

**Goal.** Add an AST scanner for Python imports, lazy export maps, dynamic imports, string module paths, and decorator registrations.

**Context to Read (and nothing else):**
- `app/services/portfolio/__init__.py` — lazy `_EXPORTS` pattern.
- `app/utils/__init__.py` — eager barrel counterexample.
- `app/services/indicators/__init__.py` — large lazy boundary.
- `pyproject.toml` — source roots and Python version.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Phase 2 static graph fields.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_static_graph.py` | CREATE | deterministic Python coupling scanner |
| `tests/architecture/test_provider_static_graph.py` | CREATE | scanner unit tests |
| `docs/dev/plugin-decoupling/audit/static_graph.json` | CREATE | generated current graph |

**Specification (copy exactly):** CLI `python scripts/architecture/provider_static_graph.py --root . --output docs/dev/plugin-decoupling/audit/static_graph.json`. JSON keys: `schema_version` (`1`), `commit`, `nodes`, `edges`, `dynamic_imports`, `lazy_exports`. Every node is a repo-relative POSIX Python path. Every edge has `source`, `target`, `kind`, `lineno`, `type_checking`, and `resolved_symbol`; `kind` is one of `import`, `from_import`, `dynamic_import`, `string_module`, `lazy_export`, `decorator_registration`.

**Behaviour Rules:**
1. Sort nodes and every edge by all serialized fields.
2. Exclude `.git`, `.venv`, caches, generated, vendor, and migrations from AST bodies; include migration module names as state references only in P2-T03.
3. Parse syntax without importing scanned modules.
4. Exit 2 and print `UNEXPLAINED_DYNAMIC_IMPORT: <path>:<line>` for a nonliteral dynamic target.

**Implementation Steps:**
1. Implement AST traversal for the six edge kinds.
2. Track `if TYPE_CHECKING` scope.
3. Decode literal `_EXPORTS` dictionaries.
4. Add deterministic JSON writer.
5. Add CLI validation and exit codes 0/2.
6. Generate the current artifact.

**DO NOT:**
- Do not import application modules.
- Do not infer runtime activation from an import.
- Do not alter scanned files.
- Do not add allowlists in this task.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_provider_static_graph.py` (CREATE)

| Test function | Input | Expected |
|---|---|---|
| `test_extracts_import_kinds` | temporary package with all literal forms | six normalized edge kinds |
| `test_marks_type_checking_edge` | guarded import | `type_checking=true` |
| `test_rejects_dynamic_expression` | `import_module(name)` | exit 2 and exact message |
| `test_output_is_deterministic` | two scans | identical bytes |

**Usage Example**
Run the CLI command; output parses as JSON and contains `app/utils/__init__.py`.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_static_graph.py tests/architecture/test_provider_static_graph.py
uv run --locked ruff check scripts/architecture/provider_static_graph.py tests/architecture/test_provider_static_graph.py
uv run --locked mypy scripts/architecture/provider_static_graph.py tests/architecture/test_provider_static_graph.py
uv run --locked pytest tests/architecture/test_provider_static_graph.py -q
uv run --locked python scripts/architecture/provider_static_graph.py --root . --output docs/dev/plugin-decoupling/audit/static_graph.json
git diff --check
```

**Documentation Updates:** generated static graph only.

**Git Commit:** `build(architecture): extract static provider graph`

**Re-run safety:** Safe — generated JSON is byte-deterministic at the same commit.

**Definition of Done:**
- [x] Four scanner tests pass.
- [x] Current graph generated without importing app.
- [x] Dynamic expressions fail closed.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P2-T02` — Extract runtime configuration graphs

**Traces to:** `Phase 2`, `G2`
**Depends on:** P2-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Extract composition, startup/shutdown, callback, worker, configuration, environment, provider-name, and secret-reference edges.

**Context to Read (and nothing else):**
- `app/services/api/composition/__init__.py` — existing API wiring.
- `app/runtime.py` — profile gate.
- `app/services/brokers/__init__.py` — broker public boundary.
- `app/utils/settings/loader.py` — configuration loading.
- `docs/dev/plugin-decoupling/audit/static_graph.json` — static nodes.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_runtime_graph.py` | CREATE | runtime/config AST extractor |
| `tests/architecture/test_provider_runtime_graph.py` | CREATE | extractor tests |
| `docs/dev/plugin-decoupling/audit/runtime_configuration_graph.json` | CREATE | generated graph |

**Specification (copy exactly):** JSON keys `schema_version`, `commit`, `runtime_edges`, `configuration_edges`, `unexplained`. Runtime kinds: `router_mount`, `startup_hook`, `shutdown_hook`, `subscriber`, `scheduled_job`, `background_task`, `callback`, `factory`, `worker`, `subprocess`. Configuration kinds: `module_path`, `provider_name`, `profile`, `feature_flag`, `environment`, `secret_reference`, `allowlist`.

**Behaviour Rules:**
1. Record repo path and line for every edge.
2. Store secret variable names only, never values.
3. A recognized construction call without a literal owner goes to `unexplained` and causes exit 2.
4. Output ordering is deterministic.

**Implementation Steps:**
1. Implement call/decorator matching for runtime kinds.
2. Implement assignment/call matching for configuration kinds.
3. Add safe redaction of environment values.
4. Add deterministic CLI and tests.
5. Generate the current artifact.

**DO NOT:**
- Do not read `.env` values.
- Do not start FastAPI, brokers, threads, or subprocess workers.
- Do not import app modules.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_provider_runtime_graph.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_extracts_runtime_edges` | ten exact runtime kinds |
| `test_extracts_configuration_edges` | seven exact configuration kinds |
| `test_never_serializes_secret_value` | name present, value absent |
| `test_unresolved_owner_exits_two` | exact unexplained record |

**Usage Example**
Run the CLI; JSON contains `runtime_edges` and `configuration_edges` arrays.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_runtime_graph.py tests/architecture/test_provider_runtime_graph.py
uv run --locked ruff check scripts/architecture/provider_runtime_graph.py tests/architecture/test_provider_runtime_graph.py
uv run --locked mypy scripts/architecture/provider_runtime_graph.py tests/architecture/test_provider_runtime_graph.py
uv run --locked pytest tests/architecture/test_provider_runtime_graph.py -q
uv run --locked python scripts/architecture/provider_runtime_graph.py --root . --output docs/dev/plugin-decoupling/audit/runtime_configuration_graph.json
git diff --check
```

**Documentation Updates:** generated runtime/configuration graph only.

**Git Commit:** `build(architecture): extract runtime configuration graphs`

**Re-run safety:** Safe — deterministic generation.

**Definition of Done:**
- [x] Runtime and config tests pass.
- [x] No secret values are read or written.
- [x] Current artifact has zero unexplained entries or task stops.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P2-T03` — Extract state frontend graphs

**Traces to:** `Phase 2`, `G2`
**Depends on:** P2-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Extract migration/table/class-path coupling and frontend import/route/navigation/client coupling into one deterministic artifact.

**Context to Read (and nothing else):**
- `app/services/data/persistence/migrations.py` — ledger behavior.
- `app/services/data/migrations/core.py` — Data migration aggregation.
- `app/ui/src/app` — Next route root; read filenames only plus matched files.
- `app/ui/src/widgets` — widget root; read filenames only plus matched files.
- `docs/dev/plugin-decoupling/audit/static_graph.json` — Python node vocabulary.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_state_frontend_graph.py` | CREATE | SQL/string/TypeScript extractor |
| `tests/architecture/test_provider_state_frontend_graph.py` | CREATE | extractor tests |
| `docs/dev/plugin-decoupling/audit/state_frontend_graph.json` | CREATE | generated graph |

**Specification (copy exactly):** JSON keys `schema_version`, `commit`, `state_edges`, `frontend_edges`, `serialized_python_paths`, `unexplained`. State kinds: `migration_order`, `table_owner`, `foreign_key`, `shared_writer`, `schema_id`, `class_path`, `cache`, `persisted_registry`, `idempotency`, `audit`. Frontend kinds: `typescript_import`, `dynamic_import`, `next_route`, `navigation`, `widget_registry`, `api_client`, `feature_store`, `backend_assumption`.

**Behaviour Rules:**
1. SQL extraction is static and never opens a database.
2. Serialized values matching `app.<segment>...` are recorded even when no import exists.
3. TS paths use POSIX repo-relative form.
4. Unknown dynamic frontend imports cause exit 2.

**Implementation Steps:**
1. Extract migration declarations and SQL table/FK tokens.
2. Find serialized Python-path literals.
3. Parse TS/TSX import and route constructs without executing Node.
4. Add deterministic writer and tests.
5. Generate current artifact.

**DO NOT:**
- Do not open or mutate SQLite.
- Do not run Next.js.
- Do not infer a table owner when none is declared; put it in `unexplained`.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_provider_state_frontend_graph.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_extracts_state_edges` | ten state kinds normalized |
| `test_finds_serialized_class_path` | literal appears in dedicated array |
| `test_extracts_frontend_edges` | eight frontend kinds normalized |
| `test_output_is_deterministic` | identical bytes |

**Usage Example**
Run the CLI; output lists current Next routes and migration owners.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_state_frontend_graph.py tests/architecture/test_provider_state_frontend_graph.py
uv run --locked ruff check scripts/architecture/provider_state_frontend_graph.py tests/architecture/test_provider_state_frontend_graph.py
uv run --locked mypy scripts/architecture/provider_state_frontend_graph.py tests/architecture/test_provider_state_frontend_graph.py
uv run --locked pytest tests/architecture/test_provider_state_frontend_graph.py -q
uv run --locked python scripts/architecture/provider_state_frontend_graph.py --root . --output docs/dev/plugin-decoupling/audit/state_frontend_graph.json
git diff --check
```

**Documentation Updates:** generated state/frontend graph only.

**Git Commit:** `build(architecture): extract state frontend graphs`

**Re-run safety:** Safe — deterministic generation.

**Definition of Done:**
- [x] Four extractor tests pass.
- [x] No database or frontend runtime starts.
- [x] Current artifact generated.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P2-T04` — Build removability matrices

**Traces to:** `Phase 2`, `G2`
**Depends on:** P2-T02, P2-T03
**Estimated size:** L (120–200 LOC)

**Goal.** Merge the five graphs with README feature registries and emit domain, provider, edge, and cycle matrices.

**Context to Read (and nothing else):**
- `docs/dev/plugin-decoupling/audit/static_graph.json` — static graph.
- `docs/dev/plugin-decoupling/audit/runtime_configuration_graph.json` — runtime/config graph.
- `docs/dev/plugin-decoupling/audit/state_frontend_graph.json` — state/frontend graph.
- `docs/PROJECT.md` — domain index.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — required matrix columns and tiers.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_removability_matrix.py` | CREATE | graph merger/classifier |
| `tests/architecture/test_provider_removability_matrix.py` | CREATE | matrix/cycle tests |
| `docs/dev/plugin-decoupling/audit/removability_matrix.json` | CREATE | canonical G2 machine artifact |

**Specification (copy exactly):** root keys `schema_version`, `commit`, `domains`, `features`, `providers`, `edges`, `cycles`, `dynamic_import_allowlist`. Edge fields: `source`, `target`, `edge_type`, `capability_id`, `required`, `cardinality`, `profile_scope`, `lifecycle_scope`, `security_critical`, `evidence`. Classification values: `protected_kernel_candidate`, `stable_capability_spec`, `required_profile_provider`, `optional_provider`, `composition_only_module`, `compatibility_facade`, `historical_migration_artifact`, `invalid_coupling`. Every provider row also contains all 22 exact fields listed in Phase 12's mandatory materialization contract; values may be empty tuples only when the field is semantically absent, never unknown.

**Behaviour Rules:**
1. No source row is discarded when graphs overlap.
2. Cycles are `hard_code_cycle` or `reactive_event_cycle`.
3. Any missing classification or unexplained dynamic import exits 2.
4. Tier is `A`, `B`, or `C` and follows the source plan.

**Implementation Steps:**
1. Parse the three graph artifacts.
2. Parse canonical README Feature Registry rows without importing packages.
3. Build normalized edges and strongly connected components.
4. Classify only mechanically provable rows; emit unresolved rows as `invalid_coupling`.
5. Add tests and generate matrix.

**DO NOT:**
- Do not silently classify ambiguous ownership as optional.
- Do not collapse a hard cycle into one provider.
- Do not assign new FEAT IDs.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_provider_removability_matrix.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_merges_all_edge_evidence` | no lost source record |
| `test_classifies_hard_cycle` | synchronous cycle is hard |
| `test_classifies_event_cycle` | versioned event cycle is reactive |
| `test_missing_classification_exits_two` | exact failing row |

**Usage Example**
Run the CLI; generated JSON contains 253 unique feature rows matching current registries after EP-01.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_removability_matrix.py tests/architecture/test_provider_removability_matrix.py
uv run --locked ruff check scripts/architecture/provider_removability_matrix.py tests/architecture/test_provider_removability_matrix.py
uv run --locked mypy scripts/architecture/provider_removability_matrix.py tests/architecture/test_provider_removability_matrix.py
uv run --locked pytest tests/architecture/test_provider_removability_matrix.py -q
uv run --locked python scripts/architecture/provider_removability_matrix.py --root . --output docs/dev/plugin-decoupling/audit/removability_matrix.json
git diff --check
```

**Documentation Updates:** generated matrix only.

**Git Commit:** `build(architecture): generate provider removability matrix`

**Re-run safety:** Safe — deterministic generation.

**Definition of Done:**
- [x] All feature rows classified.
- [x] Hard/reactive cycles separated.
- [x] No dynamic import unexplained.
- [x] Commit executed only with separate authorization.

#### - [x] Task `P2-T05` — Freeze G2 classifications

**Traces to:** `G2`, `Stop conditions`
**Depends on:** P2-T04
**Estimated size:** M (50–120 LOC)

**Goal.** Publish the human-readable G2 classification/cycle report and stop if a hard cycle lacks an explicit break edge.

**Context to Read (and nothing else):**
- `docs/dev/plugin-decoupling/audit/removability_matrix.json` — canonical matrix.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — G2 and stop conditions.
- `docs/ARCHITECTURE.md` — ownership and tiers.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `docs/dev/plugin-decoupling/audit/G2_REPORT.md` | CREATE | reviewed classifications and wave inputs |
| `tests/architecture/test_g2_report.py` | CREATE | report/matrix parity |

**Specification (copy exactly):** headings `# G2 Classification Report`, `## Inputs`, `## Domain Matrix`, `## Provider Matrix`, `## Dependency Edges`, `## Hard Cycles`, `## Reactive Event Cycles`, `## Dynamic Import Allowlist`, `## Wave Inputs`, `## Gate Result`. Each hard cycle row contains exactly one `break_edge` and `break_method` from `contract`, `event`, or `ownership_correction`. Gate result is `PASS` only with zero unresolved rows.

**Behaviour Rules:**
1. Tables are sorted by canonical ID.
2. Report counts equal JSON counts.
3. Do not invent provider IDs for ambiguous feature folders; mark gate failed and stop.
4. Wave Inputs records exact ordered provider IDs for each 12.x wave.

**Implementation Steps:**
1. Render counts and sorted tables from matrix.
2. Add one break edge for every hard cycle from reviewed evidence.
3. Add exact provider order for waves 12.1–12.21.
4. Set gate result.
5. Add parity tests.

**DO NOT:**
- Do not continue with a failed G2 gate.
- Do not merge cyclic domains as one component.
- Do not add provider code.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_g2_report.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_report_counts_match_matrix` | all counts equal |
| `test_every_hard_cycle_has_one_break_edge` | no missing or duplicate break |
| `test_every_feature_is_classified` | 253 unique current rows |
| `test_every_wave_has_ordered_inputs` | 21 nonempty/explicit wave rows |

**Usage Example**
Run pytest; four passes are the G2 certification proof.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/architecture/test_g2_report.py
uv run --locked ruff check tests/architecture/test_g2_report.py
uv run --locked mypy tests/architecture/test_g2_report.py
uv run --locked pytest tests/architecture/test_g2_report.py -q
git diff --check
```

**Documentation Updates:** create `G2_REPORT.md`; do not change canonical registries.

**Git Commit:** `docs(architecture): freeze G2 provider classifications`

**Re-run safety:** Not safe — report includes reviewed break decisions; regenerate only through a new approved audit task.

**Definition of Done:**
- [x] Four parity tests pass.
- [x] Gate result is PASS.
- [x] Wave inputs are exact.
- [x] Commit executed only with separate authorization.

**Phase 2 Exit Gate — all must be true before Phase 3 starts:**
- [x] Every task in this phase is checked off.
- [x] Full lint and type-check clean across repo.
- [x] Full test suite green and coverage at least 80%.
- [x] No PROTECTED path appears in the phase diff.
- [x] All five graph categories are present.
- [x] Every registered feature has one classification.
- [x] Every hard cycle has one approved break edge.
- [x] Unexplained dynamic imports are zero.

### Phase 3 — Capability Specification Layer

**Goal:** create provider-neutral contracts importable with zero business providers installed.
**Why now:** the kernel and pilots require stable identifiers and signatures before discovery or activation.
**Deliverable:** infrastructure package plus common, RSI, and Williams v1 specs with import-isolation tests.
**Phase Exit Gate:** G3 consumer imports succeed with `app.services` and `app.agentic` blocked.

#### - [ ] Task `P3-T01` — Create capability package skeleton

**Traces to:** `D-01`, `R-03`, `R-04`, `G3`
**Depends on:** P2-T05
**Estimated size:** S (<50 LOC)

**Goal.** Create empty non-feature namespace packages for the pilot specifications.

**Context to Read (and nothing else):**
- `AGENTS.md` — Provider Infrastructure Exception.
- `docs/ARCHITECTURE.md` — target capability layout.
- Shared Contracts §3.1 and §3.7.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/__init__.py` | CREATE | infrastructure root |
| `app/capabilities/indicator/__init__.py` | CREATE | domain namespace |
| `app/capabilities/indicator/common/__init__.py` | CREATE | capability namespace |

**Specification (copy exactly):** every file has a descriptive module docstring and `__all__: tuple[str, ...] = ()`; no imports.

**Behaviour Rules:**
1. Importing any created package imports no `app.services` or `app.agentic` module.
2. No Feature Registry or README is created.

**Implementation Steps:**
1. Create the three directories/files.
2. Add exact empty `__all__`.
3. Import each in an isolated test command.

**DO NOT:**
- Do not add re-exports.
- Do not add feature IDs or usage files.
- Do not add business types.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
No pytest file in this skeleton task; P3-T05 supplies import enforcement.

**Usage Example**
Run `uv run --locked python -I -c "import app.capabilities; print(app.capabilities.__all__)"` → `()`.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities
uv run --locked ruff check app/capabilities
uv run --locked mypy app/capabilities
uv run --locked python -I -c "import app.capabilities; print(app.capabilities.__all__)"
git diff --check
```

**Documentation Updates:** none; P1 documentation already declares this infrastructure.

**Git Commit:** `feat(capabilities): create specification namespaces`

**Re-run safety:** Safe — create-only; stop if a target exists.

**Definition of Done:**
- [ ] Three packages import.
- [ ] All exports are empty.
- [ ] No business module imported.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P3-T02` — Add indicator common contract

**Traces to:** `R-01`, `R-04`, `G3`
**Depends on:** P3-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Define structural input/config/result protocols so pure indicator specs do not import the Indicators or Data domains.

**Context to Read (and nothing else):**
- `app/services/indicators/core/contracts.py` — existing input/config attributes.
- `app/services/indicators/core/results.py` — existing result attributes.
- `app/services/indicators/momentum/rsi.py` — attributes consumed by RSI.
- `app/services/indicators/momentum/williams_r.py` — attributes consumed by Williams.
- Shared Contracts §3.1.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/indicator/common/v1.py` | CREATE | provider-neutral structural protocols |
| `tests/capabilities/indicator/test_common_v1.py` | CREATE | runtime-checkable conformance fixtures |

**Specification (copy exactly):** define `OHLCVRecordV1`, `MarketDatasetV1`, `IndicatorConfigV1`, and `IndicatorResultV1` as `Protocol` classes with only attributes accessed by the two pilot functions. Use `datetime`, `Decimal`, `Mapping`, `Sequence`, and `pandas.DataFrame/Series` types matching existing declarations. Exact `__all__ = ("IndicatorConfigV1", "IndicatorResultV1", "MarketDatasetV1", "OHLCVRecordV1")`.

**Behaviour Rules:**
1. Protocols contain no constructors or calculation behavior.
2. Existing concrete fixtures satisfy runtime attribute access.
3. Module imports no `app.services` or `app.agentic`.

**Implementation Steps:**
1. Copy only required attribute names/types from existing contracts.
2. Define four protocols in alphabetical order.
3. Add exact exports.
4. Add test-only frozen fixtures and conformance tests.

**DO NOT:**
- Do not move or modify existing domain types.
- Do not use `Any`.
- Do not import a provider/domain.
- Do not add validation behavior.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/capabilities/indicator/test_common_v1.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_common_module_has_exact_exports` | exact four-name tuple |
| `test_common_module_imports_no_business_domain` | blocked imports remain absent |
| `test_fixture_exposes_required_attributes` | all protocol attributes readable |

**Usage Example**
Run pytest; three passes demonstrate provider-free contract use.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities/indicator/common/v1.py tests/capabilities/indicator/test_common_v1.py
uv run --locked ruff check app/capabilities/indicator/common/v1.py tests/capabilities/indicator/test_common_v1.py
uv run --locked mypy app/capabilities/indicator/common/v1.py tests/capabilities/indicator/test_common_v1.py
uv run --locked pytest tests/capabilities/indicator/test_common_v1.py -q
git diff --check
```

**Documentation Updates:** none; shared contract is already frozen in this plan and architecture.

**Git Commit:** `feat(capabilities): add indicator common v1 contract`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Four exact protocols exist.
- [ ] No `Any` or business import exists.
- [ ] Three tests pass.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P3-T03` — Add RSI capability contract

**Traces to:** `R-01`, `R-04`, `G3`, `Phase 9`
**Depends on:** P3-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Define the pure callable-record contract for `indicator.rsi.v1` with the existing function signature unchanged.

**Context to Read (and nothing else):**
- `app/capabilities/indicator/common/v1.py` — shared protocols.
- `app/services/indicators/momentum/rsi.py` — existing signature.
- Shared Contracts §3.6.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/indicator/rsi/__init__.py` | CREATE | empty namespace |
| `app/capabilities/indicator/rsi/v1.py` | CREATE | RSI callable record |
| `tests/capabilities/indicator/test_rsi_v1.py` | CREATE | contract tests |

**Specification (copy exactly):**
```python
CAPABILITY_ID = "indicator.rsi.v1"

class RsiFunctionV1(Protocol):
    def __call__(
        self,
        data: MarketDatasetV1,
        *,
        period: int,
        source: str = "close",
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1: ...

@dataclass(frozen=True, slots=True)
class RsiCapabilityV1:
    calculate: RsiFunctionV1
```
Exact exports: `("CAPABILITY_ID", "RsiCapabilityV1", "RsiFunctionV1")`.

**Behaviour Rules:**
1. Record is frozen and slotted.
2. Default and keyword-only signature match current `rsi`.
3. No provider import occurs.

**Implementation Steps:**
1. Create empty namespace file.
2. Create constant, callable Protocol, and record.
3. Add signature/export/immutability tests.

**DO NOT:**
- Do not implement RSI math.
- Do not validate period.
- Do not import Indicators.
- Do not change existing RSI.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/capabilities/indicator/test_rsi_v1.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_rsi_contract_exports_are_exact` | exact tuple |
| `test_rsi_record_is_frozen` | assignment raises `FrozenInstanceError` |
| `test_rsi_callable_preserves_keywords` | fake records period/source/config |
| `test_rsi_contract_imports_without_services` | import succeeds with blocker |

**Usage Example**
Construct `RsiCapabilityV1(calculate=fake)` in the test and call keyword arguments; no provider is installed.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities/indicator/rsi tests/capabilities/indicator/test_rsi_v1.py
uv run --locked ruff check app/capabilities/indicator/rsi tests/capabilities/indicator/test_rsi_v1.py
uv run --locked mypy app/capabilities/indicator/rsi tests/capabilities/indicator/test_rsi_v1.py
uv run --locked pytest tests/capabilities/indicator/test_rsi_v1.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(capabilities): add RSI v1 contract`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Exact signature and exports exist.
- [ ] Four tests pass.
- [ ] No provider import occurs.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P3-T04` — Add Williams capability contract

**Traces to:** `R-01`, `R-04`, `G3`, `Phase 9`
**Depends on:** P3-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Define the pure callable-record contract for `indicator.williams_r.v1` with the existing function signature unchanged.

**Context to Read (and nothing else):**
- `app/capabilities/indicator/common/v1.py` — shared protocols.
- `app/services/indicators/momentum/williams_r.py` — existing signature.
- Shared Contracts §3.6.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/indicator/williams_r/__init__.py` | CREATE | empty namespace |
| `app/capabilities/indicator/williams_r/v1.py` | CREATE | Williams callable record |
| `tests/capabilities/indicator/test_williams_r_v1.py` | CREATE | contract tests |

**Specification (copy exactly):**
```python
CAPABILITY_ID = "indicator.williams_r.v1"

class WilliamsRFunctionV1(Protocol):
    def __call__(
        self,
        data: MarketDatasetV1,
        *,
        period: int,
        config: IndicatorConfigV1 | None = None,
    ) -> IndicatorResultV1: ...

@dataclass(frozen=True, slots=True)
class WilliamsRCapabilityV1:
    calculate: WilliamsRFunctionV1
```
Exact exports: `("CAPABILITY_ID", "WilliamsRCapabilityV1", "WilliamsRFunctionV1")`.

**Behaviour Rules:**
1. Record is frozen and slotted.
2. Signature matches current `williams_r`.
3. No provider import occurs.

**Implementation Steps:**
1. Create empty namespace.
2. Create constant, Protocol, and record.
3. Add signature/export/immutability/import tests.

**DO NOT:**
- Do not implement Williams math.
- Do not add `source`.
- Do not import Indicators.
- Do not change existing Williams function.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/capabilities/indicator/test_williams_r_v1.py` (CREATE): exact counterparts of P3-T03 tests, with no `source` keyword accepted.

**Usage Example**
Construct the record with a fake callable and call it with period/config.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities/indicator/williams_r tests/capabilities/indicator/test_williams_r_v1.py
uv run --locked ruff check app/capabilities/indicator/williams_r tests/capabilities/indicator/test_williams_r_v1.py
uv run --locked mypy app/capabilities/indicator/williams_r tests/capabilities/indicator/test_williams_r_v1.py
uv run --locked pytest tests/capabilities/indicator/test_williams_r_v1.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(capabilities): add Williams R v1 contract`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Exact signature and exports exist.
- [ ] Tests reject an invented `source` parameter.
- [ ] No provider import occurs.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P3-T05` — Enforce capability import isolation

**Traces to:** `G3`, `Phase 16`
**Depends on:** P3-T03, P3-T04
**Estimated size:** M (50–120 LOC)

**Goal.** Enforce that every capability module imports successfully while all business-domain imports are blocked.

**Context to Read (and nothing else):**
- `app/capabilities/` — files created in Phase 3.
- `tests/removability/harness.py` — fresh-process helper.
- `tests/architecture/test_application_import_smoke.py` — subprocess assertion style.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/architecture/test_capability_import_boundaries.py` | CREATE | AST and fresh-process import ban |

**Specification (copy exactly):** enumerate `app/capabilities/**/*.py` in sorted POSIX order. AST-reject imports whose module starts `app.services` or `app.agentic`. Fresh script installs a `MetaPathFinder` that raises `ImportError("blocked business import: {fullname}")` for those prefixes, then imports every module.

**Behaviour Rules:**
1. Test includes namespace `__init__.py` files.
2. Test asserts no blocked module appears in `sys.modules`.
3. Dynamic import text is rejected by AST when it targets either prefix.

**Implementation Steps:**
1. Add deterministic module enumeration.
2. Add AST import-ban test.
3. Add isolated import-blocker test.
4. Assert exact public exports from §3.7.

**DO NOT:**
- Do not allowlist a capability module.
- Do not import providers before installing blocker.
- Do not modify production.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/architecture/test_capability_import_boundaries.py` (CREATE)

| Test function | Expected |
|---|---|
| `test_capability_specs_have_no_business_imports` | zero forbidden AST edges |
| `test_capability_specs_import_without_business_packages` | subprocess 0 |
| `test_capability_public_exports_are_frozen` | exact §3.7 tuples |

**Usage Example**
Run the test file; three passes certify G3.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/architecture/test_capability_import_boundaries.py
uv run --locked ruff check app/capabilities tests/architecture/test_capability_import_boundaries.py
uv run --locked mypy app/capabilities tests/architecture/test_capability_import_boundaries.py
uv run --locked pytest tests/capabilities tests/architecture/test_capability_import_boundaries.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `test(capabilities): enforce provider-neutral imports`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] All capability tests pass.
- [ ] Business imports blocked statically and dynamically.
- [ ] G3 is satisfied.
- [ ] Commit executed only with separate authorization.

**Phase 3 Exit Gate — all must be true before Phase 4 starts:**
- [ ] Every task in this phase is checked off.
- [ ] Full lint and type-check clean across repo.
- [ ] Full suite green and coverage at least 80%.
- [ ] No PROTECTED path appears in the phase diff.
- [ ] Capability specs import with zero business providers.
- [ ] G3 tests pass.

### Phase 4 — Protected Microkernel

**Goal:** discover and resolve static first-party manifests without importing business providers.
**Why now:** lifecycle and composition require a complete, deterministic resolution report.
**Deliverable:** identifiers, manifest parser, discovery, immutable registry, resolver, states, health, and diagnostics.
**Phase Exit Gate:** G4 imports in a copied tree without `app/services/` and returns an empty business inventory.

#### - [ ] Task `P4-T01` — Add kernel identifiers

**Traces to:** `D-01`, `D-02`, `R-03`, `G4`
**Depends on:** P3-T05
**Estimated size:** L (120–200 LOC)

**Goal.** Create the kernel package, validated IDs/versions, and runtime-profile enum.

**Context to Read (and nothing else):**
- `AGENTS.md` — infrastructure exception.
- `docs/ARCHITECTURE.md` — identifiers and profiles.
- Shared Contracts §3.2, §3.4, §3.7.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/__init__.py` | CREATE | lazy public infrastructure boundary |
| `app/kernel/identifiers.py` | CREATE | CapabilityId, ProviderId, SemanticVersion |
| `app/kernel/profiles.py` | CREATE | RuntimeProfile enum only |
| `tests/kernel/test_identifiers.py` | CREATE | validation/ordering tests |

**Specification (copy exactly):** implement §3.2 identifier classes and §3.4 `RuntimeProfile`. `app/kernel/__init__.py` begins as lazy `_EXPORTS` for only `CapabilityId`, `ProviderId`, `SemanticVersion`, and `RuntimeProfile`; later tasks append frozen names. Regexes are module-private constants.

**Behaviour Rules:**
1. Reject uppercase, hyphen, empty, zero capability major, and malformed versions with exact §3.2 messages.
2. String conversion round-trips.
3. Dataclass ordering is lexical/numeric field order.
4. Importing kernel imports no business domain.

**Implementation Steps:**
1. Create three frozen slotted dataclasses and parsers.
2. Create four-value `RuntimeProfile`.
3. Add lazy root exports and `__dir__` matching Indicators style.
4. Add valid/invalid/round-trip/order tests.

**DO NOT:**
- Do not use Pydantic.
- Do not import capabilities or business packages.
- Do not accept compatibility aliases.
- Do not add provider selection.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_identifiers.py` (CREATE): `test_valid_identifiers_round_trip`, `test_invalid_capability_ids`, `test_invalid_provider_ids`, `test_invalid_semantic_versions`, `test_identifiers_are_orderable`, `test_runtime_profiles_are_exact`.

**Usage Example**
`CapabilityId.parse("indicator.rsi.v1")` stringifies to the same text.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel tests/kernel/test_identifiers.py
uv run --locked ruff check app/kernel tests/kernel/test_identifiers.py
uv run --locked mypy app/kernel tests/kernel/test_identifiers.py
uv run --locked pytest tests/kernel/test_identifiers.py -q
git diff --check
```

**Documentation Updates:** none; frozen in architecture.

**Git Commit:** `feat(kernel): add validated provider identifiers`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Six tests pass.
- [ ] Exact error messages match §3.2.
- [ ] Kernel import is business-neutral.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P4-T02` — Parse provider manifests

**Traces to:** `R-05`, `D-03`, `D-04`, `D-07`, `D-08`, `G4`
**Depends on:** P4-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Parse strict `manifest.toml` files into immutable values without importing entry points.

**Context to Read (and nothing else):**
- `app/kernel/identifiers.py` — IDs and versions.
- `app/kernel/profiles.py` — profile enum.
- Shared Contracts §3.2–§3.3.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — manifest requirements.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/errors.py` | CREATE | base kernel exceptions and manifest error |
| `app/kernel/manifests.py` | CREATE | strict TOML values/parser |
| `tests/kernel/test_manifests.py` | CREATE | parser tests |

**Specification (copy exactly):** implement all §3.2 enums/dataclasses and `load_manifest`. `ManifestValidationError` text is `invalid provider manifest {path}: {reason}`. Reasons are exact: `unknown key {key!r}`, `missing key {key!r}`, `duplicate provided capability {id}`, `duplicate required capability {id}`, `entry_point must be '<module>:<factory>'`, and `state fields must be all present or all absent`.

**Behaviour Rules:**
1. Parse with `tomllib.loads(path.read_text(encoding="utf-8"))`.
2. Reject unknown keys at every table level.
3. Normalize profile/scope/major lists to sorted unique tuples.
4. Default `on_missing` to fail_closed and purge authorization to false only for stateless manifests.
5. Never import entry-point modules.

**Implementation Steps:**
1. Add exceptions.
2. Add enums and immutable manifest records.
3. Validate exact TOML table/key sets.
4. Parse and normalize all values.
5. Add happy-path and one test per exact error reason.
6. Add lazy root exports for manifest values/parser/error.

**DO NOT:**
- Do not use a TOML dependency.
- Do not accept entry points from `site-packages`.
- Do not read provider config values.
- Do not import an entry point.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_manifests.py` (CREATE): valid stateless/stateful, unknown key, missing key, duplicate provides/requires, malformed entry, partial state, no-import sentinel.

**Usage Example**
Load a temporary RSI manifest and assert provider ID `indicator.rsi.default`.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel tests/kernel/test_manifests.py
uv run --locked ruff check app/kernel tests/kernel/test_manifests.py
uv run --locked mypy app/kernel tests/kernel/test_manifests.py
uv run --locked pytest tests/kernel/test_manifests.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): parse static provider manifests`

**Re-run safety:** Safe — files are additive; root export anchors must match.

**Definition of Done:**
- [ ] Strict parser tests pass.
- [ ] Unknown fields fail closed.
- [ ] Entry points remain unimported.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P4-T03` — Discover first-party manifests

**Traces to:** `D-01`, `R-05`, `G4`
**Depends on:** P4-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Discover sorted first-party `manifest.toml` paths under an explicit root and load each exactly once.

**Context to Read (and nothing else):**
- `app/kernel/manifests.py` — parser.
- `app/kernel/errors.py` — error base.
- `docs/dev/plugin-decoupling/audit/G2_REPORT.md` — approved first-party roots.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/discovery.py` | CREATE | static filesystem discovery |
| `tests/kernel/test_discovery.py` | CREATE | root/path/no-import tests |

**Specification (copy exactly):**
```python
@dataclass(frozen=True, slots=True)
class DiscoveredProvider:
    manifest_path: Path
    manifest: ProviderManifest

def discover_manifests(root: Path) -> tuple[DiscoveredProvider, ...]: ...
```
Resolve root once. Accept only files named `manifest.toml` whose resolved path is inside root and whose relative path has no hidden segment or `__pycache__`. Duplicate provider IDs raise `ManifestValidationError` reason `duplicate provider id {id}`.

**Behaviour Rules:**
1. Empty root returns `()`.
2. Symlink escape raises `ManifestValidationError` reason `manifest escapes discovery root`.
3. Results sort by provider ID string, then path.
4. No Python provider module imports.

**Implementation Steps:**
1. Walk with `Path.rglob("manifest.toml")`.
2. Resolve and validate every candidate.
3. Parse and reject duplicate IDs.
4. Return sorted tuple.
5. Add root export and tests.

**DO NOT:**
- Do not scan `site-packages` or entry points.
- Do not follow escaped symlinks.
- Do not import plugin modules.
- Do not use current working directory implicitly.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_discovery.py` (CREATE): empty, sorted, hidden excluded, duplicate rejected, symlink escape rejected when supported, no-import sentinel.

**Usage Example**
Discover a temporary two-manifest root and print sorted provider IDs.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/discovery.py tests/kernel/test_discovery.py
uv run --locked ruff check app/kernel/discovery.py tests/kernel/test_discovery.py
uv run --locked mypy app/kernel/discovery.py tests/kernel/test_discovery.py
uv run --locked pytest tests/kernel/test_discovery.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): discover first-party provider manifests`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Discovery is deterministic.
- [ ] Escapes and duplicates fail closed.
- [ ] No provider imports occur.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P4-T04` — Register provider inventory

**Traces to:** `D-01`, `D-03`, `G4`
**Depends on:** P4-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Build an immutable inventory indexed by provider and capability without selecting or activating providers.

**Context to Read (and nothing else):**
- `app/kernel/discovery.py` — discovered records.
- `app/kernel/manifests.py` — manifest types.
- `app/kernel/identifiers.py` — key types.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/registry.py` | CREATE | immutable inventory |
| `tests/kernel/test_registry.py` | CREATE | index/order tests |

**Specification (copy exactly):**
```python
@dataclass(frozen=True, slots=True)
class ProviderInventory:
    providers: tuple[ProviderManifest, ...]
    by_provider: Mapping[ProviderId, ProviderManifest]
    by_capability: Mapping[CapabilityId, tuple[ProviderManifest, ...]]

def build_inventory(
    discovered: tuple[DiscoveredProvider, ...],
) -> ProviderInventory: ...
```
Wrap dictionaries in `MappingProxyType`. Provider/capability tuples sort by provider ID.

**Behaviour Rules:**
1. Empty input produces empty immutable indexes.
2. Duplicate provider ID raises `ResolutionError("duplicate provider id: {id}")`.
3. Registry performs no selection and imports no entry points.

**Implementation Steps:**
1. Build provider dictionary with duplicate check.
2. Build capability multimap.
3. Freeze maps and sorted tuples.
4. Add root exports and tests.

**DO NOT:**
- Do not store mutable lists.
- Do not assign priority.
- Do not activate providers.
- Do not add a global singleton.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_registry.py` (CREATE): empty, sorted indexes, immutable maps, duplicate rejection, multiple providers retained.

**Usage Example**
Build an inventory with RSI/Williams manifests and query capability tuples.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/registry.py tests/kernel/test_registry.py
uv run --locked ruff check app/kernel/registry.py tests/kernel/test_registry.py
uv run --locked mypy app/kernel/registry.py tests/kernel/test_registry.py
uv run --locked pytest tests/kernel/test_registry.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): index immutable provider inventory`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Inventory maps are immutable.
- [ ] Cardinality is not resolved prematurely.
- [ ] Five tests pass.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P4-T05` — Resolve provider graph

**Traces to:** `D-02`, `D-03`, `D-04`, `D-05`, `G4`
**Depends on:** P4-T04
**Estimated size:** L (120–200 LOC)

**Goal.** Resolve enabled first-party manifests into bindings, inactive capabilities, and deterministic activation/deactivation order.

**Context to Read (and nothing else):**
- `app/kernel/registry.py` — inventory.
- `app/kernel/manifests.py` — cardinality/missing policies.
- `app/kernel/errors.py` — errors.
- Shared Contracts §3.3.
- `docs/dev/plugin-decoupling/audit/G2_REPORT.md` — approved cycle breaks.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/resolver.py` | CREATE | deterministic resolution |
| `tests/kernel/test_resolver.py` | CREATE | cardinality/version/cycle tests |

**Specification (copy exactly):** implement §3.3 records/signature. Supported majors must explicitly contain the provided capability major. Required `fail_closed` loss makes consumer inactive; `degrade` keeps it active with inactive dependency evidence; `skip` omits the consumer. Ambiguity creates `PROVIDER_AMBIGUOUS`; no silent choice.

**Behaviour Rules:**
1. Disabled manifests are treated as `DISABLED`, absent as `NOT_INSTALLED`.
2. Selected provider must be enabled and provide the selected capability.
3. Topological ties sort by provider ID.
4. Deactivation order is exact reverse activation order.
5. Hard cycles raise `ResolutionError("hard dependency cycle: {id1} -> ... -> {id1}")`.

**Implementation Steps:**
1. Filter enabled provider IDs.
2. Match explicit selection and cardinality.
3. Validate supported majors.
4. Propagate missing policies transitively.
5. Detect hard cycles and topologically sort.
6. Return frozen report.
7. Add root export and tests.

**DO NOT:**
- Do not use discovery/import order.
- Do not select the first ambiguous provider.
- Do not activate code.
- Do not hide transitive chains.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_resolver.py` (CREATE): empty, exactly-one, many, explicit one-of-several, ambiguous, version incompatible, three missing policies, transitive chain, hard cycle, deterministic order.

**Usage Example**
Resolve RSI enabled/Williams disabled; RSI binds and Williams reports disabled.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/resolver.py tests/kernel/test_resolver.py
uv run --locked ruff check app/kernel/resolver.py tests/kernel/test_resolver.py
uv run --locked mypy app/kernel/resolver.py tests/kernel/test_resolver.py
uv run --locked pytest tests/kernel/test_resolver.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): resolve provider dependency graph`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] All cardinalities and policies tested.
- [ ] No ambiguity fallback exists.
- [ ] Dependency chains are complete.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P4-T06` — Project kernel diagnostics

**Traces to:** `D-01`, `G4`
**Depends on:** P4-T05
**Estimated size:** L (120–200 LOC)

**Goal.** Add component states, bounded kernel health, and JSON-safe resolution diagnostics without business imports.

**Context to Read (and nothing else):**
- `app/kernel/resolver.py` — report values.
- `app/kernel/errors.py` — error values.
- Shared Contracts §3.3–§3.4.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/states.py` | CREATE | exact component state enum |
| `app/kernel/health.py` | CREATE | KernelHealth projection |
| `app/kernel/diagnostics.py` | CREATE | bounded JSON-safe report |
| `tests/kernel/test_diagnostics.py` | CREATE | state/health/redaction tests |

**Specification (copy exactly):** implement §3.3 `ComponentState` and §3.4 `KernelHealth`. Add `def project_diagnostics(report: ResolutionReport, *, maximum_items: int = 1000) -> Mapping[str, object]`. Reject maximum below 1 with `ValueError("maximum_items must be >= 1")`. Output keys `kernel`, `bindings`, `inactive`, `truncated`; sorted by canonical ID.

**Behaviour Rules:**
1. Empty report yields live/ready true and counts zero.
2. Kernel readiness means resolver completed, not profile readiness.
3. Limit applies to bindings plus inactive items.
4. Diagnostics never include config contents or secret values.

**Implementation Steps:**
1. Add exact state enum.
2. Add health constructor from report.
3. Add bounded diagnostic serializer.
4. Complete root exports to §3.7 Phase 4 names.
5. Add tests.

**DO NOT:**
- Do not collapse provider health and profile readiness.
- Do not log full manifests.
- Do not import business domains.
- Do not add HTTP behavior.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_diagnostics.py` (CREATE): exact states, empty health, inactive not kernel-dead, sorting, truncation, invalid bound, secret absence.

**Usage Example**
Project an empty resolution report and obtain JSON-serializable health.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel tests/kernel/test_diagnostics.py
uv run --locked ruff check app/kernel tests/kernel/test_diagnostics.py
uv run --locked mypy app/kernel tests/kernel/test_diagnostics.py
uv run --locked pytest tests/kernel -q
uv run --locked python -I -c "import app.kernel; print(app.kernel.discover_manifests(__import__('pathlib').Path('app/services-missing')))"
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): expose bounded provider diagnostics`

**Re-run safety:** Safe — additive and anchored exports.

**Definition of Done:**
- [ ] Kernel tests pass.
- [ ] Missing services root returns empty tuple.
- [ ] Diagnostics contain no configuration payload.
- [ ] G4 is satisfied.

**Phase 4 Exit Gate — all must be true before Phase 5 starts:**
- [ ] Every task in this phase is checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] Kernel LOC for identifiers through diagnostics is at most 600 excluding docstrings/tests.
- [ ] Kernel imports no business domain.
- [ ] Copied-tree import with `app/services/` absent succeeds.
- [ ] G4 tests pass.

### Phase 5 — Lifecycle and Effect Ownership

**Goal:** own every reversible resource and transition components deterministically through activation and teardown.
**Why now:** effectful providers cannot migrate until partial startup and cleanup are safe.
**Deliverable:** sync effect scope, transition machine, lifecycle coordinator, and async edge adapter.
**Phase Exit Gate:** G5 returns tasks/listeners/timers/mock clients to zero with no resource warning.

#### - [ ] Task `P5-T01` — Own synchronous effects

**Traces to:** `D-07`, `D-08`, `R-02`, `G5`
**Depends on:** P4-T06
**Estimated size:** L (120–200 LOC)

**Goal.** Implement a synchronous reverse-order effect scope with refusal, idempotent close, and cleanup-failure evidence.

**Context to Read (and nothing else):**
- `app/kernel/errors.py` — LifecycleError.
- Shared Contracts §3.5.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Phase 5 and effect classes.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/effects.py` | CREATE | ExitStack-backed scope |
| `tests/kernel/test_effects.py` | CREATE | order/idempotency/failure tests |

**Specification (copy exactly):** implement §3.5 `EffectScope`; constructor `def __init__(self, *, can_dispose: Callable[[], bool] | None = None) -> None`. `close()` refusal raises `LifecycleError("effect scope refused disposal")`. Cleanup failures raise `LifecycleError("effect scope cleanup failed: {count} disposer(s)")` after attempting every disposer in reverse order; preserve causes in attribute `failures: tuple[BaseException, ...]`.

**Behaviour Rules:**
1. Callback registration after close raises `LifecycleError("effect scope is closed")`.
2. Close twice is a no-op after successful close.
3. Refusal leaves scope open and calls no disposer.
4. Never execute financially compensating behavior automatically.

**Implementation Steps:**
1. Wrap `ExitStack` and private disposer ledger.
2. Implement callback/context registration.
3. Implement refusal and reverse cleanup.
4. Aggregate failures without skipping later disposers.
5. Add root export and tests.

**DO NOT:**
- Do not add async methods.
- Do not force cleanup after refusal.
- Do not swallow disposer failures.
- Do not add trade-specific logic.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_effects.py` (CREATE): reverse order, context exit, double close, register-after-close, refusal, all failures attempted, no compensation sentinel.

**Usage Example**
Register three append callbacks and close; observed order is `3,2,1`.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/effects.py tests/kernel/test_effects.py
uv run --locked ruff check app/kernel/effects.py tests/kernel/test_effects.py
uv run --locked mypy app/kernel/effects.py tests/kernel/test_effects.py
uv run --locked pytest tests/kernel/test_effects.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): own synchronous provider effects`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Reverse order and refusal proven.
- [ ] All cleanup failures retained.
- [ ] No async/business code added.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P5-T02` — Enforce component transitions

**Traces to:** `Phase 5`, `D-08`, `G5`
**Depends on:** P5-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Define the only legal component-state transitions and reject all others with one exact error.

**Context to Read (and nothing else):**
- `app/kernel/states.py` — exact enum.
- `app/kernel/errors.py` — LifecycleError.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — state sequence.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/states.py` | MODIFY | add transition table and function |
| `tests/kernel/test_states.py` | CREATE | exhaustive transition matrix |

Anchor: existing `ComponentState` enum; preserve every name/value.

**Specification (copy exactly):** `def transition_component(current: ComponentState, target: ComponentState) -> ComponentState`. Allowed main paths: discovered→disabled/resolving; disabled→resolving/stopped; resolving→waiting/starting/failed/version_incompatible; waiting→starting/failed; starting→active/degraded/failed/failed_cleanup; active↔degraded; active/degraded→draining; draining→stopping/failed; stopping→stopped/failed_cleanup; failed→stopping/quarantined; failed_cleanup→quarantined; version_incompatible→disabled; stopped→resolving. Same-state transition returns current. Other transitions raise `LifecycleError("invalid component transition: {current} -> {target}")`.

**Behaviour Rules:** exhaustive Cartesian test over all enum pairs; terminal `QUARANTINED` only self-transitions.

**Implementation Steps:**
1. Add immutable transition mapping.
2. Implement exact function.
3. Export function lazily.
4. Add exhaustive tests.

**DO NOT:**
- Do not remove states.
- Do not auto-skip intermediate states.
- Do not log pure transitions.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_states.py` (CREATE): allowed table, every forbidden pair, same-state, quarantined terminal.

**Usage Example**
Transition `DISCOVERED` to `RESOLVING` returns `RESOLVING`.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/states.py tests/kernel/test_states.py
uv run --locked ruff check app/kernel/states.py tests/kernel/test_states.py
uv run --locked mypy app/kernel/states.py tests/kernel/test_states.py
uv run --locked pytest tests/kernel/test_states.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): enforce component state transitions`

**Re-run safety:** Safe when exact enum anchor matches.

**Definition of Done:**
- [ ] Cartesian transition test passes.
- [ ] Error text exact.
- [ ] Enum unchanged.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P5-T03` — Coordinate component lifecycle

**Traces to:** `D-05`, `D-08`, `R-02`, `G5`
**Depends on:** P5-T02
**Estimated size:** L (120–200 LOC)

**Goal.** Activate and deactivate one provider generation with typed construction dependencies and complete partial-startup cleanup.

**Context to Read (and nothing else):**
- `app/kernel/effects.py` — resource owner.
- `app/kernel/states.py` — transition function.
- `app/kernel/manifests.py` — provider metadata.
- `app/kernel/resolver.py` — resolved dependencies.
- Shared Contracts §3.5.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/lifecycle.py` | CREATE | sync activation/deactivation |
| `tests/kernel/test_lifecycle.py` | CREATE | partial allocation/drain tests |

**Specification (copy exactly):**
```python
def activate_component(
    *, manifest: ProviderManifest, factory: ProviderFactory,
    dependencies: Mapping[CapabilityId, object],
    config: Mapping[str, object], scope: EffectScope,
) -> ActiveComponent: ...

def deactivate_component(
    component: ActiveComponent, *, timeout_seconds: float
) -> None: ...
```
Generate UUID with `uuid4`; timeout must be positive or raise `ValueError("timeout_seconds must be > 0")`. Factory failure closes scope and raises `LifecycleError("provider activation failed: {provider_id}")`. Cleanup failure sets state `FAILED_CLEANUP` in mutable internal controller evidence and raises the scope error.

**Behaviour Rules:**
1. Dependencies are passed once at construction; no registry lookup.
2. Failure before/after partial allocation closes all registered resources.
3. Deactivation transitions draining→stopping→stopped.
4. Double deactivation is idempotent for stopped components.
5. No admission occurs after draining begins.

**Implementation Steps:**
1. Define factory Protocol and frozen public component snapshot.
2. Add private controller for mutable state/admission count.
3. Implement activation sequence and cleanup-on-failure.
4. Implement drain/timeout/deactivation.
5. Add root exports and lifecycle tests.

**DO NOT:**
- Do not use async or threads.
- Do not call a global registry from factory code.
- Do not compensate irreversible effects.
- Do not force disposal after `can_dispose` refusal.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_lifecycle.py` (CREATE): success, failure before allocation, failure after partial allocation, double shutdown, reverse cleanup, timeout, refusal, upstream loss, admission while draining.

**Usage Example**
Activate a fake provider owning four counters, deactivate, and assert all counters zero.

**Logging**
- Logger: `from app.utils import logger` is prohibited because kernel must remain import-neutral. Accept an optional callback? No: kernel emits structured state only; composition logs it later.
- Never include config values in error text.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/lifecycle.py tests/kernel/test_lifecycle.py
uv run --locked ruff check app/kernel/lifecycle.py tests/kernel/test_lifecycle.py
uv run --locked mypy app/kernel/lifecycle.py tests/kernel/test_lifecycle.py
uv run --locked pytest tests/kernel/test_lifecycle.py -q -W error::ResourceWarning -W error::RuntimeWarning
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): coordinate provider lifecycle`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Nine lifecycle tests pass.
- [ ] Partial-startup resources return to zero.
- [ ] No warning leaks.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P5-T04` — Adapt asynchronous edges

**Traces to:** `R-02`, `G5`
**Depends on:** P5-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Add an async adapter that owns async resources while retaining one synchronous kernel scope.

**Context to Read (and nothing else):**
- `app/kernel/effects.py` — sync scope.
- `app/kernel/lifecycle.py` — lifecycle ownership.
- Shared Contracts §3.5.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/async_effects.py` | CREATE | edge-only AsyncExitStack adapter |
| `tests/kernel/test_async_effects.py` | CREATE | coroutine cleanup tests |

**Specification (copy exactly):** implement §3.5 `AsyncEffectScopeAdapter`. Constructor rejects a closed sync scope with `LifecycleError("cannot adapt a closed effect scope")`. `aclose()` first closes async stack, then sync scope. Aggregate failures in encounter order and raise `LifecycleError("async effect scope cleanup failed: {count} failure(s)")`.

**Behaviour Rules:**
1. Async close is idempotent after success.
2. Genuine `async def` fixtures are used.
3. Async cleanup precedes sync cleanup.
4. No event loop is created by production code.

**Implementation Steps:**
1. Wrap `AsyncExitStack` and sync scope.
2. Implement async context entry and sync callback delegation.
3. Implement ordered aggregate close.
4. Add lazy root export and tests.

**DO NOT:**
- Do not convert kernel resolver/lifecycle to async.
- Do not call `asyncio.run` in production.
- Do not use AsyncMock returning non-coroutines.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_async_effects.py` (CREATE): closed constructor, order, double close, partial async failure, genuine coroutine, zero RuntimeWarning.

**Usage Example**
Enter a fake async client, register a sync callback, call `aclose`, and observe async then sync cleanup.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/async_effects.py tests/kernel/test_async_effects.py
uv run --locked ruff check app/kernel/async_effects.py tests/kernel/test_async_effects.py
uv run --locked mypy app/kernel/async_effects.py tests/kernel/test_async_effects.py
uv run --locked pytest tests/kernel/test_async_effects.py tests/kernel/test_lifecycle.py -q -W error::ResourceWarning -W error::RuntimeWarning
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): adapt asynchronous provider edges`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Async/sync order proven.
- [ ] No RuntimeWarning.
- [ ] Core remains synchronous.
- [ ] G5 resource counts reach zero.

**Phase 5 Exit Gate — all must be true before Phase 6 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] No PROTECTED path appears in phase diff.
- [ ] Partial activation cleanup reaches zero resources.
- [ ] No ResourceWarning or RuntimeWarning.
- [ ] G5 passes.

### Phase 6 — Composition, Injection, Generations

**Goal:** activate selected providers through construction-time injection and replace installed-provider configuration transactionally.
**Why now:** resolver output and lifecycle ownership are complete.
**Deliverable:** generation records, leases, composition runtime, and Tier-1 configuration reconciliation.
**Phase Exit Gate:** G6 switches a consumer to a new generation without retaining a stale instance.

#### - [ ] Task `P6-T01` — Define provider generations

**Traces to:** `Phase 6`, `G6`
**Depends on:** P5-T04
**Estimated size:** L (120–200 LOC)

**Goal.** Create composition infrastructure and immutable generation, lease, and pinned-graph values.

**Context to Read (and nothing else):**
- `app/kernel/identifiers.py` — ID/version types.
- `app/kernel/lifecycle.py` — active component.
- Shared Contracts §3.5 and §3.7.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/__init__.py` | CREATE | lazy infrastructure boundary |
| `app/composition/generations.py` | CREATE | generation/lease/pin values |
| `tests/composition/test_generations.py` | CREATE | immutability/digest/pinning tests |

**Specification (copy exactly):** implement §3.5 generation values plus `def configuration_digest(config: Mapping[str, object]) -> str`. `ProviderGeneration.activated_at` must be timezone-aware UTC or raise `ValueError("activated_at must be timezone-aware UTC")`. Dependency generation IDs sort by UUID hex. Pinned graph rejects duplicate provider IDs with `ValueError("duplicate pinned provider: {id}")`.

**Behaviour Rules:**
1. Canonical digest is stable across mapping insertion order.
2. Lease is frozen and contains direct typed value.
3. Pinned graph returns the same generation set for its lifetime.
4. No config secrets are persisted; only caller-provided secret references.

**Implementation Steps:**
1. Create lazy composition root.
2. Implement canonical JSON digest.
3. Implement three frozen values and validation.
4. Add exact root exports available in this phase.
5. Add tests.

**DO NOT:**
- Do not add global active generation.
- Do not inspect object internals for secrets.
- Do not mutate a lease.
- Do not import business domains.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/composition/test_generations.py` (CREATE): digest stability, timezone rejection, sorted dependencies, frozen lease, duplicate pin rejection, stable pin.

**Usage Example**
Create two generations and pin them for a fake simulation run.

**Quality Gates:**
```powershell
uv run --locked ruff format app/composition tests/composition/test_generations.py
uv run --locked ruff check app/composition tests/composition/test_generations.py
uv run --locked mypy app/composition tests/composition/test_generations.py
uv run --locked pytest tests/composition/test_generations.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(composition): define provider generations`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Generation and lease values frozen.
- [ ] Digest deterministic.
- [ ] Pinning tests pass.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P6-T02` — Compose injected providers

**Traces to:** `D-05`, `D-10`, `Phase 6`, `G6`
**Depends on:** P6-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Activate a complete resolution report, inject direct dependencies, publish atomic leases, and drain in reverse order.

**Context to Read (and nothing else):**
- `app/kernel/resolver.py` — activation order/bindings.
- `app/kernel/lifecycle.py` — activation API.
- `app/composition/generations.py` — public values.
- `app/kernel/discovery.py` — manifest paths.
- Shared Contracts §3.5.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/runtime.py` | CREATE | composition runtime |
| `tests/composition/test_runtime.py` | CREATE | injection/lease/rollback tests |

**Specification (copy exactly):**
```python
class CompositionRuntime:
    def activate(
        self, report: ResolutionReport, *,
        factories: Mapping[ProviderId, ProviderFactory],
        configs: Mapping[ProviderId, Mapping[str, object]],
    ) -> tuple[ProviderGeneration, ...]: ...
    def lease(self, capability_id: CapabilityId) -> CapabilityLease[object]: ...
    def deactivate_all(self, *, timeout_seconds: float) -> None: ...
    def pin_graph(self) -> PinnedCapabilityGraph: ...
```
Constructor `def __init__(self) -> None`. Missing factory raises `LifecycleError("missing provider factory: {id}")`. Missing/inactive lease raises `CapabilityUnavailableError` reason `NOT_INSTALLED`. Activation failure deactivates all candidate components and leaves incumbent bindings unchanged.

**Behaviour Rules:**
1. Build dependency mapping from already activated direct instances.
2. Never expose a partially activated candidate graph.
3. Lease switch is one locked mapping assignment; use `threading.RLock` only for this atomic state boundary.
4. Existing lease value remains valid for in-flight caller; new lease uses new generation.
5. Business code receives no registry.

**Implementation Steps:**
1. Add private candidate maps.
2. Activate in report order with injected dependencies.
3. Build generations/digests.
4. Atomically replace active maps after full success.
5. Drain old components in reverse order.
6. Add lease/pin/deactivate methods and tests.

**DO NOT:**
- Do not expose `registry.get`.
- Do not mutate existing generation objects.
- Do not publish partial candidates.
- Do not create background threads.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/composition/test_runtime.py` (CREATE): dependency injection, ordered activation, partial failure rollback, lease switch, old lease stability, reverse shutdown, missing factory, inactive lease.

**Usage Example**
Activate fake producer/consumer; consumer receives producer object during construction.

**Logging**
- Import `logger` from `app.utils` in composition only.
- INFO messages: `Activating provider generation %s` and `Deactivating provider generation %s` with provider ID only.
- Never log configs, credentials, or object representations.

**Quality Gates:**
```powershell
uv run --locked ruff format app/composition/runtime.py tests/composition/test_runtime.py
uv run --locked ruff check app/composition/runtime.py tests/composition/test_runtime.py
uv run --locked mypy app/composition/runtime.py tests/composition/test_runtime.py
uv run --locked pytest tests/composition/test_runtime.py -q -W error::ResourceWarning -W error::RuntimeWarning
git diff --check
```

**Documentation Updates:** none.

**Rollback:** deactivate all components before reverting; verify runtime test leaves resource counters zero.

**Git Commit:** `feat(composition): activate injected provider graph`

**Re-run safety:** Safe — additive.

**Definition of Done:**
- [ ] Direct injection proven.
- [ ] Candidate failure preserves incumbent.
- [ ] Old/new lease behavior proven.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P6-T03` — Reconcile installed configuration

**Traces to:** `Phase 6`, `Phase 17`, `D-13`, `G6`
**Depends on:** P6-T02
**Estimated size:** L (120–200 LOC)

**Goal.** Compute and apply provider enable/selection/config changes among already discovered providers only.

**Context to Read (and nothing else):**
- `app/composition/runtime.py` — active runtime.
- `app/kernel/resolver.py` — deterministic resolution.
- `app/kernel/registry.py` — installed inventory.
- `app/composition/generations.py` — digests.
- §7 CF-06 — initial-scope boundary.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/reconciliation.py` | CREATE | config diff/apply/rollback |
| `tests/composition/test_reconciliation.py` | CREATE | affected-set and rollback tests |

**Specification (copy exactly):**
```python
@dataclass(frozen=True, slots=True)
class ProviderConfiguration:
    enabled_provider_ids: frozenset[ProviderId]
    selected_provider_ids: Mapping[CapabilityId, ProviderId]
    provider_configs: Mapping[ProviderId, Mapping[str, object]]

@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    changed_provider_ids: tuple[ProviderId, ...]
    activated_generation_ids: tuple[UUID, ...]
    rolled_back: bool

def reconcile_configuration(
    runtime: CompositionRuntime, inventory: ProviderInventory,
    current: ProviderConfiguration, candidate: ProviderConfiguration,
    *, factories: Mapping[ProviderId, ProviderFactory],
) -> ReconciliationResult: ...
```
Unknown provider ID raises `ManifestValidationError` reason `provider is not installed: {id}` before deactivation.

**Behaviour Rules:**
1. Affected set includes changed providers and transitive dependents.
2. Deactivate affected incumbents in reverse dependency order; activate candidate in forward order.
3. Candidate failure restores the exact incumbent binding/generation IDs and returns `rolled_back=True` only after successful restoration.
4. No source discovery/reload occurs.

**Implementation Steps:**
1. Freeze config/result values.
2. Validate candidate IDs against inventory.
3. Compute changed/affected set using resolver edges.
4. Apply candidate through shadow activation.
5. Restore incumbent on failure.
6. Export and test.

**DO NOT:**
- Do not call importlib reload.
- Do not discover new files.
- Do not replace live broker source code.
- Do not continue after failed rollback.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/composition/test_reconciliation.py` (CREATE): no-op, enable, disable, selection switch, config digest change, transitive dependent, candidate fail rollback, unknown provider.

**Usage Example**
Switch between two installed fake providers and assert a new lease generation.

**Logging**
- INFO `Reconciling %d affected provider(s)`.
- ERROR `Provider reconciliation failed; restoring incumbent graph`.
- Never log provider config contents.

**Quality Gates:**
```powershell
uv run --locked ruff format app/composition/reconciliation.py tests/composition/test_reconciliation.py
uv run --locked ruff check app/composition tests/composition/test_reconciliation.py
uv run --locked mypy app/composition tests/composition/test_reconciliation.py
uv run --locked pytest tests/composition/test_reconciliation.py tests/composition/test_runtime.py -q
git diff --check
```

**Documentation Updates:** none.

**Rollback:** call reconciliation with the previous configuration; if that fails, stop the runtime and restart the process with previous config.

**Git Commit:** `feat(composition): reconcile installed provider config`

**Re-run safety:** Safe — reconciliation is idempotent for identical configs.

**Definition of Done:**
- [ ] Installed-only restriction enforced.
- [ ] Transitive affected set tested.
- [ ] Rollback restores incumbent IDs.
- [ ] G6 passes.

**Phase 6 Exit Gate — all must be true before Phase 7 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] No PROTECTED path appears in phase diff.
- [ ] Business consumers receive direct objects, not registry access.
- [ ] Replacement is atomic and generational.
- [ ] G6 passes.

### Phase 7 — Errors, Health, Profile Readiness

**Goal:** expose one structured unavailable family and keep liveness, kernel readiness, provider health, profile readiness, and authorization distinct.
**Why now:** provider absence must have stable semantics before pilots expose it.
**Deliverable:** full error payload, readiness evaluator, and backward-compatible runtime validation extension.
**Phase Exit Gate:** G7 normalizes missing capability at kernel/runtime boundaries.

#### - [ ] Task `P7-T01` — Normalize capability failures

**Traces to:** `D-06`, `G7`
**Depends on:** P6-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Complete the `CAPABILITY_UNAVAILABLE` reason enum, payload, exception, and JSON projection.

**Context to Read (and nothing else):**
- `app/kernel/errors.py` — existing kernel errors.
- `app/kernel/resolver.py` — inactive evidence.
- Shared Contracts §3.3.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/errors.py` | MODIFY | add exact reason/payload/exception family |
| `tests/kernel/test_capability_errors.py` | CREATE | payload/message/redaction tests |

Anchor: existing exception definitions; preserve manifest/resolution/lifecycle exceptions.

**Specification (copy exactly):** implement §3.3. Add `def capability_unavailable_payload(detail: CapabilityUnavailable) -> Mapping[str, object]`; output list for `dependency_chain`, enum value strings, all nine fields, no omitted nulls.

**Behaviour Rules:**
1. Payload is JSON-serializable.
2. Dependency chain is nonempty and ends with `capability`; otherwise `ValueError("dependency_chain must end with capability")`.
3. Retryable is caller-supplied; do not infer it.
4. Message and enum values are exact.

**Implementation Steps:**
1. Add exact 13 reason codes.
2. Add frozen detail and exception.
3. Validate dependency chain.
4. Add serializer/root exports/tests.

**DO NOT:**
- Do not create separate error families.
- Do not include causes/configs in public payload.
- Do not infer authorization from no error.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/kernel/test_capability_errors.py` (CREATE): reason values, exact message, JSON shape, null retention, invalid chain, secret-free payload.

**Usage Example**
Serialize the §3.3 example dependency-unavailable detail.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/errors.py tests/kernel/test_capability_errors.py
uv run --locked ruff check app/kernel/errors.py tests/kernel/test_capability_errors.py
uv run --locked mypy app/kernel/errors.py tests/kernel/test_capability_errors.py
uv run --locked pytest tests/kernel/test_capability_errors.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): normalize capability unavailable errors`

**Re-run safety:** Safe at exact error anchor.

**Definition of Done:**
- [ ] One error family exists.
- [ ] Thirteen reasons exact.
- [ ] Payload test passes.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P7-T02` — Compute profile readiness

**Traces to:** `D-04`, `G7`, `Profile readiness`
**Depends on:** P7-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Evaluate research/simulation/demo/live readiness from explicit capability requirements without changing process liveness.

**Context to Read (and nothing else):**
- `app/kernel/profiles.py` — enum.
- `app/kernel/resolver.py` — report.
- `app/kernel/errors.py` — structured missing detail.
- `docs/dev/plugin-decoupling/audit/G2_REPORT.md` — profile requirement IDs.
- Shared Contracts §3.4.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/profiles.py` | MODIFY | readiness value/evaluator |
| `tests/kernel/test_profiles.py` | CREATE | four-profile and safety tests |

Anchor: existing `RuntimeProfile`; preserve values.

**Specification (copy exactly):** implement §3.4 `ProfileReadiness` and evaluator. Missing details use reason `PROFILE_REQUIREMENT_UNSATISFIED`, state from underlying inactive evidence, consumer `{profile}.profile`, chain `({profile}.profile, capability)`, retryable false.

**Behaviour Rules:**
1. Every profile appears exactly once sorted enum order.
2. Empty requirement tuple is ready.
3. Kernel liveness is unchanged by profile unready.
4. Demo/live missing any required safety/execution ID are unready.
5. No fallback provider is selected by readiness evaluation.

**Implementation Steps:**
1. Add readiness value.
2. Map report bindings/inactive IDs.
3. Build missing details per profile.
4. Add root exports/tests.

**DO NOT:**
- Do not boot or activate providers.
- Do not authorize an operation.
- Do not downgrade live to demo/research.
- Do not touch Risk/Trading protected paths.

**Unit Tests**
File: `tests/kernel/test_profiles.py` (CREATE): all ready, research optional loss, simulation required loss, demo safety loss, live safety loss, kernel remains live, no fallback.

**Usage Example**
Evaluate an empty report with empty research requirements and one live safety requirement; research ready/live unready.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/profiles.py tests/kernel/test_profiles.py
uv run --locked ruff check app/kernel/profiles.py tests/kernel/test_profiles.py
uv run --locked mypy app/kernel/profiles.py tests/kernel/test_profiles.py
uv run --locked pytest tests/kernel/test_profiles.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): compute runtime profile readiness`

**Re-run safety:** Safe at exact enum anchor.

**Definition of Done:**
- [ ] Four profiles returned.
- [ ] Demo/live fail closed.
- [ ] Kernel liveness stays distinct.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P7-T03` — Extend runtime validation

**Traces to:** `G7`, `Profile readiness`, `Existing assets`
**Depends on:** P7-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Extend the existing runtime gate with an optional readiness input while preserving the current signature and result for existing callers.

**Context to Read (and nothing else):**
- `app/runtime.py` — current implementation/signature.
- `app/__init__.py` — exact export.
- `app/kernel/profiles.py` — readiness values.
- existing runtime unit test located in G2 report — current behavior evidence.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/runtime.py` | MODIFY | add separate readiness-aware function |
| `app/__init__.py` | MODIFY | export new function without changing old |
| `tests/test_runtime_capability_readiness.py` | CREATE | compatibility/fail-closed tests |

Anchors: existing `validate_runtime_configuration` and `__all__`. Preserve its signature and mapping exactly.

**Specification (copy exactly):**
```python
def validate_runtime_capability_readiness(
    *, runtime_profile: str, execution_route: str,
    readiness: tuple[ProfileReadiness, ...],
) -> object: ...
```
First call existing validator. Find exactly one matching profile; missing/duplicate raises `ValueError("profile readiness missing or duplicated: {runtime_profile}")`. If unready, raise `CapabilityUnavailableError` using first missing item sorted by capability. If ready, return existing validator result. `app.__all__` becomes `("validate_runtime_capability_readiness", "validate_runtime_configuration")`.

**Behaviour Rules:**
1. Existing function is byte-behavior compatible.
2. Research/simulation/demo/live route validation runs before readiness.
3. No mutation function is called.

**Implementation Steps:**
1. Add imports from kernel public boundary.
2. Add new function after existing validator.
3. Update root lazy/eager export in current style.
4. Add compatibility and unready tests.

**DO NOT:**
- Do not add a parameter to existing function.
- Do not change existing error strings.
- Do not select a fallback route.
- Do not touch Risk/Trading protected paths.

**Unit Tests**
File: `tests/test_runtime_capability_readiness.py` (CREATE): legacy return equality, ready return, missing tuple, duplicate tuple, unready raises structured detail, route invalid precedes readiness.

**Regression Tests**
Run the existing runtime test path recorded in G2 report; same count and behavior as G0.

**Usage Example**
Call new function for unready live and inspect `CAPABILITY_UNAVAILABLE` detail.

**Quality Gates:**
```powershell
uv run --locked ruff format app/runtime.py app/__init__.py tests/test_runtime_capability_readiness.py
uv run --locked ruff check app/runtime.py app/__init__.py tests/test_runtime_capability_readiness.py
uv run --locked mypy app/runtime.py app/__init__.py tests/test_runtime_capability_readiness.py
uv run --locked pytest tests/test_runtime_capability_readiness.py -q
git diff --check
```

**Documentation Updates:** none; architecture already defines distinction.

**Git Commit:** `feat(runtime): enforce capability profile readiness`

**Re-run safety:** Safe when exact signature/export anchors match.

**Definition of Done:**
- [ ] Existing signature unchanged.
- [ ] New function fails closed.
- [ ] Compatibility tests pass.
- [ ] G7 kernel/runtime boundary passes.

**Phase 7 Exit Gate — all must be true before Phase 8 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] No PROTECTED path appears in phase diff.
- [ ] Six status concepts remain distinct.
- [ ] Runtime compatibility is unchanged.
- [ ] G7 passes at implemented boundaries.

### Phase 8 — Provider State and Migration Lifecycle

**Goal:** preserve provider-owned historical state across uninstall and compatible reinstall without weakening checksum enforcement.
**Why now:** stateful provider waves cannot begin until owner absence is startup-safe.
**Deliverable:** manifest state rules, tombstone-aware migration request, and retained-state cycle proof.
**Phase Exit Gate:** G8 restarts without provider code and validates preserved state on reinstall.

#### - [ ] Task `P8-T01` — Define provider state metadata

**Traces to:** `D-09`, `Phase 8`, `G8`
**Depends on:** P7-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Enforce stateful-manifest compatibility, retention, migration, downgrade, and purge authorization fields.

**Context to Read (and nothing else):**
- `app/kernel/manifests.py` — parser and state fields.
- `app/services/data/persistence/contracts.py` — current migration values.
- Shared Contracts §3.2.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/kernel/manifests.py` | MODIFY | complete state validation |
| `tests/kernel/test_stateful_manifests.py` | CREATE | schema/retention/purge tests |

Anchor: `ProviderManifest` state fields and parser's `[state]` branch.

**Specification (copy exactly):** state table keys `schema_id`, `schema_version`, `migration_manifest`, `compatible_prior_majors`, `downgrade_policy`, `uninstall_retention`, `purge_requires_authorization`. Accepted downgrade policies `reject`, `read_only`; retention must equal `retain`; purge flag must be true. Stateful manifest without these exact values raises reason `stateful provider must retain data and require purge authorization`.

**Behaviour Rules:**
1. Stable schema ID matches `[a-z][a-z0-9_.-]*` and may not start `app.`.
2. Migration manifest is a stable schema reference, not a Python class path.
3. Compatible majors are sorted unique positive ints.

**Implementation Steps:**
1. Add downgrade policy value/type.
2. Validate state key completeness and exact retention/purge rules.
3. Reject Python class-path schema IDs.
4. Add tests.

**DO NOT:**
- Do not run migrations.
- Do not accept `drop` retention.
- Do not auto-authorize purge.
- Do not modify immutable migration files.
- Do not touch other PROTECTED paths.

**Unit Tests**
File: `tests/kernel/test_stateful_manifests.py` (CREATE): valid, missing key, bad schema ID, class path, bad retention, purge false, prior-major normalization.

**Usage Example**
Parse a temporary retained-state provider manifest.

**Quality Gates:**
```powershell
uv run --locked ruff format app/kernel/manifests.py tests/kernel/test_stateful_manifests.py
uv run --locked ruff check app/kernel/manifests.py tests/kernel/test_stateful_manifests.py
uv run --locked mypy app/kernel/manifests.py tests/kernel/test_stateful_manifests.py
uv run --locked pytest tests/kernel/test_stateful_manifests.py tests/kernel/test_manifests.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(kernel): validate provider state metadata`

**Re-run safety:** Safe at exact parser anchors.

**Definition of Done:**
- [ ] Retention/purge fail closed.
- [ ] Python class paths rejected.
- [ ] Existing stateless manifests pass.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P8-T02` — Accept migration tombstones

**Traces to:** `D-09`, `Phase 8`, `G8`
**Depends on:** P8-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Permit applied migrations whose provider owner is absent only when an explicit immutable tombstone supplies the recorded checksum.

**Context to Read (and nothing else):**
- `app/services/data/persistence/contracts.py` — MigrationRequest/Step.
- `app/services/data/persistence/migrations.py` — orphan/checksum logic.
- `tests/data/unit/test_persistence_migrations.py` — existing ledger tests.
- `AGENTS.md` — tombstone/uninstall rule.
- `docs/dev/plugin-decoupling/REFACTOR_PLAN.md` — Phase 8 cycle.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/data/persistence/contracts.py` | MODIFY | add MigrationTombstone and request field |
| `app/services/data/persistence/migrations.py` | MODIFY | validate owner-absent applied rows |
| `tests/data/unit/test_provider_migration_tombstones.py` | CREATE | tombstone safety tests |

Anchors: existing `MigrationStep`, `MigrationRequest`, and orphaned-ID check. Preserve every applied-step checksum and SQL statement.

**Specification (copy exactly):**
```python
class MigrationTombstone(BaseModel):
    domain: str
    migration_id: str
    checksum: str
    owner_provider_id: str
    state_schema_id: str

# Add to MigrationRequest
tombstones: tuple[MigrationTombstone, ...] = ()
```
For each ledger ID absent from steps: matching tombstone with same domain/ID/checksum permits startup; missing tombstone keeps existing `DATA_MIGRATION_LEDGER_INVALID`; checksum mismatch keeps existing checksum failure. Tombstones execute no statements.

**Behaviour Rules:**
1. Applied step definitions remain immutable.
2. Tombstone cannot authorize a new migration.
3. Duplicate step/tombstone ID fails validation.
4. Uninstall never deletes a row/table.
5. No purge API is added.

**Implementation Steps:**
1. Add validated tombstone model.
2. Add defaulted request field and uniqueness checks.
3. Replace orphan rejection with exact tombstone verification.
4. Preserve existing checksum and ordering branches.
5. Add focused tests.

**DO NOT:**
- Do not edit `app/services/data/migrations/*.py`.
- Do not drop or alter tables.
- Do not accept tombstone checksum mismatch.
- Do not add purge.
- Do not touch other PROTECTED paths.

**Unit Tests**
File: `tests/data/unit/test_provider_migration_tombstones.py` (CREATE): owner-present normal, owner-absent valid, missing tombstone reject, checksum mismatch reject, tombstone cannot apply, duplicate reject, tables preserved.

**Regression Tests**
`uv run --locked pytest tests/data/unit/test_persistence_migrations.py -q` → same count as G0 and all pass.

**Usage Example**
Run the focused test against a temporary SQLite database only.

**Logging**
- INFO `Validated retained migration tombstone %s/%s` with domain and ID.
- Never log database path contents or row data.

**Rollback:** revert code; tombstones have changed no schema or data. Existing ledgers remain unchanged.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/data/persistence/contracts.py app/services/data/persistence/migrations.py tests/data/unit/test_provider_migration_tombstones.py
uv run --locked ruff check app/services/data/persistence/contracts.py app/services/data/persistence/migrations.py tests/data/unit/test_provider_migration_tombstones.py
uv run --locked mypy app/services/data/persistence/contracts.py app/services/data/persistence/migrations.py tests/data/unit/test_provider_migration_tombstones.py
uv run --locked pytest tests/data/unit/test_provider_migration_tombstones.py tests/data/unit/test_persistence_migrations.py -q
git diff --check
```

**Documentation Updates:** none; AGENTS/architecture already own the rule.

**Git Commit:** `feat(data): validate retained migration tombstones`

**Re-run safety:** Safe — no migration or schema mutation occurs outside temporary tests.

**Definition of Done:**
- [ ] Existing checksum enforcement preserved.
- [ ] Valid owner absence accepted.
- [ ] Data remains intact.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P8-T03` — Prove retained-state reinstall

**Traces to:** `Phase 8`, `G8`
**Depends on:** P8-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Execute the install→migrate→disable→restart absent→reinstall-compatible cycle in fresh processes against a temporary SQLite file.

**Context to Read (and nothing else):**
- `tests/removability/harness.py` — subprocess helper.
- `app/services/data/persistence/contracts.py` — tombstone values.
- `app/services/data/persistence/migrations.py` — runner.
- `tests/data/unit/test_provider_migration_tombstones.py` — fixture pattern.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_stateful_provider_reinstall.py` | CREATE | complete retained-state cycle |
| `tests/removability/fixtures/stateful_provider/manifest.toml` | CREATE | deterministic fake stateful manifest |
| `tests/removability/fixtures/stateful_provider/migration.json` | CREATE | stable fake migration/tombstone data |

**Specification (copy exactly):** provider ID `test.stateful.default`; schema ID `test.stateful.v1`; migration ID `001_test_stateful`; table `test_stateful_records`; inserted row `("record-1", "preserved")`. Every process receives temp DB path through a command argument, never environment/global config.

**Behaviour Rules:**
1. Absent restart imports no provider module.
2. Row/table survive disable and code absence.
3. Compatible reinstall reads exact row.
4. Incompatible schema major fails with `VERSION_INCOMPATIBLE`.
5. Purge attempt without explicit authority is unavailable because no purge API exists.

**Implementation Steps:**
1. Create deterministic manifest/migration fixture.
2. Write one test with four fresh-process stages.
3. Assert row/table after every stage.
4. Assert incompatible reinstall fails before write.
5. Assert no provider entry remains in absent process `sys.modules`.

**DO NOT:**
- Do not use repository `data/`.
- Do not delete the temp table during intermediate stages.
- Do not import provider in absent stage.
- Do not call live services.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/removability/test_stateful_provider_reinstall.py` (CREATE): `test_stateful_provider_absence_and_compatible_reinstall`, `test_incompatible_state_schema_is_rejected`, `test_uninstall_does_not_expose_purge`.

**Usage Example**
Run the test file; three passes are G8 proof.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/removability/test_stateful_provider_reinstall.py
uv run --locked ruff check tests/removability/test_stateful_provider_reinstall.py
uv run --locked mypy tests/removability/test_stateful_provider_reinstall.py
uv run --locked pytest tests/removability/test_stateful_provider_reinstall.py -q -W error::ResourceWarning
git diff --check
```

**Documentation Updates:** none.

**Rollback:** tests use temporary databases; revert test/fixture commit. No repository data cleanup.

**Git Commit:** `test(removability): prove retained-state reinstall`

**Re-run safety:** Safe — all state is temporary and closed.

**Definition of Done:**
- [ ] Three fresh-process tests pass.
- [ ] State preserved and incompatible reinstall blocked.
- [ ] No handle leaks.
- [ ] G8 passes.

**Phase 8 Exit Gate — all must be true before Phase 9 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] No immutable migration definition changed.
- [ ] No PROTECTED path appears except approved Data persistence files.
- [ ] Uninstall preserves data.
- [ ] Compatible reinstall restores access.
- [ ] G8 passes.

### Phase 9 — Pure Pilot: RSI and Williams %R

**Goal:** make RSI and Williams %R independently removable providers while preserving FEAT-INDI-03, formulas, signatures, and outputs.
**Why now:** two pure functions are the lowest-cost test of contract, manifest, injection, absence, replacement, and compatibility façade behavior.
**Deliverable:** two nested provider packages, root tests/examples, temporary façade modules, and physical deletion/reinstall proof.
**Phase Exit Gate:** G9 passes for each provider independently and financial hashes remain unchanged.

#### - [ ] Task `P9-T01` — Create RSI provider package

**Traces to:** `Phase 9`, `R-01`, `R-04`, `R-05`, `G9`
**Depends on:** P8-T03
**Estimated size:** L (120–200 LOC production; formula moved without semantic edits)

**Goal.** Create the RSI default manifest, implementation, and factory while leaving the current public module untouched.

**Context to Read (and nothing else):**
- `app/services/indicators/momentum/rsi.py` — exact formula to copy.
- `app/capabilities/indicator/rsi/v1.py` — callable record.
- `app/kernel/manifests.py` — TOML schema.
- `app/kernel/lifecycle.py` — factory signature.
- `tests/indicators/fixtures/momentum_golden.json` — parity source.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/momentum/rsi_default/manifest.toml` | CREATE | static provider declaration |
| `app/services/indicators/momentum/rsi_default/implementation.py` | CREATE | moved RSI implementation |
| `app/services/indicators/momentum/rsi_default/plugin.py` | CREATE | pure factory |

**Specification (copy exactly):** manifest uses provider/capability values from §3.6, entry point `app.services.indicators.momentum.rsi_default.plugin:create_provider`, profiles all four, scope `process`, no requirements/effects/state. `implementation.py` copies `_FORMULA_VERSION`, `_INDICATOR_VERSION`, `_FLAT_RSI`, `_build_config`, `_wilder_rsi`, and `rsi` byte-semantically from the existing module; only internal imports may change. `plugin.create_provider(*, dependencies: Mapping[CapabilityId, object], config: Mapping[str, object], scope: EffectScope) -> RsiCapabilityV1` rejects nonempty values with `ValueError("RSI provider accepts no dependencies or config")` and returns `RsiCapabilityV1(calculate=rsi)`.

**Behaviour Rules:**
1. Formula constants, validation, logging, warmup, dtype, metadata, and errors are unchanged.
2. Import starts no I/O and creates no mutable state.
3. Implementation `__all__` is empty; plugin exports only factory.

**Implementation Steps:**
1. Create strict manifest.
2. Copy RSI implementation without arithmetic edits.
3. Replace only imports required by the new path.
4. Create pure factory with exact rejection.
5. Verify old module remains unchanged in this task.

**DO NOT:**
- Do not edit `momentum/rsi.py`.
- Do not change formula or defaults.
- Do not add smoothing/fill/cache.
- Do not register at import time.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
Added in P9-T02; run existing RSI tests identified in G2 report and require all pass.

**Usage Example**
Added in P9-T02; in this task import factory in a fresh process and print capability ID only.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/indicators/momentum/rsi_default
uv run --locked ruff check app/services/indicators/momentum/rsi_default
uv run --locked mypy app/services/indicators/momentum/rsi_default
uv run --locked pytest tests/indicators -q -k 'rsi and not williams'
git diff --check
```

**Documentation Updates:** none; provider README is P9-T02.

**Git Commit:** `refactor(indicators): extract RSI default provider`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Three production files created.
- [ ] Existing RSI tests pass.
- [ ] Old public module unchanged.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P9-T02` — Activate RSI provider

**Traces to:** `Phase 9`, `G9`, `H — Verify`
**Depends on:** P9-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Add RSI provider documentation, executable example, and contract/parity/factory tests through the provider contract.

**Context to Read (and nothing else):**
- `app/services/indicators/momentum/rsi_default/manifest.toml` — identity.
- `app/services/indicators/momentum/rsi_default/plugin.py` — factory.
- `tests/indicators/fixtures/momentum_golden.json` — exact outputs.
- `tests/indicators/unit/test_momentum.py` or G2-recorded RSI test — fixture construction.
- `app/composition/runtime.py` — activation API.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/momentum/rsi_default/README.md` | CREATE | provider ownership/removal record |
| `app/services/indicators/momentum/rsi_default/example.py` | CREATE | provider-local executable evidence |
| `tests/indicators/providers/indicator.rsi.default/test_provider.py` | CREATE | contract/parity/activation tests |

**Specification (copy exactly):** README uses §4 headings and states FEAT-INDI-03 ownership. Example builds the same bounded dataset as existing usage evidence, discovers/activates only RSI, calls through `RsiCapabilityV1.calculate(period=14)`, prints the last five JSON-safe values, and defines `main()` plus guard.

**Behaviour Rules:**
1. Provider output object equals existing `rsi` result projection for golden fixture.
2. Empty dependencies/config activate; nonempty values reject exactly.
3. Example opens no network/database.
4. Import has no I/O.

**Implementation Steps:**
1. Create README with exact identity/capability/profile/removal data.
2. Create bounded example through composition.
3. Add manifest parse/factory/contract/parity/import tests.
4. Compare output hashes to Phase 0.

**DO NOT:**
- Do not call implementation directly in example/parity consumer.
- Do not duplicate golden values.
- Do not change FEAT-INDI-03 registry row.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/indicators/providers/indicator.rsi.default/test_provider.py` (CREATE): manifest exact, factory exact, contract call, Phase0 parity, import no I/O, composition activation.

**Usage Example**
`uv run --locked python app/services/indicators/momentum/rsi_default/example.py` → five bounded result rows, exit 0.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/indicators/momentum/rsi_default/example.py tests/indicators/providers/indicator.rsi.default/test_provider.py
uv run --locked ruff check app/services/indicators/momentum/rsi_default tests/indicators/providers/indicator.rsi.default
uv run --locked mypy app/services/indicators/momentum/rsi_default tests/indicators/providers/indicator.rsi.default
uv run --locked pytest tests/indicators/providers/indicator.rsi.default/test_provider.py -q
uv run --locked python app/services/indicators/momentum/rsi_default/example.py
git diff --check
```

**Documentation Updates:** provider README only; domain registry remains canonical and unchanged.

**Git Commit:** `test(indicators): prove RSI provider parity`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Six tests pass.
- [ ] Example exits 0.
- [ ] Golden parity exact.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P9-T03` — Create Williams provider package

**Traces to:** `Phase 9`, `R-01`, `R-04`, `R-05`, `G9`
**Depends on:** P9-T02
**Estimated size:** L (120–200 LOC production; formula moved without semantic edits)

**Goal.** Create Williams %R default manifest, implementation, and factory while leaving the public module untouched.

**Context to Read (and nothing else):**
- `app/services/indicators/momentum/williams_r.py` — exact formula.
- `app/capabilities/indicator/williams_r/v1.py` — contract.
- `app/services/indicators/momentum/rsi_default/manifest.toml` — manifest style.
- `app/services/indicators/momentum/rsi_default/plugin.py` — factory style.
- `tests/indicators/fixtures/momentum_golden.json` — parity source.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/momentum/williams_r_default/manifest.toml` | CREATE | static provider declaration |
| `app/services/indicators/momentum/williams_r_default/implementation.py` | CREATE | moved Williams implementation |
| `app/services/indicators/momentum/williams_r_default/plugin.py` | CREATE | pure factory |

**Specification (copy exactly):** use §3.6 IDs, entry point `app.services.indicators.momentum.williams_r_default.plugin:create_provider`, all profiles, process scope, no requirements/effects/state. Copy all existing formula behavior. Factory rejects nonempty values with `ValueError("Williams R provider accepts no dependencies or config")` and returns `WilliamsRCapabilityV1(calculate=williams_r)`.

**Behaviour Rules:** same as P9-T01, substituting Williams; rolling availability and zero-range error remain exact.

**Implementation Steps:**
1. Create strict manifest.
2. Copy Williams implementation without arithmetic edits.
3. Adjust only path imports.
4. Add factory.
5. Verify old module unchanged.

**DO NOT:**
- Do not edit public Williams module.
- Do not add `source`.
- Do not change rolling window/zero-range behavior.
- Do not register on import.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
P9-T04 adds provider tests; run existing Williams tests selected by G2 report.

**Usage Example**
P9-T04 adds executable example.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/indicators/momentum/williams_r_default
uv run --locked ruff check app/services/indicators/momentum/williams_r_default
uv run --locked mypy app/services/indicators/momentum/williams_r_default
uv run --locked pytest tests/indicators -q -k 'williams'
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `refactor(indicators): extract Williams R provider`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Three production files created.
- [ ] Existing tests pass.
- [ ] Public module unchanged.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P9-T04` — Activate Williams provider

**Traces to:** `Phase 9`, `G9`, `H — Verify`
**Depends on:** P9-T03
**Estimated size:** M (50–120 LOC)

**Goal.** Add Williams provider README/example and exact contract/parity/factory tests.

**Context to Read (and nothing else):**
- `app/services/indicators/momentum/williams_r_default/manifest.toml` — identity.
- `app/services/indicators/momentum/williams_r_default/plugin.py` — factory.
- `app/services/indicators/momentum/rsi_default/example.py` — example style.
- `tests/indicators/fixtures/momentum_golden.json` — parity.
- `app/composition/runtime.py` — activation.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/indicators/momentum/williams_r_default/README.md` | CREATE | provider ownership/removal record |
| `app/services/indicators/momentum/williams_r_default/example.py` | CREATE | executable evidence |
| `tests/indicators/providers/indicator.williams_r.default/test_provider.py` | CREATE | provider proof |

**Specification (copy exactly):** same structure as P9-T02, capability `indicator.williams_r.v1`, period 14, no source keyword, FEAT-INDI-03 ownership.

**Behaviour Rules:** exact Williams output/result/error parity; no network/database; no import effects.

**Implementation Steps:** create README, example, six provider tests, and hash comparison.

**DO NOT:**
- Do not call implementation directly from example.
- Do not alter golden fixture.
- Do not add a new Feature Registry row.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
Manifest exact, factory exact, contract, parity, no-I/O import, activation.

**Usage Example**
`uv run --locked python app/services/indicators/momentum/williams_r_default/example.py` → five rows, exit 0.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/indicators/momentum/williams_r_default/example.py tests/indicators/providers/indicator.williams_r.default/test_provider.py
uv run --locked ruff check app/services/indicators/momentum/williams_r_default tests/indicators/providers/indicator.williams_r.default
uv run --locked mypy app/services/indicators/momentum/williams_r_default tests/indicators/providers/indicator.williams_r.default
uv run --locked pytest tests/indicators/providers/indicator.williams_r.default/test_provider.py -q
uv run --locked python app/services/indicators/momentum/williams_r_default/example.py
git diff --check
```

**Documentation Updates:** provider README only.

**Git Commit:** `test(indicators): prove Williams R provider parity`

**Re-run safety:** Safe — create-only.

**Definition of Done:**
- [ ] Six tests pass.
- [ ] Example passes.
- [ ] Golden parity exact.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P9-T05` — Preserve indicator façade

**Traces to:** `G — Compatibility façade`, `Phase 9`, `G9`
**Depends on:** P9-T04
**Estimated size:** L (120–200 LOC)

**Goal.** Convert existing RSI/Williams modules to temporary boundary façades that resolve context-bound active capabilities while preserving signatures.

**Context to Read (and nothing else):**
- `app/services/indicators/momentum/rsi.py` — current public module.
- `app/services/indicators/momentum/williams_r.py` — current public module.
- `app/composition/runtime.py` — leasing.
- `app/services/indicators/__init__.py` — root export paths.
- `tests/indicators/unit/test_public_api.py` — public contract.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/facade.py` | CREATE | context-bound runtime for external façades |
| `app/services/indicators/momentum/rsi.py` | MODIFY | temporary RSI resolver wrapper |
| `app/services/indicators/momentum/williams_r.py` | MODIFY | temporary Williams resolver wrapper |

Anchors: replace implementation bodies only after exact signatures; preserve module docstrings, function names, signatures, docstrings, logging behavior observable by tests, and `__all__`.

**Specification (copy exactly):**
```python
@contextmanager
def bind_runtime(runtime: CompositionRuntime) -> Iterator[None]: ...
def lease_capability(capability_id: CapabilityId) -> CapabilityLease[object]: ...
```
Use `ContextVar[CompositionRuntime | None]`, reset token in `finally`. Missing binding raises `CapabilityUnavailableError` reason `NOT_INSTALLED`, state `NOT_INSTALLED`, consumer `compatibility_facade`, chain `(compatibility_facade, capability)`. Wrappers cast leased value to the exact capability record then call `calculate` with unchanged arguments.

**Behaviour Rules:**
1. Nested bindings restore prior runtime.
2. Internal production code may not import wrapper modules after its provider wave.
3. Existing package root still resolves both names.
4. Missing provider yields structured error, not import failure.

**Implementation Steps:**
1. Add context-bound façade bridge.
2. Replace RSI formula module content with wrapper/imports.
3. Replace Williams formula module content with wrapper/imports.
4. Keep both bridge functions private to composition; do not add them to `app.composition.__all__`.
5. Run public API and parity tests.

**DO NOT:**
- Do not change signatures/defaults.
- Do not retain duplicate formulas in wrapper modules.
- Do not create a process-global mutable registry.
- Do not fallback to direct implementation.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
Add façade tests to existing provider test files: bound success, unbound structured absence, nested restore. Public API exact test remains green.

**Regression Tests**
Run all Indicators tests and Phase 0 financial hash test.

**Usage Example**
Both provider examples bind their local composition runtime before calling domain-root functions in an added compatibility demonstration block.

**Quality Gates:**
```powershell
uv run --locked ruff format app/composition/facade.py app/services/indicators/momentum/rsi.py app/services/indicators/momentum/williams_r.py
uv run --locked ruff check app/composition/facade.py app/services/indicators/momentum/rsi.py app/services/indicators/momentum/williams_r.py
uv run --locked mypy app/composition/facade.py app/services/indicators/momentum/rsi.py app/services/indicators/momentum/williams_r.py
uv run --locked pytest tests/indicators tests/architecture/test_plugin_financial_baseline.py -q
git diff --check
```

**Documentation Updates:** none; provider READMEs describe temporary façade.

**Git Commit:** `refactor(indicators): route momentum façades through capabilities`

**Re-run safety:** Not safe — formula removal is one-time; revert restores old modules.

**Definition of Done:**
- [ ] Public signatures/exports unchanged.
- [ ] One formula copy per provider.
- [ ] Missing provider structured.
- [ ] Commit executed only with separate authorization.

#### - [ ] Task `P9-T06` — Prove independent removal

**Traces to:** `Phase 9`, `G9`, `J — Deletion proof`
**Depends on:** P9-T05
**Estimated size:** M (50–120 LOC)

**Goal.** Prove delete/reinstall independence and transitive consumer behavior for both pure providers in fresh copied trees.

**Context to Read (and nothing else):**
- `tests/removability/harness.py` — subprocess helper.
- `app/services/indicators/momentum/rsi_default/manifest.toml` — RSI path/ID.
- `app/services/indicators/momentum/williams_r_default/manifest.toml` — Williams path/ID.
- `tests/indicators/providers/indicator.rsi.default/test_provider.py` — parity proof.
- `app/services/indicators/README.md` — FEAT-INDI-03 registry row and evidence style.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_momentum_provider_deletion.py` | CREATE | physical delete/reinstall proof |
| `tests/removability/fixtures/rsi_consumer/manifest.toml` | CREATE | consumer requiring RSI only |
| `tests/removability/fixtures/rsi_consumer/plugin.py` | CREATE | deterministic test consumer |
| `app/services/indicators/README.md` | MODIFY | update FEAT-INDI-03 provider/removal evidence |

Anchor text: the existing Feature Registry row beginning `| FEAT-INDI-03 |`. Preserve its feature ID, status, public API names, requirements, and existing evidence; append provider/removal evidence only.

**Specification (copy exactly):** copy repo to pytest temp path excluding `.git`, `.venv`, `htmlcov`, caches, `data`, and `node_modules`. Delete one explicit provider directory using Python `shutil.rmtree` inside temp copy only. Fresh script imports kernel/app, asserts deleted provider module absent from `sys.modules`, resolves, checks other provider active and consumer behavior, then copy provider directory back from source and rerun.

**Behaviour Rules:**
1. Williams deletion does not deactivate RSI consumer.
2. RSI deletion deactivates RSI consumer with chain ending `indicator.rsi.v1`.
3. Reinstall RSI reactivates consumer.
4. Unrelated indicator outputs/hashes unchanged.

**Implementation Steps:**
1. Add deterministic consumer fixture.
2. Add copied-tree helper local to test for one exact directory.
3. Run two deletion scenarios in new interpreters.
4. Run reinstall and hash assertions.

**DO NOT:**
- Do not delete in source workspace.
- Do not use config-disable as physical proof.
- Do not permit stale `sys.modules`.
- Do not modify provider code.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/removability/test_momentum_provider_deletion.py` (CREATE): delete Williams, delete RSI/transitive, reinstall RSI, unrelated hash.

**Usage Example**
Run the test file; four passes certify G9.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/removability/test_momentum_provider_deletion.py tests/removability/fixtures/rsi_consumer/plugin.py
uv run --locked ruff check tests/removability/test_momentum_provider_deletion.py tests/removability/fixtures/rsi_consumer/plugin.py
uv run --locked mypy tests/removability/test_momentum_provider_deletion.py tests/removability/fixtures/rsi_consumer/plugin.py
uv run --locked pytest tests/removability/test_momentum_provider_deletion.py -q
uv run --locked pytest tests/architecture/test_plugin_financial_baseline.py -q
git diff --check
```

**Documentation Updates:** under the existing FEAT-INDI-03 row, preserve ID/status/public API and add the two provider IDs, capability IDs, provider READMEs, provider test paths, and physical deletion/reinstall evidence path.

**Git Commit:** `test(removability): prove momentum provider deletion`

**Re-run safety:** Safe — deletion occurs only under pytest temp roots.

**Definition of Done:**
- [ ] Four deletion/reinstall tests pass.
- [ ] Source workspace unchanged by deletion.
- [ ] Financial hashes pass.
- [ ] G9 passes.

**Phase 9 Exit Gate — all must be true before Phase 10 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] Provider examples exit 0.
- [ ] FEAT-INDI-03 remains one feature.
- [ ] Each provider independently deletes/reinstalls.
- [ ] Financial outputs unchanged.
- [ ] G9 passes.

### Phase 10 — Effectful Pilots

**Goal:** prove scoped external delivery and an async MT5-backed Data stream without trading mutation.
**Why now:** pure-provider success does not prove sockets, queues, subscriptions, tasks, or partial cleanup.
**Deliverable:** lazy Utils boundary, notification capability/transports, injected manager, tick-stream capability, MT5/fake adapters, and replacement proof.
**Phase Exit Gate:** G10 proves pure and effectful models with zero leaked resources and no duplicate stream events.

#### - [ ] Task `P10-T01` — Make Utils boundary lazy

**Traces to:** `Phase 10`, `Pilot A — Notifications`, `G10`
**Depends on:** P9-T06
**Estimated size:** L (120–200 LOC)

**Goal.** Convert `app.utils` to the existing lazy `_EXPORTS` pattern so importing logger/runtime does not import notifications or security.

**Context to Read (and nothing else):**
- `app/utils/__init__.py` — eager boundary.
- `app/services/portfolio/__init__.py` — approved lazy pattern.
- `app/services/indicators/__init__.py` — lazy boundary test pattern.
- `app/utils/README.md` — exact public export list.
- `tests/utils/unit/test_public_api.py` or G2-recorded equivalent — export test.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/utils/__init__.py` | MODIFY | lazy export map and PEP 562 resolver |
| `app/utils/README.md` | MODIFY | record lazy boundary without changing exports |
| `tests/utils/unit/test_lazy_public_api.py` | CREATE | exact exports/lazy import proof |

Anchor: current eager imports and existing `__all__`; preserve every export name and target.

**Specification (copy exactly):** follow Indicators' `TYPE_CHECKING`, `_EXPORTS`, `__getattr__`, `__dir__` pattern. `__all__` remains byte-equivalent as a tuple. Unknown name raises `AttributeError("module 'app.utils' has no attribute {name!r}")`.

**Behaviour Rules:** `import app.utils`, `from app.utils import get_logger`, and `import app.runtime` leave every `app.utils.notifications*` module absent from `sys.modules`; resolving each declared export still works.

**Implementation Steps:** map every existing export to its current owner; add type-checking imports; remove eager runtime imports; add exact tests.

**DO NOT:**
- Do not change an export or implementation.
- Do not move notifications yet.
- Do not add fallback import behavior.
- Do not touch any PROTECTED path from §5.

**Unit Tests**
File: `tests/utils/unit/test_lazy_public_api.py` (CREATE): exact `__all__`, resolve every export, notifications absent after logger/runtime import, unknown attribute exact error.

**Usage Example**
`uv run --locked python -I -c "import app.runtime,sys; print(any(x.startswith('app.utils.notifications') for x in sys.modules))"` → `False`.

**Quality Gates:**
```powershell
uv run --locked ruff format app/utils/__init__.py tests/utils/unit/test_lazy_public_api.py
uv run --locked ruff check app/utils/__init__.py tests/utils/unit/test_lazy_public_api.py
uv run --locked mypy app/utils/__init__.py tests/utils/unit/test_lazy_public_api.py
uv run --locked pytest tests/utils/unit/test_lazy_public_api.py -q
git diff --check
```

**Documentation Updates:** update only the existing `Public boundary` paragraph to state that exports resolve lazily and importing logger/runtime does not load notifications.

**Git Commit:** `refactor(utils): make public boundary lazy`

**Re-run safety:** Not safe — one-time eager-to-lazy conversion.

**Definition of Done:** exact exports preserved; eager notification import removed; tests pass; commit separately authorized.

#### - [ ] Task `P10-T02` — Specify notification delivery

**Traces to:** `R-01`, `R-04`, `Pilot A — Notifications`, `G10`
**Depends on:** P10-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Define one effectful notification delivery Protocol shared by the four transports.

**Context to Read (and nothing else):**
- `app/utils/notifications/manager.py` — current notifier protocol.
- `app/kernel/async_effects.py` — edge lifecycle type.
- Shared Contracts §3.6.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/notification/__init__.py` | CREATE | empty domain namespace |
| `app/capabilities/notification/delivery/__init__.py` | CREATE | empty capability namespace |
| `app/capabilities/notification/delivery/v1.py` | CREATE | delivery Protocol and immutable result |
| `tests/capabilities/notification/test_delivery_v1.py` | CREATE | contract tests |

**Specification (copy exactly):** `CAPABILITY_ID = "notification.delivery.v1"`; frozen `NotificationDeliveryResultV1(channel: str, status: Literal["accepted"], recipient_count: int | None)`; Protocol properties `channel: str`, `active: bool`; method `send(title: str, text: str, html_body: str | None = None) -> NotificationDeliveryResultV1`; `close() -> None`. Exact exports are constant, Protocol, result.

**Behaviour Rules:** effectful Protocol owns close; input validation stays provider-owned; contract imports no Utils/business provider.

**Implementation Steps:** create namespaces, value, Protocol, exact exports, fake conformance tests.

**DO NOT:** do not add async send; do not expose credentials/config; do not import Utils; do not touch PROTECTED paths.

**Unit Tests**
Exact exports, frozen result, fake send, fake close, provider-free import.

**Usage Example**
Construct fake Protocol implementation in test and send bounded text.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities/notification tests/capabilities/notification
uv run --locked ruff check app/capabilities/notification tests/capabilities/notification
uv run --locked mypy app/capabilities/notification tests/capabilities/notification
uv run --locked pytest tests/capabilities/notification -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(capabilities): add notification delivery v1`

**Re-run safety:** Safe — create-only.

**Definition of Done:** Protocol/result exact; import neutral; tests pass; commit separately authorized.

#### - [ ] Tasks `P10-T03a`–`P10-T03d` — Scope notification transports

**Traces to:** `Pilot A — Notifications`, `D-07`, `D-08`, `G10`
**Depends on:** P10-T02; execute a→b→c→d
**Estimated size:** M (50–120 LOC each)

**Goal.** Add one manifest/factory/example/test unit per existing transport without changing its current delivery semantics.

**Context to Read (and nothing else), per task:** the row's current module; `app/capabilities/notification/delivery/v1.py`; `app/kernel/effects.py`; `app/utils/notifications/manager.py`; the matching existing notification unit test from G2.

| Task | Channel | Current module | Provider folder | Provider ID | Unavailable external operation in tests |
|---|---|---|---|---|---|
| P10-T03a | email | `app/utils/notifications/email.py` | `app/utils/notifications/providers/email/` | `notification.delivery.email` | SMTP |
| P10-T03b | sms | `app/utils/notifications/sms.py` | `app/utils/notifications/providers/sms/` | `notification.delivery.sms` | HTTPS SMS gateway |
| P10-T03c | telegram | `app/utils/notifications/telegram.py` | `app/utils/notifications/providers/telegram/` | `notification.delivery.telegram` | Telegram HTTPS API |
| P10-T03d | desktop | `app/utils/notifications/desktop.py` | `app/utils/notifications/providers/desktop/` | `notification.delivery.desktop` | OS subprocess |

**Files to Create/Modify, per task:** `<folder>/manifest.toml` (CREATE), `<folder>/plugin.py` (CREATE), `<folder>/README.md` (CREATE), `<folder>/example.py` (CREATE), `tests/utils/providers/<provider-id>/test_provider.py` (CREATE). Only manifest and plugin count as production files.

**Specification (copy exactly):** manifest uses §3.6 identity, entry point `<folder-as-module>.plugin:create_provider`, all profiles, process scope, `reversible_ephemeral`, scoped lifecycle, config_restart. Factory receives config mapping containing exactly `configuration` with the existing opaque config object, constructs the existing private notifier, wraps its mapping result into `NotificationDeliveryResultV1`, registers `close` on scope, and returns the wrapper. Unknown/missing config raises `ValueError("{channel} notification provider requires only 'configuration'")`. Wrapper close is idempotent; if current notifier has no close, close only marks wrapper inactive.

**Behaviour Rules:** no network/subprocess at import or activation; external operation mocked; no silent channel fallback; accepted result parity; credentials never logged; example uses disabled config and prints `active=False` without delivery.

**Implementation Steps:** create strict manifest; implement scoped wrapper/factory; create README/example; add manifest/no-I/O/lifecycle/result/no-fallback tests; run existing channel tests.

**DO NOT:** do not send real notifications; do not log config; do not change current channel module; do not choose another channel; do not touch PROTECTED paths.

**Unit Tests**
Per provider: exact manifest, no import I/O, activation, send mapping parity with mock, close inactive/resource zero, no fallback.

**Usage Example**
Run `<folder>/example.py`; output `{channel}: active=False`, exit 0, no external call.

**Logging**
Provider logs only channel name and lifecycle state; never title/body/recipient/credential.

**Quality Gates, substitute the exact row values:** format/check/mypy the provider folder and exact test file; run exact provider test plus existing channel test; run exact example; `git diff --check`.

**Documentation Updates:** provider README only.

**Git Commits:**
- P10-T03a `refactor(notifications): add scoped email provider`
- P10-T03b `refactor(notifications): add scoped SMS provider`
- P10-T03c `refactor(notifications): add scoped Telegram provider`
- P10-T03d `refactor(notifications): add scoped desktop provider`

**Re-run safety:** Safe — each row is create-only.

**Definition of Done:** six provider tests pass; example exits 0 without external action; existing channel tests pass; exactly one separately authorized commit.

#### - [ ] Task `P10-T04` — Inject notification manager

**Traces to:** `D-10`, `Pilot A — Notifications`, `G10`
**Depends on:** P10-T03d
**Estimated size:** L (120–200 LOC)

**Goal.** Remove direct notifier construction from the manager and route the temporary Utils façade through injected delivery capabilities.

**Context to Read (and nothing else):**
- `app/utils/notifications/manager.py` — current direct constructors.
- `app/utils/notifications/__init__.py` — public façade.
- `app/composition/facade.py` — context binding.
- `app/capabilities/notification/delivery/v1.py` — Protocol.
- existing notification manager tests from G2.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/utils/notifications/manager.py` | MODIFY | accept injected delivery mapping |
| `app/utils/notifications/__init__.py` | MODIFY | retain exact callable façade |
| `tests/utils/providers/test_notification_composition.py` | CREATE | absence/replacement/no-fallback tests |

Anchors: `create_notification_manager` and `_Notifier`; preserve every public signature by adapting opaque channel configs through the bound runtime only at the façade boundary.

**Specification (copy exactly):** internal `NotificationManager` accepts `Mapping[str, NotificationDeliveryV1]`. `create_notification_manager` leases only explicitly supplied channel capabilities from bound runtime. Missing channel produces unavailable result for that channel; it never substitutes another. Close invokes every injected delivery close once then clears state.

**Behaviour Rules:** exact public exports/signatures; direct imports of Email/SMS/Telegram/Desktop constructors removed from manager; sent records are irreversible and never compensated on close; `app.runtime` imports with provider folders absent.

**Implementation Steps:** replace private Protocol/imports; lease explicit channels; preserve manager response mapping; close deliveries; add absence/replacement/import tests.

**DO NOT:** do not change response codes; do not fallback; do not resend/compensate; do not expose provider objects; do not touch PROTECTED paths.

**Unit Tests**
Existing manager tests plus: one missing channel, no fallback, replacement changes new manager generation, old manager closes, runtime import with notification providers absent.

**Usage Example**
Run four provider examples; manager test is the multi-provider usage proof.

**Logging**
Preserve secret-safe channel-only logs; no content/config.

**Quality Gates:**
```powershell
uv run --locked ruff format app/utils/notifications/manager.py app/utils/notifications/__init__.py tests/utils/providers/test_notification_composition.py
uv run --locked ruff check app/utils/notifications/manager.py app/utils/notifications/__init__.py tests/utils/providers/test_notification_composition.py
uv run --locked mypy app/utils/notifications/manager.py app/utils/notifications/__init__.py tests/utils/providers/test_notification_composition.py
uv run --locked pytest tests/utils -q -k 'notification'
git diff --check
```

**Documentation Updates:** none; the four provider READMEs created in P10-T03a–P10-T03d own lifecycle/removal evidence.

**Rollback:** close manager instances before reverting; no external compensation.

**Git Commit:** `refactor(notifications): inject delivery capabilities`

**Re-run safety:** Not safe — one-time construction change.

**Definition of Done:** no direct construction; no fallback; lifecycle tests zero resources; commit separately authorized.

#### - [ ] Task `P10-T05` — Specify tick stream

**Traces to:** `R-01`, `R-02`, `Pilot B — one Data stream`, `G10`
**Depends on:** P10-T04
**Estimated size:** M (50–120 LOC)

**Goal.** Define the effectful async tick-stream contract used by MT5 and deterministic fake providers.

**Context to Read (and nothing else):**
- `app/services/brokers/metatrader/snapshot_gateway.py` — async stream lifecycle.
- `app/services/data/market_events/__init__.py` — Data public stream behavior.
- `app/kernel/async_effects.py` — async owner.
- G2 report — canonical tick record type path.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/capabilities/data/__init__.py` | CREATE | empty namespace |
| `app/capabilities/data/tick_stream/__init__.py` | CREATE | empty namespace |
| `app/capabilities/data/tick_stream/v1.py` | CREATE | stream Protocol/request/event |
| `tests/capabilities/data/test_tick_stream_v1.py` | CREATE | contract tests |

**Specification (copy exactly):** `CAPABILITY_ID = "data.tick_stream.v1"`; frozen request fields `symbol: str`, `buffer_size: int = 256`; frozen event fields `sequence: int`, `symbol: str`, `payload: Mapping[str, object]`; Protocol `async def start(request)`, `def events() -> AsyncIterator[TickStreamEventV1]`, `async def stop()`, properties `active`, `generation_id`. Validate nonblank symbol, buffer 1..4096, sequence ≥1.

**Behaviour Rules:** no provider import; no broker types cross contract; payload immutable mapping; stop idempotency belongs provider conformance.

**Implementation Steps:** create namespaces/value/Protocol/validation/tests.

**DO NOT:** do not include credentials; do not define order mutation; do not import Brokers/Data; do not touch PROTECTED paths.

**Unit Tests**
Exact exports, request bounds, event sequence, fake async conformance, blocked business imports.

**Usage Example**
Test fake yields sequences 1,2,3 and stops.

**Quality Gates:**
```powershell
uv run --locked ruff format app/capabilities/data tests/capabilities/data/test_tick_stream_v1.py
uv run --locked ruff check app/capabilities/data tests/capabilities/data/test_tick_stream_v1.py
uv run --locked mypy app/capabilities/data tests/capabilities/data/test_tick_stream_v1.py
uv run --locked pytest tests/capabilities/data/test_tick_stream_v1.py -q
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `feat(capabilities): add tick stream v1`

**Re-run safety:** Safe — create-only.

**Definition of Done:** neutral async contract; bounds exact; tests pass; commit separately authorized.

#### - [ ] Task `P10-T06a` — Add MT5 tick stream

**Traces to:** `Pilot B — one Data stream`, `R-02`, `G10`
**Depends on:** P10-T05
**Estimated size:** L (120–200 LOC)

**Goal.** Adapt the existing read-only MT5 snapshot stream to the tick-stream contract with complete subscription/task/buffer/connection ownership.

**Context to Read (and nothing else):**
- `app/services/brokers/metatrader/snapshot_gateway.py` — bounded read stream.
- `app/services/brokers/metatrader/adapter.py` — read-only tick mapping.
- `app/capabilities/data/tick_stream/v1.py` — contract.
- `app/kernel/async_effects.py` — lifecycle owner.
- `docs/dev/plugin-decoupling/audit/G2_REPORT.md` — exact broker read/session requirement IDs.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/data/market_events/metatrader_tick_stream/manifest.toml` | CREATE | MT5 stream declaration |
| `app/services/data/market_events/metatrader_tick_stream/plugin.py` | CREATE | adapter/factory |
| `app/services/data/market_events/metatrader_tick_stream/README.md` | CREATE | ownership/removal record |
| `app/services/data/market_events/metatrader_tick_stream/example.py` | CREATE | guarded diagnostics |
| `tests/data/providers/data.tick_stream.metatrader/test_provider.py` | CREATE | conformance/lifecycle tests |

**Specification (copy exactly):** provider/capability values are §3.6; reload is `process_restart`; lifecycle scoped; effects reversible ephemeral; requirements are the exact broker read/session capability IDs and majors in G2. Factory configuration keys are exactly `symbol` and `buffer_size`. Sequence starts 1 for each generation. Upstream loss raises structured reason `LOST_DURING_OPERATION`.

**Behaviour Rules:** start owns task, subscription, buffer, and broker-session lease; stop closes reverse order; no order-command import; no external call at import/activation tests; optional real smoke only when `ENVIRONMENT=dev`, `ACCOUNT_MODE=demo`, and explicit credentials are present.

**Implementation Steps:** create manifest; adapt read stream; register four resource classes; add README/guarded example; add conformance/partial-start/upstream-loss/cleanup tests.

**DO NOT:** do not import `app.services.brokers.metatrader.commands`; do not open MT5 in quality gates; do not log credentials/account/full ticks; do not touch broker command files or other PROTECTED paths.

**Unit Tests**
Exact manifest, no-I/O import, read-only import graph, monotonic sequence, partial start cleanup, active lease drain, upstream loss, zero resources.

**Usage Example**
`uv run --locked python app/services/data/market_events/metatrader_tick_stream/example.py` → `MT5 smoke disabled`, exit 0 with no credentials.

**Logging**
Log provider ID, generation, state, and event count only.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/data/market_events/metatrader_tick_stream/plugin.py app/services/data/market_events/metatrader_tick_stream/example.py tests/data/providers/data.tick_stream.metatrader/test_provider.py
uv run --locked ruff check app/services/data/market_events/metatrader_tick_stream tests/data/providers/data.tick_stream.metatrader
uv run --locked mypy app/services/data/market_events/metatrader_tick_stream tests/data/providers/data.tick_stream.metatrader
uv run --locked pytest tests/data/providers/data.tick_stream.metatrader/test_provider.py -q -W error::ResourceWarning -W error::RuntimeWarning
uv run --locked python app/services/data/market_events/metatrader_tick_stream/example.py
git diff --check
```

**Documentation Updates:** MT5 provider README only.

**Rollback:** stop stream and close scope before revert; no persistent data is changed.

**Git Commit:** `refactor(data): add scoped MT5 tick stream`

**Re-run safety:** Safe when no active stream exists; tests use fakes.

**Definition of Done:** eight tests pass; example performs no external call; zero resources; commit separately authorized.

#### - [ ] Task `P10-T06b` — Add fake tick stream

**Traces to:** `Pilot B — one Data stream`, `R-02`, `G10`
**Depends on:** P10-T06a
**Estimated size:** M (50–120 LOC)

**Goal.** Add a deterministic fake provider used to prove stream lifecycle and replacement without MT5 access.

**Context to Read (and nothing else):**
- `app/capabilities/data/tick_stream/v1.py` — contract.
- `app/services/data/market_events/metatrader_tick_stream/manifest.toml` — manifest style.
- `app/kernel/async_effects.py` — lifecycle owner.
- `tests/data/providers/data.tick_stream.metatrader/test_provider.py` — conformance names.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/services/data/market_events/fake_tick_stream/manifest.toml` | CREATE | fake provider declaration |
| `app/services/data/market_events/fake_tick_stream/plugin.py` | CREATE | deterministic stream/factory |
| `app/services/data/market_events/fake_tick_stream/README.md` | CREATE | test-provider ownership record |
| `app/services/data/market_events/fake_tick_stream/example.py` | CREATE | deterministic usage evidence |
| `tests/data/providers/data.tick_stream.fake/test_provider.py` | CREATE | known-value/lifecycle tests |

**Specification (copy exactly):** provider/capability values are §3.6; no requirements; `config_restart`; process scope. For symbol `EURUSD`, emit exactly three payloads `{"bid": "1.1000"}`, `{"bid": "1.1001"}`, `{"bid": "1.1002"}` with sequences 1,2,3. Factory accepts only `symbol="EURUSD"` and `buffer_size=3`; other keys raise `ValueError("fake tick stream config must be symbol EURUSD and buffer_size 3")`.

**Behaviour Rules:** genuine async iterator; no sleep/network/database; stop idempotent; replacement uses new generation UUID; event identity `(generation_id, sequence)` unique.

**Implementation Steps:** create manifest; implement fake stream; register task/buffer cleanup; create README/example; add known-value/conformance/replacement tests.

**DO NOT:** do not label payload as live; do not persist events; do not use thread/sleep/network; do not touch PROTECTED paths.

**Unit Tests**
Manifest, exact three events, config rejection, stop twice, new generation, unique identities, zero counters.

**Usage Example**
`uv run --locked python app/services/data/market_events/fake_tick_stream/example.py` → three JSON lines with exact bids.

**Quality Gates:**
```powershell
uv run --locked ruff format app/services/data/market_events/fake_tick_stream/plugin.py app/services/data/market_events/fake_tick_stream/example.py tests/data/providers/data.tick_stream.fake/test_provider.py
uv run --locked ruff check app/services/data/market_events/fake_tick_stream tests/data/providers/data.tick_stream.fake
uv run --locked mypy app/services/data/market_events/fake_tick_stream tests/data/providers/data.tick_stream.fake
uv run --locked pytest tests/data/providers/data.tick_stream.fake/test_provider.py -q -W error::ResourceWarning -W error::RuntimeWarning
uv run --locked python app/services/data/market_events/fake_tick_stream/example.py
git diff --check
```

**Documentation Updates:** fake provider README only.

**Rollback:** close fake scope; revert create-only files.

**Git Commit:** `test(data): add deterministic fake tick stream`

**Re-run safety:** Safe — create-only and no I/O.

**Definition of Done:** seven tests pass; exact three-line example; zero resources; commit separately authorized.

#### - [ ] Task `P10-T07` — Prove effectful replacement

**Traces to:** `G10`, `H — Verify`
**Depends on:** P10-T06b
**Estimated size:** M (50–120 LOC)

**Goal.** Prove notification and stream activation failure, absence, upstream loss, drain, replacement, and cleanup as one system test.

**Context to Read (and nothing else):** notification composition test; fake tick provider; `app/composition/reconciliation.py`; `tests/removability/harness.py`; Phase 10 provider manifests.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/removability/test_effectful_pilots.py` | CREATE | cross-pilot lifecycle proof |

**Specification (copy exactly):** track counters `tasks`, `listeners`, `timers`, `clients`, `subscriptions`, `buffers`; each is zero before activation, expected positive while active, and zero after every success/failure/replacement branch. Assert event identity pairs unique.

**Behaviour Rules:** no external I/O; genuine coroutines; no sleep above 0.001s; absent notifications do not break runtime import; no fallback; failure reasons distinct.

**Implementation Steps:** add parameterized counter fixtures; test notification replacement; test stream drain/replacement; test partial failure; assert warning-free shutdown.

**DO NOT:** do not send/open live; do not hide leaked counters in teardown; do not use long sleeps; do not touch PROTECTED paths.

**Unit Tests**
Four tests: notification absence/no fallback, notification replacement, stream upstream loss/replacement, partial startup all-zero.

**Usage Example**
The fake stream example remains the executable proof.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/removability/test_effectful_pilots.py
uv run --locked ruff check tests/removability/test_effectful_pilots.py
uv run --locked mypy tests/removability/test_effectful_pilots.py
uv run --locked pytest tests/removability/test_effectful_pilots.py tests/utils/providers tests/data/providers -q -W error::ResourceWarning -W error::RuntimeWarning
uv run --locked python app/services/data/market_events/fake_tick_stream/example.py
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `test(removability): prove effectful provider lifecycle`

**Re-run safety:** Safe — fake-only.

**Definition of Done:** all counters zero; identities unique; warning-free; G10 passes.

**Phase 10 Exit Gate — all must be true before Phase 11 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] All provider examples exit 0 without external action.
- [ ] No PROTECTED mutation path imported by stream providers.
- [ ] No resource/warning leaks or duplicate events.
- [ ] G10 passes.

### Phase 11 — Deletion, Reinstall, Enforcement CI

**Goal:** turn provider absence into fast per-merge evidence plus slow physical-deletion/reinstall evidence.
**Why now:** broad waves must not proceed on config-disable claims alone.
**Deliverable:** generated matrices, copied-tree runner, CI scheduling, and inverse safety assertions.
**Phase Exit Gate:** G11 fast/slow/reinstall suites pass and are required at their assigned cadence.

#### - [ ] Task `P11-T01` — Gate configuration disablement

**Traces to:** `Phase 11` proof `1`, `G11`
**Depends on:** P10-T07
**Estimated size:** L (120–200 LOC)

**Goal.** Generate and execute a config-disable case for every manifest-classified optional provider on every merge.

**Context to Read (and nothing else):** `docs/dev/plugin-decoupling/audit/removability_matrix.json`; `app/kernel/discovery.py`; `app/composition/reconciliation.py`; pilot deletion tests; `.github/workflows/ci.yml`.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_disable_matrix.py` | CREATE | deterministic case generator/runner |
| `tests/removability/test_config_disable_matrix.py` | CREATE | parameterized fast gate |
| `.github/workflows/ci.yml` | MODIFY | add fast matrix to existing quality job |

Anchor: existing `Run CI quality gates` step; preserve it and add the new step immediately after.

**Specification (copy exactly):** generated case fields `provider_id`, `tier`, `provided_capabilities`, `expected_profiles_unready`, `expected_inactive_consumers`, `expected_reason`. Optional cases expect boot success and reason `DISABLED`; Tier C cases are excluded for P11-T03 inverse suite. CLI `--mode generate|run` and `--matrix <path>`.

**Behaviour Rules:** one case per optional provider; kernel/app boot; direct/transitive assertions; deterministic order; import-side-effect sentinel; no source deletion.

**Implementation Steps:** parse matrix; generate cases; add parameterized test; add CI step `uv run pytest tests/removability/test_config_disable_matrix.py -q`; verify case count equals optional provider count.

**DO NOT:** do not disable Tier C here; do not edit manifests; do not skip slow providers silently; do not touch protected paths except approved CI file.

**Unit Tests**
Generator schema/order/count plus parameterized current cases.

**Usage Example**
Run generator in `generate` then pytest in `run` mode.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_disable_matrix.py tests/removability/test_config_disable_matrix.py
uv run --locked ruff check scripts/architecture/provider_disable_matrix.py tests/removability/test_config_disable_matrix.py
uv run --locked mypy scripts/architecture/provider_disable_matrix.py tests/removability/test_config_disable_matrix.py
uv run --locked pytest tests/removability/test_config_disable_matrix.py -q
uv run --locked pre-commit run check-yaml --files .github/workflows/ci.yml
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `ci(removability): gate provider config disablement`

**Re-run safety:** Safe at exact workflow anchor.

**Definition of Done:** all optional providers represented; fast cases green; CI step present; commit separately authorized.

#### - [ ] Task `P11-T02` — Prove physical deletion

**Traces to:** `Phase 11` proof `2`, `G11`
**Depends on:** P11-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Add a fresh-process copied-tree physical deletion runner with Python/package/type/frontend verification.

**Context to Read (and nothing else):** disable matrix script; removability harness; momentum deletion proof; `pyproject.toml`; `app/ui/package.json`.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_deletion_matrix.py` | CREATE | copied-tree delete/reinstall runner |
| `tests/removability/test_physical_deletion_matrix.py` | CREATE | runner unit/current pilot tests |
| `.github/workflows/provider-removability.yml` | CREATE | nightly/release/manual slow workflow |

**Specification (copy exactly):** modes `--provider-id`, `--all`, `--reinstall`; copy exclusions from P9-T06. Validate resolved delete path is within copied `app/` and equals matrix `provider_path` before `shutil.rmtree`. Fresh process sequence exactly: import kernel; import app; resolve profiles; call affected capability; verify consumers; run unaffected test command list; assert deleted module absent from `sys.modules`; run `ruff check`, `mypy app tests`, package import, frontend build when frontend impact true.

**Behaviour Rules:** never delete source; one subprocess per stage; nonzero fails with provider/stage; workflow triggers schedule, workflow_dispatch, release published; next wave dry run must cite latest green result.

**Implementation Steps:** implement validated copy/delete; implement staged runner; add pilot unit tests; create Windows workflow using existing setup steps; upload bounded text report only.

**DO NOT:** do not use `git clean`, `rm -rf`, or source path deletion; do not reuse interpreter; do not omit sys.modules check; do not expose secrets.

**Unit Tests**
Reject source target, reject escaped path, delete pilot, fresh modules, stage failure report.

**Usage Example**
Run `--provider-id indicator.rsi.default` and obtain pass report.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_deletion_matrix.py tests/removability/test_physical_deletion_matrix.py
uv run --locked ruff check scripts/architecture/provider_deletion_matrix.py tests/removability/test_physical_deletion_matrix.py
uv run --locked mypy scripts/architecture/provider_deletion_matrix.py tests/removability/test_physical_deletion_matrix.py
uv run --locked pytest tests/removability/test_physical_deletion_matrix.py -q
uv run --locked pre-commit run check-yaml --files .github/workflows/provider-removability.yml
git diff --check
```

**Documentation Updates:** none.

**Rollback:** workflow removal and script/test revert; copied temp roots are pytest-cleaned.

**Git Commit:** `ci(removability): prove fresh-process provider deletion`

**Re-run safety:** Safe — all destructive action constrained to validated temp copy.

**Definition of Done:** source guard tested; fresh interpreter enforced; workflow scheduled; commit separately authorized.

#### - [ ] Task `P11-T03` — Prove reinstall and inverse safety

**Traces to:** `Phase 11` proof `3`, `Inverse assertion`, `G11`
**Depends on:** P11-T02
**Estimated size:** L (120–200 LOC)

**Goal.** Extend slow proof with provider reinstall/state restoration and Tier C fail-closed readiness/mutation assertions.

**Context to Read (and nothing else):** deletion matrix runner; stateful reinstall test; profile evaluator; G2 matrix; slow workflow.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/provider_deletion_matrix.py` | MODIFY | reinstall and Tier C modes |
| `tests/removability/test_required_provider_inverse.py` | CREATE | safety absence proof |
| `.github/workflows/provider-removability.yml` | MODIFY | run reinstall/inverse stages |

Anchors: runner mode dispatch and workflow test step; preserve deletion proof.

**Specification (copy exactly):** reinstall copies exact original provider folder back, starts new interpreter, checks compatible state and consumers active. Tier C business-safety absence expects kernel/API liveness true, affected profile ready false, mutation result `CAPABILITY_UNAVAILABLE` reason `PROFILE_REQUIREMENT_UNSATISFIED`; kernel/spec infrastructure absence expects import/boot failure. No weaker provider selection.

**Behaviour Rules:** one inverse case per Tier C row; kill-switch and live safety set explicit; historical data preserved; reinstall version same as removed; no production target.

**Implementation Steps:** add reinstall stage; add inverse case generation; add safety tests; extend workflow; assert counts equal matrix Tier C/removable counts.

**DO NOT:** do not call live mutation; do not classify unready as dead process; do not purge state; do not accept fallback; do not touch protected production paths.

**Unit Tests**
Reinstall pilot, retained-state fake, kernel absence boot fail, kill-switch absence live-unready, mutation blocked, no fallback.

**Usage Example**
Run slow runner with RSI `--reinstall`; consumers reactivate.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_deletion_matrix.py tests/removability/test_required_provider_inverse.py
uv run --locked ruff check scripts/architecture/provider_deletion_matrix.py tests/removability/test_required_provider_inverse.py
uv run --locked mypy scripts/architecture/provider_deletion_matrix.py tests/removability/test_required_provider_inverse.py
uv run --locked pytest tests/removability/test_stateful_provider_reinstall.py tests/removability/test_required_provider_inverse.py -q
uv run --locked pre-commit run check-yaml --files .github/workflows/provider-removability.yml
git diff --check
```

**Documentation Updates:** none.

**Rollback:** revert workflow/runner; no state purge.

**Git Commit:** `ci(removability): enforce reinstall and inverse safety`

**Re-run safety:** Safe — temp-copy and fake-state only.

**Definition of Done:** reinstall/current state proven; Tier C counts exact; mutation fail-closed; G11 passes.

**Phase 11 Exit Gate — all must be true before wave 12.1 starts:**
- [ ] Every task checked off.
- [ ] Full lint, type-check, tests, and 80% coverage pass.
- [ ] Fast matrix gates every merge.
- [ ] Physical deletion/reinstall/inverse workflow is green.
- [ ] No source workspace deletion occurs.
- [ ] Latest slow result is cited by wave 12.1 dry run.
- [ ] G11 passes.

### Phase 12 — Cross-Domain Waves

**Goal:** migrate every G2-classified provider in dependency order while preserving public contracts and financial behavior.
**Why now:** G0–G11 make provider extraction, absence, lifecycle, state, and deletion mechanically verifiable.
**Deliverable:** 21 separately approved waves and one generated, exact per-provider work-order appendix per wave.
**Phase Exit Gate:** each wave has its own exit gate; wave 12.21 leaves no internal compatibility import.

#### Mandatory wave work-order materialization contract

The first task in each wave generates `docs/dev/plugin-decoupling/waves/12.<n>.md` from the reviewed `G2_REPORT.md` and `removability_matrix.json`. No provider implementation task may start until that appendix contains no unresolved field and its structural test passes. The generator never chooses architecture; it copies reviewed G2 values into the following deterministic task groups for each provider, using ID `P12.<n>-P<three-digit-ordinal><suffix>`:

| Suffix | Exact purpose | Production-file limit |
|---|---|---|
| `a` | create provider-neutral capability spec and its namespace files | 3 |
| `b` | create provider manifest, implementation, and factory | 3 |
| `c1`, `c2`, … | migrate consumers in G2 order, maximum three files per task | 3 |
| `d` | retain/convert temporary compatibility façade | 3 |
| `e` | add provider README, example, root provider tests, and registry evidence | 1 documentation file; tests/examples excluded |
| `f` | add system absence, deletion, reinstall, profile, and parity proof | tests only |

If the reviewed G2 row declares an atomic bundle, one ordinal covers the bundle and lists every bundled capability. If it declares independent providers, each gets a separate ordinal. A generated task contains every mandatory field from the user task template, exact source and target paths, exact current/target signatures, manifest TOML, errors, test names/values, commands, commit, and task-specific protected paths. The generator exits 2 with `INCOMPLETE_G2_ROW: <provider-id>: <field>` when any of these fields is absent:

```text
provider_id, feature_id, tier, source_paths, target_provider_path,
capability_ids, capability_spec_paths, existing_public_signatures,
target_contracts, manifest_values, requirements, consumers,
compatibility_facades, profile_impact, effect_classes, state_ownership,
migration_ownership, parity_artifacts, test_commands, example_command,
removal_expectations, reinstall_expectations, protected_paths
```

Every generated provider follows steps A–J verbatim. Consumer `c*` tasks may depend only on the same provider's `a/b` tasks, earlier consumers, and already completed providers in the same/earlier waves. The generator rejects a later-wave dependency with `INVALID_WAVE_DEPENDENCY: <consumer> -> <provider>`.

#### Wave directives

| Wave | Required provider order | Additional fail-closed proof | Protected until later wave |
|---|---|---|---|
| 12.1 | kernel primitives; response/error contracts; time; identity; serialization; units; validation; security; settings/config; idempotency; state machine; logging; notifications; progress | `import app.runtime` with optional Utils providers absent | all business domains |
| 12.2 | connection/locking/transaction/ledger; dataset/event specs; historical storage/retrieval; normalization/alignment; resampling/closed bars; lineage/persistence; acquisitions | ledger checksum/tombstone and data-core required assertions | live Data stream providers |
| 12.3 | neutral specs; identity/venue; symbol metadata; read-only account/market; session lifecycle; snapshot gateways; MT5/cTrader/Binance/Dukascopy/Yahoo | no mutation capability in composition | every broker `commands.py` |
| 12.4 | broker stream adapter; normalization; sequencing; freshness/gaps; persistence/fan-out; reconnection | no duplicate events, stale/gap reasons exact | broker mutation |
| 12.5 | common specs; leaf indicators; structure/patterns; market-speed composites; regimes; snapshots/catalogue | every Phase0 indicator hash unchanged | none outside Indicators |
| 12.6 | evidence/metric contracts; leaf calculators; groups; comparison; reports; dashboards; journal/behavior; persistence; workbench | every Phase0 analytics hash unchanged | none outside Analytics |
| 12.7 | identity/version; parameter/config; declarations; signal; state/checkpoints; persistence; lifecycle/promotion; orchestration | strategy registry reconciled, never parallel | Trading/Risk mutations |
| 12.8 | positions/holdings; FX/valuation; exposure; margin; performance/reconciliation views | read-only; no execution authority | Portfolio actions |
| 12.9 | evidence/policy; limits; exposure/correlation; projections; policy; drawdown/loss; restrictions; kill switch; authorization; durable state; readiness | explicit positive authorization; kill switch non-disableable | Trading mutation |
| 12.10 | allocation proposals; rebalance proposals; transitions; Risk-review requests; evidence | emits proposals only | Trading execution |
| 12.11 | intent; order request; fill/lifetime; position/order state; session; idempotency; reconciliation; audit | no broker mutation | broker commands/live |
| 12.12 | intent/lineage validation; authorization requirement; preflight; cycle; timeout | no broker mutation; absence of denial is not consent | broker commands/live |
| 12.13 | clock; queue; replay; simulated broker/fills/account; Strategy/Risk/Trading integration; artifacts/lineage/reproduction/workbench/batching | full graph pinned per run; Phase0 simulator hashes unchanged | live mutation |
| 12.14 | translation; provider preflight; demo/live transports; cancel/close/modify; connection loss; unknown outcome | provider cannot grant permission | none inside approved broker mutation paths |
| 12.15 | evaluation; positive Risk authorization; idempotency; audit; reconciliation; kill switch; broker mutation; credential/profile binding | start demo/live only with complete safety set | none inside approved composition paths |
| 12.16 | datasets/leakage; pure features; statistics; seasonality; structure; studies/nulls; projections; persistence; drift; fundamental/sentiment; orchestration | absent tools degrade only declared consumers | none outside Research |
| 12.17 | search-space; objective; trial; sampler; simulator adapter; robustness/stability; persistence; orchestration/workbench | removing sampler removes only algorithm | none outside Optimization |
| 12.18 | contracts; manifests; model runtime; permissions; context/memory; tools; agents; deliberation/workflow; artifacts; API orchestration | no concrete Trading/Risk/Broker/Data/Research imports | all deterministic mutation authorities |
| 12.19 | identity/security/core health/error normalization; kernel resolution; route contributions; stable dispatch; generations; projections; compatibility routes; remove inventories/imports | stable paths/OpenAPI and structured unavailable response | UI production |
| 12.20 | typed client; store; shell; navigation; dynamic modules; unavailable/disabled/loading/stale/unhealthy; call prevention; deep links; readiness; absent builds | component/integration/browser unavailable-state evidence | backend contracts |
| 12.21 | remove internal compatibility imports and obsolete wrappers/inventories | full deletion matrix and public external compatibility proof | public external façades until evidence permits removal |

#### - [ ] Task `P12.1-T01` — Materialize Utils work orders

**Traces to:** `12.1`, `A — Removal boundary` through `J — Deletion proof`
**Depends on:** P11-T03
**Estimated size:** L (120–200 LOC generator; generated Markdown excluded)

**Goal.** Create the deterministic appendix generator and exact Utils provider tasks in G2 order.

**Context to Read (and nothing else):** `G2_REPORT.md`; `removability_matrix.json`; this phase's materialization contract; `app/utils/README.md`; `tests/architecture/test_g2_report.py`.

**Files to Create/Modify:** `scripts/architecture/provider_work_order_generator.py` (CREATE), `tests/architecture/test_provider_work_order_generator.py` (CREATE), `docs/dev/plugin-decoupling/waves/12.1.md` (CREATE).

**Specification (copy exactly):** CLI invocation is `uv run --locked python scripts/architecture/provider_work_order_generator.py --wave 12.1 --matrix docs/dev/plugin-decoupling/audit/removability_matrix.json --report docs/dev/plugin-decoupling/audit/G2_REPORT.md --output docs/dev/plugin-decoupling/waves/12.1.md`; require every field and generated template rule above; include only providers assigned to 12.1 and order by G2 `wave_ordinal`.

**Behaviour Rules:** byte-deterministic; no repository scan beyond inputs; no source modification; generated tasks satisfy file/LOC/step/title limits; every task traces to `12.1` and provider's existing verbatim Feature Registry requirement IDs.

**Implementation Steps:** implement strict input parser; validate fields/dependencies; render full tasks; add tests for missing field/order/sizing/determinism; generate appendix.

**DO NOT:** do not infer a missing path/signature/requirement; do not generate task placeholders; do not migrate code; do not touch PROTECTED paths.

**Unit Tests:** `test_rejects_incomplete_row`, `test_rejects_later_wave_dependency`, `test_generated_tasks_are_sized`, `test_generation_is_deterministic`, `test_utils_order_matches_directive`.

**Usage Example:** run exact CLI; appendix ends with its own self-verification PASS.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/provider_work_order_generator.py tests/architecture/test_provider_work_order_generator.py
uv run --locked ruff check scripts/architecture/provider_work_order_generator.py tests/architecture/test_provider_work_order_generator.py
uv run --locked mypy scripts/architecture/provider_work_order_generator.py tests/architecture/test_provider_work_order_generator.py
uv run --locked pytest tests/architecture/test_provider_work_order_generator.py -q
uv run --locked python scripts/architecture/provider_work_order_generator.py --wave 12.1 --matrix docs/dev/plugin-decoupling/audit/removability_matrix.json --report docs/dev/plugin-decoupling/audit/G2_REPORT.md --output docs/dev/plugin-decoupling/waves/12.1.md
git diff --check
```

**Documentation Updates:** generated 12.1 appendix only.

**Git Commit:** `docs(composition): materialize Utils provider work orders`

**Re-run safety:** Safe — same inputs produce identical appendix.

**Definition of Done:** five tests pass; appendix complete; no source code changed; commit separately authorized.

After P12.1-T01, execute every unchecked task in `waves/12.1.md` in order under the same wave approval. Do not start 12.2 until all generated tasks and the wave exit gate pass.

#### - [ ] Tasks `P12.2-T01`–`P12.21-T01` — Materialize remaining waves

Each task below is one documentation-only, one-commit materialization task. It uses the existing generator from P12.1-T01, creates exactly the listed appendix, and then the executor runs every generated provider task under that wave's single approval. All fields below are mandatory and exact for every row.

**Traces to:** the exact `12.2`–`12.21` value and `A — Removal boundary` through `J — Deletion proof` printed in the selected row.

**Depends on:** the preceding wave exit printed in the selected row.

**Estimated size:** S (<50 LOC) per generated appendix commit; no production code.

| Task | Traces to | Depends on | Output | Extra generator assertion | Commit message |
|---|---|---|---|---|---|
| P12.2-T01 | `12.2`, A–J | 12.1 exit | `waves/12.2.md` | Data core rows Tier C; immutable migration files never MODIFY | `docs(composition): materialize Data foundation work orders` |
| P12.3-T01 | `12.3`, A–J | 12.2 exit | `waves/12.3.md` | no broker mutation source path | `docs(composition): materialize Brokers read work orders` |
| P12.4-T01 | `12.4`, A–J | 12.3 exit | `waves/12.4.md` | stream dependencies follow 12.3 | `docs(composition): materialize Data live work orders` |
| P12.5-T01 | `12.5`, A–J | 12.4 exit | `waves/12.5.md` | leaves precede composites/regimes | `docs(composition): materialize Indicators work orders` |
| P12.6-T01 | `12.6`, A–J | 12.5 exit | `waves/12.6.md` | calculators precede reports/workbench | `docs(composition): materialize Analytics work orders` |
| P12.7-T01 | `12.7`, A–J | 12.6 exit | `waves/12.7.md` | one global resolver; old strategy registry becomes façade or is removed | `docs(composition): materialize Strategy work orders` |
| P12.8-T01 | `12.8`, A–J | 12.7 exit | `waves/12.8.md` | no action/mutation provider | `docs(composition): materialize Portfolio read work orders` |
| P12.9-T01 | `12.9`, A–J | 12.8 exit | `waves/12.9.md` | kill switch Tier C and authorization positive-only | `docs(composition): materialize Risk work orders` |
| P12.10-T01 | `12.10`, A–J | 12.9 exit | `waves/12.10.md` | proposals depend on Risk review, never Trading implementation | `docs(composition): materialize Portfolio action work orders` |
| P12.11-T01 | `12.11`, A–J | 12.10 exit | `waves/12.11.md` | contracts/state only; no broker command path | `docs(composition): materialize Trading state work orders` |
| P12.12-T01 | `12.12`, A–J | 12.11 exit | `waves/12.12.md` | authorization required; no mutation | `docs(composition): materialize Trading evaluation work orders` |
| P12.13-T01 | `12.13`, A–J | 12.12 exit | `waves/12.13.md` | every run pins all generations | `docs(composition): materialize Simulator work orders` |
| P12.14-T01 | `12.14`, A–J | 12.13 exit | `waves/12.14.md` | every mutation depends on authorization and kill switch | `docs(composition): materialize broker mutation work orders` |
| P12.15-T01 | `12.15`, A–J | 12.14 exit | `waves/12.15.md` | demo/live complete safety set exact | `docs(composition): materialize live composition work orders` |
| P12.16-T01 | `12.16`, A–J | 12.15 exit | `waves/12.16.md` | research/data name collision resolved by G2 target path | `docs(composition): materialize Research work orders` |
| P12.17-T01 | `12.17`, A–J | 12.16 exit | `waves/12.17.md` | one task set per sampler provider | `docs(composition): materialize Optimization work orders` |
| P12.18-T01 | `12.18`, A–J | 12.17 exit | `waves/12.18.md` | concrete deterministic-domain imports forbidden | `docs(composition): materialize Agentic work orders` |
| P12.19-T01 | `12.19`, A–J | 12.18 exit | `waves/12.19.md` | stable dispatch/generation; no route-table mutation loop | `docs(composition): materialize API work orders` |
| P12.20-T01 | `12.20`, A–J | 12.19 exit | `waves/12.20.md` | FEAT-UI unavailable/loading/stale/error/browser evidence | `docs(composition): materialize UI work orders` |
| P12.21-T01 | `12.21`, A–J | 12.20 exit | `waves/12.21.md` | internal compatibility import count reaches zero | `docs(composition): materialize cutover work orders` |

**Context to Read (and nothing else), each task:** `G2_REPORT.md`, `removability_matrix.json`, `provider_work_order_generator.py`, preceding wave appendix exit evidence, and the owning domain README named by the row.

**Files to Create/Modify, each task:** exactly one `waves/12.<n>.md` CREATE. No generator modification is permitted; if it cannot represent the reviewed row, stop and issue a separately approved plan delta.

**Specification (copy exactly):** run the P12.1 CLI with the task's wave/output; the appendix contains exact generated provider task blocks and one phase exit gate.

**Behaviour Rules:** output deterministic; only current-wave rows; dependencies same/earlier wave; extra assertion from table true; zero incomplete fields.

**Implementation Steps:** verify preceding exit; run generator; run structural validator; inspect zero incomplete markers; stage only appendix; commit if separately authorized.

**DO NOT:** do not edit generator; do not change G2 inputs; do not implement provider code in T01; do not start next wave; do not touch PROTECTED paths.

**Unit Tests:** run `test_provider_work_order_generator.py` plus generated appendix validator mode `--validate-only`.

**Usage Example:** `Get-Content <output> -TotalCount 20` shows wave title/source commit/provider count.

**Quality Gates:** run `uv run --locked pytest tests/architecture/test_provider_work_order_generator.py -q`; run the generator with the exact selected row's wave and output plus `--validate-only`; run `git diff --check`; `git diff --name-only` must contain only the selected output appendix.

**Documentation Updates:** exact output appendix only.

**Git Commit:** use the exact commit message in the selected table row.

**Re-run safety:** Safe — deterministic create; stop if file exists with different bytes.

**Definition of Done:** appendix complete; assertion true; only listed file changed; one separately authorized commit. Then execute its generated tasks in order before the next materializer.

#### Wave exit gate — applies separately to every 12.x wave

- [ ] Materializer task and every generated provider task checked off.
- [ ] Full Python lint/type-check/test/80% coverage green.
- [ ] Applicable frontend unit/type/build/E2E green.
- [ ] All new provider examples exit 0 without production action.
- [ ] Phase 0 parity artifacts unchanged.
- [ ] Config-disable proof passes on every merge.
- [ ] Physical deletion and reinstall proof passes before next wave.
- [ ] No path protected for a later wave appears in diff.
- [ ] Owning README registry evidence is updated while README remains canonical.
- [ ] Latest slow removability report is cited in the next wave dry run.

### Phase 16 — Executable Architecture Constraints

**Goal:** make every completed provider boundary, manifest, lifecycle, profile, UI, and removability rule mandatory in CI.
**Why now:** cutover must be enforced only after all waves can satisfy the rules.
**Deliverable:** static boundary lints, manifest/spec parity, evidence matrix, and manifest-to-README registry generation.
**Phase Exit Gate:** all Phase 16 constraints gate every merge and generated registries are byte-current.

#### - [ ] Task `P16-T01` — Enforce Python boundaries

**Traces to:** `Phase 16`
**Depends on:** P12.21-T01 and all generated 12.21 tasks
**Estimated size:** L (120–200 LOC)

**Goal.** Fail CI on kernel-to-business, spec-to-provider, cross-domain concrete-provider, unapproved dynamic-import, import-time-I/O, and internal compatibility-façade edges.

**Context to Read (and nothing else):** static graph script; final G2 matrix; 12.21 appendix; `scripts/ci_check.py`; `.github/workflows/ci.yml`.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/enforce_provider_boundaries.py` | CREATE | final AST/graph rule gate |
| `tests/architecture/test_enforce_provider_boundaries.py` | CREATE | rule fixtures/current tree |
| `scripts/ci_check.py` | MODIFY | run architecture gate after mypy and before pytest |

Anchor: `steps` list in `scripts/ci_check.py`; preserve existing four steps and insert `provider architecture` before pytest.

**Specification (copy exactly):** violation codes `KERNEL_BUSINESS_IMPORT`, `SPEC_PROVIDER_IMPORT`, `CROSS_DOMAIN_PROVIDER_IMPORT`, `DYNAMIC_IMPORT_NOT_ALLOWLISTED`, `PROVIDER_IMPORT_IO`, `INTERNAL_COMPATIBILITY_IMPORT`. Output one line `<code> <path>:<line> <target>`, sorted. Exit 0 no violations, 1 violations, 2 invalid audit input.

**Behaviour Rules:** scan AST and final matrix; only loader modules listed in matrix allow dynamic import; detect module-level calls matching network/database/thread/process/subscription constructors; tests may import concrete providers only inside provider-local tests and system deletion harnesses.

**Implementation Steps:** implement six checks; add fixtures for each; run current tree; insert CI step; assert zero violations.

**DO NOT:** do not add blanket allowlist; do not suppress a current violation; do not change production imports in this task; do not touch PROTECTED paths.

**Unit Tests**
One test per violation, deterministic ordering, current tree zero.

**Usage Example**
Run gate on repository; prints `provider architecture: PASS`.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/enforce_provider_boundaries.py tests/architecture/test_enforce_provider_boundaries.py scripts/ci_check.py
uv run --locked ruff check scripts/architecture/enforce_provider_boundaries.py tests/architecture/test_enforce_provider_boundaries.py scripts/ci_check.py
uv run --locked mypy scripts/architecture/enforce_provider_boundaries.py tests/architecture/test_enforce_provider_boundaries.py scripts/ci_check.py
uv run --locked pytest tests/architecture/test_enforce_provider_boundaries.py -q
uv run --locked python scripts/architecture/enforce_provider_boundaries.py --root . --matrix docs/dev/plugin-decoupling/audit/removability_matrix.json
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `ci(architecture): enforce provider import boundaries`

**Re-run safety:** Safe at exact CI anchor.

**Definition of Done:** six violation fixtures fail correctly; current tree passes; CI includes gate; commit separately authorized.

#### - [ ] Task `P16-T02` — Enforce provider manifests

**Traces to:** `Phase 16`
**Depends on:** P16-T01
**Estimated size:** L (120–200 LOC)

**Goal.** Enforce one valid manifest per provider, one stable spec per provided capability, resolvable requirements, deterministic selection, and no hard cycles.

**Context to Read (and nothing else):** kernel manifest/discovery/resolver; final removability matrix; boundary gate script; provider work-order generator.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/enforce_provider_manifests.py` | CREATE | manifest/spec/resolution gate |
| `tests/architecture/test_enforce_provider_manifests.py` | CREATE | invalid/current matrix tests |
| `scripts/ci_check.py` | MODIFY | add manifest gate after boundary gate |

Anchor: provider architecture step inserted by P16-T01.

**Specification (copy exactly):** violation codes `PROVIDER_MANIFEST_MISSING`, `PROVIDER_MANIFEST_DUPLICATE`, `CAPABILITY_SPEC_MISSING`, `REQUIREMENT_UNRESOLVED`, `HARD_DEPENDENCY_CYCLE`, `IMPORT_ORDER_SELECTION`, `PROFILE_SAFETY_INCOMPLETE`. Same output/exit contract as P16-T01.

**Behaviour Rules:** use kernel parser/resolver; compare final G2 provider paths; demo/live safety set exact; every required capability either binds or appears inactive with exact policy.

**Implementation Steps:** implement seven checks; add fixture tests; insert CI step; run current tree.

**DO NOT:** do not import provider entry points; do not auto-create a spec/manifest; do not downgrade required dependency; do not touch PROTECTED paths.

**Unit Tests:** one per violation plus current-tree pass.

**Usage Example:** gate prints `provider manifests: PASS`.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/enforce_provider_manifests.py tests/architecture/test_enforce_provider_manifests.py scripts/ci_check.py
uv run --locked ruff check scripts/architecture/enforce_provider_manifests.py tests/architecture/test_enforce_provider_manifests.py scripts/ci_check.py
uv run --locked mypy scripts/architecture/enforce_provider_manifests.py tests/architecture/test_enforce_provider_manifests.py scripts/ci_check.py
uv run --locked pytest tests/architecture/test_enforce_provider_manifests.py -q
uv run --locked python scripts/architecture/enforce_provider_manifests.py --root . --matrix docs/dev/plugin-decoupling/audit/removability_matrix.json
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `ci(architecture): enforce provider manifest graph`

**Re-run safety:** Safe at exact CI anchor.

**Definition of Done:** seven violations tested; current graph passes; CI gate active; commit separately authorized.

#### - [ ] Task `P16-T03` — Enforce removability evidence

**Traces to:** `Phase 16`, `Phase 11`
**Depends on:** P16-T02
**Estimated size:** M (50–120 LOC)

**Goal.** Require lifecycle, physical deletion, reinstall, profile, and UI unavailable-state evidence for every applicable provider.

**Context to Read (and nothing else):** final matrix; config-disable test; physical deletion workflow; UI Feature Registry tests; CI script.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/enforce_provider_evidence.py` | CREATE | evidence-path/count gate |
| `tests/architecture/test_enforce_provider_evidence.py` | CREATE | missing/current evidence tests |
| `scripts/ci_check.py` | MODIFY | add evidence gate after manifest gate |

**Specification (copy exactly):** every effectful row needs lifecycle test; every removable row needs config-disable and physical deletion/reinstall case; every profile-impact row needs readiness test; every UI row needs component/integration/browser unavailable evidence. Violation codes `LIFECYCLE_EVIDENCE_MISSING`, `DELETION_EVIDENCE_MISSING`, `REINSTALL_EVIDENCE_MISSING`, `PROFILE_EVIDENCE_MISSING`, `UI_UNAVAILABLE_EVIDENCE_MISSING`.

**Behaviour Rules:** evidence files must exist and collect at least one named test; production UI is not evidence; generated matrix case counts match provider counts.

**Implementation Steps:** map rows to evidence; validate files/test names; add fixtures/current-tree test; insert CI step.

**DO NOT:** do not count examples as tests; do not count production UI; do not skip Tier C inverse evidence; do not touch PROTECTED paths.

**Unit Tests:** five missing classes, empty test file rejection, current pass.

**Usage Example:** gate prints `provider evidence: PASS`.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/enforce_provider_evidence.py tests/architecture/test_enforce_provider_evidence.py scripts/ci_check.py
uv run --locked ruff check scripts/architecture/enforce_provider_evidence.py tests/architecture/test_enforce_provider_evidence.py scripts/ci_check.py
uv run --locked mypy scripts/architecture/enforce_provider_evidence.py tests/architecture/test_enforce_provider_evidence.py scripts/ci_check.py
uv run --locked pytest tests/architecture/test_enforce_provider_evidence.py tests/removability/test_config_disable_matrix.py -q
uv run --locked python scripts/architecture/enforce_provider_evidence.py --root . --matrix docs/dev/plugin-decoupling/audit/removability_matrix.json
git diff --check
```

**Documentation Updates:** none.

**Git Commit:** `ci(architecture): enforce provider removability evidence`

**Re-run safety:** Safe at exact CI anchor.

**Definition of Done:** all applicability counts exact; current tree passes; CI gate active; commit separately authorized.

#### - [ ] Task `P16-T04` — Generate feature registries

**Traces to:** `D-11`, `Phase 16`
**Depends on:** P16-T03
**Estimated size:** L (120–200 LOC)

**Goal.** Generate each README Feature Registry from manifests and atomically cut canonical authority from README input to manifest input.

**Context to Read (and nothing else):** `AGENTS.md` Manifest Authority Transition; `docs/ARCHITECTURE.md` provider architecture; final matrix; every owning README path listed by final matrix; existing feature-registry structural test.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `scripts/architecture/generate_feature_registries.py` | CREATE | manifest-to-table generator/checker |
| `tests/architecture/test_generated_feature_registries.py` | CREATE | byte-current/unique/count tests |
| `AGENTS.md` | MODIFY | make manifest canonical after generator is enforced |

Anchor: `Manifest Authority Transition`; replace transitional wording only after check mode passes all READMEs. `docs/ARCHITECTURE.md` requires a separate follow-up task if authority wording also exists there; stop rather than touch a fourth non-test file.

**Specification (copy exactly):** modes `--write` and `--check`; replace only content between one `### Feature Registry` heading and next same/higher heading; preserve all prose. Provider manifests carry existing feature ID/status/ownership/requirements/evidence metadata frozen by wave tasks. Generated rows sort feature ID then provider ID. Check mismatch exits 1 with `FEATURE_REGISTRY_STALE: <path>`.

**Behaviour Rules:** exactly one registry per owning README; no registry for infrastructure; no new feature ID; current totals derive from manifests; cutover occurs only when all check tests pass.

**Implementation Steps:** implement parser/renderer; add round-trip/no-infra/count tests; run write; run check; change AGENTS transition rule to canonical manifest/published README output.

**DO NOT:** do not rewrite README prose; do not invent IDs; do not change statuses; do not touch CHANGELOG or PROTECTED paths.

**Unit Tests:** round-trip, one registry, infrastructure excluded, unique IDs, totals, stale failure.

**Usage Example:** run `--check`; no output and exit 0.

**Quality Gates:**
```powershell
uv run --locked ruff format scripts/architecture/generate_feature_registries.py tests/architecture/test_generated_feature_registries.py
uv run --locked ruff check scripts/architecture/generate_feature_registries.py tests/architecture/test_generated_feature_registries.py
uv run --locked mypy scripts/architecture/generate_feature_registries.py tests/architecture/test_generated_feature_registries.py
uv run --locked pytest tests/architecture/test_generated_feature_registries.py tests/ui/structural/test_feature_registry.py -q
uv run --locked python scripts/architecture/generate_feature_registries.py --check --root .
git diff --check
```

**Documentation Updates:** `AGENTS.md` authority cutover plus generated README sections produced by tool. Because generated README files exceed three, they are outputs of the generator and must be committed in separately numbered mechanical subtasks emitted by the generator, maximum three READMEs per subtask.

**Git Commit:** `ci(architecture): generate manifest-backed feature registries`

**Re-run safety:** Safe after generator check; authority switch is one-time.

**Definition of Done:** generator/tests green; mechanical README subtasks complete; AGENTS authority switched; commit separately authorized.

**Phase 16 Exit Gate — all must be true before Phase 17 starts:**
- [ ] Every task and generated README subtask checked off.
- [ ] Full lint, type-check, tests, coverage, frontend gates green.
- [ ] All architecture/manifest/evidence gates run in CI.
- [ ] Registries are byte-current from manifests.
- [ ] No hard cycle, import-order selection, or internal façade import exists.
- [ ] Removability matrices regenerate deterministically.

### Phase 17 — Controlled Configuration Replacement

**Goal:** expose Tier-1 transactional reconciliation for already-installed first-party providers and prove rollback.
**Why now:** enforcement is complete; source-code and process replacement remain deferred.
**Deliverable:** controlled configuration controller and failure/rollback system proof.
**Phase Exit Gate:** candidate configuration succeeds atomically or restores the exact incumbent graph.

#### - [ ] Task `P17-T01` — Reconcile provider configuration

**Traces to:** `D-13`, `Phase 17` Tier `1`
**Depends on:** P16-T04 and generated subtasks
**Estimated size:** L (120–200 LOC)

**Goal.** Add a synchronous controller that validates a new installed-provider configuration, computes the affected set, applies reconciliation, and records bounded evidence.

**Context to Read (and nothing else):** `app/composition/reconciliation.py`; `app/composition/runtime.py`; `app/kernel/diagnostics.py`; `app/utils/settings/models.py`; final manifest architecture gate.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `app/composition/controller.py` | CREATE | controlled Tier-1 entry point |
| `app/composition/__init__.py` | MODIFY | export controller function/value |
| `tests/composition/test_configuration_controller.py` | CREATE | validation/switch evidence tests |

Anchor: exact composition `_EXPORTS`/`__all__`; preserve existing names and append `ConfigurationReplacementEvidence`, `replace_provider_configuration` in alphabetical order.

**Specification (copy exactly):** frozen evidence fields `request_id`, `changed_provider_ids`, `previous_generation_ids`, `active_generation_ids`, `rolled_back`, `completed_at`. Function `replace_provider_configuration(runtime, inventory, current, candidate, *, factories, request_id, clock) -> ConfigurationReplacementEvidence`. Validate nonblank request ID; reject any provider absent from initial inventory; source paths/modules are never rescanned/reloaded.

**Behaviour Rules:** sync; serialized by one controller lock; candidate validation precedes deactivation; evidence secret-safe; identical config returns no-change evidence with same generation IDs.

**Implementation Steps:** add value/function; validate request/inventory; delegate reconciliation; build UTC evidence; export; add tests.

**DO NOT:** do not watch files; do not reload modules; do not replace process-isolated/live native providers; do not log config; do not touch PROTECTED paths.

**Unit Tests:** no-op, installed switch, disabled provider, unknown provider before mutation, serialized calls, secret-free evidence.

**Usage Example:** switch two installed fake pure providers and print generation IDs only.

**Logging:** INFO request ID and changed IDs; ERROR rollback state; no config/credentials.

**Quality Gates:**
```powershell
uv run --locked ruff format app/composition/controller.py app/composition/__init__.py tests/composition/test_configuration_controller.py
uv run --locked ruff check app/composition/controller.py app/composition/__init__.py tests/composition/test_configuration_controller.py
uv run --locked mypy app/composition/controller.py app/composition/__init__.py tests/composition/test_configuration_controller.py
uv run --locked pytest tests/composition/test_configuration_controller.py tests/composition/test_reconciliation.py tests/composition/test_runtime.py -q
git diff --check
```

**Documentation Updates:** none; Phase 17 architecture already defines Tier 1.

**Rollback:** use previous configuration through same controller; restart with previous config if controller cannot restore.

**Git Commit:** `feat(composition): expose controlled config replacement`

**Re-run safety:** Safe — identical config is no-op.

**Definition of Done:** installed-only enforced; evidence bounded; no source reload; commit separately authorized.

#### - [ ] Task `P17-T02` — Prove transactional rollback

**Traces to:** `Phase 17` Tier `1`, `Definition of done`
**Depends on:** P17-T01
**Estimated size:** M (50–120 LOC)

**Goal.** Prove candidate failure leaves incumbent capabilities, generation pins, in-flight leases, resources, and profile readiness unchanged.

**Context to Read (and nothing else):** configuration controller test; reconciliation test; lifecycle test; profile test; simulator pinned-graph test generated in wave 12.13.

**Files to Create/Modify:**

| Path | Action | Purpose |
|---|---|---|
| `tests/composition/test_transactional_replacement_system.py` | CREATE | end-to-end rollback proof |

**Specification (copy exactly):** fake graph producer→consumer plus independent provider; candidate allocates task/listener/client then readiness fails. Capture incumbent leases/pin/readiness before call. After failure assert exact object identity for incumbent lease values, exact generation IDs, same readiness tuple, all candidate counters zero, incumbent counters unchanged. Error reason `ACTIVATION_FAILED`, `rolled_back=True` evidence.

**Behaviour Rules:** no sleeps over 0.001s; old in-flight lease remains valid; new lease after rollback is incumbent; deactivation order reverse; no warning leaks.

**Implementation Steps:** create counter fixtures; activate incumbent; pin graph/lease; apply failing candidate; assert restoration/cleanup; run successful candidate branch; shutdown all.

**DO NOT:** do not use live provider; do not mutate a generation; do not accept a new incumbent ID after rollback; do not touch PROTECTED paths.

**Unit Tests:** `test_failed_candidate_restores_exact_incumbent`, `test_inflight_lease_survives_successful_switch`, `test_successful_switch_drains_old_generation`, `test_candidate_cleanup_has_zero_resources`.

**Usage Example:** the system test is the executable Tier-1 proof; no standalone feature example is required for infrastructure.

**Quality Gates:**
```powershell
uv run --locked ruff format tests/composition/test_transactional_replacement_system.py
uv run --locked ruff check tests/composition/test_transactional_replacement_system.py
uv run --locked mypy tests/composition/test_transactional_replacement_system.py
uv run --locked pytest tests/composition/test_transactional_replacement_system.py tests/composition tests/kernel -q -W error::ResourceWarning -W error::RuntimeWarning
uv run --locked python scripts/ci_check.py
git diff --check
```

**Documentation Updates:** none.

**Rollback:** test-only commit; revert directly.

**Git Commit:** `test(composition): prove transactional provider rollback`

**Re-run safety:** Safe — fake-only.

**Definition of Done:** four tests pass; resources zero; incumbent exact after failure; full CI green.

**Phase 17 Exit Gate — all must be true:**
- [ ] P17 tasks checked off.
- [ ] Full backend/frontend gates green and coverage at least 80%.
- [ ] Installed-only Tier 1 switching and rollback proven.
- [ ] Tiers 2–3 remain absent.
- [ ] Live source-code HMR remains disabled.
- [ ] Full definition of done from source plan passes.

## 12. TRACEABILITY MAP

The source has no `FR-*` identifiers. This map uses only identifiers printed verbatim in `REFACTOR_PLAN.md`.

| Requirement ID | Task IDs |
|---|---|
| D-01 | P1-T02, P3-T01, P4-T01, P4-T03, P4-T06 |
| D-02 | P4-T01, P4-T05 |
| D-03 | P4-T02, P4-T04, P4-T05 |
| D-04 | P4-T02, P4-T05, P7-T02 |
| D-05 | P4-T05, P5-T03, P6-T02 |
| D-06 | P7-T01 |
| D-07 | P4-T02, P5-T01, P10-T03a–P10-T03d |
| D-08 | P4-T02, P5-T01, P5-T02, P5-T03 |
| D-09 | P1-T01, P8-T01, P8-T02 |
| D-10 | P1-T01, P6-T02, P10-T04 |
| D-11 | P16-T04 |
| D-12 | P1-T01, all generated provider `e/f` tasks |
| D-13 | P6-T03, P17-T01, P17-T02 |
| R-01 | P1-T02, P3-T02–P3-T04, P9-T01, P9-T03, P10-T02, P10-T05 |
| R-02 | P1-T02, P5-T01, P5-T03, P5-T04, P10-T05, P10-T06a, P10-T06b |
| R-03 | P1-T01, P1-T03, P3-T01, P4-T01, P6-T01 |
| R-04 | P3-T01–P3-T04 and every generated capability-spec task |
| R-05 | P4-T02, P4-T03 and every provider manifest task |
| R-06 | P1-T02, P1-T03, P6-T01 |
| R-07 | every phase/wave approval gate |
| G0 | P0-T01–P0-T04 |
| G1 | P1-T01–P1-T04 |
| G2 | P2-T01–P2-T05 |
| G3 | P3-T01–P3-T05 |
| G4 | P4-T01–P4-T06 |
| G5 | P5-T01–P5-T04 |
| G6 | P6-T01–P6-T03 |
| G7 | P7-T01–P7-T03 |
| G8 | P8-T01–P8-T03 |
| G9 | P9-T01–P9-T06 |
| G10 | P10-T01–P10-T05, P10-T06a, P10-T06b, P10-T07 |
| G11 | P11-T01–P11-T03 |
| 12.1 | P12.1-T01 and all tasks generated in `waves/12.1.md` |
| 12.2 | P12.2-T01 and all tasks generated in `waves/12.2.md` |
| 12.3 | P12.3-T01 and all tasks generated in `waves/12.3.md` |
| 12.4 | P12.4-T01 and all tasks generated in `waves/12.4.md` |
| 12.5 | P12.5-T01 and all tasks generated in `waves/12.5.md` |
| 12.6 | P12.6-T01 and all tasks generated in `waves/12.6.md` |
| 12.7 | P12.7-T01 and all tasks generated in `waves/12.7.md` |
| 12.8 | P12.8-T01 and all tasks generated in `waves/12.8.md` |
| 12.9 | P12.9-T01 and all tasks generated in `waves/12.9.md` |
| 12.10 | P12.10-T01 and all tasks generated in `waves/12.10.md` |
| 12.11 | P12.11-T01 and all tasks generated in `waves/12.11.md` |
| 12.12 | P12.12-T01 and all tasks generated in `waves/12.12.md` |
| 12.13 | P12.13-T01 and all tasks generated in `waves/12.13.md` |
| 12.14 | P12.14-T01 and all tasks generated in `waves/12.14.md` |
| 12.15 | P12.15-T01 and all tasks generated in `waves/12.15.md` |
| 12.16 | P12.16-T01 and all tasks generated in `waves/12.16.md` |
| 12.17 | P12.17-T01 and all tasks generated in `waves/12.17.md` |
| 12.18 | P12.18-T01 and all tasks generated in `waves/12.18.md` |
| 12.19 | P12.19-T01 and all tasks generated in `waves/12.19.md` |
| 12.20 | P12.20-T01 and all tasks generated in `waves/12.20.md` |
| 12.21 | P12.21-T01 and all tasks generated in `waves/12.21.md` |
| Phase 16 | P16-T01–P16-T04 |
| Phase 17 | P6-T03, P17-T01, P17-T02 |

Source checklist bullets without identifiers are covered by the phase/task whose `Traces to` cites their exact phase/step heading. The Definition of done and Stop conditions have no IDs; §9 records that fact, and every phase exit gate plus §14 maps their enforcement.

## 13. COMMIT SEQUENCE

Commits require separate owner authorization. Generated provider-task commits appear in their wave appendices between the corresponding materializer row and the next row.

| Order | Task ID | Commit message |
|---|---|---|
| 1 | P0-T01 | `test(architecture): record pre-composability baseline` |
| 2 | P0-T02 | `test(architecture): freeze financial baseline hashes` |
| 3 | P0-T03 | `test(architecture): scaffold fresh-process deletion harness` |
| 4 | P0-T04 | `test(architecture): certify composability baseline` |
| 5 | P1-T01 | `docs(architecture): define provider builder rules` |
| 6 | P1-T02 | `docs(architecture): freeze provider architecture` |
| 7 | P1-T03 | `docs(project): index provider infrastructure` |
| 8 | P1-T04 | `test(architecture): enforce provider governance` |
| 9 | P2-T01 | `build(architecture): extract static provider graph` |
| 10 | P2-T02 | `build(architecture): extract runtime configuration graphs` |
| 11 | P2-T03 | `build(architecture): extract state frontend graphs` |
| 12 | P2-T04 | `build(architecture): generate provider removability matrix` |
| 13 | P2-T05 | `docs(architecture): freeze G2 provider classifications` |
| 14 | P3-T01 | `feat(capabilities): create specification namespaces` |
| 15 | P3-T02 | `feat(capabilities): add indicator common v1 contract` |
| 16 | P3-T03 | `feat(capabilities): add RSI v1 contract` |
| 17 | P3-T04 | `feat(capabilities): add Williams R v1 contract` |
| 18 | P3-T05 | `test(capabilities): enforce provider-neutral imports` |
| 19 | P4-T01 | `feat(kernel): add validated provider identifiers` |
| 20 | P4-T02 | `feat(kernel): parse static provider manifests` |
| 21 | P4-T03 | `feat(kernel): discover first-party provider manifests` |
| 22 | P4-T04 | `feat(kernel): index immutable provider inventory` |
| 23 | P4-T05 | `feat(kernel): resolve provider dependency graph` |
| 24 | P4-T06 | `feat(kernel): expose bounded provider diagnostics` |
| 25 | P5-T01 | `feat(kernel): own synchronous provider effects` |
| 26 | P5-T02 | `feat(kernel): enforce component state transitions` |
| 27 | P5-T03 | `feat(kernel): coordinate provider lifecycle` |
| 28 | P5-T04 | `feat(kernel): adapt asynchronous provider edges` |
| 29 | P6-T01 | `feat(composition): define provider generations` |
| 30 | P6-T02 | `feat(composition): activate injected provider graph` |
| 31 | P6-T03 | `feat(composition): reconcile installed provider config` |
| 32 | P7-T01 | `feat(kernel): normalize capability unavailable errors` |
| 33 | P7-T02 | `feat(kernel): compute runtime profile readiness` |
| 34 | P7-T03 | `feat(runtime): enforce capability profile readiness` |
| 35 | P8-T01 | `feat(kernel): validate provider state metadata` |
| 36 | P8-T02 | `feat(data): validate retained migration tombstones` |
| 37 | P8-T03 | `test(removability): prove retained-state reinstall` |
| 38 | P9-T01 | `refactor(indicators): extract RSI default provider` |
| 39 | P9-T02 | `test(indicators): prove RSI provider parity` |
| 40 | P9-T03 | `refactor(indicators): extract Williams R provider` |
| 41 | P9-T04 | `test(indicators): prove Williams R provider parity` |
| 42 | P9-T05 | `refactor(indicators): route momentum façades through capabilities` |
| 43 | P9-T06 | `test(removability): prove momentum provider deletion` |
| 44 | P10-T01 | `refactor(utils): make public boundary lazy` |
| 45 | P10-T02 | `feat(capabilities): add notification delivery v1` |
| 46 | P10-T03a | `refactor(notifications): add scoped email provider` |
| 47 | P10-T03b | `refactor(notifications): add scoped SMS provider` |
| 48 | P10-T03c | `refactor(notifications): add scoped Telegram provider` |
| 49 | P10-T03d | `refactor(notifications): add scoped desktop provider` |
| 50 | P10-T04 | `refactor(notifications): inject delivery capabilities` |
| 51 | P10-T05 | `feat(capabilities): add tick stream v1` |
| 52 | P10-T06a | `refactor(data): add scoped MT5 tick stream` |
| 53 | P10-T06b | `test(data): add deterministic fake tick stream` |
| 54 | P10-T07 | `test(removability): prove effectful provider lifecycle` |
| 55 | P11-T01 | `ci(removability): gate provider config disablement` |
| 56 | P11-T02 | `ci(removability): prove fresh-process provider deletion` |
| 57 | P11-T03 | `ci(removability): enforce reinstall and inverse safety` |
| 58 | P12.1-T01 | `docs(composition): materialize Utils provider work orders` |
| 59–78 | P12.2-T01–P12.21-T01 | exact messages in Phase 12 table; generated provider commits precede each next materializer |
| 79 | P16-T01 | `ci(architecture): enforce provider import boundaries` |
| 80 | P16-T02 | `ci(architecture): enforce provider manifest graph` |
| 81 | P16-T03 | `ci(architecture): enforce provider removability evidence` |
| 82 | P16-T04 | `ci(architecture): generate manifest-backed feature registries` |
| 83 | P17-T01 | `feat(composition): expose controlled config replacement` |
| 84 | P17-T02 | `test(composition): prove transactional provider rollback` |

## 14. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Current baseline is red | High | High | EP-01 blocks G0; no failure waiver |
| Financial output changes during moves | Medium | Critical | byte hashes plus provider parity and full Phase 0 artifact gate |
| Migration ledger rejects removed owner | High | Critical | G1 tombstone policy; P8 checksum-preserving implementation; reinstall test |
| Resolver becomes a safety bypass | Medium | Critical | positive Risk authorization, profile readiness, Tier C inverse matrix |
| Import coupling moves into strings | Medium | High | five-graph audit plus Phase 16 string/dynamic import gates |
| Import-time I/O makes disablement false | Medium | High | no-I/O manifest/provider tests and Phase 16 lint |
| Config-disable hides physical coupling | High | High | fresh copied-tree interpreter deletion and `sys.modules` assertion |
| Cleanup places compensating trade | Low | Critical | effect-scope prohibition; mutation providers preserve/reconcile evidence only |
| State uses Python implementation paths | Medium | High | stable schema ID validation and state graph scan |
| Provider folder explosion | Medium | Medium | G2 natural-family bundling; split only for independent consumers/dependencies |
| Two registries coexist | Medium | High | Strategy reconciliation in 12.7 and Phase 16 single resolver gate |
| Route replacement corrupts FastAPI table | Medium | High | stable dispatch/generation rules in 12.19; no iterative route mutation |
| Async resource leak | Medium | High | genuine coroutines, reverse close, warning-as-error lifecycle suites |
| UI calls absent capability | Medium | High | typed readiness store, call prevention, deep-link unavailable E2E |
| Wave plan invents pre-audit paths | High | High | strict G2 row fields and deterministic appendix generator exit 2 |
| Approval cadence stalls migration | Medium | Medium | one approval per phase; each 12.x wave is one phase with generated mechanical tasks |
| Kernel absorbs business behavior | Medium | High | 600-LOC stop condition and business-import gate |

## SELF-VERIFICATION REPORT

1. **No placeholders in task bodies:** PASS. Code ellipses in §3 denote interface-only implementations, not undecided fields. Phase 12 generated tasks fail closed on every absent G2 value.
2. **Requirement IDs are verbatim:** PASS. Confirmed IDs are D-01–D-13 as present (with gaps only where source has none), R-01–R-07, G0–G11, 12.1–12.21, Phase 16, and Phase 17. Unconfirmed IDs: none.
3. **No vague implementation verbs:** PASS. The only banned-word match is the mandatory verbatim executor rule `"improve" the API`; no implementation step contains a banned vague verb.
4. **Task sizing:** PASS for explicitly emitted implementation tasks. Each touches at most three production files and stays at or below 200 production LOC. Parameterized notification tasks are separate commits. Phase 12 appendices split each provider into `a`–`f` tasks and consumer batches of at most three files.
5. **Existing/MODIFY artifacts are evidenced:** PASS. All master-plan MODIFY paths appear in §2 grounding or G2-dependent tasks stop until the reviewed artifact supplies exact anchors.
6. **Commands are verified:** PASS. Repository-wide commands come from inspected config/CI or were executed during grounding. Commands for future-created scripts are the exact CLIs those tasks create and test.

Final planner checks:

- Source plan SHA-256 recorded.
- Current commit and real red baseline recorded.
- No task authorizes a new dependency, live operation, data purge, source-code HMR, or commit without separate owner authority.
- README registry authority remains current until P16-T04.
- Every 12.x wave has a separate approval boundary.
- All decisions supplied by the owner are reflected in §3 or §7.

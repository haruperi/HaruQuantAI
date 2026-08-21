# A Python blueprint for spatiotemporal composability

Your four-level structure is a strong **static organization model**, but folders alone do not provide spatiotemporal composability. They tell developers where code belongs; they do not control imports, dependencies, timers, listeners, tasks, routes, services, or teardown.

The complete design should therefore be:

> **A small, non-removable composition kernel that dynamically mounts removable feature packages through versioned capability contracts and lifecycle-owned scopes.**

That maps closely to the Cordis model: components declare dependencies through a shared context, publish capabilities through stable keys, and register side effects through lifecycle-aware operations that are undone during teardown. The Cordis repository currently describes itself as under active development with an unstable API, and its paper is explicitly a preprint under revision, so I would adopt the architectural principles rather than attempt a literal Python port of its API. ([GitHub][1])

---

## 1. Decide what is actually composable

Your four tiers should not all become runtime plugins.

| Tier                   | Python representation                 | Architectural purpose                  | Runtime lifecycle               |
| ---------------------- | ------------------------------------- | -------------------------------------- | ------------------------------- |
| Domain                 | Package such as`app/services/data/` | Business ownership boundary            | Aggregate status only           |
| Feature                | Package such as`historical_bars/`   | One capability                         | Primary mount/unmount unit      |
| Responsibility         | File such as`retrieve.py`           | One use case or focused responsibility | Ordinary application code       |
| Functional requirement | Public class/function/method          | One defined behavior                   | Unit-test and traceability unit |

The **feature** should be the normal unit of composition.

A domain is a collection of independently composable features. Removing a domain means removing or disabling all its feature packages. Files and methods should not independently register themselves with the runtime.

This prevents turning the application into thousands of tiny plugins.

A public method should map clearly to one functional requirement, but this should be an ownership rule rather than a file-count rule. A class may contain several methods when they share the same invariant and responsibility; each method can still implement one behavior.

---

# 2. Add three non-business foundations

Your four-level rule applies inside business domains. A removable architecture also needs three supporting areas that are not themselves business tiers:

```text
app/
├── kernel/                 # Composition and lifecycle runtime
├── contracts/              # Stable cross-feature capability contracts
├── services/               # Business domains and removable features
├── composition/            # Configuration, discovery, bootstrap
├── api/                    # Optional stable public facade
└── __main__.py
```

Their responsibilities are:

| Foundation       | Responsibility                                                    |
| ---------------- | ----------------------------------------------------------------- |
| `kernel/`      | Context, scopes, effects, registry, graph, loader, reconciliation |
| `contracts/`   | Protocols, DTOs, events, capability identifiers                   |
| `composition/` | Desired configuration, feature discovery, application startup     |
| `services/`    | Actual business implementations                                   |

This separation is essential.

Suppose `research` directly imports this:

```python
from app.services.data.historical_bars.service import HistoricalBarsService
```

Deleting the historical-bars feature immediately breaks the import graph.

Instead, it should import a neutral contract:

```python
from app.contracts.data.historical_bars import HISTORICAL_BARS, HistoricalBars
```

The implementation may disappear while the stable contract remains. The registry simply has no active provider for that capability.

The contract package is not an implementation of the Data domain. It is the stable vocabulary through which the rest of the application can ask whether that capability exists.

---

# 3. Define four levels of removal guarantees

Do not begin with full hot module replacement. Build composability progressively.

| Level | Guarantee                 | Expected behavior                                                         |
| ----- | ------------------------- | ------------------------------------------------------------------------- |
| 1     | Configuration disable     | Feature is installed but disabled                                         |
| 2     | Package absent at startup | Feature code is physically unavailable, but startup succeeds              |
| 3     | Runtime unmount           | Active feature can be stopped and all owned runtime effects disappear     |
| 4     | Transactional replacement | Old version remains active until a replacement is validated and committed |

Implement them in this order.

Level 1 and Level 2 establish spatial composability.

Level 3 establishes temporal composability.

Level 4 is the advanced no-downtime replacement layer.

Your first architectural milestone should be:

> Remove one feature package from the source tree, start the application, and observe an unavailable capability rather than an import exception.

---

# 4. Phase 0 — Write the architecture contract

Before creating business code, create:

```text
docs/
├── architecture/
│   ├── composability.md
│   ├── capability-model.md
│   ├── lifecycle-model.md
│   └── dependency-rules.md
└── adr/
    ├── 0001-feature-is-composition-unit.md
    ├── 0002-neutral-capability-contracts.md
    ├── 0003-reversible-effect-scopes.md
    └── 0004-persistent-state-is-not-an-effect.md
```

The architecture document should establish these invariants.

| Invariant                      | Rule                                                                                                        |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| Kernel independence            | `app/kernel` never imports business features                                                              |
| Feature independence           | One feature never imports another feature implementation                                                    |
| Contract dependency            | Cross-feature calls use`app/contracts`                                                                    |
| Declared dependencies          | Every required and optional capability appears in the feature specification                                 |
| Scoped effects                 | Every listener, task, route, timer, service registration, and managed resource belongs to a feature scope   |
| No import effects              | Importing a module never starts work or mutates global application state                                    |
| Graceful absence               | Missing optional features do not prevent application startup                                                |
| Safe dependency loss           | Required consumers stop before their provider stops                                                         |
| State retention                | Unmounting does not automatically delete persistent state                                                   |
| Explicit criticality           | Deployment profiles, not feature code, decide which capabilities are mandatory                              |
| Irreversible-action separation | Trades, emails, database commits, and external commands are not treated as automatically reversible effects |

The last distinction is especially important.

Temporal composability can automatically reverse:

* Event-listener registration
* Service registration
* Timers
* Background tasks
* Router registration
* File watches
* Cache subscriptions
* Open sockets and pools
* Metric collectors

It cannot literally reverse:

* An executed trade
* A sent email
* A published external message
* A committed payment
* A durable business record

Those require idempotency, audit records, compensating operations, or explicit business policies.

Temporal composability is resource ownership, not time travel.

---

# 5. Phase 1 — Bootstrap the Python project

## 5.1 Initialize the project with uv

Using your existing Python standards:

```bash
# Check python version
python --version

# Initialize a new project
uv init --package project_name

# Add dev dependencies
uv add --dev \
  pytest \
  pytest-asyncio \
  pytest-cov \
  ruff \
  mypy \
  import-linter
```

`uv` supports application/library initialization and dependency groups, Ruff can be configured through `pyproject.toml`, and mypy provides a strict mode suitable for enforcing strongly typed architectural contracts. ([Astral Docs][2])

### Helpful Commands

- Add dependencies: `uv add <package>`
- Add dev dependencies: `uv add --dev <package>`
- Run the project: `uv run haruquantai`
- Sync environment: `uv sync`

## 5.2 Create a professional .gitignore

```bash
# Python
__pycache__/
*.py[cod]
*$py.class

# Environment
.venv/
venv/
ENV/
env/

# Distribution
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/

# Logs
logs/
*.log

# Temporary files
*.tmp
*.swp

# Data (optional)
data/
db/

# OS
.DS_Store
Thumbs.db

# Other
*.md
!README.md
```

## 5.3 Create the initial project structure:

```text
your-project/
├── pyproject.toml
├── uv.lock
├── app/
├── tests/
├── docs/
└── scripts/
```

## 5.4 Configure Project and linters

- Configure Ruff formatting.
- Configure Ruff linting.
- Configure Ruff import sorting.
- Configure Ruff security checks.
- Configure Ruff complexity rules.
- Configure Mypy strict typing.
- Configure Pytest.
- Configure coverage so that:
  - Overall project coverage must be at least 80%.
  - Coverage failures must fail the test command.
  - Each source file should target at least 80% coverage by test discipline.
- Configure Pre-commit.
- Install Pre-commit hooks.
- Create a simple source file and matching test file to verify the setup.
- Run all quality checks.
- Fix any issues found by the quality checks.
- Run the final full validation suite.
- Create the initial Git commit with the message:

```text
chore: initial project setup with quality tooling
```

```toml
[project]
requires-python = ">=3.14"

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.mypy]
python_version = "3.13"
strict = true
warn_unreachable = true
extra_checks = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Every domain and feature `__init__.py` should initially be empty:

```python
"""Historical-bars feature package."""
```

Do not use `__init__.py` to eagerly import and re-export every implementation. Eager re-exports recreate the exact hard dependency you are trying to remove.

---

# 6. Phase 2 — Create the capability catalog

Before implementing features, describe every feature in capability terms.

For example:

| Feature                            | Provides                   | Required capabilities                       | Optional capabilities | Removal result                           |
| ---------------------------------- | -------------------------- | ------------------------------------------- | --------------------- | ---------------------------------------- |
| `FEAT-BROKER-01` MT5 market data | `broker.market-data@1`   | `system.clock@1`                          | `system.metrics@1`  | MT5 market data becomes unavailable      |
| `FEAT-DATA-01` Historical bars   | `data.historical-bars@1` | `broker.market-data@1`                    | `data.bar-cache@1`  | Historical retrieval becomes unavailable |
| `FEAT-RES-01` Research dataset   | `research.dataset@1`     | `data.historical-bars@1`                  | —                    | Research feature becomes blocked         |
| `FEAT-TRADING-01` Live execution | `trading.execution@1`    | `broker.execution@1`, `risk.approval@1` | `notifications@1`   | Live trading becomes blocked             |

This table is more important than the folder tree because it defines the runtime graph.

## Capability granularity

Avoid this:

```python
class DataService(Protocol):
    async def historical_bars(...): ...
    async def realtime_ticks(...): ...
    async def symbol_info(...): ...
    async def economic_calendar(...): ...
```

That creates a monolithic Data capability where deleting one feature produces a partially functioning interface.

Prefer narrow capabilities:

```text
data.historical-bars@1
data.realtime-ticks@1
data.symbol-metadata@1
data.economic-calendar@1
```

Each can have an independent provider and lifecycle.

## Criticality belongs to deployment profiles

A feature should not declare itself globally mandatory.

For example:

```toml
[profiles.research]
required_capabilities = [
    "data.historical-bars@1",
    "research.dataset@1",
]

[profiles.live]
required_capabilities = [
    "broker.execution@1",
    "risk.approval@1",
    "trading.execution@1",
]
```

The Research profile can function without live execution. The Live profile must not become ready without a Risk capability.

This gives you an important safety property:

> Removing Risk does not crash the application, but it blocks every capability that is unsafe without Risk.

---

# 7. Phase 3 — Define neutral, versioned contracts

Create a contract package independent of implementations:

```text
src/app/contracts/
├── broker/
│   ├── market_data.py
│   └── execution.py
├── data/
│   ├── historical_bars.py
│   └── realtime_ticks.py
├── risk/
│   └── approval.py
└── system/
    ├── clock.py
    └── storage.py
```

Python `Protocol` is well suited to this because implementations can satisfy a contract structurally without inheriting from a common base class. ([Python documentation][3])

First create the generic capability identifier:

```python
# src/app/kernel/capability.py

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class CapabilityKey(Generic[T]):
    """Stable identifier for one versioned capability contract."""

    name: str
    major: int = 1

    @property
    def identifier(self) -> str:
        return f"{self.name}@{self.major}"
```

Then define the historical-bars contract:

```python
# src/app/contracts/data/historical_bars.py

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class HistoricalBarsRequest:
    symbol: str
    timeframe: str
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class Bar:
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoricalBars(Protocol):
    """Retrieve normalized historical bars."""

    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        ...


HISTORICAL_BARS = CapabilityKey[HistoricalBars](
    name="data.historical-bars",
    major=1,
)
```

Contract rules should be strict:

1. Contracts may import the generic kernel contract types.
2. Contracts may not import feature implementations.
3. Contracts must not expose MT5, Binance, SQLAlchemy, Pandas, FastAPI, or other adapter-specific objects unless the entire application intentionally adopts them as public boundary types.
4. Contract DTOs should preferably be immutable.
5. Breaking changes create a new major capability version.
6. Business exceptions should also be neutral contract types.

For example:

```python
class HistoricalBarsUnavailableError(RuntimeError):
    """No active historical-bars provider is available."""
```

---

# 8. Phase 4 — Define feature specifications

Each feature declares what it provides and consumes.

```python
# src/app/kernel/feature.py

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    feature_id: str
    domain: str
    provides: frozenset[CapabilityKey[Any]]
    requires: frozenset[CapabilityKey[Any]] = field(
        default_factory=frozenset
    )
    optional: frozenset[CapabilityKey[Any]] = field(
        default_factory=frozenset
    )
    conflicts: frozenset[str] = field(default_factory=frozenset)


class Feature(Protocol):
    spec: FeatureSpec

    async def mount(
        self,
        context: "FeatureContext",
        config: object,
    ) -> None:
        ...
```

The runtime should reject:

* Requesting a capability not listed in `requires` or `optional`
* Providing a capability not listed in `provides`
* Duplicate feature IDs
* Incompatible capability versions
* Ambiguous providers where only one is allowed
* Required dependency cycles

This turns the context into a controlled capability boundary rather than an unrestricted service locator.

## Recommended lifecycle states

```text
DISCOVERED
DISABLED
MISSING
BLOCKED
PREPARING
ACTIVE
QUIESCING
STOPPING
STOPPED
FAILED_IMPORT
FAILED_CONFIG
FAILED_START
FAILED_RUNTIME
```

Examples:

* Installed but disabled: `DISABLED`
* Configured but package deleted: `MISSING`
* Package exists but required provider does not: `BLOCKED`
* Mount raised an exception: `FAILED_START`
* Background task failed after activation: `FAILED_RUNTIME`

None of these states should automatically mean “the entire process must crash.”

The deployment profile determines whether the process is ready to serve work.

---

# 9. Phase 5 — Implement temporal scopes

This is the core of temporal composability.

Each active feature receives a private scope that owns everything the feature registers.

Python’s `AsyncExitStack` is a good primitive because it combines a variable number of synchronous and asynchronous resources and invokes cleanup callbacks in reverse registration order. Structured task ownership should also ensure that feature tasks are awaited or cancelled during teardown. ([Python documentation][4])

A conceptual implementation:

```python
# src/app/kernel/scope.py

import asyncio
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import AsyncExitStack
from typing import Any, TypeVar

T = TypeVar("T")


async def cancel_and_wait(task: asyncio.Task[Any]) -> None:
    if not task.done():
        task.cancel()

    await asyncio.gather(task, return_exceptions=True)


class FeatureScope:
    """Owns the reversible effects of one mounted feature."""

    def __init__(self, owner_id: str) -> None:
        self.owner_id = owner_id
        self._stack = AsyncExitStack()
        self._closed = False

    def callback(
        self,
        callback: Callable[..., Any],
        *args: object,
    ) -> None:
        self._stack.callback(callback, *args)

    def async_callback(
        self,
        callback: Callable[..., Awaitable[Any]],
        *args: object,
    ) -> None:
        self._stack.push_async_callback(callback, *args)

    def spawn(
        self,
        coroutine: Coroutine[Any, Any, T],
        *,
        name: str,
    ) -> asyncio.Task[T]:
        task = asyncio.create_task(
            coroutine,
            name=f"{self.owner_id}:{name}",
        )
        self.async_callback(cancel_and_wait, task)
        return task

    async def close(self) -> None:
        if self._closed:
            return

        self._closed = True
        await self._stack.aclose()
```

The real implementation should also record effect metadata:

```text
owner feature
effect type
resource name
created time
cleanup status
last failure
```

That allows the runtime to expose:

```text
FEAT-DATA-01 owns:
- 1 service binding
- 2 event listeners
- 1 background task
- 1 database pool
```

## FeatureContext operations

Features should never manipulate global registries directly. They should use operations such as:

```python
context.require(capability)
context.optional(capability)
context.provide(capability, implementation)
context.subscribe(event_type, handler)
context.spawn(coroutine, name="...")
context.enter_context(resource)
context.enter_async_context(resource)
context.register_callback(cleanup)
```

Each operation records its inverse in the feature scope.

Forbidden feature code:

```python
asyncio.create_task(run_forever())
global_registry["data"] = service
event_bus.subscribe("tick", handler)
app.add_route("/bars", endpoint)
scheduler.add_job(refresh)
```

Correct feature code:

```python
context.spawn(run_forever(), name="refresh")
context.provide(HISTORICAL_BARS, service)
context.subscribe(TickReceived, handler)
context.route("/bars", endpoint)
context.schedule(refresh, every=60)
```

Each `context.*` operation must register a disposer automatically.

## Mounting must be transactional

Conceptually:

```python
async def mount_feature(feature: Feature, config: object) -> None:
    scope = FeatureScope(feature.spec.feature_id)
    context = FeatureContext(scope=scope, ...)

    try:
        await feature.mount(context, config)
        await validate_feature_health(feature)
    except BaseException:
        await scope.close()
        raise

    store_active_scope(feature.spec.feature_id, scope)
```

If the third registration fails after two successful registrations, the first two must be undone before the error leaves `mount_feature`.

Later, you can add true atomic publication so no other feature sees partially registered services during `PREPARING`.

---

# 10. Classify all effects correctly

Every feature README should classify its behavior.

| Operation                 | Lifecycle-managed effect? | Unmount behavior             |
| ------------------------- | ------------------------: | ---------------------------- |
| Register service provider |                       Yes | Provider removed             |
| Subscribe to event        |                       Yes | Listener removed             |
| Start timer               |                       Yes | Timer cancelled              |
| Start background task     |                       Yes | Task cancelled and awaited   |
| Open database pool        |                       Yes | Pool closed                  |
| Mount HTTP route          |                       Yes | Route detached or disabled   |
| Add broker adapter        |                       Yes | Adapter unregistered         |
| Write cached bars         |         No, durable state | Retained                     |
| Apply database migration  |        No, durable schema | Retained                     |
| Send order to broker      |      No, external command | Reconcile/idempotency policy |
| Send email                |       No, external action | No automatic reversal        |
| Open a live position      |        No, business state | Position-management policy   |

A feature must not perform irreversible business operations merely because it was mounted.

Mounting should register capabilities and start controlled infrastructure. It should not place orders, send notifications, or change external business state.

---

# 11. Phase 6 — Implement the service registry

The registry maps capability keys to active providers:

```text
data.historical-bars@1
    provider: FEAT-DATA-01
    generation: 4
    status: ACTIVE
```

Every binding should have an ownership token:

```python
@dataclass(frozen=True, slots=True)
class BindingToken:
    capability: str
    owner_id: str
    generation: int
```

When a scope closes, it removes only its own exact binding. An old disposer must never be able to delete a newer replacement provider.

## Required dependency behavior

When a required provider disappears:

1. Mark dependent features as no longer eligible.
2. Quiesce and stop transitive dependents.
3. Stop the provider.
4. Mark dependents `BLOCKED`.
5. Restart them automatically if a compatible provider later returns.

Stop order is reverse topological order.

For example:

```text
MT5 Market Data
      ↓
Historical Bars
      ↓
Research Dataset
```

Removing MT5 stops:

```text
Research Dataset
Historical Bars
MT5 Market Data
```

Starting them occurs in the opposite order.

## Optional dependency behavior

For the first runtime version, use this simple rule:

> When the availability of an optional dependency changes, remount the consumer.

That is easier to reason about than dynamic mutable proxies.

Later, add a reactive reference:

```python
cache_ref = context.capability_ref(BAR_CACHE)
```

The feature can then observe the optional capability appearing or disappearing without a full remount.

Cordis expresses a similar model by storing services under stable context keys, declaring dependencies explicitly, and treating registrations as reversible effects. ([Deepseek Harness][5])

## Avoid stale service references

If a consumer stores a raw provider object, it must stop before that provider is disposed.

For the first implementation:

* Required dependency change → remount the consumer
* Optional dependency change → remount the consumer
* Public facade → resolve the service from the registry for every call

Later, introduce leases or generation-aware `CapabilityRef` proxies when uninterrupted provider swapping is required.

---

# 12. Phase 7 — Implement the dependency graph and reconciler

The application configuration describes the **desired state**.

The runtime maintains the **actual state**.

The reconciler continuously compares them.

```text
Desired features
       +
Discovered feature factories
       +
Available capability providers
       ↓
Validated target dependency graph
       ↓
Stop plan + Start plan
       ↓
Actual active graph
```

A reconciliation pass should:

1. Discover available feature factories.
2. Read and validate configuration.
3. Validate unique feature and capability IDs.
4. Select providers.
5. Detect required dependency cycles.
6. Determine which enabled features are eligible.
7. Calculate features to stop.
8. Stop them in reverse dependency order.
9. Calculate features to start.
10. Start them in dependency order.
11. Repeat until no new capabilities enable additional features.
12. Publish a complete status report.

A feature is eligible when:

```text
enabled
AND package exists
AND configuration is valid
AND every required capability has a selected active provider
AND no declared conflict is active
```

Required dependency cycles should initially be rejected completely. Supporting cyclic startup introduces complexity with little value for this architecture.

---

# 13. Phase 8 — Add declarative configuration and discovery

A deployment configuration might look like this:

```toml
[application]
profile = "research"

[features."FEAT-BROKER-MT5-01"]
enabled = true

[features."FEAT-BROKER-MT5-01".config]
terminal_path = "C:/MetaTrader 5/terminal64.exe"

[features."FEAT-DATA-01"]
enabled = true

[features."FEAT-DATA-01".config]
default_timeframe = "M1"
cache_enabled = true

[features."FEAT-RES-01"]
enabled = true
```

The loader should tolerate this situation:

```toml
[features."FEAT-DATA-01"]
enabled = true
```

while the feature package no longer exists.

The result should be:

```text
FEAT-DATA-01: MISSING
data.historical-bars@1: UNAVAILABLE
FEAT-RES-01: BLOCKED
application process: RUNNING
research profile readiness: NOT READY
```

That is graceful capability loss.

## Feature discovery

For installed plugins, use Python package entry points:

```toml
[project.entry-points."your_project.features"]
historical-bars = "app.services.data.historical_bars.feature:create_feature"
mt5-market-data = "app.services.broker.mt5_market_data.feature:create_feature"
```

Then discover them with `importlib.metadata.entry_points()`.

Python’s package metadata API supports entry-point-based discovery for installed distributions, making it suitable for external plugin packages. ([Python documentation][6])

The loader must isolate failures:

| Failure                       | Runtime result     |
| ----------------------------- | ------------------ |
| Entry point target absent     | `MISSING`        |
| Third-party dependency absent | `FAILED_IMPORT`  |
| Invalid feature specification | `FAILED_SPEC`    |
| Invalid config                | `FAILED_CONFIG`  |
| Mount error                   | `FAILED_START`   |
| Background task error         | `FAILED_RUNTIME` |

Do not catch every `ModuleNotFoundError` and misreport it as “feature missing.” Distinguish between:

* The feature module itself being absent
* A dependency imported by that feature being absent

## Configuration reconciliation

When configuration changes, default to:

```text
validate new config
→ stop/remount affected feature
→ reconcile dependents
```

Do not mutate dozens of fields on a live feature object unless that feature has an explicitly designed reconfiguration protocol.

Remounting naturally applies the old scope’s cleanup and creates a fresh scope.

---

# 14. Phase 9 — Build the first vertical feature pair

Do not begin with all domains. Build two features:

1. One provider
2. One consumer

For example:

```text
FEAT-BROKER-01
    provides broker.market-data@1

FEAT-DATA-01
    requires broker.market-data@1
    provides data.historical-bars@1
```

## Data feature package

```text
src/app/services/data/
└── historical_bars/
    ├── __init__.py
    ├── manifest.py
    ├── config.py
    ├── validate_request.py
    ├── retrieve.py
    ├── normalize.py
    ├── feature.py
    └── README.md
```

Mapping:

| File                    | Responsibility                            |
| ----------------------- | ----------------------------------------- |
| `manifest.py`         | Feature identity and dependencies         |
| `config.py`           | Feature configuration validation          |
| `validate_request.py` | Validate historical-data requests         |
| `retrieve.py`         | Orchestrate historical-bar retrieval      |
| `normalize.py`        | Convert provider data into canonical bars |
| `feature.py`          | Compose and mount the feature             |
| `README.md`           | Capability and removal contract           |

The implementation:

```python
# src/app/services/data/historical_bars/retrieve.py

from collections.abc import Sequence

from app.contracts.broker.market_data import BrokerMarketData
from app.contracts.data.historical_bars import (
    Bar,
    HistoricalBarsRequest,
)


class HistoricalBarsService:
    """Historical-bars use case."""

    def __init__(self, market_data: BrokerMarketData) -> None:
        self._market_data = market_data

    async def retrieve(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        raw_bars = await self._market_data.retrieve_bars(request)
        return normalize_bars(raw_bars)
```

The feature wiring:

```python
# src/app/services/data/historical_bars/feature.py

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.feature import FeatureSpec
from app.services.data.historical_bars.retrieve import (
    HistoricalBarsService,
)


class HistoricalBarsFeature:
    spec = FeatureSpec(
        feature_id="FEAT-DATA-01",
        domain="data",
        provides=frozenset({HISTORICAL_BARS}),
        requires=frozenset({BROKER_MARKET_DATA}),
    )

    async def mount(
        self,
        context: "FeatureContext",
        config: object,
    ) -> None:
        market_data = context.require(BROKER_MARKET_DATA)

        service = HistoricalBarsService(
            market_data=market_data,
        )

        context.provide(
            HISTORICAL_BARS,
            service,
        )


def create_feature() -> HistoricalBarsFeature:
    return HistoricalBarsFeature()
```

Notice what is absent:

```python
from app.services.broker.mt5_market_data import ...
```

The Data feature knows the broker contract, not the MT5 implementation.

Therefore either MT5, cTrader, Binance, a simulation provider, or a test provider can satisfy the capability.

---

# 15. Verify the deletion behavior immediately

After implementing those two features, test these scenarios before building anything else.

## Scenario A — Consumer deleted

Delete `historical_bars/`.

Expected:

```text
broker.market-data@1: ACTIVE
data.historical-bars@1: UNAVAILABLE
application: RUNNING
```

## Scenario B — Provider deleted

Delete the selected broker-market-data provider.

Expected:

```text
broker.market-data@1: UNAVAILABLE
FEAT-DATA-01: BLOCKED
data.historical-bars@1: UNAVAILABLE
application: RUNNING
```

## Scenario C — Replacement provider installed

Install another feature providing `broker.market-data@1`.

Expected:

```text
new broker provider: ACTIVE
FEAT-DATA-01: automatically becomes eligible
FEAT-DATA-01: ACTIVE
data.historical-bars@1: ACTIVE
```

## Scenario D — All Data features deleted

Expected:

```text
Data domain: no active capabilities
other domains: unaffected unless they explicitly require Data capabilities
application shell: RUNNING
```

This is the point where the architecture proves its value.

---

# 16. Phase 10 — Introduce typed events carefully

Not every interaction should use events.

Use a capability service for direct work:

```python
bars = await historical_bars.retrieve(request)
```

Use events for published facts:

```text
TickReceived
OrderFilled
FeatureActivated
FeatureStopped
RiskLimitBreached
```

Use an interceptor or pipeline for policy extension:

```text
OrderProposal
    → market-session policy
    → news policy
    → exposure policy
    → risk approval
    → final decision
```

Cordis explicitly treats event dispatch mode as part of the event’s public contract, distinguishing observational, serial, parallel, and waterfall-style dispatch. The same principle is useful in Python: every event should declare whether handlers observe, transform, run concurrently, or can short-circuit a decision. ([Deepseek Harness][5])

For example:

```python
class EventMode(Enum):
    PUBLISH = "publish"
    SERIAL = "serial"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
```

Each subscription returns a token or disposer, and the feature context records it:

```python
context.subscribe(
    RiskLimitBreached,
    service.handle_risk_breach,
)
```

On unmount, the subscription disappears automatically.

## Registry-contributor pattern

Some features should not provide a completely new top-level service. They contribute to a registry owned by another feature.

For example:

```text
Broker Registry Feature
    provides broker.registry@1

MT5 Adapter Feature
    requires broker.registry@1
    registers adapter "mt5"

Binance Adapter Feature
    requires broker.registry@1
    registers adapter "binance"
```

The adapter registration must return a disposer:

```python
disposer = broker_registry.register(
    name="mt5",
    adapter=adapter,
)

context.register_callback(disposer)
```

Removing MT5 unregisters only the MT5 adapter.

This pattern works particularly well for:

* Broker adapters
* Indicators
* Strategies
* Data providers
* Optimization algorithms
* Research analyzers
* Agent tools
* UI panels

---

# 17. Phase 11 — Design persistent state ownership

Shared databases can silently destroy composability.

Each feature should declare:

```text
State namespace
Schema version
Migration owner
Retention policy
Export policy
Purge command
```

Example:

```text
Feature: FEAT-DATA-01
Namespace: data.historical_bars
Schema version: 3
Unload policy: retain
Uninstall policy: retain
Purge policy: explicit administrator action
```

Rules:

1. A feature owns its logical tables, collections, cache keys, and files.
2. Another feature may not query those tables directly.
3. Other features access the data through capability contracts.
4. Unmounting never drops tables.
5. Uninstalling does not implicitly drop state.
6. State deletion is an explicit administrative operation.
7. Shared ORM entities should not cross domain boundaries.
8. Rolling replacement requires schema compatibility between old and new versions.

A generic database or object-store connection may be provided as an infrastructure capability:

```text
storage.database@1
storage.object-store@1
```

The Data feature can require the database capability while retaining ownership of its own repository and schema.

---

# 18. Handle irreversible actions separately

For a trading system, this is critical.

Consider:

```text
FEAT-TRADING-LIVE
    requires:
        broker.execution@1
        risk.approval@1
        portfolio.positions@1
```

Unmounting this feature should:

1. Stop accepting new order requests.
2. Mark the provider as quiescing.
3. Unpublish the execution capability.
4. Wait for or cancel in-flight internal operations.
5. Reconcile broker acknowledgements.
6. Flush audit records.
7. Close broker resources.
8. Leave already executed trades and open positions under explicit position-management policy.

It must not blindly “reverse” live orders merely because the plugin was removed.

External commands should use:

* Idempotency keys
* Durable command records
* Broker reconciliation
* Explicit command states
* Audit logs
* Retry classification
* Compensating actions where valid
* Kill-switch policies

This is where spatiotemporal composability and business transaction safety meet, but they are not the same mechanism.

---

# 19. Phase 12 — Make the public API capability-aware

A stable Python facade can remain available even when an implementation is absent.

```python
class DataAPI:
    def __init__(self, registry: ServiceRegistry) -> None:
        self._registry = registry

    async def historical_bars(
        self,
        request: HistoricalBarsRequest,
    ) -> Sequence[Bar]:
        service = self._registry.require(HISTORICAL_BARS)
        return await service.retrieve(request)
```

When unavailable, raise an explicit error:

```python
CapabilityUnavailableError(
    capability="data.historical-bars@1",
    blocked_by="broker.market-data@1",
)
```

The facade imports contracts and the registry. It does not import the feature implementation.

## HTTP API

Expose a capability endpoint:

```http
GET /system/capabilities
```

Example response:

```json
{
  "data.historical-bars@1": {
    "available": false,
    "provider": null,
    "reason": "Required capability broker.market-data@1 is unavailable"
  },
  "data.realtime-ticks@1": {
    "available": true,
    "provider": "FEAT-DATA-02"
  }
}
```

The UI can then:

* Hide unavailable panels
* Disable unavailable commands
* Display dependency reasons
* Avoid calling missing endpoints
* Refresh when capability state changes

For runtime-removable routes, avoid permanent import-time route decoration:

```python
@app.get("/historical-bars")
async def historical_bars(...):
    ...
```

Prefer route registration through a lifecycle-managed router registry:

```python
context.route(
    method="GET",
    path="/historical-bars",
    handler=endpoint,
)
```

Removing the feature removes or disables its routes and invalidates the generated API catalog.

---

# 20. Separate liveness from readiness

The application process should usually remain alive so it can explain why a capability is unavailable.

| State     | Meaning                                                               |
| --------- | --------------------------------------------------------------------- |
| Liveness  | Kernel, loader, diagnostics, and control plane are running            |
| Readiness | The selected deployment profile has all required capabilities         |
| Degraded  | Process works, but one or more noncritical capabilities are missing   |
| Unsafe    | A required safety capability is missing; relevant actions are blocked |

For example:

```text
Risk feature missing:
    process live: yes
    research ready: yes
    live trading ready: no
    live order endpoint: blocked
```

This is much safer and more diagnosable than terminating the entire process with an import error.

---

# 21. Phase 13 — Enforce the architecture automatically

Architectural rules that exist only in documentation will eventually be violated.

Import Linter supports forbidden-import, independence, layering, protected-module, and cycle-oriented contracts, so it can enforce much of the static dependency model in CI. ([Import Linter][7])

An initial configuration could include:

```ini
[importlinter]
root_package = app

[importlinter:contract:kernel-independent]
name = Kernel must not import application layers
type = forbidden
source_modules =
    app.kernel
forbidden_modules =
    app.contracts
    app.services
    app.api
    app.composition

[importlinter:contract:contracts-independent]
name = Contracts must not import implementations
type = forbidden
source_modules =
    app.contracts
forbidden_modules =
    app.services
    app.api
    app.composition

[importlinter:contract:api-does-not-import-services]
name = Public API resolves capabilities rather than implementations
type = forbidden
source_modules =
    app.api
forbidden_modules =
    app.services
```

Generate feature-independence contracts from the feature catalog so that:

```text
app.services.data.historical_bars
```

cannot import:

```text
app.services.data.realtime_ticks
app.services.broker.mt5_market_data
app.services.research.edge_analysis
```

Additional AST checks should reject:

* `asyncio.create_task()` outside the kernel
* Direct writes to the global service registry
* Import-time network or database calls
* Import-time route decoration
* Feature modules calling `logging.basicConfig()`
* Mutable module-level service singletons
* Direct cross-feature database repository imports
* Undeclared dynamic imports

---

# 22. Build composability tests, not only business tests

Your test suite should contain four categories.

## A. Functional-requirement tests

Mirror the feature structure:

```text
tests/services/data/historical_bars/
├── test_validate_request.py
├── test_retrieve.py
├── test_normalize.py
└── test_feature.py
```

Each test should map to a functional requirement.

## B. Feature contract tests

Every feature should pass the same reusable suite:

```text
Feature ID is unique
Provided capability matches its Protocol
Only declared dependencies are requested
Invalid config produces no effects
Mount succeeds with valid dependencies
Unmount is idempotent
```

## C. Lifecycle-leak tests

Capture the runtime before mount:

```text
providers
listeners
tasks
routes
timers
open resources
```

Mount and unmount the feature, then assert that the runtime snapshot returns to the exact baseline.

Essential tests:

| Test                                     | Expected result                             |
| ---------------------------------------- | ------------------------------------------- |
| Mount failure after partial registration | All earlier registrations removed           |
| Mount/unmount repeated 100 times         | No accumulating effects                     |
| Background task active during unmount    | Task cancelled and awaited                  |
| Listener registered during mount         | Listener absent after unmount               |
| Provider replaced                        | Old disposer cannot delete new provider     |
| Unmount called twice                     | Second call harmless                        |
| Required provider removed                | Consumer stops first                        |
| Optional provider removed                | Consumer remounts or degrades as specified  |
| Feature runtime task crashes             | Feature becomes failed and its scope closes |

## D. Physical-removal tests

Create:

```text
scripts/verify_feature_removal.py
```

It should:

1. Copy the repository into a temporary directory.
2. Remove the selected feature package.
3. Remove its feature-local tests and entry-point declaration.
4. Run Ruff.
5. Run mypy.
6. Run architectural checks.
7. Run core tests.
8. Start the application.
9. Query the capability catalog.
10. Confirm that the expected capability is unavailable.
11. Confirm that unrelated capabilities remain active.

Run it as:

```bash
uv run --frozen \
  python scripts/verify_feature_removal.py FEAT-DATA-01
```

Also run a second variant that deliberately leaves stale configuration behind. That proves stale configuration results in `MISSING`, not a startup crash.

---

# 23. Definition of done for every feature

A feature is not complete until all of these are true:

* [ ] It has a stable feature ID.
* [ ] It belongs to exactly one domain.
* [ ] It provides one cohesive capability or closely related capability set.
* [ ] Its contracts live outside its removable implementation package.
* [ ] Required and optional capabilities are declared.
* [ ] It never imports another feature implementation.
* [ ] It performs no import-time I/O or registration.
* [ ] Every runtime effect is registered through `FeatureContext`.
* [ ] Its mount failure fully rolls back.
* [ ] Its unmount operation is idempotent.
* [ ] Required-dependency loss behavior is tested.
* [ ] Optional-dependency loss behavior is tested.
* [ ] Persistent-state retention is documented.
* [ ] Irreversible actions have idempotency and reconciliation rules.
* [ ] The application starts with the feature absent.
* [ ] Its UI and API removal behavior is documented.
* [ ] Its README lists capability, dependencies, effects, state, and removal result.
* [ ] Ruff, mypy, import architecture checks, and pytest pass.

---

# 24. Recommended feature README template

```markdown
# FEAT-DATA-01 — Historical Bars

## Purpose

Retrieve normalized historical bars.

## Domain

Data

## Provides

- data.historical-bars@1

## Required Capabilities

- broker.market-data@1

## Optional Capabilities

- data.bar-cache@1
- system.metrics@1

## Configuration

| Field | Type | Required | Description |
|---|---|---:|---|
| default_timeframe | str | No | Default bar timeframe |
| cache_enabled | bool | No | Enable persistent cache |

## Runtime Effects

| Effect | Owner | Disposal |
|---|---|---|
| HistoricalBars service binding | FEAT-DATA-01 | Unregister provider |
| Provider-disconnect listener | FEAT-DATA-01 | Remove listener |
| Cache refresh task | FEAT-DATA-01 | Cancel and await |

## Persistent State

- Namespace: data.historical_bars
- Unload policy: retain
- Purge policy: explicit

## Functional Requirements

| Requirement | Responsibility | Symbol |
|---|---|---|
| FR-DATA-001 | Validate request | validate_request() |
| FR-DATA-002 | Retrieve bars | HistoricalBarsService.retrieve() |
| FR-DATA-003 | Normalize provider output | normalize_bars() |
| FR-DATA-004 | Append cache | append_bars() |

## Failure Behavior

- Missing broker.market-data@1 → BLOCKED
- Cache unavailable → runs without caching
- Provider timeout → typed transient error

## Removal Behavior

Removing this feature makes data.historical-bars@1 unavailable.
No persistent bar data is automatically deleted.
```

This README can be used to generate the domain capability catalog automatically.

---

# 25. Phase 14 — Package external plugins

Keep all features in one repository initially. Split them into separately installable distributions only after the contracts and lifecycle model stabilize.

A later package structure might be:

```text
your-project-core
your-project-contracts
your-project-broker-mt5
your-project-broker-binance
your-project-data-historical
your-project-research-edge-lab
```

The dependency direction should be:

```text
plugin distribution
    → contracts
    → kernel

core
    ✕ plugin distributions
```

The core application must not list every optional plugin as a mandatory dependency.

Distinguish two dependency types:

| Dependency type       | Example                    | Meaning                                            |
| --------------------- | -------------------------- | -------------------------------------------------- |
| Package dependency    | `MetaTrader5`, `numpy` | Code/library required to import or run the feature |
| Capability dependency | `broker.market-data@1`   | Runtime service required from another feature      |

A feature might have its Python package dependency installed while its runtime capability dependency is unavailable. Those are different states and should be diagnosed separately.

---

# 26. Phase 15 — Add hot reconfiguration before hot code reload

Start with configuration hot reload:

```text
app.toml changes
→ validate complete desired graph
→ calculate reconciliation plan
→ remount affected features
```

This already gives you most practical benefits:

* Enable or disable a provider
* Change feature configuration
* Change provider selection
* Add or remove adapters
* Recompose a runtime without restarting the process

## Transactional feature replacement

A no-downtime replacement should follow this sequence:

1. Discover the new feature factory.
2. Validate its contract compatibility.
3. Validate configuration.
4. Create a shadow scope.
5. Mount the new version without publishing it globally.
6. Run its health check.
7. Mark the old version quiescing.
8. Stop new calls to the old provider.
9. Atomically swap the registry generation.
10. Allow new calls to reach the replacement.
11. Drain in-flight old calls.
12. Dispose the old scope.
13. Roll back to the old provider if any pre-commit step fails.

The registry swap should happen under a lock and should use generation tokens.

## Python code HMR caution

Do not build production HMR around `importlib.reload()`.

Python documents that external references to old objects are not rebound, existing instances continue using old class definitions, old module dictionary entries can remain, and `reload()` is not thread-safe. ([Python documentation][8])

Therefore distinguish:

| Operation                                   | Recommended approach                          |
| ------------------------------------------- | --------------------------------------------- |
| Configuration reload                        | Same process, remount feature                 |
| Provider instance replacement               | Same process, transactional scope swap        |
| Pure Python code replacement in development | Isolated module generation with strict limits |
| Critical production code upgrade            | Blue/green process replacement                |
| Untrusted/native plugin replacement         | Subprocess isolation                          |

A process-level replacement can still provide zero application downtime through a supervisor, proxy, or worker pool, without pretending that Python can reliably erase all old code references from one interpreter.

---

# 27. Recommended kernel file order

Implement the kernel in this exact sequence:

```text
src/app/kernel/
├── errors.py
├── capability.py
├── feature.py
├── scope.py
├── registry.py
├── events.py
├── graph.py
├── reconciler.py
├── discovery.py
├── loader.py
├── runtime.py
└── status.py
```

## Implementation order

| Order | File              | First responsibility                      |
| ----: | ----------------- | ----------------------------------------- |
|     1 | `errors.py`     | Typed composition and capability errors   |
|     2 | `capability.py` | Versioned capability keys                 |
|     3 | `feature.py`    | Feature specs and lifecycle interfaces    |
|     4 | `scope.py`      | Reversible effect ownership               |
|     5 | `registry.py`   | Provider bindings and ownership tokens    |
|     6 | `graph.py`      | Dependency validation and ordering        |
|     7 | `reconciler.py` | Desired-versus-actual graph calculation   |
|     8 | `discovery.py`  | Find available feature factories          |
|     9 | `loader.py`     | Validate, instantiate, mount, and unmount |
|    10 | `events.py`     | Typed disposable event subscriptions      |
|    11 | `status.py`     | Feature and capability diagnostics        |
|    12 | `runtime.py`    | Public composition runtime                |

Then build:

```text
1 provider feature
1 consumer feature
1 optional dependency
1 background task
1 event listener
1 persistent repository
```

Prove that all six are removed correctly before implementing the full application.

---

# 28. The resulting architectural model

Your final application would conceptually look like this:

```text
Application Kernel
│
├── Capability Registry
├── Effect Scopes
├── Dependency Graph
├── Event Runtime
├── Loader
└── Reconciler
     │
     ├── Domain: Broker
     │    ├── Feature: MT5 Market Data
     │    ├── Feature: MT5 Execution
     │    └── Feature: Binance Adapter
     │
     ├── Domain: Data
     │    ├── Feature: Historical Bars
     │    ├── Feature: Real-time Ticks
     │    └── Feature: Symbol Metadata
     │
     ├── Domain: Risk
     │    ├── Feature: Trade Approval
     │    ├── Feature: Exposure Limits
     │    └── Feature: Kill Switch
     │
     └── Domain: Research
          ├── Feature: Dataset Builder
          ├── Feature: Signal Analysis
          └── Feature: Robustness Testing
```

The dependency graph might be:

```text
MT5 Market Data
      │
      ▼
Historical Bars
      │
      ▼
Research Dataset
      │
      ▼
Signal Analysis
```

Deleting `Historical Bars` causes:

```text
MT5 Market Data: ACTIVE
Historical Bars: MISSING
Research Dataset: BLOCKED
Signal Analysis: BLOCKED
Other broker/data/risk/trading capabilities: UNAFFECTED
Application shell: RUNNING
```

That is the practical meaning of:

> The application loses a capability rather than losing structural integrity.

The most important first milestone is not a complete Data domain. It is a minimal kernel plus two features that conclusively prove configuration disablement, package absence, runtime unmount, dependency cascading, and zero-effect leakage. Once that vertical slice passes, the same four-tier pattern can be expanded domain by domain.

[1]: https://github.com/cordiverse/paper
[2]: https://docs.astral.sh/uv/concepts/projects/init/?utm_source=chatgpt.com
[3]: https://docs.python.org/3/library/typing.html?utm_source=chatgpt.com
[4]: https://docs.python.org/3/library/contextlib.html?utm_source=chatgpt.com
[5]: https://deepseek-harness.github.io/deepseek-harness/en/reference/cordis-primer
[6]: https://docs.python.org/3/library/importlib.metadata.html?utm_source=chatgpt.com
[7]: https://import-linter.readthedocs.io/en/v2.6/contract_types.html?utm_source=chatgpt.com
[8]: https://docs.python.org/3/library/importlib.html?utm_source=chatgpt.com

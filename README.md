# HaruQuantAI

> **Quantitative Financial Trading & Research System**
> Built on a strictly decoupled, capability-oriented spatiotemporal composability kernel in Python 3.14+.

---

## 1. Project Overview

**HaruQuantAI** is a quantitative trading and financial research platform designed around strict architectural isolation and dynamic runtime composability.

Trading strategies, market-data pipelines, analytics, interfaces, and infrastructure communicate through typed, versioned capability contracts instead of importing one another's implementations.

The current repository is the clean composability foundation from which registered product features will be built. It implements the Kernel and Composition runtime, but it does not yet provide completed research, simulation, broker, trading, or D-IFACE HTTP features.

### Key Architectural Pillars

- **Zero Coupling Between Service Features**: Feature packages never import or call one another directly. They interact through exact versioned capability contracts declared in `FeatureSpec`.
- **Spatiotemporal Scoping**: Every feature executes within an isolated `FeatureScope` that owns its services, background tasks, context managers, and event subscriptions. Closing or replacing the feature disposes of those effects safely.
- **Graceful Absence and Physical Removability**: A feature package and its local tests can be physically removed without breaking the shared runtime or unrelated features. Missing requirements block only the affected dependency closure.
- **Profile-Driven Readiness**: Runtime profiles declare required capabilities. Composition reports liveness, readiness, active capabilities, feature states, and missing dependencies independently of any future transport.
- **Interface Ownership**: Product-facing HTTP, CLI, MCP, and other gateways are registered D-IFACE features owned by `app/services/interfaces/`; they are not part of the shared composability foundation.
- **Unified Trading Execution**: Simulation, paper, demo, and live execution share one Trading-owned business lifecycle. Simulator and Broker Connectivity provide route-specific execution authority mechanics through versioned capabilities rather than implementing parallel trading lifecycles.

---

## 2. Architecture and Documentation

- [Project Specification](docs/PROJECT.md) — Product scope, system workflows, requirements, NFRs, and release gates.
- [Architecture](docs/ARCHITECTURE.md) — Universal structural, lifecycle, persistence, and runtime constraints.
- [Unified Trading Execution Parity](docs/EXECUTION_PARITY.md) — Ratified cross-domain amendment restoring one Trading lifecycle with Simulator/Broker execution authorities and the revised Risk → Trading → Simulator dependency core.
- [Implementation Order](docs/dev/IMPLEMENTATION_ORDER.md) — Incremental, UI-visible delivery sequence. Its affected Trading/Simulator/Runtime-Risk ordering is pending mechanical reconciliation with the ratified execution-parity decision above.
- [Domain Specifications](app/services) — Authoritative domain boundaries, feature registries, responsibilities, and acceptance evidence.
- [Feature Implementation Pipeline](docs/dev/feature_implementation_pipeline.md) — Procedure for designing, implementing, demonstrating, testing, replacing, and removing features.
- [Builder Guide](AGENTS.md) — Contributor process, approval gates, coding standards, and verification policy.

---

## 3. Getting Started

HaruQuantAI uses `uv` for deterministic dependency and environment management.

### Prerequisites

- Python `>= 3.14`
- [uv](https://github.com/astral-sh/uv) `>= 0.12.3`

### Installation

```powershell
git clone https://github.com/haruperi/HaruQuantAI.git
cd HaruQuantAI
uv sync --frozen --dev
```

---

## 4. Running the Implemented Foundation

> [!WARNING]
> HaruQuantAI is under active development. The current foundation exposes diagnostics only and does not authorize research claims, simulated performance claims, broker operations, or live-capital execution.

Print machine-readable Composition diagnostics:

```powershell
# Default configuration status
uv run haruquantai --status

# Research profile readiness; missing product capabilities are reported explicitly
uv run haruquantai --config config/examples/research.toml --status
```

The `/system/*` diagnostic projections and `/api/v1/*` product routes specified by D-IFACE are targets, not currently running endpoints. They will become available only through implemented and registered Interfaces features.

---

## 5. Development Verification

During implementation, derive the affected test set from all uncommitted files and run only those tests:

```powershell
git diff --name-only
git diff --cached --name-only
git status --short
uv run pytest --no-cov <affected_test_path> [<affected_test_path> ...]
```

Run focused formatting, linting, typing, architecture, and documentation checks applicable to the changed paths. Do not run bare pytest, coverage, or the complete repository gate during iterative implementation.

The complete repository gate is reserved for pre-commit, CI, and release verification:

```powershell
uv run python scripts/ci_check.py
```

The authoritative testing and completion procedure is defined in [AGENTS.md](AGENTS.md) and the [Feature Implementation Pipeline](docs/dev/feature_implementation_pipeline.md).

---

## 6. License

Proprietary / All Rights Reserved. Author: Haruperi (<r.haruperi@hotmail.com>).

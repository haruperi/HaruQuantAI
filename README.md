# HaruQuantAI

> **Quantitative Financial Trading & Research System**
> Built on a strictly decoupled, capability-oriented spatiotemporal composability kernel in Python 3.14+.

---

## 1. Project Overview

**HaruQuantAI** is a quantitative trading and financial research platform designed around strict architectural isolation and dynamic runtime composability.

Trading strategies, market-data pipelines, analytics, interfaces, and infrastructure communicate through typed, versioned capability contracts instead of importing one another's implementations.

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
- [Domain Specifications](app/services) — Authoritative domain boundaries, feature registries, responsibilities, and acceptance evidence.
- [Feature Implementation Pipeline](docs/dev/feature_implementation_pipeline.md) — Procedure for designing, implementing, demonstrating, testing, replacing, and removing features.
- [Builder Guide](AGENTS.md) — Contributor process, approval gates, coding standards, and verification policy.

---

## 3. Project Structure

This repository is structured as a modular architecture organized around a pure kernel, runtime composition, contracts, and isolated service domains:

- `app/kernel`: Pure composability kernel, manifests, lifecycle, resolvers, health, and diagnostics.
- `app/composition`: Dynamic runtime engine, feature reconciler, generation manager, and profile controller.
- `app/contracts`: Public cross-boundary DTOs, protocols, capability keys, and events.
- `app/services`: Core quantitative and trading logic modules (analytics, broker, data, indicators, interfaces, optimization, orchestration, portfolio, research, risk, simulator, strategy, system, trading, workspace).
- `docs/`: System specifications, architecture guide, and development standards.
- `scripts/`: Quality assurance, release checks, schema validation, and CI tooling.
- `tests/`: Change-scoped unit, integration, architecture, removability, and usage tests.

---

## 4. Getting Started

HaruQuantAI uses **[uv](https://github.com/astral-sh/uv)** for fast, deterministic Python dependency and environment management.

### Prerequisites

- Python `>= 3.14`
- [uv](https://github.com/astral-sh/uv) `>= 0.12.3`

### Installation

Clone the repository and synchronize the environment (installs the correct Python version and all dependencies into a local virtual environment):

```bash
git clone https://github.com/haruperi/HaruQuantAI.git
cd HaruQuantAI
uv sync --all-extras --dev
```

---

## 5. Running the Application

> [!WARNING]
> HaruQuantAI is under active development. The current foundation exposes diagnostics and registered service features; live-capital trading requires verified broker integration and explicit gate authorization.

Run the canonical CLI / API server:

```bash
# Run with default settings:
uv run haruquantai

# Run with custom host, port, or auto-reload in development:
uv run haruquantai --host 127.0.0.1 --port 8000 --reload
```

---

## 6. Local Development Quality Gates

We enforce high code quality standards via Ruff (formatting, linting, import-sorting), mypy (strict static typing), and pytest (testing & coverage).

### Change-Scoped Testing

During implementation, derive the affected test set from all uncommitted files and run only those tests:

```bash
git diff --name-only
git diff --cached --name-only
git status --short
uv run pytest --no-cov <affected_test_path> [<affected_test_path> ...]
```

### 1. Code Formatting (Ruff Format)
Ruff format is the canonical formatter.
- **Preview changes (check):**
  ```bash
  uv run ruff format --check .
  ```
- **Apply formatting:**
  ```bash
  uv run ruff format .
  ```

### 2. Linting & Import Ordering (Ruff Check)
Ruff check is the canonical linting and import-order gate.
- **Run linting checks:**
  ```bash
  uv run ruff check .
  ```
- **Automatically fix safe violations:**
  ```bash
  uv run ruff check --fix .
  ```

### 3. Static Type Checking (mypy strict)
Mypy strict is the canonical static typing gate.
- **Run static type checking:**
  ```bash
  uv run mypy .
  ```

### 4. Running Tests & Coverage (pytest)
Pytest is the canonical unit and usage-test runner. Coverage must remain above **80%** across the packages.

- **Fast Tests (No coverage calculation):**
  Useful during active coding to run tests quickly:
  ```bash
  uv run pytest --no-cov
  ```

- **Full Tests (With coverage check & HTML report):**
  Generates terminal and HTML coverage reports and enforces the 80% coverage floor:
  ```bash
  uv run pytest
  ```
  *Coverage HTML reports are generated at `htmlcov/index.html`.*

### 5. Running Usage Examples
To run usage examples (such as integration flows or sample domain workflows) under the `tests/usage/` directory:
```bash
uv run pytest tests/usage
```
Or run individual example scripts directly:
```bash
uv run python tests/usage/<example_script>.py
```

---

## 7. Local CI, Pre-Release Checks & Pre-Commit

### Run Local CI Checks
Executes Ruff format check, Ruff check, mypy strict, and pytest + coverage in the approved sequence:
```bash
uv run python scripts/ci_check.py
```

### Run Pre-Release Safety Checks
Runs the full CI suite and performs additional safety checks before generating a release:
```bash
uv run python scripts/release_check.py
```

### Git Pre-Commit Hooks
A git `pre-commit` configuration is provided to run formatting, linting, type-checking, and secret scanning locally before each commit.

- **Install pre-commit hooks:**
  ```bash
  uv run pre-commit install
  ```
- **Run pre-commit checks manually on all files:**
  ```bash
  uv run pre-commit run --all-files
  ```

The authoritative testing and contributor procedure is defined in [AGENTS.md](AGENTS.md) and the [Feature Implementation Pipeline](docs/dev/feature_implementation_pipeline.md).

---

## 8. License

Proprietary / All Rights Reserved. Author: Haruperi (<r.haruperi@hotmail.com>).

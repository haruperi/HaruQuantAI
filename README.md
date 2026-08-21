# HaruQuantAI

> **Quantitative Financial Trading & Research System**
> Built on a strictly decoupled, capability-oriented spatiotemporal composability kernel in Python 3.14+.

---

## 1. Project Overview

**HaruQuantAI** is a high-performance quantitative trading and financial research platform designed with strict architectural isolation and dynamic runtime composability.

Rather than coupling trading strategies, market data pipelines, and analytics directly to concrete broker APIs or specific infrastructure implementations, HaruQuantAI coordinates all domain operations through **versioned capability contracts**.

### Key Architectural Pillars

- **Zero Coupling Between Service Features**: Feature packages never import or call each other directly. All interactions flow through typed, versioned capability contracts (e.g. `data.historical-bars@1`, `broker.market-data@1`, `system.storage@1`).
- **Spatiotemporal Scoping**: Every feature executes within an isolated `FeatureScope` that tracks all bound services, spawned background tasks, context managers, and event subscriptions. Unmounting or replacing a feature completely and safely disposes of all associated resources without leaks.
- **Graceful Absence & Physical Removability**: Any feature package (code and local tests) can be physically deleted from disk without breaking the core application or failing unrelated tests. The system detects missing dependencies, transitions dependents to `BLOCKED`, and continues running in degraded modes.
- **Profile-Driven Readiness**: Deployments select runtime profiles (`research`, `backtest`, `live`, `offline`). The system control plane observes `/system/liveness` independently from `/system/readiness`.

---

## 2. Architecture & Documentation

- [Capability Catalog & Model](docs/architecture/capability-model.md) — Implemented vs roadmap capabilities, naming conventions, and profiles.
- [Feature Implementation Pipeline](docs/architecture/feature_implementation_pipeline.md) — 7-step guide to developing, testing, and packaging new features.
- [External Plugin Packaging](docs/architecture/external_plugin_packaging.md) — Guidelines for distributing third-party plugin packages.
- [Composability Gap Remediation Plan](docs/architecture/composability_gap_remediation_plan.md) — Comprehensive 11-phase architecture specification and audit trail.

---

## 3. Getting Started & Development Setup

HaruQuantAI uses `uv` for deterministic, high-speed Python dependency management and environments.

### Prerequisites

- Python `>= 3.14`
- [uv](https://github.com/astral-sh/uv) `>= 0.12.3`

### Installation

```bash
# Clone repository
git clone https://github.com/haruperi/HaruQuantAI.git
cd HaruQuantAI

# Create virtual environment and synchronize dependencies
uv sync --frozen --dev
```

---

## 4. Running the Application (Non-Production)

> [!WARNING]
> **Safety Notice:** HaruQuantAI is currently under active quantitative development. The existing foundation provides research, backtesting, and mock simulation capabilities. **It does not authorize or support unmonitored live capital execution.**

### Print Machine-Readable Status Diagnostics

```bash
# Inspect runtime diagnostics for the research profile
uv run haruquantai --config config/examples/research.toml --status

# Inspect status for live profile (demonstrates graceful capability degradation)
uv run haruquantai --config config/examples/live.toml --status
```

### Start System HTTP Control Plane

```bash
# Start async HTTP control plane server on port 8000
uv run haruquantai --config config/examples/research.toml --serve --host 127.0.0.1 --port 8000
```

### Query Control Plane Endpoints

```bash
# Check kernel liveness (200 OK)
curl http://127.0.0.1:8000/system/liveness

# Check profile readiness (200 OK or 503 Service Unavailable with missing capabilities)
curl http://127.0.0.1:8000/system/readiness

# List active capabilities and provider metadata
curl http://127.0.0.1:8000/system/capabilities

# Inspect feature lifecycle states and dependency health
curl http://127.0.0.1:8000/system/features
```

---

## 5. Quality Assurance & CI Verification

HaruQuantAI enforces strict architectural invariants, formatting standards, type safety, and physical-removal testing.

### Run All Quality Gates

```bash
uv run python scripts/ci_check.py
```

### Individual Quality Commands

```bash
# Format check
uv run ruff format --check .

# Lint check
uv run ruff check .

# Static type check
uv run mypy

# Architectural import boundary contracts
uv run lint-imports

# AST invariant verification
uv run python scripts/architecture_check.py

# Feature documentation synchronization
uv run python scripts/validate_feature_docs.py

# Full test suite with coverage
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80

# Physical feature removability matrix verification
uv run python scripts/verify_feature_removal.py --all --report removability-report.json
```

---

## 6. License

Proprietary / All Rights Reserved. Author: Haruperi (<r.haruperi@hotmail.com>).

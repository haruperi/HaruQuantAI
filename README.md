# Project Template

> **Generic Modular Monolith Architecture**
> Built on a strictly decoupled, capability-oriented spatiotemporal composability kernel in Python 3.14+.

---

## 1. Project Overview

**Project Template** is a production-grade Python 3.14+ starter application architected as a clean, decoupled **modular monolith**. It provides an uncompromised structural foundation with a zero-dependency kernel, deterministic runtime composition, typed capability-based dependency injection, spatiotemporally scoped lifecycles, and automated architectural guardrails.

Application business features, domain contracts, persistence layers, interfaces, and external integrations are intentionally left for each new product to define according to its domain requirements.

### Key Architectural Pillars

- **Zero Coupling Between Service Features**: Single-file feature modules never import or call one another directly. Features declare exact capability dependencies in `FeatureSpec` and resolve them through `FeatureContext`.
- **Spatiotemporal Scoping**: Every feature executes within an isolated `FeatureScope` that owns its services, background tasks, context managers, and event subscriptions. Disposing of a feature cleans up all its side effects safely without leaks.
- **Graceful Absence and Physical Removability**: A feature module and its local tests can be physically removed without breaking the shared runtime or unrelated features. Missing requirements block only the affected dependency closure.
- **Profile-Driven Readiness**: Runtime profiles declare required capabilities. The kernel composition container reports liveness, readiness, active capabilities, feature states, and missing dependencies independently of any future transport.
- **Interface Ownership**: Product-facing HTTP, CLI, worker, or messaging gateways are registered interface features owned by `app/services/interfaces/`; they are not part of the shared composability foundation.
- **Pure Kernel Foundation**: The entire kernel (`app/kernel/`) relies exclusively on the Python standard library, ensuring a resilient, lightweight, and long-term maintainable core with zero third-party lock-in.

---

## 2. Architecture and Documentation

- [Project Specification](docs/PROJECT.md) — Product scope, system workflows, requirements, NFRs, and release gates.
- [Architecture Guide](docs/ARCHITECTURE.md) — Universal structural, lifecycle, persistence, and runtime constraints.
- [Feature Implementation Pipeline](docs/dev/feature_implementation_pipeline.md) — Canonical 10-step procedure for designing, implementing, demonstrating, testing, replacing, and removing features.
- [Domain Implementation Audit](docs/dev/domain_implementation_audit.md) — 26-control verification matrix ensuring architectural compliance.
- [Kernel Architecture & Semantics](app/kernel/README.md) — Runtime composability, capabilities, event bus, scopes, and structured logging.

---

## 3. Project Structure

This repository is a simplified modular monolith organized around a pure kernel, one runtime composition container, domain contracts, single-file service features, and dedicated domain persistence:

```text
HaruQuantAI/
├── .github/
│   ├── workflows/             # CI/CD automation workflows
│   └── .secrets.baseline      # Pinned baseline for detect-secrets
├── app/
│   ├── contracts/             # Domain contract modules (DTOs, protocols, capabilities, events)
│   ├── kernel/                # Standard-library composability kernel
│   │   ├── bootstrapper.py    # Runtime lifecycle, dependency sorting, health diagnostics
│   │   ├── capability.py      # Typed capability tokens (PEP 695 generics)
│   │   ├── context.py         # Dynamic container, FeatureScope, and task management
│   │   ├── events.py          # Decoupled async event broker
│   │   ├── feature.py         # FeatureSpec, lifecycle hooks, status models
│   │   └── logging.py         # High-performance structured JSONL logging & rotation
│   ├── services/              # Domain service features and persistence
│   │   ├── persistence/       # Dedicated domain database schemas, SQL, and transactions
│   │   └── <domain>/          # Single-file cohesive service features
│   ├── main.py                # CLI entry point and runtime bootstrap
│   └── registry.py            # Explicit feature factory registry
├── docs/
│   ├── dev/                   # Developer workflows, pipelines, and audit checklists
│   ├── ARCHITECTURE.md        # Architectural rules and structural invariants
│   └── PROJECT.md             # System specifications and requirements
├── scripts/
│   ├── architecture_check.py  # AST-based architectural boundary and invariant linter
│   ├── ci_check.py               # Unified qualification runner (lint, types, tests, AST)
│   └── detect_secrets_filters.py # Custom verification filters for secret scanning
├── tests/
│   ├── architecture/          # Architectural boundary and boundary invariant tests
│   ├── examples/              # Consolidated executable feature usage scenarios
│   └── kernel/                # Comprehensive unit tests for kernel components
├── .gitignore                 # Production-grade repository exclusions
├── .pre-commit-config.yaml    # Git hooks for linting, typing, AST checks, and secrets
└── pyproject.toml             # Project configuration, Ruff, Mypy, Pytest, and profiles
```

---

## 4. Getting Started

Project Template uses **[uv](https://github.com/astral-sh/uv)** for fast, deterministic Python dependency and environment management.

### Prerequisites

- Python `>= 3.14`
- [uv](https://github.com/astral-sh/uv) `>= 0.12.0`
- Git `>= 2.40.0`

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd HaruQuantAI
   ```

2. **Install dependencies and create virtual environment:**
   ```bash
   uv sync --all-extras --dev
   ```

3. **Install Git pre-commit hooks:**
   ```bash
   uv run pre-commit install
   ```

### Using as a Starter for a New Project

1. Copy the source tree, excluding `.venv`, caches (`.mypy_cache`, `.ruff_cache`, `.pytest_cache`), coverage outputs (`htmlcov`, `.coverage`), and local data.
2. Update the project metadata, name, version, and dependencies in `pyproject.toml`, then run `uv lock`.
3. Complete product specifications in `docs/PROJECT.md` and review `docs/ARCHITECTURE.md`.
4. Define domain contracts in `app/contracts/<domain>.py` and cohesive features in `app/services/<domain>/<feature>.py`.
5. Register side-effect-free feature factories in `app/registry.py`.
6. Host domain startup and coordination inside the runtime context in `app/main.py`.
7. Add feature tests and extend test suites to maintain the 80% coverage floor.

---

## 5. Running the Application

### 1. Starting the Runtime CLI

The application entry point is defined in [`app/main.py`](app/main.py) and exposed via `[project.scripts]` as `template`:

```bash
# Run with default settings:
uv run template

# Alternatively, run via Python module:
uv run python -m app.main
```

### 2. Command-Line Options and Diagnostics

- **Inspect Runtime Status:** Inspect registered features, active capabilities, and dependency readiness without executing background tasks:
  ```bash
  uv run template --status
  ```
- **Select Active Profile:** Load a specific profile configured in `pyproject.toml`:
  ```bash
  uv run template --profile full
  ```
- **Dry-Run Validation:** Validate dependency sorting and capability satisfaction:
  ```bash
  uv run template --dry-run
  ```
- **Log Configuration:** Adjust verbosity or route output to an explicit log file:
  ```bash
  uv run template --log-level DEBUG --log-file data/logs/app.log
  ```

### 3. Running Executable Feature Examples

Consolidated usage scenarios demonstrate core capabilities offline with deterministic, secret-safe inputs:

```bash
# Run runtime composition example:
uv run python -m tests.examples.composition

# Run structured logging and redaction example:
uv run python -m tests.examples.logging_usage
```

---

## 6. Local Development Quality Gates

We enforce rigorous code quality standards via Ruff (formatting, linting, complexity), Mypy (strict static typing), Pytest (testing & coverage), and AST architectural checking.

### Change-Scoped Testing

During active implementation, inspect changed files and run targeted tests:

```bash
git diff --name-only
uv run pytest --no-cov <affected_test_path>
```

### 1. Code Formatting (Ruff Format)

Ruff format is the canonical code formatter:

```bash
# Preview formatting changes:
uv run ruff format --check .

# Apply formatting:
uv run ruff format .
```

### 2. Linting & Import Ordering (Ruff Check)

Ruff check enforces 50+ rule groups including PEP8 naming, imports, docstrings, and security:

```bash
# Run linter:
uv run ruff check .

# Automatically fix safe violations:
uv run ruff check --fix .
```

### 3. Static Type Checking (Mypy Strict)

Mypy is configured in strict mode with advanced error codes enabled (`deprecated`, `explicit-override`, `truthy-bool`):

```bash
uv run mypy
```

### 4. Architectural AST Invariant Linter

Ensures cross-boundary isolation, forbids unauthorized imports, and verifies docstring-only `__init__.py` files:

```bash
uv run python scripts/architecture_check.py
```

### 5. Running Tests & Coverage (Pytest)

Enforces 100% test passing and an **80% minimum coverage floor** across the application:

```bash
# Fast test run without coverage calculation:
uv run pytest --no-cov

# Full test run enforcing 80% coverage threshold:
uv run pytest
```

*Interactive HTML coverage reports are written to `htmlcov/index.html`.*

### 6. Secret Detection

Detects accidental leaks of credentials, keys, and tokens:

```bash
uv run detect-secrets scan
```

---

## 7. Unified Local CI & Pre-Commit

### Unified Check Runner

The repository provides a single qualification script executing all gates in canonical order:

```bash
uv run python scripts/ci_check.py
```

This runs:
1. Ruff format validation
2. Ruff lint and complexity checks
3. Strict Mypy type verification
4. AST architectural invariant validation
5. Pytest suite with 80% coverage floor enforcement
6. Executable composition and logging sanity checks
7. Application bootstrap dry-run

### Git Pre-Commit Hooks

Ensure all commits comply with local quality gates:

```bash
# Install hooks:
uv run pre-commit install

# Run checks manually on all files:
uv run pre-commit run --all-files
```

The authoritative development methodology is defined in [docs/dev/feature_implementation_pipeline.md](docs/dev/feature_implementation_pipeline.md) and [docs/dev/domain_implementation_audit.md](docs/dev/domain_implementation_audit.md).

---

## 8. License

This project template is distributed under the MIT License. See [LICENSE](LICENSE) for details.

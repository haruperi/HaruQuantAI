# HaruQuantAI

Quantitative Financial Trading System.

---

## Getting Started

### Prerequisites
This project uses **[uv](https://github.com/astral-sh/uv)** for fast, reliable Python package management. Make sure `uv` is installed on your system.

### Installation
Clone the repository and synchronize the environment (this will install the correct Python version and all dependencies into a local virtual environment):
```bash
uv sync --all-extras --dev
```

---

## Local Development Quality Gates

We enforce high code quality standards via Ruff (formatting, linting, import-sorting), mypy (strict static typing), and pytest (testing & coverage).

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

---

## Local CI and Pre-Release Checks

Before committing or pushing, you should run the automated quality checks.

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

---

## Git Pre-Commit Hooks

A git `pre-commit` configuration is provided to run formatting, linting, type-checking, and secret scanning locally before each commit.

- **Install pre-commit hooks:**
  ```bash
  uv run pre-commit install
  ```
- **Run pre-commit checks manually on all files:**
  ```bash
  uv run pre-commit run --all-files
  ```

---

## Running Usage Examples
To run usage examples (such as integration flows or sample agent setups) under the `tests/usage/` directory:
```bash
uv run pytest tests/usage
```
Or run individual example scripts directly:
```bash
uv run python tests/usage/<example_script>.py
```

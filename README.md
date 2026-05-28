# HaruQuantAI

HaruQuantAI is a domain-driven, agentic AI quantitative trading platform for research, strategy development, backtesting, analytics, risk management, portfolio operations, and controlled execution.

The project is a clean rebuild of HaruQuant using a simpler, agile architecture where each `tools/` folder is treated as a bounded tool domain.

## Architecture

```text
haruquantai/
  pyproject.toml
  README.md
  .env.example
  .gitignore
  .pre-commit-config.yaml
  LICENSE

  api/
  docs/
  scripts/
  data/
  tools/
  ui/
  tests/
```

## Tool Domains

Each folder inside `tools/` is a domain:

```text
tools/data/
tools/indicators/
tools/strategies/
tools/backtesting/
tools/analytics/
tools/research/
tools/optimization/
tools/risk/
tools/execution/
tools/portfolio/
tools/notification/
tools/governance/
tools/agentic/
tools/conversation/
tools/utils/
```

Domains are built incrementally. Do not create schemas or contracts for future domains until that domain is being implemented.

## Initial Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"
pre-commit install
```

## Common Commands

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type check
mypy api tools scripts

# Run tests with coverage
pytest

# Run tests manually with coverage threshold
pytest --cov=tools --cov=api --cov=scripts --cov-fail-under=80
```

## Coverage Policy

Testing coverage must always stay at or above **80%**.

The coverage gate is enforced in `pyproject.toml`:

```toml
--cov-fail-under=80
```

and:

```toml
[tool.coverage.report]
fail_under = 80
```

## Code Quality Policy

This project uses:

- **Black** for formatting.
- **isort** for import sorting.
- **Flake8** for linting.
- **mypy** for static type checking.
- **pytest** for testing.
- **coverage.py / pytest-cov** for coverage enforcement.
- **pre-commit** for local quality gates.

Black and Flake8 are configured to avoid conflicts:

- Both use line length `88`.
- Flake8 ignores `E203` and `W503`, which conflict with Black formatting.

## Development Rule

Build one domain at a time:

1. Domain purpose.
2. Existing functionality to preserve.
3. Domain language.
4. Minimal files needed now.
5. Domain models/schemas needed now.
6. Validators.
7. Core implementation.
8. Unit tests.
9. Usage examples.
10. Integration tests if needed.
11. API only if needed.
12. UI only if needed.
13. Agent tools/permissions only when needed.
14. Documentation.
15. Exit acceptance checklist.

## License

This project is licensed under the MIT License. See `LICENSE`.

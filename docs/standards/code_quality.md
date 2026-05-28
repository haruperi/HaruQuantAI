# HaruQuantAI Code Quality Standard

## Tools

HaruQuantAI uses:

- Black for formatting.
- isort for import sorting.
- Flake8 for linting.
- mypy for static typing.
- pytest for testing.
- pytest-cov / coverage.py for coverage enforcement.
- pre-commit for local quality gates.

## Compatibility Rules

To avoid conflicts:

- Black line length is `88`.
- isort uses `profile = "black"`.
- Flake8 max line length is `88`.
- Flake8 ignores `E203` and `W503` because they conflict with Black.
- Coverage minimum is `80%`.

## Required Commands

```bash
black .
isort .
flake8 .
mypy api tools scripts
pytest
```

## Coverage Gate

Coverage must never fall below 80%.

```bash
pytest --cov=tools --cov=api --cov=scripts --cov-fail-under=80
```

## HaruQuantAI Production Standards

When writting code, keep the result clear, safe, testable, and maintainable without adding unnecessary complexity.

File must include:

- A clear module-level docstring.
- Clear class and function docstrings.
- Type hints for all public functions and methods.
- Input validation where appropriate.
- Output validation where appropriate.
- Structured logging for important runtime events.
- Safe error handling with explicit, helpful exceptions.
- No unnecessary hardcoded values.
- Clean function and class organization.
- Small, focused functions.
- Separation of business logic from I/O where possible.
- Deterministic behavior where required.
- Production-friendly defaults.
- Compatibility with future unit testing.
- Compatibility with future agent or tool usage where relevant.
- Clear naming conventions.
- Minimal but useful comments.
- No unnecessary complexity.

## Logging Standard

Every production Python file should define a module logger:

```python
from tools.utils import logger
```

Use logging for important events, warnings, validation failures, and recoverable
errors.

Avoid using `print()` in production code. Use `print()` only in simple examples,
CLI entry points, or scripts where stdout is the intended interface.

## Error Handling Standard

Use explicit exceptions with helpful error messages.

Avoid silent failures. If a failure is recoverable, log enough context for a
future maintainer or agent to understand what happened.

Avoid broad `except Exception` blocks unless there is a clear reason. When a
broad exception handler is necessary, always log, re-raise, or convert the error
to a more specific domain exception.

## Documentation Standard

Each public function or method should explain:

- What it does.
- Parameters.
- Return value.
- Raised exceptions, where relevant.

Docstrings should be useful to humans, tests, and future agent/tool workflows.
Avoid restating obvious implementation details.

## Testing Standard

After rewriting the main file, also create or update a unit test file.

The test file should include:

- Normal expected usage tests.
- Edge case tests.
- Invalid input tests.
- Error handling tests.
- Regression-style tests where appropriate.
- Mocking where external systems are involved.
- Clear test names.

Tests should verify behavior, not implementation details, unless the
implementation detail is part of the contract.

## Usage Example Standard

After rewriting the main file, also create or update a usage example file that
shows how the file should be used in a realistic HaruQuant workflow.

The example should be:

- Simple.
- Runnable.
- Easy to understand.
- Focused on the intended workflow rather than exhaustive coverage.

## Write Output Format

When providing rewritten code, return separate files using filename headers:

```text
# filename: path/to/file.py
```

Then provide the full code for that file.

Create at least:

- The standardized production file.
- The unit test file.
- The usage example file.

Add supporting files only when they are truly necessary.

## Production-Readiness Checklist

At the end of a write, provide a checklist confirming:

- Module, class, and public function docstrings are present.
- Public functions and methods have type hints.
- Inputs and outputs are validated where appropriate.
- Logging follows the module logger standard.
- Errors are explicit, helpful, and not silently swallowed.
- Business logic is separated from I/O where practical.
- Functions and classes are small and focused.
- Hardcoded values are avoided unless justified.
- Defaults are deterministic and production-friendly.
- Unit tests cover normal usage, edge cases, invalid input, and errors.
- External systems are mocked in tests.
- A realistic usage example is included.
- The implementation avoids unnecessary complexity.

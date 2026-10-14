# Standard Python Module Docstring and Logging Specification

> **Authority:** This document defines the mandatory repository-wide standard for top-of-file module docstrings and functional requirement (FR) logging.
> **Canonical Implementation:** `app/host/bootstrap.py`
> **Constitutional Mandate:** `AGENTS.md` Section 4 & `docs/ARCHITECTURE.md` Section 8.

---

## 1. Top-of-File Module Docstring Structure

Every Python source file in the repository (excluding empty/docstring-only `__init__.py` files) must begin with a comprehensive module docstring containing a concise summary line, a blank line, and exactly five standardized sections formatted as follows:

```python
"""[Concise Single-Line Module Summary Ending With A Period].

Description:
    [Business logic description: Explain why this file exists, its role within the
    broader quantitative or host system, its external relations and workflows with
    other files/subsystems, and the internal coordination/flow between classes and
    functions declared within this file.]

Purpose:
    [Feature identifier and technical feature scope. Follow the feature naming
    convention: FEAT-<SUBSYSTEM>-<NAME> (e.g. FEAT-HOST-BOOT, FEAT-DATA-DUKASCOPY).]

Key Capabilities:
    - FR-<SUBSYSTEM>-<CAPABILITY-SLUG>: [Descriptive capability summary]
      Associated: `[Class.method()]`, `[function()]`
      Logging: [Explicit description of the log emission when this requirement fires.
      NO functional requirement may run silently; every firing or lifecycle transition
      must be logged with appropriate severity (DEBUG, INFO, WARNING, ERROR).]

Python API Usage:
    ```python
    [Self-contained Python code snippet illustrating typical imports, instantiation,
    invocation of public methods, and cleanup.]
    ```

CLI Usage:
    [Self-contained shell commands showing how this feature or its enclosing
    entrypoint is executed externally via the command line.]
    ```bash
    [CLI command examples]
    ```
"""
```

---

## 2. Detailed Section Rules

### 2.1 Description (Business Logic vs Technical Detail)

- **Why this file exists:** State the system rationale, architectural role, and domain responsibility.
- **External relations (workflows):** Detail how external components interact with this file during key application flows (e.g., startup sequence, data acquisition flow, strategy execution graph, websocket streaming).
- **Internal relationship of functions:** Describe how functions and classes inside this file coordinate with each other (e.g., state machines, coordinators, helper dispatch).

### 2.2 Purpose (Feature Tracking)

- Follow the feature naming convention: `FEAT-<SUBSYSTEM>-<CONCEPT>` (e.g., `FEAT-HOST-BOOT`, `FEAT-HOST-SESSION`, `FEAT-HOST-TRANSPORT`, `FEAT-DATA-DUKASCOPY`).
- Do not use arbitrary numbers (e.g., avoid `FEAT-001`). Use uppercase kebab-case tokens representing subsystem and concept.
- Provide a 2–3 sentence operational summary of the feature.

### 2.3 Key Capabilities (Functional Requirements & Non-Silent Logging)

- **Descriptive Labels (No Numbers):** Functional requirements must use descriptive semantic labels matching the feature naming convention, e.g., `FR-HOST-BOOT-STAGE-PROGRESSION`, `FR-HOST-BOOT-LIFECYCLE-HOOKS`, `FR-HOST-BOOT-CLIENT-HANDSHAKE`. **Never use sequential numbers like `FR-BOOT-001` or `FR-002`**.
- **Traceability:** Explicitly link each capability to the concrete class methods or functions implementing it (`Associated: ...`).
- **Non-Silent Logging Invariant:**
  - **No functional requirement may execute silently.**
  - Every time a functional requirement is triggered, executes work, or transitions state, a structured log event must be emitted using the module's `logger = get_logger(__name__)`.
  - The docstring must document the exact log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`), message intent, and structured attributes emitted.

#### Centralized Logger Requirement

- Every Python module covered by this specification must import the centralized
  logger factory and create its module-level logger using exactly this pattern:

  ```python
  from app.host.logging import get_logger

  # After all imports and the module's __all__ declaration:
  logger = get_logger(__name__)
  ```
- Place the import with the other imports, keep `__all__` immediately after all
  imports, and initialize `logger` after `__all__`, before feature code.
- Emit module logs through this `logger`. Consuming modules must not import the
  standard-library `logging` module, call `logging.getLogger()`, use direct
  standard-library logging calls, or substitute another logger provider.
- Keep `logger` and the imported `get_logger` internal rather than re-exporting
  them. Logging configuration belongs to the host lifecycle; consuming modules
  must not configure handlers or perform hidden logging setup except if its a special case and logger re-configration is needed.
- The centralized provider, `app/host/logging.py`, may use standard-library
  logging internally to implement this capability and must not import itself.
  Empty or docstring-only `__init__.py` files retain their existing exemption.

### 2.4 Python API Usage

- Provide a clean, copy-pasteable Python snippet demonstrating how peer modules or test harnesses import and invoke this module's public interfaces.
- Show configuration, async execution (if applicable), and resource cleanup.

### 2.5 CLI Usage

- Show practical command-line invocations via `uv run python -m ...` demonstrating direct execution, entrypoint flags, or CLI utility commands.
- Include the command that runs this module's executable `main()` demonstration.

### 2.6 Executable Real-Usage Demonstration

- Every Python source file covered by this specification must define a typed
  `main()` function and invoke it through an `if __name__ == "__main__":` guard.
  Empty or docstring-only `__init__.py` files retain their existing exemption.
- The executable `main()` block must demonstrate real usage of the feature
  implemented in that file by calling its actual functions or classes with
  representative inputs; placeholders and mock-only demonstrations do not qualify.
- Show the required configuration, async execution where applicable, and resource
  cleanup. Follow the existing logging rules for every triggered capability.
- Keep the docstring's Python API and CLI usage examples consistent with this
  runnable demonstration. Importing the module must not run the demonstration. Don't use logger in the `main()` of usage demonstration, use `print()`.

---

## 3. Public Module Exports (`__all__`)

1. **Placement:** Declare a static `__all__` immediately after all imports and
   before constants, instance creation, functions, classes, or other module code.
   List exported names as strings so their definitions can appear later.
2. **Minimal core API:** Export only essential interfaces, preferably matching
   documented functional requirements. The number of exported names must not
   exceed the module's documented FR count: five FRs allow at most five exports,
   and fewer are preferred. Do not invent FRs to justify additional exports.
   Defining a class does not automatically make it part of the public API.
3. **Prefer suitable shared instances:** Where a shared read-only interface makes
   sense, export an instantiated variable such as `settings = HostSettings()`
   instead of the class. Consumers can then import `settings` and access its
   attributes with dot notation. Use this pattern only when initialization is safe
   at import time and one shared instance fits the feature's ownership model.
   Export a class or factory when callers need independent configuration, mutable
   state, or explicit lifecycle ownership. Instantiation alone does not make an
   object's attributes read-only; enforce that property in the implementation.
4. **Internal implementation:** Keep helpers, implementation classes, imported
   dependencies, and demonstration-only `main()` out of `__all__` unless they are
   necessary core interfaces. Prefer underscore prefixes for internal definitions.
   Use an empty `__all__` when the module has no public API. `__all__` declares the
   supported API; it does not prevent direct access to other module attributes.
5. **Explicit and consistent names:** Each export must be unique and resolve to an
   actual module attribute. Avoid dynamic mutation of `__all__`, wildcard imports,
   and incidental re-exports of dependencies. Keep Python API usage examples
   aligned with the declared exports.

Illustrative excerpt from `settings.py` (the full module must also satisfy the
docstring, logging, and executable demonstration requirements):

```python
from dataclasses import dataclass

from app.host.logging import get_logger

__all__ = ["settings"]

logger = get_logger(__name__)


@dataclass(frozen=True)
class _HostSettings:
    """Hold shared read-only host settings."""

    environment: str = "development"


settings = _HostSettings()
```

Consumers use `from settings import settings`, then `settings.environment`.
The implementation class stays internal; only the shared instance is exported.

---

## 4. Formatting & Linter Rules

1. **Line Length:** Strictly $\le 88$ characters per line. Indented text, code blocks, and list items must wrap cleanly to avoid `line-too-long` violations under `ruff`.
2. **Indentation:** Four spaces for section bodies and list items; two additional spaces for nested metadata (`Associated:`, `Logging:`).
3. **Markdown Syntax in Docstrings:** Use backticks for symbols, parameters, and classes. Enclose Python snippets in `` ```python `` and CLI commands in `` ```bash ``.

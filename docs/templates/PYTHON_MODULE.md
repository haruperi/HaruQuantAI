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

Capabilities:
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

### 2.4 Python API Usage

- Provide a clean, copy-pasteable Python snippet demonstrating how peer modules or test harnesses import and invoke this module's public interfaces.
- Show configuration, async execution (if applicable), and resource cleanup.

### 2.5 CLI Usage

- Show practical command-line invocations via `uv run python -m ...` demonstrating direct execution, entrypoint flags, or CLI utility commands.

---

## 3. Formatting & Linter Rules

1. **Line Length:** Strictly $\le 88$ characters per line. Indented text, code blocks, and list items must wrap cleanly to avoid `line-too-long` violations under `ruff`.
2. **Indentation:** Four spaces for section bodies and list items; two additional spaces for nested metadata (`Associated:`, `Logging:`).
3. **Markdown Syntax in Docstrings:** Use backticks for symbols, parameters, and classes. Enclose Python snippets in `` ```python `` and CLI commands in `` ```bash ``.

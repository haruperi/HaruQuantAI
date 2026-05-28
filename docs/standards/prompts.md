# HaruQuantAI Reusable Production Prompts

Use these prompts as standard workflows for auditing and rewriting HaruQuant
source files. The recommended flow is:

1. Upload the file you want to standardize.
2. Send Prompt 1 to audit it.
3. After the audit, attach `Tools_Functions_Standard.md` when the file is a
   tool file or may be agent-callable.
4. Send Prompt 2 to generate the production-ready file, tests, usage example,
   and registry updates where needed.

## Prompt 1: Production Readiness Audit Prompt

I will upload one source file from my HaruQuant trading application.

Your task is to review the file carefully and tell me whether it is
production-ready.

Please evaluate the file against a professional production standard for a Python
trading application, especially considering maintainability, testing, logging,
documentation, error handling, type safety, modularity, and future agentic AI
integration.

Do **not** rewrite the file yet.

Instead, provide a structured audit with the following sections:

### 1. File Purpose Summary

Explain what this file currently does in simple terms.

### 2. Production Readiness Verdict

State clearly whether the file is:

- Production-ready
- Almost production-ready
- Partially production-ready
- Not production-ready

Explain why.

### 3. Strengths

List what is already good in the file.

### 4. Critical Issues

Identify serious problems that could cause bugs, confusion, unreliable trading
behavior, incorrect results, or maintenance problems.

### 5. Missing Production Features

Check whether the file has:

- Clear module-level docstring
- Clear class/function docstrings
- Type hints
- Input validation
- Output validation
- Error handling
- Logging
- Configurable parameters
- No hardcoded values unless justified
- Clean separation of responsibilities
- Deterministic behavior where required
- Proper exception strategy
- Testability
- Unit-test coverage expectations
- Usage example requirements
- Compatibility with the rest of HaruQuant
- Agent/tool compatibility if relevant
- Security and safety considerations if relevant
- Performance concerns if relevant

### 6. Standardization Recommendations

Recommend exactly what should be added, removed, renamed, split, merged, or
refactored.

### 7. Suggested Target Structure

Show the ideal structure of the improved file, including expected classes,
functions, helper functions, constants, and logging setup.

### 8. Required Supporting Files

Tell me whether this file should also have:

- A unit test file
- A usage example file
- A README or documentation section
- A config/schema file
- Mock/stub files
- Fixtures or sample data

### 9. Acceptance Criteria

Create a checklist that must be satisfied before this file can be considered
production-ready.

### 10. Final Recommendation

Tell me what should happen next before rewriting the file.

## Prompt 2: Production Tool Standardization and File Rewrite Prompt

Using the audit and recommendations from Prompt 1, now standardize the uploaded
HaruQuant file into a production-ready version.

You must also follow the attached document:

the **HaruQuant AI Tool Function Standard**.

Treat that document as the official standard for any file that belongs inside
`tools/` or contains functions intended to be used by HaruQuant agents
as tools.

Your task is to create a clean, consistent, maintainable, and production-grade
version of the uploaded file.

---

### 1. Preserve the Original Purpose

Do not remove the original purpose or important functionality unless it is
clearly wrong, duplicated, unsafe, or unnecessary.

If functionality is unclear, preserve it but improve the structure around it.

Do not make the file unnecessarily bloated.

The goal is not to add complexity.
The goal is to make the file clear, safe, consistent, testable, agent-friendly,
and easy to maintain.

---

### 2. Determine Whether This Is an AI Tool File

Before rewriting, determine whether the uploaded file is:

- An official AI tool file
- A tool helper/internal implementation file
- A domain `__init__.py` registry file
- A non-tool production module

Use the attached **HaruQuant AI Tool Function Standard** to decide.

A function is considered an official AI Tool if it is exported through a tool
domain `__init__.py` and listed in `__all__`.

If the file contains functions intended to be called by agents, standardize them
as official AI Tools.

If the file contains only internal helpers, keep them clean, typed, documented,
and tested, but do not force every helper into the full AI Tool response schema
unless it is exported as an agent-callable tool.

---

### 3. Apply the HaruQuantAI Tool Function Standard

For every official AI Tool, apply the attached standard fully.

Each official AI Tool must include:

- Agent-facing docstring
- Type hints
- Input validation
- Structured logging
- Standard return schema
- Deterministic error codes
- Tool metadata
- Risk metadata
- Side-effect declarations
- `request_id: Optional[str] = None`
- Execution timing using `execution_ms`
- No silent failures
- No raw `None` returns
- No `print()` in production logic
- Safe exception handling
- Clear success and error responses

The standard return schema must follow this structure:

```python
{
    "status": "success" | "error",
    "message": str,
    "data": Any,
    "error": None | {
        "code": str,
        "details": str,
    },
    "metadata": {
        "tool_name": str,
        "tool_version": str,
        "tool_category": str,
        "tool_risk_level": str,
        "request_id": str | None,
        "execution_ms": float,
        "read_only": bool,
        "writes_file": bool,
        "modifies_database": bool,
        "places_trade": bool,
        "requires_network": bool,
    },
}
```

---

### 4. Tool Metadata Standard

Every official AI Tool must define metadata constants such as:

```python
TOOL_NAME = "tool_name_here"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
```

The values must reflect the actual behavior of the tool.

Use these risk levels:

- `low`: read-only, safe, no state mutation
- `medium`: creates files, generates reports, writes local artifacts, or runs
  expensive jobs
- `high`: modifies strategy settings, risk settings, database state, or
  configurations
- `critical`: places trades, closes trades, changes live account state, or
  activates live systems

If a tool is high-risk or critical, include explicit approval and permission
checks before execution.

---

### 5. Logging Standard

Every production file must use structured logging.

For tool files, follow the attached standard and import the project logger as
required by HaruQuant:

```python
from tools.utils import logger
```

Each official AI Tool must log:

- Tool called
- Validation failure
- Successful completion
- Execution failure

Do not log secrets, passwords, broker credentials, API keys, account tokens, or
sensitive data.

Avoid `print()` in production code.

---

### 6. Error Handling Standard

Use deterministic error codes so agents can reason about failures.

Allowed common error codes include:

```text
INVALID_INPUT
PERMISSION_DENIED
DATA_NOT_FOUND
EMPTY_RESULT
SERVICE_UNAVAILABLE
BROKER_UNAVAILABLE
DATABASE_ERROR
NETWORK_ERROR
TIMEOUT
VALIDATION_FAILED
TOOL_EXECUTION_FAILED
UNKNOWN_ERROR
```

Every failure must return a structured error response.

Do not silently swallow exceptions.

Do not return raw exceptions.

Avoid broad `except Exception` unless it is used at the tool boundary and logs
the failure properly.

---

### 7. File-Level Documentation Standard

Every Python file must start with a file-level docstring explaining:

- Purpose of the file
- Whether it contains AI tools or internal helpers
- Classes in the file
- Functions in the file
- Which functions are intended to be exported as AI Tools

Every public function and class must have a clear docstring.

For AI Tools, docstrings must be agent-facing and explain:

- What the tool does
- When an agent should use it
- Arguments
- Return value
- Error cases
- Side effects

---

### 8. `__init__.py` Registry Rule

If the uploaded file is a tool domain `__init__.py`, it must only expose
approved tools.

It must not contain:

- Business logic
- Broker logic
- API calls
- Database logic
- Validation logic
- Calculation logic

It should only import approved tools and define `__all__`.

Organize imports by source file.

Example pattern:

```python
"""
Data tools exposed to HaruQuant agents.

Only approved AI-callable data tools should be exported here.
"""

# market_data.py tools
from tools.data.market_data import get_market_data

# validators.py tools
from tools.data.validators import validate_ohlcv_quality


__all__ = [
    # market_data.py tools
    "get_market_data",

    # validators.py tools
    "validate_ohlcv_quality",
]
```

Agents must import tools from the domain package:

```python
from tools.data import get_market_data
```

Avoid agent imports from deep implementation files:

```python
from tools.data.market_data import get_market_data
```

---

### 9. Input Validation Standard

Every official AI Tool must validate all external inputs before execution.

Validation should check for:

- Missing required values
- Wrong types
- Invalid enum/string choices
- Invalid numeric ranges
- Unsafe paths
- Unsupported symbols
- Unsupported timeframes
- Invalid date ranges
- Invalid risk values
- Invalid order sizes

Invalid input must return a structured error response using `INVALID_INPUT`.

---

### 10. Testing Standard

After rewriting the main file, also create a unit test file.

The unit test file must be placed under:

```text
tests/unit/tools/{domain}/test_{source_file}.py
```

Every exported AI Tool must test:

- Successful call
- Invalid input
- Empty result where applicable
- Service/tool failure where applicable
- Standard return schema compliance
- Metadata correctness
- Error code correctness
- Logging footprint
- Permission denial for high-risk or critical tools

Use mocks where external systems are involved.

---

### 11. Usage Example Standard

Also create a real-world usage example file.

The usage example must be placed under:

```text
tests/usage/tools/{domain}/{source_file}.py
```

The usage example must:

- Demonstrate actual function calls
- Avoid mocks
- Show how an agent or workflow would consume the result
- Handle both success and error responses
- Use a realistic `request_id`

---

### 12. Output Format

Provide the output as separate files using filename headers.

Use this format:

```text
# filename: path/to/file.py
```

Then provide the full code for that file.

Create at least:

1. The standardized production implementation file
2. The domain `__init__.py` file if tool exports are required
3. The unit test file
4. The usage example file

Only add extra files if they are truly necessary.

---

### 13. Final Production Checklist

At the end, provide a checklist confirming:

- File-level docstring added
- Tool metadata added
- Side-effect flags added
- `request_id` support added
- Standard return schema implemented
- Input validation implemented
- Logging implemented
- Error handling implemented
- Permission/risk checks implemented where needed
- `__init__.py` registry updated where needed
- Unit tests created
- Usage example created
- Agent import boundary respected
- No unnecessary complexity added

---

### 14. Important Constraint

Do not over-engineer the file.

Do not create duplicate wrapper functions unless the original function is too
low-level, unsafe, or not agent-friendly.

Keep the implementation readable, compact, and production-ready.

The final result should be easy for future agents and humans to understand,
test, debug, and extend.

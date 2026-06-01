# Re-write Prompt v2 — Service-Specific HaruQuant Production Rewrite

You are an expert AI Systems Architect, Senior Python Developer, Quant Trading Systems Engineer, and Production Refactoring Specialist.

You specialize in transforming incomplete, inconsistent, or prototype-level Python trading code into clean, production-ready HaruQuant modules.

Using the audit and recommendations from Prompt 1, now standardize the uploaded HaruQuant file into a production-ready version.

This rewrite prompt applies to files inside the HaruQuant `tools/` stack and to supporting files that are intended to be used by HaruQuant agents, workflows, simulations, risk review, portfolio management, analytics, optimization, or execution.

---

## 0. Required Specification Selection Rule

Before rewriting any file, first identify the file's target domain from its path, imports, purpose, and exported functions.

Then apply the correct service-level technical specification document for that domain.

The rewrite must not rely only on the generic Tool Function Standard. The rewrite must also follow the matching module specification below.

### 0.1 Domain-to-Specification Mapping

Use this table as the mandatory mapping:

| Uploaded file location / domain | Required service specification document |
|---|---|
| `tools/utils/` | `Utils_Module_Technical_Specification.md` |
| `tools/data/` | `Data_Module_Technical_Specification.md` |
| `tools/simulation/` | `HaruQuant_Simulator_Technical_Specification.md` |
| `tools/indicators/` | `HaruQuant_Simulator_Technical_Specification.md` unless a dedicated indicator spec is supplied |
| `tools/strategies/` | `HaruQuant_Simulator_Technical_Specification.md` unless a dedicated strategy spec is supplied |
| `tools/analytics/` | `Analytics_Module_Technical_Specification.md` |
| `tools/optimization/` | `Optimization_Evidence_Engine_Technical_Specification.md` |
| `tools/risk/` | `Risk_Module_Technical_Specification.md` |
| `tools/portfolio/` | `Portfolio_Module_Technical_Specification.md` |
| `tools/execution/` | `Execution_Module_Technical_Specification.md` |
| `tools/execution/brokers/mt5.py` or MT5 adapter files | both `Execution_Module_Technical_Specification.md` and `HaruQuant_MT5_Broker_Adapter_Implementation_Specification_v1.md` |
| Cross-domain shared contracts, shared implementation plans, or orchestration-level files | `HaruQuant_Core_Stack_Implementation_Blueprint_v1.md` plus any directly affected domain specs |

### 0.2 Always-Apply Standards

In addition to the selected service specification, always apply these shared standards:

1. `Tools_Functions_Standard.md` for any official AI Tool or tool-domain registry.
2. `code_quality.md` for code formatting, typing, logging, testing, and coverage expectations.
3. `Agent_Standard.md` only when the file defines or configures agents.
4. `Agentic_AI_Playbook.md` only when the file participates in agentic workflow design, routing, policy, approval, audit, or orchestration.
5. `HaruQuant_Core_Stack_Implementation_Blueprint_v1.md` when the file has cross-domain dependencies, shared contracts, shared errors, shared audit records, or implementation-order implications.

### 0.3 Conflict Precedence

When documents overlap, use this precedence order:

1. The specific user instruction in the current message.
2. The latest audit findings from Prompt 1.
3. The matching service-level technical specification document.
4. `HaruQuant_Core_Stack_Implementation_Blueprint_v1.md` for cross-domain architecture and DRY placement.
5. `Tools_Functions_Standard.md` for official AI Tool mechanics.
6. `code_quality.md` for general code quality.
7. `Agent_Standard.md` and `Agentic_AI_Playbook.md` for agent/workflow files.

If two documents appear to duplicate the same rule, implement it once in the most DRY and domain-appropriate location.

If a service specification says a capability belongs in another module, do not duplicate it. Import or depend on the proper domain boundary instead.

---

## 1. Preserve the Original Purpose

Do not remove the original purpose or important functionality unless it is clearly wrong, duplicated, unsafe, obsolete, or explicitly replaced by the selected service specification.

If functionality is unclear, preserve it but improve the structure around it.

Do not make the file unnecessarily bloated.

The goal is not to add complexity. The goal is to make the file clear, safe, consistent, testable, agent-friendly where relevant, and easy to maintain.

---

## 2. Determine File Role Before Rewriting

Before writing code, classify the uploaded file as one of the following:

- official AI tool file
- tool helper/internal implementation file
- domain `__init__.py` registry file
- contracts/schema/model file
- service/orchestration file
- adapter/integration file
- test file
- usage example file
- non-tool production module
- agent file
- workflow/policy/audit file

Use the selected service-level specification and `Tools_Functions_Standard.md` to decide.

A function is considered an official AI Tool if it is exported through a tool domain `__init__.py` and listed in `__all__`.

If the file contains functions intended to be called by agents, standardize them as official AI Tools.

If the file contains only internal helpers, keep them clean, typed, documented, and tested, but do not force every helper into the full AI Tool response schema unless it is exported as an agent-callable tool.

---

## 3. Apply the Service Specification First

For the selected domain, rewrite the file so it aligns with the official folder structure, public tool surface, contracts, error codes, side-effect rules, and acceptance criteria defined by that domain's technical specification.

The rewrite must answer these questions before producing code:

1. Which service specification applies?
2. Is this file part of the official public tool surface, an internal service, a contract, an adapter, or a registry?
3. Which functionality belongs in this file and which functionality should be moved to another file or reused from another domain?
4. Which required supporting files are needed: tests, usage example, registry update, contracts, config, errors, fixtures, mocks, or README update?
5. Does this file introduce a dependency that must be built earlier according to the core-stack implementation blueprint?

Do not silently create new architecture that conflicts with the selected service specification.

---

## 4. Apply the HaruQuantAI Tool Function Standard

For every official AI Tool, apply the attached standard fully.

Each official AI Tool must include:

- agent-facing docstring
- type hints
- input validation
- output validation where appropriate
- structured logging
- standard return schema
- deterministic error codes
- tool metadata
- risk metadata
- side-effect declarations
- `request_id: Optional[str] = None`
- `workflow_id: Optional[str] = None` where required by the domain specification
- execution timing using `execution_ms`
- no silent failures
- no raw `None` returns
- no `print()` in production logic
- safe exception handling
- clear success and error responses
- tests for schema compliance and metadata correctness

The standard return schema must follow this structure unless the selected service specification adds required metadata fields:

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

For execution tools, risk tools, portfolio lifecycle tools, and approval-sensitive tools, include any extra metadata required by the selected service spec, such as:

```python
"workflow_id": str | None
"requires_approval": bool
"approval_required": bool
```

---

## 5. Tool Metadata Standard

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

The values must reflect the actual behavior of the tool and the selected service specification.

Use these risk levels:

- `low`: read-only, safe, no state mutation
- `medium`: creates files, generates reports, writes local artifacts, runs expensive jobs, or changes local non-live state
- `high`: modifies strategy settings, risk settings, portfolio lifecycle state, database state, or configurations
- `critical`: places trades, closes trades, changes live account state, activates kill switches, or mutates live broker/account state

If a tool is high-risk or critical, include explicit approval and permission checks before execution.

---

## 6. Logging Standard

Every production file must use structured logging.

For tool files, follow the attached standard and import the project logger as required by HaruQuant:

```python
from tools.utils import logger
```

Each official AI Tool must log:

- tool called
- validation failure
- successful completion
- execution failure

Internal services must log important validation failures, external service failures, recoverable errors, state transitions, and audit-relevant events.

Do not log secrets, passwords, broker credentials, API keys, account tokens, private connection strings, or sensitive data.

Avoid `print()` in production code.

---

## 7. Error Handling Standard

Use deterministic error codes so agents can reason about failures.

Start with common error codes from the Tool Function Standard and extend only with domain-approved codes from the selected service specification.

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

Domain-specific examples must use the selected spec's taxonomy, for example:

- data errors should use data-module error codes
- risk errors should use risk-module error codes
- optimization errors should use `OPT_` prefixed error codes where specified
- execution and MT5 errors should use deterministic execution/MT5 broker error codes

Every failure must return a structured error response at the official tool boundary.

Do not silently swallow exceptions.

Do not return raw exceptions.

Avoid broad `except Exception` unless it is used at the tool boundary and logs the failure properly.

---

## 8. File-Level Documentation Standard

Every Python file must start with a file-level docstring explaining:

- purpose of the file
- whether it contains AI tools or internal helpers
- classes in the file
- functions in the file
- which functions are intended to be exported as AI Tools
- which domain specification this file follows

Every public function and class must have a clear docstring.

For AI Tools, docstrings must be agent-facing and explain:

- what the tool does
- when an agent should use it
- arguments
- return value
- error cases
- side effects

---

## 9. `__init__.py` Registry Rule

If the uploaded file is a tool domain `__init__.py`, it must only expose approved tools for that domain.

It must not contain:

- business logic
- broker logic
- API calls
- database logic
- validation logic
- calculation logic
- dynamic service loading
- runtime mutation of exported callables

It should only import approved tools and define `__all__`.

Organize imports by source file.

Example pattern:

```python
"""
Data tools exposed to HaruQuant agents.

Only approved AI-callable data tools should be exported here.
Follows Data_Module_Technical_Specification.md and Tools_Functions_Standard.md.
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

## 10. Input Validation Standard

Every official AI Tool must validate all external inputs before execution.

Validation should check for:

- missing required values
- wrong types
- invalid enum/string choices
- invalid numeric ranges
- unsafe paths
- unsupported symbols
- unsupported timeframes
- invalid date ranges
- invalid risk values
- invalid order sizes
- invalid approval packets
- invalid evidence references
- stale or missing data where the domain requires freshness
- invalid cross-domain contracts

Invalid input must return a structured error response using `INVALID_INPUT` or the selected service specification's more precise deterministic error code.

---

## 11. DRY and Cross-Domain Boundary Rules

Do not duplicate shared infrastructure inside each service module.

Use the shared foundation instead:

- standard responses, metadata, and schema validation belong in `tools.utils`
- request IDs, workflow IDs, canonical JSON, timestamps, redaction, and safe paths belong in `tools.utils`
- reusable cross-domain contracts should follow the core-stack blueprint
- market data acquisition belongs in `tools.data`
- trade execution and broker mutation belong in `tools.execution`
- risk approval belongs in `tools.risk`
- portfolio allocation and lifecycle belong in `tools.portfolio`
- analytics reports belong in `tools.analytics`
- optimization evidence belongs in `tools.optimization`
- simulation trading truth belongs in `tools.simulation`

If the uploaded file duplicates a shared concern, refactor it to import the shared helper or explicitly note the supporting file that must be created first.

---

## 12. Testing Standard

After rewriting the main file, also create or update a unit test file.

The unit test file must be placed under:

```text
tests/unit/tools/{domain}/test_{source_file}.py
```

Every exported AI Tool must test:

- successful call
- invalid input
- empty result where applicable
- service/tool failure where applicable
- standard return schema compliance
- metadata correctness
- side-effect metadata correctness
- error code correctness
- logging footprint
- permission denial for high-risk or critical tools
- domain-specific contract compliance from the selected service specification

Use mocks where external systems are involved.

For adapter files such as MT5, broker/network/terminal calls must be mocked in unit tests.

---

## 13. Usage Example Standard

Also create a real-world usage example file.

The usage example must be placed under:

```text
tests/usage/tools/{domain}/{source_file}.py
```

The usage example must:

- demonstrate actual function calls
- avoid mocks
- show how an agent or workflow would consume the result
- handle both success and error responses
- use a realistic `request_id`
- use `workflow_id` where the selected domain requires it
- avoid secrets and live credentials

---

## 14. Output Format

Provide the output as separate files using filename headers.

Use this format:

```text
# filename: path/to/file.py
```

Then provide the full code for that file.

Create at least:

1. the standardized production implementation file
2. the domain `__init__.py` file if tool exports are required
3. the unit test file
4. the usage example file

Add supporting files only when they are truly necessary, such as:

- `contracts.py`
- `errors.py`
- `config.py`
- `fixtures.py`
- mock adapters
- registry updates
- README section

If a supporting file is required but too large to include in the same answer, list it clearly under `Required Supporting Files Still Needed`.

---

## 15. Final Production Checklist

At the end, provide a checklist confirming:

- correct service specification selected and named
- file role classified correctly
- file-level docstring added
- tool metadata added where needed
- side-effect flags added where needed
- `request_id` support added
- `workflow_id` support added where required
- standard return schema implemented for official AI Tools
- input validation implemented
- output validation implemented where appropriate
- logging implemented
- error handling implemented
- permission/risk checks implemented where needed
- `__init__.py` registry updated where needed
- DRY shared helpers reused instead of duplicated
- domain-specific contracts followed
- unit tests created
- usage example created
- agent import boundary respected
- no unnecessary complexity added
- no live broker mutation outside the approved execution gateway
- no secrets logged or returned
- coverage target remains compatible with the 80% minimum gate

---

## 16. Important Constraint

Do not over-engineer the file.

Do not create duplicate wrapper functions unless the original function is too low-level, unsafe, or not agent-friendly.

Do not expand the public AI Tool surface beyond what the selected service specification allows.

Keep the implementation readable, compact, deterministic, and production-ready.

The final result should be easy for future agents and humans to understand, test, debug, and extend.

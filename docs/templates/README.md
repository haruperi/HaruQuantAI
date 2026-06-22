# [Module/Service Name] (`[path/to/module]`)

## Overview
[Briefly describe what this module is, its core responsibility, and its place in the broader system architecture. Mention any strict guarantees it provides, e.g., "import-safe", "thread-safe", "side-effect-free".]

## Design Philosophy & Non-Negotiable Rules
[List the core principles that govern this module. These are rules that contributors must never break.]
* **Rule 1 (e.g., Import Safety):** [Description of the rule and why it matters.]
* **Rule 2 (e.g., No Domain Logic):** [Description.]
* **Rule 3 (e.g., Unified Entry Point):** [Description of how external services should interact with this module.]

## Features
[Break down the module into its core files/components. For each, provide a brief description and list the public API.]

### `[filename_1.py]` — [Feature Name]
[1-2 sentences describing what this file does.]
**Key exports:** `FunctionA`, `ClassB`, `CONSTANT_C`

### `[filename_2.py]` — [Feature Name]
[1-2 sentences describing what this file does.]
**Key exports:** `FunctionX`, `ClassY`

## Installation
### Prerequisites
* `uv` installed and available globally.

### Dependencies
* **Standard Library:** `[lib1]`, `[lib2]`
* **Required Third-Party:** `[lib3]` — [Brief reason, e.g., "Used for X"]
* **Optional Third-Party:** `[lib4]` — [Fallback behavior, e.g., "Falls back to Y if absent"]

**Install command:**
```bash
uv add [package_name]
```

### Integration with `app` package
Use of local modules
```python
# Correct — unified public registry
from app.services.[module_name] import FunctionA, FunctionB

# Incorrect — bypasses the registry and violates the design contract
from app.services.[module_name].function_a import FunctionA  # Do not do this
from app.services.[module_name].function_b import FunctionB  # Do not do this
```

## Usage Examples
[Provide code examples demonstrating the intended usage patterns. Highlight the "safe" or "recommended" way to interact with this module, referencing the rules in the Design Philosophy section.]

### Basic Usage
This is like the "hello world" of this module.

```python
# Example 1: [Description]
from [module_path] import FunctionA

result = FunctionA(param1, param2)
```

### Feature-Specific Usage
[Describe any feature-specific usage patterns, such as using optional features, configuring the module, or working with edge cases. Reference relevant rules from the Design Philosophy section.]

```python
# Example 2: [Description]
from [module_path] import FunctionB

result = FunctionB(param1, param2)
```

### Advanced Usage / Error Handling and Edge Cases
[Describe how the module handles errors and edge cases. Mention any fallback behaviors, retry mechanisms, or error handling strategies. Reference relevant rules from the Design Philosophy section.]

```python
# Example 3: [Description]
from [module_path] import FunctionC

result = FunctionC(param1, param2)
```

## API Reference

### `[Module]`

#### `FunctionA(param1: str, param2: int) -> str`
[Brief description of what this function does, its parameters, and what it returns. Mention any important constraints or side effects.]

**Parameters:**
* `param1` (str): [Description]
* `param2` (int): [Description]

**Returns:**
* `str`: [Description]

**Raises:**
* `ValueError`: [Description]
* `TypeError`: [Description]

**Example:**
```python
# Example usage
from [module_path] import FunctionA

result = FunctionA("hello", 42)
print(result)
```

## Testing Strategy
[Describe the testing strategy for this module. Mention any specific testing approaches, such as unit testing, integration testing, property-based testing, or contract testing. Reference relevant rules from the Design Philosophy section.]

### Unit Tests
[Describe the unit testing approach for this module. Mention any specific unit testing patterns, such as test-driven development, behavior-driven development, or test doubles. Reference relevant rules from the Design Philosophy section.]

**Test command:**
```bash
pytest tests/[module_path]/test_[function_name].py
```

### Property-Based Tests
[Describe any property-based testing approaches for this module. Mention any specific property-based testing frameworks or libraries used. Reference relevant rules from the Design Philosophy section.]

**Test command:**
```bash
pytest tests/[module_path]/test_property_based.py
```

### Integration Tests
[Describe any integration testing approaches for this module. Mention any specific integration testing patterns, such as contract testing, component testing, or system testing. Reference relevant rules from the Design Philosophy section.]

**Test command:**
```bash
pytest tests/[module_path]/test_integration.py
``` 
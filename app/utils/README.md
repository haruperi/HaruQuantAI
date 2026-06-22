# Utilities Module (`app/utils`)

## Overview
The `app/utils` module provides fundamental, framework-wide utilities that form the foundation of HaruQuantAI. These utilities are strictly **import-safe, thread-safe, and side-effect-free** at import time. They handle logging, configuration, paths, error classification, standard API envelopes, and encryption/redaction.

## Design Philosophy & Non-Negotiable Rules
* **Rule 1 (Import Safety):** Importing any utility module must not configure logging, access the filesystem, call networks, or mutate state. All such side effects are deferred until explicit function calls.
* **Rule 2 (No Domain Logic):** Utilities must remain strictly domain-agnostic. They provide standard structures and mathematical or computational support, leaving quant rules, risk constraints, and strategy definitions to other layers.
* **Rule 3 (Fail-Closed Security):** Path manipulation, secret handling, and configurations must fail securely. Path traversal is rejected by default, and sensitive data is actively redacted from logs and tool envelopes.

## Features

### `logger.py` — Logger & Configuration
Provides the central loguru logger export and setup functions to configure rotating file logs.
* **Key exports:** `logger`, `setup_logging`

### `errors.py` — Deterministic Error Utility
Consolidates standard exception definitions, error routing, and the official HaruQuant deterministic error-code registry.
* **Key exports:** `Error`, `ValidationError`, `ConfigurationError`, `SecurityError`, `DataError`, `ExternalServiceError`, `TradingError`, `route_error`, `code_for_exception`

### `paths.py` — Safe Path Normalization
Handles file path canonicalization with traversal protection to prevent escaping the application home directory.
* **Key exports:** `normalize_path`, `safe_join`, `validate_path_within_root`, `ensure_dir`, `ensure_parent_dir`

### `security.py` — Security & Redaction
Provides Argon2id/PBKDF2 password hashing, Fernet symmetric encryption, secret-version selection, and recursively redacts credentials from objects and logs.
* **Key exports:** `redact_text`, `redact_mapping`, `hash_password`, `verify_password`, `encrypt_text`, `decrypt_text`, `redact_payload`

### `settings.py` — Runtime Configuration
Loads environment settings using Pydantic, validates live trading flags/adapters, and holds research/EdgeLab configuration schemas.
* **Key exports:** `Settings`, `settings`, `load_config`, `validate_config`, `EdgeLabConfig`

### `standard.py` — Standard Response Envelopes
Defines the required metadata structures and output contracts (`success_response`, `error_response`) returned by official AI tools, alongside OHLCV data validation.
* **Key exports:** `build_metadata`, `success_response`, `error_response`, `response_from_exception`, `validate_standard_response`, `canonical_json`, `stable_identifier`

### `event_bus.py` — Diagnostic Event Bus
Exposes an in-memory event bus and structured event envelope builder.
* **Key exports:** `InMemoryEventBus`, `build_event_envelope`

## Installation
### Prerequisites
* `uv` installed globally.

### Dependencies
* **Standard Library:** `hashlib`, `json`, `math`, `re`, `time`, `pathlib`, `uuid`
* **Required Third-Party:**
  * `loguru` — Structured, contextual application logging
  * `pydantic` & `pydantic-settings` — Strong type-safe configuration loading
  * `cryptography` — Strong symmetric Fernet encryption
* **Optional Third-Party:**
  * `argon2-cffi` — High-security password hashing (falls back to PBKDF2 if missing)

**Install command:**
```bash
uv add loguru pydantic pydantic-settings cryptography
```

### Integration with `app` package
Always import utilities from the top-level package namespace:
```python
# Correct — unified public registry
from app.utils.errors import ValidationError
from app.utils.paths import normalize_path

# Incorrect — bypasses design contract
from app.utils.errors.validation_error import ValidationError  # Do not do this
```

## Usage Examples

### Deterministic Error Handling
```python
from app.utils.errors import ValidationError, exception_to_error_payload

try:
    raise ValidationError("Input volume must be positive.", code="INVALID_INPUT")
except ValidationError as exc:
    # Safely convert exception to standard JSON-serializable payload
    payload = exception_to_error_payload(exc)
    print(payload)  # {'code': 'INVALID_INPUT', 'details': 'ValidationError: ...'}
```

### Path Traversal Protection
```python
from app.utils.paths import safe_join
from app.utils.errors import SecurityError
from pathlib import Path

base_dir = Path("/app/data")
try:
    # Traversal attempt that escapes base_dir is blocked
    safe_path = safe_join(base_dir, "../../etc/passwd")
except SecurityError:
    print("Blocked traversal attempt!")
```

### Standard Tool Envelope
```python
import time
from app.utils.standard import build_metadata, success_response, validate_standard_response

start = time.perf_counter()
# Execute tool logic here...

# Prepare standard metadata
meta = build_metadata(
    tool_name="my_quant_tool",
    start_time=start,
    reads=True,
    writes=False
)

# Return canonical response envelope
res = success_response(
    message="Action executed.",
    data={"status": "active"},
    metadata=meta
)
validate_standard_response(res)
```

## API Reference

### `app.utils.paths`

#### `safe_join(base_dir: str | Path, *parts: str | Path) -> Path`
Resolves and joins path parts relative to `base_dir` while verifying the result does not escape `base_dir`.

**Parameters:**
* `base_dir` (str | Path): Boundary root directory.
* `*parts` (str | Path): Components to append.

**Returns:**
* `Path`: Normalized, absolute resolved path.

**Raises:**
* `ValidationError`: If parameters are empty/malformed.
* `SecurityError`: If resolved path attempts to escape the root directory.

## Testing Strategy
The utilities directory is covered by comprehensive unit tests located under `tests/unit/app/utils/`.

### Unit Tests
Unit tests verify exceptions, route deduplication, path traversal defenses, redaction depth limits, password hashing, and config overrides.

**Test command:**
```bash
uv run pytest tests/unit/app/utils/
```

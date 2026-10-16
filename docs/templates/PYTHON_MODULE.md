# Standard Python Feature Module Specification

> **Authority:** Mandatory repository-wide standard for Python feature and service
> modules.
> **Constitutional Mandate:** `AGENTS.md` Section 2.
> **Clean-Room Brand Invariant:** Under clean-room implementation rules, no
> third-party brand names or proprietary acronyms (e.g., StrategyQuant, SQX, etc.)
> may appear anywhere in code, comments, docstrings, constants, or identifiers.
> **Exclusions:** Pure contracts (`_common.py`), package facades (`__init__.py`),
> unit/integration tests, and non-feature helper libraries.

---

## Canonical Python Feature Module Template

All sections, docstrings, exports, classes, and architectural invariants are
demonstrated below in a single self-documenting template:

```python
"""[Concise Single-Line Module Summary Ending With A Period].

Description:
    [Business logic description: System rationale, architectural role, external
    relations/workflows with other subsystems, and internal flow between classes.
    Clean-room invariant: Zero references to third-party brand names or acronyms
    (e.g., StrategyQuant, SQX, etc.) in docstrings, comments, or code.]

Purpose:
    [Feature identifier and scope: FEAT-<SUBSYSTEM>-<NAME> (e.g. FEAT-DATAMGR-HOME).]

Key Capabilities:
    - FR-<SUBSYSTEM>-<NAME>-<CAPABILITY>: [Descriptive semantic summary]
      Associated: `[Feature.method()]`
      Logging: [Explicit log level (DEBUG, INFO, WARNING, ERROR) and payload.
      NO functional requirement may execute silently.]

Python API Usage:
    ```python
    from app.domain.feature import Feature, FeatureCLI

    service = Feature()
    result = service.execute_task()
    print(FeatureCLI.format_output(result))
    ```

CLI Usage:
    ```bash
    uv run python -m app.domain.feature
    ```
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.host.logging import get_logger

# Domain-internal models and contracts imported from relative _common
from ._common import DomainContract

# 1. Public Exports: Export ONLY the main service class and optional CLI class.
# Never export internal _Config, logger, helpers, or external dependencies.
__all__ = [
    "Feature",
    "FeatureCLI",
]

# 2. Centralized Logger: Consuming modules must not import standard logging.
logger = get_logger(__name__)


# 3. Internal Module Settings Config: Standardized naming convention `_Config`.
# Strictly private to this file (prefixed with _), holds parameters/metrics.
# Never exported in __all__ or imported by external modules.
@dataclass(frozen=True)
class _Config:
    """Internal module configuration and execution parameters."""

    timeout_seconds: int = 30
    batch_size: int = 100

    def to_dict(self) -> dict[str, Any]:
        """Convert internal config or metrics to standard dictionary."""
        return {
            "timeout_seconds": self.timeout_seconds,
            "batch_size": self.batch_size,
        }


# 4. Main Feature Service Class: Named identically to file basename in PascalCase.
# (e.g., class Home: for home.py, class Data: for data.py).
class Feature:
    """Service implementing core business logic for this feature."""

    def __init__(self, config: _Config | None = None) -> None:
        """Initialize service with optional internal configuration."""
        self._config = config or _Config()

    # 1:1 Mapping: Exactly one public method per functional requirement (FR-*).
    # If a file declares 5 FRs, it must contain exactly 5 public methods.
    # No extraneous public helper methods on the service class.
    def execute_task(self) -> dict[str, Any]:
        """Execute core functional requirement."""
        self._validate_prerequisites()
        # No functional requirement may execute silently. Every FR must be logged.
        # To state what the function did, we use a f-string if there is values to show.
        logger.info(f"State what the function did (add any params if needed)")
        return self._config.to_dict()

    # Helper methods: MUST always be prefixed with a leading underscore `_*`.
    # Deduplication hierarchy:
    # - If duplicated within this domain folder -> move to <domain>/_common.py
    # - If duplicated across different domains -> move to app/services/libs/
    def _validate_prerequisites(self) -> None:
        """Private internal helper method validating execution prerequisites."""
        return None


# 6. CLI Class (Optional): Headless CLI formatter for app/cli.py and main demo.
#  Replace the `Feature` of FeatureCLI with the filename just like #5
class FeatureCLI:
    """Headless CLI formatter and table presentation helper."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format data into human-readable terminal output e.g tables, key-value pairs."""
        logger.debug("Any necessary info")
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)


# 7. Executable Demonstration: Real-usage demonstration using `print()` (not logger).
if __name__ == "__main__":
    """Demonstrate real usage of the feature."""
    service = Feature()
    output = service.execute_task()
    print(FeatureCLI.format_output(output))
```

---

## Formatting, Clean-Room & Linter Rules

- **Clean-Room Brand Prohibition:** Zero references to third-party proprietary
  brands, trademarks, or acronyms (e.g., StrategyQuant, SQX) in comments,
  docstrings, constants, string literals, or identifiers.
- **Line Length:** Strictly $\le 88$ characters per line under `ruff`.
- **Docstrings:** Google-style docstrings with four-space indentation.
- **Typing:** Strict Mypy compliance with all public arguments and return types
  explicitly annotated.

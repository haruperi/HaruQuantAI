# Standard Python Feature Module Specification

> **Authority:** Mandatory repository-wide standard for Python feature, host,
> workspace, and service modules.
> **Constitutional Mandate:** `AGENTS.md` Section 2.
> **Clean-Room Brand Invariant:** Under clean-room implementation rules, no
> third-party brand names or proprietary acronyms (e.g., StrategyQuant, SQX, etc.)
> may appear anywhere in code, comments, docstrings, constants, or identifiers.
> **Exclusions:** Pure contracts (`_common.py`), static DDL (`_schema.py`),
> package facades (`__init__.py`), and `tests/` are exempt from the service-class
> and top-of-file `FR-*` docstring rules (`0.1`, `0.3`), but remain bound by
> physical line-count, layering, and import rules (`0.2`, `0.4`–`0.8`).

---

## 0. Constitutional Anti-Spaghetti & Refactoring Rules (`0.1`–`0.8`)

### 0.1 Top-of-File Docstring Rule ($\le 100$ Physical Lines Hard Maximum)
- **Scope:** Applies to all Python feature, host, workspace, and service modules (excludes `__init__.py`, `_common.py`, `_schema.py`, and `tests/`).
- **Length:** Enforce a hard maximum of **$\le 100$ physical lines** (target `25–50` lines), adhering to the $\le 88$-character Ruff line limit.
- **Required Sections:** Include `Description:`, `Purpose:`, `Key Capabilities:`, `Python API Usage:`, and `CLI Usage:`.
- **`FR-*` Bullet Format:** Format each requirement under `Key Capabilities:` as a single compact bullet containing the `FR-*` ID, brief summary, `[ClassName.method_name()]`, and explicit log level (`INFO`, `WARNING`, `ERROR`, `DEBUG`).

### 0.2 File Line-Count & Complexity Cutoff Rule (1,000 Physical Lines Hard Maximum)
- **Scope:** Applies to **all** Python and TypeScript/React source files across the repository (including `_common.py` and `app/services/include/*`).
- **Physical Line Rubric** (counting all code, comments, and blank lines):
  - `< 200` lines: 🟢 **Ideal** — Focused, easy to test, and readable.
  - `200 – 500` lines: 🟡 **Sweet Spot** — Standard for closely related domain logic.
  - `501 – 1,000` lines: 🟠 **Warning** — Audit for Single Responsibility Principle (SRP) violations.
  - `> 1,000` lines: 🔴 **Refactor** — Strictly forbidden; split by cohesive subdomain or extract shared logic.
- **Cyclomatic Complexity:** Enforce Ruff McCabe `max-complexity = 10` per function/method (`pyproject.toml`).
- **Controlled Exceptions (Only 2 Allowed Categories):**
  1. **Generated Files:** Auto-generated schemas, protocol buffers, or compiled artifacts.
  2. **Static Configuration & DDL Assets:** Pure static data dictionaries, catalog mappings, or SQL DDL definitions (specifically `app/host/_schema.py`).
  - *Note:* No blanket exception for GUI components; UI files `> 1,000` lines must be decomposed into sub-components and hooks.

### 0.3 Upfront `FR-*` & Exact Method Signature Contract (AI-Tool Ready, Zero Aliases)
- **Strict 1:1 `FR-*` Mapping:** Specify every `FR-*` ID and its exact typed signature (`ClassName.method_name(args: Type) -> ReturnType`) upfront in the blueprint and `implementation-plan.md`.
- **No Invented Public Methods:** Expose **only** the $N$ public methods matching the $N$ declared `FR-*` requirements on a service class (standard dunders like `__init__`/`__len__` and `@abstractmethod` protocol hooks like `calculate` are structural and exempt).
- **Private Helpers Only:** Prefix all non-`FR` helper methods with a leading underscore (`_helper_name()`).
- **Zero Compatibility Shims or Aliases:** Never create alias methods (e.g., `_to_numpy = to_numpy`), deprecated wrappers, or duplicate module-level wrapper functions; update all internal callers atomically in the same refactor slice.
- **Typed & Tool-Ready Contracts:**
  - Host and Workspace `FR-*` methods must accept explicit typed inputs and return deterministic `dict[str, Any]` or `.to_dict()`-capable `@dataclass(frozen=True)` / `TypedDict` payloads for direct AI Agent / MCP tool registration.
  - Quantitative/kernel primitives (e.g., indicators) must return typed numerical contracts (`IndicatorSeries`, `np.ndarray`, or frozen dataclasses) with explicit mutation/copy policies.
- **Non-Silent Boundary Logging (Zero Hot-Loop Logging):**
  - Emit a structured log entry once per high-level `FR-*` operation via `logger = get_logger(__name__)` (`app/host/logging.py`) with `extra={"fr_id": ...}`.
  - **Forbid** logging inside per-bar, per-tick, or array-element hot loops (such as inside `IndicatorSeries` shift/condition checks).

### 0.4 Repository-Wide Semantic DRY Deduplication Hierarchy
- **Centralized Database Persistence (`HostPersistence` + `_schema.py`):**
  - Restrict all SQLite connections, WAL configuration, and parameterized CRUD/batch execution exclusively to `HostPersistence` (`app/host/persistence.py`).
  - Extract static SQL DDL strings, table lists, and primary/foreign-key metadata into private `app/host/_schema.py` (imported only by `app/host/persistence.py`) so `persistence.py` stays well under `1,000` lines.
  - Forbid `sqlite3` imports, `resolved_db_path()`, or `_get_connection()` in all other files; callers must exclusively use `HostPersistence.create_record()`, `read_records()`, `update_record()`, `delete_record()`, `create_entity()`, `read_entity()`, `update_entity()`, `delete_entity()`, or `apply_batch()`.
- **Indicator Base & Series Architecture (`app/services/indicators/`):**
  - Keep all 8 universal condition evaluators (`is_rising`, `is_falling`, `crosses_above`, `crosses_below`, `is_greater`, `is_lower`, `is_higher`, `changes_up`, `changes_down`) and shift indexing once on `IndicatorSeries` in `app/services/indicators/base.py`.
  - Keep shared array conversion and parameter validation once on `BaseIndicator` in `app/services/indicators/base.py`.
  - Subclass `BaseIndicator` in `app/services/indicators/<category>/<name>.py`, implementing only `calculate()` (and multi-buffer accessors where needed), targeting `< 150` lines (`🟢 Ideal`).
- **Broker Transport & History Parsers (`app/services/brokers/`):**
  - Isolate shared HTTP retry, rate-limiting, and secret redaction in `app/services/brokers/_http.py`.
  - Isolate shared CSV/TXT/archive history parsing in `app/services/brokers/_file_history.py`.
  - Isolate shared binary tick/bar decoding (`.bi5`, `.fxt`, `.hst`, `.dat`) in `app/services/brokers/_native_history.py`.
- **Semantic DRY & Cohesive Shared Modules:**
  - Extract shared logic only when 2+ modules share the **same semantic responsibility and reason to change** (no multi-flag "God helpers").
  - Same-domain shared contracts/helpers $\rightarrow$ `<domain>/_common.py` (or descriptive `<domain>/_<topic>.py`).
  - Cross-domain shared contracts/primitives $\rightarrow$ cohesive modules in `app/services/include/` (each strictly `< 1,000` lines, target `< 500`).

### 0.5 Strict One-Way Layering & Zero Inline Imports
- **One-Way Import DAG:** Enforce strict top-down dependency direction per `docs/ARCHITECTURE.md`:
  - `UI / CLI` $\rightarrow$ `app/workspace/*` $\rightarrow$ `app/services/*` $\rightarrow$ `app/host/*` $\rightarrow$ `app/services/include/*`
  - Plugins (`app/plugins/*`) attach dynamically via declared `SlotRegistry` contracts (`SC-02`, `SC-03`).
- **Forbidden Cross-Imports:**
  - `app/host/*` must contain zero quantitative/trading logic and never import `app/workspace/*` or `app/services/brokers/*` (except top-level wiring in `bootstrap.py`).
  - `app/services/*` must **never** import from `app/workspace/*`.
  - Sibling workspaces (`app/workspace/<domain_a>` and `app/workspace/<domain_b>`) and sibling plugins must **never** import from each other.
- **Top-of-File Imports Only:** Place all `import` statements at the module top level; function-scope or method-scope inline imports to bypass circular dependencies are strictly forbidden.

### 0.6 Single Service Class, Pure Calculation Separation & Route Isolation
- **1 Feature File = 1 Service Class:** Export at most `__all__ = ["<Feature>", "<Feature>CLI"]` (matching the file basename in PascalCase) with a private `@dataclass(frozen=True) class _Config`.
- **Separate I/O from Calculations:** Keep pure numerical/quantitative calculations decoupled from database access, network I/O, and filesystem mutations.
- **Isolate FastAPI/HTTP Routing:** Forbid FastAPI/HTTP imports (`APIRouter`, `HTTPException`, `JSONResponse`, `Request`) inside business, host-core, or service modules; isolate all HTTP endpoints, auth dependencies, and `StandardResponse` wrapping in dedicated `routes.py` modules.
- **Thin `__init__.py` Facades:** Restrict package `__init__.py` files to **$\le 100$ lines** containing only `__all__` and re-exports—zero executable logic, classes, or helper functions.

### 0.7 Explicit State, Resource Custody & Single-Path Dependency Injection
- **Zero Module-Level Mutable Singletons:** Forbid instantiating mutable global services or open handles at import time.
- **Single Wiring Path:** Instantiate and wire runtime capabilities (`EventBus`, `SessionManager`, `ResourceManager`, `JobManager`, `PluginLifecycleManager`) once in `AppHost` (`app/host/bootstrap.py`) and pass them via explicit constructor injection.
- **No Multi-Tier Fallback Chains:** Forbid fallback chains that probe `request.app.state` $\rightarrow$ optional `kwarg` $\rightarrow$ global singleton.
- **Explicit Lifecycle Ownership:** Every connection, worker pool, subscription, and background task must have one acquisition owner and deterministic LIFO teardown, with explicit transaction and idempotency guarantees on retries.

### 0.8 Behavior Preservation, Test Mirroring & Automated Architecture Gates
- **Characterize Before Refactoring:** Verify existing tests pass (or add missing characterization tests for outputs, errors, `HostPersistence` records, warm-up periods, `NaN` handling, and shift indexing) *before* restructuring any module.
- **1:1 Test Mirroring:** Map every `app/<tier>/<domain>/<module>.py` to `tests/unit/<tier>/<domain>/test_<module>.py`.
- **Test Public `FR-*` Contracts Only:** Unit tests must assert against public `FR-*` methods and persisted records—never private `_helper()` methods or private attributes.
- **Automated AST/CI Enforcement:** Enforce physical line limits ($\le 1,000$ file, $\le 100$ docstring/facade), McCabe complexity ($\le 10$), `sqlite3` import isolation, top-level-only imports, and the allowed-import matrix via `scripts/check_architecture.py` (wired into `scripts/ci_check.py` and `.pre-commit-config.yaml`) on every refactor slice.

---

## 1. Canonical Python Feature Module Template

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
    - FR-<SUBSYSTEM>-<NAME>-<CAPABILITY>: [Brief summary] [`Feature.execute_task()`] (`INFO`).

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

from collections.abc import Mapping
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

EXECUTE_TASK_FR = "FR-<SUBSYSTEM>-<NAME>-<CAPABILITY>"


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
    # If a file declares N FRs, it exposes only those N public methods.
    # No extraneous public helper methods or compatibility aliases on the class.
    def execute_task(self) -> dict[str, Any]:
        """Execute core functional requirement."""
        self._validate_prerequisites()
        result = self._config.to_dict()
        logger.info(
            "%s: Executed task (batch_size=%d)",
            EXECUTE_TASK_FR,
            self._config.batch_size,
            extra={"fr_id": EXECUTE_TASK_FR, **result},
        )
        return result

    # Helper methods: MUST always be prefixed with a leading underscore `_*`.
    # Deduplication hierarchy:
    # - If duplicated within this domain folder -> move to <domain>/_common.py
    # - If duplicated across different domains -> move to app/services/include/
    def _validate_prerequisites(self) -> None:
        """Private internal helper method validating execution prerequisites."""
        return None


# 5. CLI Class (Optional): Headless CLI formatter for app/cli.py and main demo.
# Replace `Feature` of FeatureCLI with the PascalCase filename.
class FeatureCLI:
    """Headless CLI formatter and table presentation helper."""

    @classmethod
    def format_output(cls, data: Mapping[str, Any]) -> str:
        """Format data into human-readable terminal output."""
        logger.debug("Formatting CLI output (%d keys)", len(data))
        lines = [f"{k}: {v}" for k, v in data.items()]
        return "\n".join(lines)


# 6. Executable Demonstration: Real-usage demonstration using `print()` (not logger).
if __name__ == "__main__":
    service = Feature()
    output = service.execute_task()
    print(FeatureCLI.format_output(output))
```

---

## 2. Formatting, Clean-Room & Linter Rules

- **Clean-Room Brand Prohibition:** Zero references to third-party proprietary
  brands, trademarks, or acronyms (e.g., StrategyQuant, SQX) in comments,
  docstrings, constants, string literals, or identifiers.
- **Line Length:** Strictly $\le 88$ characters per line under `ruff`.
- **Docstrings:** Google-style docstrings with four-space indentation ($\le 100$
  physical lines at top of file).
- **Typing:** Strict Mypy compliance with all public arguments and return types
  explicitly annotated.

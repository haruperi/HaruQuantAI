# ruff: noqa: INP001
"""Dynamic plugin discovery engine, dependency resolver, and lifecycle manager.

Description:
    Implements the core plugin architecture for the HaruQuant host platform.
    Provides a formal extension slot registry, strict Pydantic manifest schema
    validation, recursive 1-level and 2-level filesystem plugin scanning,
    directory containment verification, topological dependency resolution with
    circular reference quarantine, dynamic isolated module loading via
    ``importlib.util.spec_from_file_location``, and thread-safe lazy plugin
    instantiation and lifecycle management.

    Internal workflow:
        1. ``SlotRegistry`` initializes core extension slots (e.g.,
           ``data.provider``, ``workspace.root``, ``workspace.panel``,
           ``broker``, ``engine.evaluator``, ``export.platform``).
        2. ``PluginDiscoveryEngine`` scans configured search directories for
           package manifests (``plugin.json`` / ``manifest.json``) or single-file
           Python AST manifests (``PLUGIN_MANIFEST``), validating containment
           via ``verify_containment`` and schema integrity via ``PluginManifest``.
        3. ``PluginDiscoveryEngine.resolve_dependencies`` validates semantic
           version bounds, checks slot cardinality and required capabilities,
           quarantines circular dependency chains, and computes a deterministic
           topological load order.
        4. ``PluginLifecycleManager`` manages ``RLock``-synchronized lazy
           instantiation (``get_instance``, ``get_instances_for_slot``) and
           explicit lifecycle transitions (``attach_plugin``, ``enable_plugin``,
           ``disable_plugin``, ``reload_plugin``, ``uninstall_plugin``).

    External workflow:
        - Host services query ``get_instance(plugin_id)`` or
          ``get_instances_for_slot(slot_id)`` to obtain active plugin adapters
          without hard-coded imports across plugin boundaries (``SC-02``).
        - FastAPI mounts ``create_discovery_router()`` to expose live plugin
          inventory, diagnostics, slot bindings, and enable/disable/reload
          controls.

Purpose:
    FEAT-HOST-DISCOVERY — Provide an orthogonal, fail-closed plugin discovery,
    validation, dependency resolution, and thread-safe lazy lifecycle engine.

Key Capabilities:
    - FR-HOST-DISC-SLOT-REGISTRY: Register and query typed host extension slots
      with single/multiple cardinality enforcement and required capability checks.
    - FR-HOST-DISC-MANIFEST-SCHEMA: Validate plugin manifests against strict
      Pydantic schema rules (supporting both ``entry_point`` and ``entrypoint``),
      rejecting duplicate JSON keys, non-finite numbers, and oversized files.
    - FR-HOST-DISC-FILESYSTEM-SCANNER: Scan 1-level and 2-level plugin
      directories and single-file AST manifests while isolating malformed or
      duplicate plugins without crashing the host.
    - FR-HOST-DISC-CONTAINMENT-GUARD: Enforce strict path containment within
      authorized plugin search roots, blocking path traversal and symlink escapes.
    - FR-HOST-DISC-DEPENDENCY-RESOLVER: Validate required and optional
      inter-plugin dependencies, check semantic version bounds, quarantine cycles,
      and compute topological load ordering.
    - FR-HOST-DISC-LIFECYCLE-MANAGER: Load plugin entrypoints via isolated
      ``importlib.util.spec_from_file_location`` specs and manage thread-safe
      lazy instantiation, caching, enable/disable cascades, reload, and teardown.
    - FR-HOST-DISC-INSPECTION-API: Expose FastAPI endpoints for listing plugins,
      inspecting diagnostics and slots, and toggling plugin lifecycle states.

Python API Usage:
    from pathlib import Path
    from app.host.discovery import (
        PluginDiscoveryEngine,
        PluginLifecycleManager,
        SlotRegistry,
    )

    slots = SlotRegistry()
    engine = PluginDiscoveryEngine(
        search_dirs=[Path("app/plugins")],
        slot_registry=slots,
    )
    engine.discover()
    engine.resolve_dependencies()

    lifecycle = PluginLifecycleManager(
        discovery_engine=engine,
        data_root=Path("data/plugins"),
    )
    providers = lifecycle.get_instances_for_slot("data.provider")

CLI Usage:
    uv run python -m app.host.discovery --scan-dir app/plugins
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import inspect
import json
import re
import sys
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from fastapi import APIRouter, HTTPException, status
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

__all__ = [
    "PluginDiscoveryEngine",
    "PluginHostContext",
    "PluginLifecycleManager",
    "PluginManifest",
    "SlotDefinition",
    "SlotRegistry",
    "create_discovery_router",
]

logger = get_logger(__name__)

# ============================================================================
# Constants & Validation Patterns
# ============================================================================

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,62}[a-z0-9]$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
ENTRYPOINT_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*:[a-zA-Z_][a-zA-Z0-9_]*$")

MAX_MANIFEST_BYTES = 1_048_576  # 1 MiB ceiling for manifest files


def _parse_semver_tuple(version_str: str) -> tuple[int, int, int]:
    """Extract (major, minor, patch) integers from a validated semver string."""
    match = SEMVER_PATTERN.match(version_str.strip())
    if not match:
        raise ValueError(f"Invalid semantic version string: '{version_str}'")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _strict_json_loads(raw_text: str) -> Any:
    """Parse JSON while rejecting duplicate keys and non-finite constants."""

    def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, val in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key detected: '{key}'")
            result[key] = val
        return result

    def _reject_nonfinite(token: str) -> Any:
        raise ValueError(f"Non-finite JSON constant rejected: '{token}'")

    return json.loads(
        raw_text,
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_nonfinite,
    )


# ============================================================================
# Extension Slot Definitions & Registry (FR-HOST-DISC-SLOT-REGISTRY)
# ============================================================================


class SlotDefinition(BaseModel):
    """Formal contract for a host extension slot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_id: str = Field(
        ...,
        description="Unique dot-separated identifier for the extension slot.",
    )
    description: str = Field(
        ...,
        description="Human-readable explanation of the slot's role.",
    )
    allow_multiple: bool = Field(
        default=True,
        description="Whether multiple active plugins can bind to this slot.",
    )
    required_capabilities: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Capabilities a plugin must declare to bind to this slot.",
    )


class SlotRegistry:
    """Registry of host extension slots available for plugin binding."""

    def __init__(self) -> None:
        """Initialize the slot registry with core HaruQuant extension slots."""
        self._slots: dict[str, SlotDefinition] = {}
        self._register_core_slots()

    def _register_core_slots(self) -> None:
        """Register the built-in HaruQuant host extension slots."""
        core_slots = [
            SlotDefinition(
                slot_id="workspace.root",
                description="Top-level workspace view mounted in the main shell.",
                allow_multiple=True,
                required_capabilities=("ui.workspace",),
            ),
            SlotDefinition(
                slot_id="workspace.panel",
                description="Auxiliary panel or sub-tab within a workspace.",
                allow_multiple=True,
                required_capabilities=(),
            ),
            SlotDefinition(
                slot_id="data.provider",
                description="Historical or live market data source adapter.",
                allow_multiple=True,
                required_capabilities=("data.fetch",),
            ),
            SlotDefinition(
                slot_id="engine.evaluator",
                description="Strategy candidate evaluation or fitness scoring stage.",
                allow_multiple=True,
                required_capabilities=("engine.evaluate",),
            ),
            SlotDefinition(
                slot_id="export.platform",
                description="Target execution platform code generator or exporter.",
                allow_multiple=True,
                required_capabilities=("export.codegen",),
            ),
            SlotDefinition(
                slot_id="export.formatter",
                description="Artifact serializer or report output formatter.",
                allow_multiple=True,
                required_capabilities=(),
            ),
            SlotDefinition(
                slot_id="validation.crosscheck",
                description="Robustness or cross-check validation stage.",
                allow_multiple=True,
                required_capabilities=("validation.run",),
            ),
            SlotDefinition(
                slot_id="diagnostic.probe",
                description="Custom system health or runtime diagnostic probe.",
                allow_multiple=True,
                required_capabilities=(),
            ),
            SlotDefinition(
                slot_id="broker",
                description="Live or demo execution broker gateway adapter.",
                allow_multiple=True,
                required_capabilities=("broker.execute",),
            ),
        ]
        for slot in core_slots:
            self._slots[slot.slot_id] = slot

    def register_slot(self, slot: SlotDefinition) -> None:
        """Register a custom extension slot definition."""
        self._slots[slot.slot_id] = slot
        logger.info(
            "FR-HOST-DISC-SLOT-REGISTRY: Registered extension slot '%s' "
            "(allow_multiple=%s).",
            slot.slot_id,
            slot.allow_multiple,
            extra={"fr_id": "FR-HOST-DISC-SLOT-REGISTRY"},
        )

    def get_slot(self, slot_id: str) -> SlotDefinition | None:
        """Look up a registered slot definition by ID."""
        slot = self._slots.get(slot_id)
        logger.debug(
            "FR-HOST-DISC-SLOT-REGISTRY: Looked up slot '%s' (found=%s).",
            slot_id,
            slot is not None,
            extra={"fr_id": "FR-HOST-DISC-SLOT-REGISTRY"},
        )
        return slot

    def list_slots(self) -> list[SlotDefinition]:
        """Return all registered slot definitions sorted by ID."""
        slots = [self._slots[k] for k in sorted(self._slots.keys())]
        logger.debug(
            "FR-HOST-DISC-SLOT-REGISTRY: Listed %d registered slots.",
            len(slots),
            extra={"fr_id": "FR-HOST-DISC-SLOT-REGISTRY"},
        )
        return slots


# ============================================================================
# Plugin Manifest & Lifecycle Models (FR-HOST-DISC-MANIFEST-SCHEMA)
# ============================================================================


class PluginState(StrEnum):
    """Lifecycle states for a discovered plugin."""

    DISCOVERED = "DISCOVERED"
    VALIDATED = "VALIDATED"
    ATTACHED = "ATTACHED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    QUARANTINED = "QUARANTINED"
    FAILED = "FAILED"
    UNINSTALLED = "UNINSTALLED"


class PluginDependency(BaseModel):
    """Dependency specification declared by a plugin manifest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plugin_id: str = Field(
        ...,
        description="Target plugin ID required or optionally consumed.",
    )
    min_version: str | None = Field(
        default=None,
        description="Minimum inclusive semantic version required.",
    )
    max_version: str | None = Field(
        default=None,
        description="Maximum inclusive semantic version allowed.",
    )
    optional: bool = Field(
        default=False,
        description="If True, missing dependency does not block attachment.",
    )

    @field_validator("plugin_id")
    @classmethod
    def _validate_plugin_id(cls, value: str) -> str:
        if not PLUGIN_ID_PATTERN.match(value):
            raise ValueError(
                f"Invalid dependency plugin_id '{value}'. Must match "
                f"{PLUGIN_ID_PATTERN.pattern}"
            )
        return value

    @field_validator("min_version", "max_version")
    @classmethod
    def _validate_version(cls, value: str | None) -> str | None:
        if value is not None and not SEMVER_PATTERN.match(value):
            raise ValueError(
                f"Invalid semantic version '{value}'. Expected MAJOR.MINOR.PATCH."
            )
        return value


class PluginManifest(BaseModel):
    """Validated metadata manifest describing a HaruQuant plugin."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
    )

    id: str = Field(
        ...,
        description="Globally unique plugin identifier (lowercase kebab/dot/snake).",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Human-readable display name of the plugin.",
    )
    version: str = Field(
        ...,
        description="Semantic version string (MAJOR.MINOR.PATCH).",
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Summary of the plugin's functionality.",
    )
    author: str = Field(
        default="HaruQuant",
        max_length=200,
        description="Plugin author or maintainer identifier.",
    )
    slot: str = Field(
        ...,
        min_length=1,
        description="Target host extension slot ID (e.g., 'data.provider').",
    )
    entry_point: str = Field(
        ...,
        validation_alias=AliasChoices("entry_point", "entrypoint"),
        serialization_alias="entry_point",
        description="Module and callable/class in '<module>:<target>' format.",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="Capabilities provided or required by this plugin.",
    )
    dependencies: list[PluginDependency] = Field(
        default_factory=list,
        description="Declared inter-plugin dependencies.",
    )
    settings_schema: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON-Schema-compatible dictionary for plugin settings.",
    )
    ui_bundle: str | None = Field(
        default=None,
        description="Optional relative path to a frontend UI bundle file.",
    )
    enabled_by_default: bool = Field(
        default=True,
        description="Whether the plugin should be enabled automatically on boot.",
    )

    @property
    def entrypoint(self) -> str:
        """Backward-compatible alias returning ``entry_point``."""
        return self.entry_point

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        if not PLUGIN_ID_PATTERN.match(value):
            logger.error(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Rejected invalid plugin id '%s'.",
                value,
                extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
            )
            raise ValueError(
                f"Invalid plugin id '{value}'. Must be 3-64 chars of lowercase "
                "alphanumerics, dots, hyphens, or underscores."
            )
        return value

    @field_validator("version")
    @classmethod
    def _validate_semver(cls, value: str) -> str:
        if not SEMVER_PATTERN.match(value):
            logger.error(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Rejected invalid version '%s'.",
                value,
                extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
            )
            raise ValueError(
                f"Invalid version '{value}'. Must follow semantic versioning "
                "(e.g., '1.0.0')."
            )
        return value

    @field_validator("entry_point")
    @classmethod
    def _validate_entry_point(cls, value: str) -> str:
        if not ENTRYPOINT_PATTERN.match(value):
            logger.error(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Rejected invalid entry_point '%s'.",
                value,
                extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
            )
            raise ValueError(
                f"Invalid entry_point '{value}'. Expected '<module>:<callable>'."
            )
        return value

    @field_validator("ui_bundle")
    @classmethod
    def _validate_ui_bundle(cls, value: str | None) -> str | None:
        if value is not None:
            cleaned = value.strip()
            if (
                not cleaned
                or cleaned.startswith(("/", "\\"))
                or ".." in Path(cleaned).parts
            ):
                logger.error(
                    "FR-HOST-DISC-MANIFEST-SCHEMA: Rejected unsafe ui_bundle '%s'.",
                    value,
                    extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
                )
                raise ValueError(
                    f"Unsafe ui_bundle path '{value}'. Must be a relative path "
                    "within the plugin directory."
                )
        return value


class DiscoveryDiagnostic(BaseModel):
    """Structured diagnostic event generated during plugin discovery or loading."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plugin_id: str | None = Field(
        default=None,
        description="Plugin ID if identifiable, or None for unparseable packages.",
    )
    source_path: str = Field(
        ...,
        description="Filesystem path where the diagnostic originated.",
    )
    severity: str = Field(
        default="ERROR",
        description="Diagnostic severity ('INFO', 'WARNING', 'ERROR').",
    )
    code: str = Field(
        ...,
        description="Machine-readable diagnostic category code.",
    )
    message: str = Field(
        ...,
        description="Detailed human-readable explanation of the issue.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 UTC timestamp when the diagnostic was recorded.",
    )


class PluginRecord(BaseModel):
    """Runtime registry record tracking a discovered plugin's state and metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    manifest: PluginManifest
    package_dir: Path
    manifest_path: Path
    is_single_file: bool = False
    state: PluginState = PluginState.DISCOVERED
    enabled: bool = True
    load_order: int | None = None
    diagnostics: list[DiscoveryDiagnostic] = Field(default_factory=list)
    attached_at: str | None = None
    instance: Any = Field(default=None, exclude=True)

    def to_summary_dict(self) -> dict[str, Any]:
        """Serialize the plugin record into a JSON-safe summary dictionary."""
        return {
            "id": self.manifest.id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "slot": self.manifest.slot,
            "entry_point": self.manifest.entry_point,
            "entrypoint": self.manifest.entrypoint,
            "capabilities": list(self.manifest.capabilities),
            "dependencies": [dep.model_dump() for dep in self.manifest.dependencies],
            "state": self.state.value,
            "enabled": self.enabled,
            "load_order": self.load_order,
            "package_dir": str(self.package_dir),
            "is_single_file": self.is_single_file,
            "attached_at": self.attached_at,
            "diagnostics": [diag.model_dump() for diag in self.diagnostics],
        }


class DiscoveryReport(BaseModel):
    """Consolidated report emitted after scanning and resolving plugins."""

    model_config = ConfigDict(extra="forbid")

    scanned_dirs: list[str]
    total_discovered: int
    validated_count: int
    attached_count: int
    enabled_count: int
    quarantined_count: int
    failed_count: int
    load_order: list[str]
    diagnostics: list[DiscoveryDiagnostic]


# ============================================================================
# Security & Containment Verification (FR-HOST-DISC-CONTAINMENT-GUARD)
# ============================================================================


def verify_containment(target_path: Path, allowed_root: Path) -> Path:
    """Verify that ``target_path`` resolves strictly inside ``allowed_root``.

    Rejects path traversal sequences (``..``) and symlinks pointing outside the
    authorized root directory.

    Args:
        target_path: Candidate file or directory path to verify.
        allowed_root: Authorized root directory boundary.

    Returns:
        The canonical resolved ``Path`` if containment is satisfied.

    Raises:
        ValueError: If ``target_path`` escapes ``allowed_root`` or does not exist.
    """
    resolved_root = allowed_root.resolve()
    try:
        resolved_target = target_path.resolve(strict=True)
    except FileNotFoundError as exc:
        logger.exception(
            "FR-HOST-DISC-CONTAINMENT-GUARD: Target path does not exist: %s",
            target_path,
            extra={"fr_id": "FR-HOST-DISC-CONTAINMENT-GUARD"},
        )
        raise ValueError(f"Target path does not exist: {target_path}") from exc
    except OSError as exc:
        logger.exception(
            "FR-HOST-DISC-CONTAINMENT-GUARD: Failed to resolve path %s",
            target_path,
            extra={"fr_id": "FR-HOST-DISC-CONTAINMENT-GUARD"},
        )
        raise ValueError(f"OS error resolving path '{target_path}': {exc}") from exc

    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        logger.exception(
            "FR-HOST-DISC-CONTAINMENT-GUARD: Path traversal or symlink escape "
            "blocked: '%s' resolves to '%s', outside root '%s'.",
            target_path,
            resolved_target,
            resolved_root,
            extra={"fr_id": "FR-HOST-DISC-CONTAINMENT-GUARD"},
        )
        raise ValueError(
            f"Containment violation: '{target_path}' resolves to "
            f"'{resolved_target}', which is outside allowed root "
            f"'{resolved_root}'."
        ) from exc

    logger.debug(
        "FR-HOST-DISC-CONTAINMENT-GUARD: Verified containment of '%s' within '%s'.",
        resolved_target,
        resolved_root,
        extra={"fr_id": "FR-HOST-DISC-CONTAINMENT-GUARD"},
    )
    return resolved_target


# ============================================================================
# Plugin Host Context (Typed Sandboxed Facade)
# ============================================================================


class PluginHostContext:
    """Sandboxed host interface provided to plugins during initialization.

    Exposes only bounded, typed host capabilities to the plugin (isolated data
    directory, scoped logger, configuration settings, and registration hooks for
    routes, jobs, events, and teardown callbacks).
    """

    def __init__(
        self,
        plugin_id: str,
        manifest: PluginManifest,
        package_dir: Path,
        data_dir: Path,
        settings: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the plugin host context."""
        self.plugin_id = plugin_id
        self.manifest = manifest
        self.package_dir = package_dir
        self.data_dir = data_dir
        self.settings: dict[str, Any] = dict(settings or {})
        self.logger = get_logger(f"app.plugins.{plugin_id}")

        self._routers: list[APIRouter] = []
        self._teardown_callbacks: list[Callable[[], None]] = []
        self._event_handlers: dict[str, list[Callable[..., Any]]] = {}
        self._job_handlers: dict[str, Callable[..., Any]] = {}

    def ensure_data_dir(self) -> Path:
        """Create and return the plugin's isolated persistent data directory."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir

    def register_router(self, router: APIRouter) -> None:
        """Register a FastAPI ``APIRouter`` owned by this plugin."""
        self._routers.append(router)

    def register_teardown(self, callback: Callable[[], None]) -> None:
        """Register a cleanup callback invoked when the plugin is disabled."""
        self._teardown_callbacks.append(callback)

    def subscribe_event(self, event_topic: str, handler: Callable[..., Any]) -> None:
        """Subscribe a handler callable to a named host event topic."""
        self._event_handlers.setdefault(event_topic, []).append(handler)

    def register_job_handler(self, job_type: str, handler: Callable[..., Any]) -> None:
        """Register a background job handler callable for a specific job type."""
        self._job_handlers[job_type] = handler

    @property
    def routers(self) -> list[APIRouter]:
        """Return registered FastAPI routers for this plugin."""
        return list(self._routers)

    @property
    def teardown_callbacks(self) -> list[Callable[[], None]]:
        """Return registered teardown callbacks for this plugin."""
        return list(self._teardown_callbacks)

    @property
    def event_handlers(self) -> dict[str, list[Callable[..., Any]]]:
        """Return a shallow copy of subscribed event handlers."""
        return {k: list(v) for k, v in self._event_handlers.items()}

    @property
    def job_handlers(self) -> dict[str, Callable[..., Any]]:
        """Return a copy of registered job handlers."""
        return dict(self._job_handlers)


# ============================================================================
# Discovery Engine & Dependency Resolver
# ============================================================================


class PluginDiscoveryEngine:
    """Scans plugin directories, validates manifests, and resolves dependencies."""

    def __init__(
        self,
        search_dirs: list[Path],
        slot_registry: SlotRegistry | None = None,
    ) -> None:
        """Initialize the discovery engine with search directories and slots."""
        self.search_dirs = [Path(d) for d in search_dirs]
        self.slot_registry = slot_registry or SlotRegistry()
        self._records: dict[str, PluginRecord] = {}
        self._diagnostics: list[DiscoveryDiagnostic] = []
        self._load_order: list[str] = []
        self._default_lifecycle: PluginLifecycleManager | None = None

    @property
    def registry(self) -> dict[str, PluginRecord]:
        """Return the mapping of discovered plugin IDs to ``PluginRecord`` items."""
        return self._records

    @property
    def diagnostics(self) -> list[DiscoveryDiagnostic]:
        """Return all global and plugin-level discovery diagnostics."""
        return list(self._diagnostics)

    @property
    def load_order(self) -> list[str]:
        """Return the resolved topological plugin load order."""
        return list(self._load_order)

    def bind_lifecycle(self, lifecycle: PluginLifecycleManager) -> None:
        """Bind a ``PluginLifecycleManager`` to handle lazy instance queries."""
        self._default_lifecycle = lifecycle

    def remove_from_load_order(self, plugin_id: str) -> None:
        """Remove ``plugin_id`` from the active topological load order."""
        if plugin_id in self._load_order:
            self._load_order.remove(plugin_id)

    def record_diagnostic(
        self,
        *,
        plugin_id: str | None,
        source_path: Path | str,
        severity: str,
        code: str,
        message: str,
    ) -> DiscoveryDiagnostic:
        """Create and store a structured discovery diagnostic."""
        diag = DiscoveryDiagnostic(
            plugin_id=plugin_id,
            source_path=str(source_path),
            severity=severity,
            code=code,
            message=message,
        )
        self._diagnostics.append(diag)
        if plugin_id and plugin_id in self._records:
            self._records[plugin_id].diagnostics.append(diag)

        log_fn = (
            logger.error
            if severity == "ERROR"
            else logger.warning
            if severity == "WARNING"
            else logger.info
        )
        log_fn(
            "FR-HOST-DISC-FILESYSTEM-SCANNER: [%s] plugin=%s path=%s: %s",
            code,
            plugin_id or "<unknown>",
            source_path,
            message,
            extra={"fr_id": "FR-HOST-DISC-FILESYSTEM-SCANNER"},
        )
        return diag

    def discover(self) -> dict[str, PluginRecord]:
        """Scan configured ``search_dirs`` and populate the plugin registry."""
        self._records.clear()
        self._diagnostics.clear()
        self._load_order.clear()

        logger.info(
            "FR-HOST-DISC-FILESYSTEM-SCANNER: Starting plugin discovery across "
            "%d search directories.",
            len(self.search_dirs),
            extra={"fr_id": "FR-HOST-DISC-FILESYSTEM-SCANNER"},
        )

        for search_dir in self.search_dirs:
            self._scan_search_root(search_dir)

        logger.info(
            "FR-HOST-DISC-FILESYSTEM-SCANNER: Discovery scan complete. "
            "Found %d candidate plugins (%d diagnostics).",
            len(self._records),
            len(self._diagnostics),
            extra={"fr_id": "FR-HOST-DISC-FILESYSTEM-SCANNER"},
        )
        return self._records

    def _scan_search_root(self, search_dir: Path) -> None:
        """Scan a single configured plugin search root directory."""
        if not search_dir.exists():
            logger.info(
                "FR-HOST-DISC-FILESYSTEM-SCANNER: Skipping non-existent "
                "plugin search directory: %s",
                search_dir,
                extra={"fr_id": "FR-HOST-DISC-FILESYSTEM-SCANNER"},
            )
            return

        if not search_dir.is_dir():
            self.record_diagnostic(
                plugin_id=None,
                source_path=search_dir,
                severity="WARNING",
                code="SEARCH_PATH_NOT_DIR",
                message=(f"Configured search path '{search_dir}' is not a directory."),
            )
            return

        root_resolved = search_dir.resolve()
        for item in sorted(root_resolved.iterdir()):
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            self._inspect_root_entry(item, root_resolved)

    def _inspect_root_entry(self, item: Path, root_resolved: Path) -> None:
        """Inspect a top-level item inside a plugin search root."""
        try:
            verify_containment(item, root_resolved)
        except ValueError as exc:
            self.record_diagnostic(
                plugin_id=None,
                source_path=item,
                severity="ERROR",
                code="CONTAINMENT_VIOLATION",
                message=str(exc),
            )
            return

        if item.is_dir():
            manifest_path = self._find_manifest_in_dir(item)
            if manifest_path is not None:
                self._discover_package_plugin(item, manifest_path, root_resolved)
            else:
                self._scan_slot_family_dir(item, root_resolved)
        elif item.is_file() and item.suffix == ".py" and item.name != "__init__.py":
            self._discover_single_file_plugin(item, root_resolved)

    def _scan_slot_family_dir(self, family_dir: Path, root_resolved: Path) -> None:
        """Scan 2-level slot-family directory ``<root>/<slot_family>/<plugin>``."""
        sub_dirs = [
            sub
            for sub in sorted(family_dir.iterdir())
            if (sub.is_dir() or sub.is_symlink())
            and not sub.name.startswith(".")
            and sub.name != "__pycache__"
        ]
        if not sub_dirs:
            self.record_diagnostic(
                plugin_id=None,
                source_path=family_dir,
                severity="ERROR",
                code="MISSING_MANIFEST",
                message="Directory plugin missing plugin.json or manifest.json.",
            )
            return

        for sub_item in sub_dirs:
            try:
                verify_containment(sub_item, root_resolved)
            except ValueError as exc:
                self.record_diagnostic(
                    plugin_id=None,
                    source_path=sub_item,
                    severity="ERROR",
                    code="CONTAINMENT_VIOLATION",
                    message=str(exc),
                )
                continue

            if sub_item.is_dir():
                sub_manifest = self._find_manifest_in_dir(sub_item)
                if sub_manifest is not None:
                    self._discover_package_plugin(sub_item, sub_manifest, root_resolved)
                else:
                    self.record_diagnostic(
                        plugin_id=None,
                        source_path=sub_item,
                        severity="ERROR",
                        code="MISSING_MANIFEST",
                        message=(
                            "Directory plugin missing plugin.json or manifest.json."
                        ),
                    )

    @staticmethod
    def _find_manifest_in_dir(package_dir: Path) -> Path | None:
        """Return ``plugin.json`` or ``manifest.json`` inside ``package_dir``."""
        for candidate_name in ("plugin.json", "manifest.json"):
            candidate = package_dir / candidate_name
            if candidate.exists() or candidate.is_symlink():
                return candidate
        return None

    def _discover_package_plugin(
        self,
        package_dir: Path,
        manifest_path: Path,
        root_resolved: Path,
    ) -> None:
        """Inspect a directory-based plugin package and parse its manifest."""
        try:
            resolved_manifest = verify_containment(manifest_path, root_resolved)
            verify_containment(resolved_manifest, package_dir.resolve())
        except ValueError as exc:
            self.record_diagnostic(
                plugin_id=None,
                source_path=manifest_path,
                severity="ERROR",
                code="CONTAINMENT_VIOLATION",
                message=str(exc),
            )
            return

        try:
            stat = resolved_manifest.stat()
            if stat.st_size > MAX_MANIFEST_BYTES:
                self.record_diagnostic(
                    plugin_id=None,
                    source_path=resolved_manifest,
                    severity="ERROR",
                    code="MANIFEST_TOO_LARGE",
                    message=(
                        f"Manifest size ({stat.st_size} bytes) exceeds limit "
                        f"({MAX_MANIFEST_BYTES} bytes)."
                    ),
                )
                return

            raw_text = resolved_manifest.read_text(encoding="utf-8")
            raw_data = _strict_json_loads(raw_text)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            logger.exception(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Malformed JSON manifest at %s",
                resolved_manifest,
                extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
            )
            self.record_diagnostic(
                plugin_id=None,
                source_path=resolved_manifest,
                severity="ERROR",
                code="MALFORMED_MANIFEST_JSON",
                message=f"Failed to parse manifest JSON: {exc}",
            )
            return

        if not isinstance(raw_data, dict):
            logger.error(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Manifest root is not an object at %s.",
                resolved_manifest,
                extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
            )
            self.record_diagnostic(
                plugin_id=None,
                source_path=resolved_manifest,
                severity="ERROR",
                code="INVALID_MANIFEST_ROOT",
                message="Manifest JSON root must be an object.",
            )
            return

        self._register_parsed_manifest(
            raw_data=raw_data,
            package_dir=package_dir.resolve(),
            manifest_path=resolved_manifest,
            is_single_file=False,
            root_resolved=root_resolved,
        )

    def _discover_single_file_plugin(
        self, file_path: Path, root_resolved: Path
    ) -> None:
        """Inspect a single-file Python plugin using AST literal evaluation."""
        try:
            stat = file_path.stat()
            if stat.st_size > MAX_MANIFEST_BYTES:
                self.record_diagnostic(
                    plugin_id=None,
                    source_path=file_path,
                    severity="ERROR",
                    code="PLUGIN_FILE_TOO_LARGE",
                    message=(
                        f"Single-file plugin ({stat.st_size} bytes) exceeds "
                        f"limit ({MAX_MANIFEST_BYTES} bytes)."
                    ),
                )
                return

            source_text = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=str(file_path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            self.record_diagnostic(
                plugin_id=None,
                source_path=file_path,
                severity="ERROR",
                code="AST_PARSE_ERROR",
                message=f"Failed to parse Python file AST: {exc}",
            )
            return

        manifest_dict = self._extract_ast_manifest(tree, file_path)
        if manifest_dict is None:
            return

        self._register_parsed_manifest(
            raw_data=manifest_dict,
            package_dir=file_path.parent.resolve(),
            manifest_path=file_path.resolve(),
            is_single_file=True,
            root_resolved=root_resolved,
        )

    def _extract_ast_manifest(
        self, tree: ast.Module, file_path: Path
    ) -> dict[str, Any] | None:
        """Extract literal ``PLUGIN_MANIFEST`` dict from a parsed AST module."""
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PLUGIN_MANIFEST":
                    try:
                        evaluated = ast.literal_eval(node.value)
                    except (ValueError, SyntaxError) as exc:
                        self.record_diagnostic(
                            plugin_id=None,
                            source_path=file_path,
                            severity="ERROR",
                            code="INVALID_AST_MANIFEST",
                            message=(
                                "PLUGIN_MANIFEST must be a static literal "
                                f"dictionary: {exc}"
                            ),
                        )
                        return None
                    if isinstance(evaluated, dict):
                        return evaluated
        return None

    def _register_parsed_manifest(
        self,
        *,
        raw_data: dict[str, Any],
        package_dir: Path,
        manifest_path: Path,
        is_single_file: bool,
        root_resolved: Path,
    ) -> None:
        """Validate raw manifest dictionary and insert into registry."""
        candidate_id = (
            raw_data.get("id") if isinstance(raw_data.get("id"), str) else None
        )
        logger.debug(
            "FR-HOST-DISC-MANIFEST-SCHEMA: Validating manifest for candidate '%s' "
            "at %s.",
            candidate_id or "<unnamed>",
            manifest_path,
            extra={"fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA"},
        )
        try:
            manifest = PluginManifest.model_validate(raw_data)
        except ValidationError as exc:
            self.record_diagnostic(
                plugin_id=candidate_id,
                source_path=manifest_path,
                severity="ERROR",
                code="MANIFEST_SCHEMA_INVALID",
                message=f"Manifest schema validation failed: {exc}",
            )
            return

        if manifest.id in self._records:
            existing = self._records[manifest.id]
            self.record_diagnostic(
                plugin_id=manifest.id,
                source_path=manifest_path,
                severity="ERROR",
                code="DUPLICATE_PLUGIN_ID",
                message=(
                    f"Duplicate plugin ID '{manifest.id}' at '{manifest_path}' "
                    f"(already registered from '{existing.manifest_path}')."
                ),
            )
            return

        record = PluginRecord(
            manifest=manifest,
            package_dir=package_dir,
            manifest_path=manifest_path,
            is_single_file=is_single_file,
            state=PluginState.DISCOVERED,
            enabled=manifest.enabled_by_default,
        )
        self._records[manifest.id] = record
        self._verify_record_artifacts(record, root_resolved)

    def _verify_record_artifacts(
        self, record: PluginRecord, root_resolved: Path
    ) -> None:
        """Verify entrypoint module file and optional ui_bundle exist inside bounds."""
        manifest = record.manifest
        mod_part, _ = manifest.entry_point.split(":", 1)

        if record.is_single_file:
            expected_stem = record.manifest_path.stem
            if mod_part != expected_stem:
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=manifest.id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="SINGLE_FILE_ENTRYPOINT_MISMATCH",
                    message=(
                        f"Single-file plugin entry_point module '{mod_part}' "
                        f"must match file stem '{expected_stem}'."
                    ),
                )
            return

        if not self._verify_package_entrypoint_file(record, mod_part, root_resolved):
            return

        if manifest.ui_bundle is not None:
            bundle_path = record.package_dir / manifest.ui_bundle
            if not bundle_path.exists() and not bundle_path.is_symlink():
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=manifest.id,
                    source_path=bundle_path,
                    severity="ERROR",
                    code="UI_BUNDLE_MISSING",
                    message=(
                        f"Declared ui_bundle '{manifest.ui_bundle}' does not exist."
                    ),
                )
                return
            try:
                verify_containment(bundle_path, record.package_dir)
            except ValueError as exc:
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=manifest.id,
                    source_path=bundle_path,
                    severity="ERROR",
                    code="UI_BUNDLE_CONTAINMENT_VIOLATION",
                    message=str(exc),
                )

    def _verify_package_entrypoint_file(
        self, record: PluginRecord, mod_part: str, root_resolved: Path
    ) -> bool:
        """Verify that a package plugin's entrypoint file exists within bounds."""
        rel_mod_path = Path(*mod_part.split("."))
        py_file = record.package_dir / f"{rel_mod_path}.py"
        pkg_init = record.package_dir / rel_mod_path / "__init__.py"
        target_mod_file = (
            py_file if (py_file.exists() or py_file.is_symlink()) else pkg_init
        )
        if not target_mod_file.exists() and not target_mod_file.is_symlink():
            record.state = PluginState.QUARANTINED
            self.record_diagnostic(
                plugin_id=record.manifest.id,
                source_path=record.manifest_path,
                severity="ERROR",
                code="ENTRYPOINT_MODULE_MISSING",
                message=(
                    f"Entrypoint module '{mod_part}' not found inside "
                    f"package directory '{record.package_dir}'."
                ),
            )
            return False
        try:
            verify_containment(target_mod_file, root_resolved)
            verify_containment(target_mod_file, record.package_dir)
        except ValueError as exc:
            record.state = PluginState.QUARANTINED
            self.record_diagnostic(
                plugin_id=record.manifest.id,
                source_path=target_mod_file,
                severity="ERROR",
                code="ENTRYPOINT_CONTAINMENT_VIOLATION",
                message=str(exc),
            )
            return False
        return True

    def resolve_dependencies(self) -> list[str]:
        """Validate slots, capabilities, and dependencies; compute topological order."""
        self._load_order.clear()
        self._validate_slots_and_capabilities()
        self._validate_dependency_availability()
        ordered = self._compute_topological_order()

        for idx, pid in enumerate(ordered):
            rec = self._records[pid]
            rec.state = PluginState.VALIDATED
            rec.load_order = idx

        self._load_order = ordered
        logger.info(
            "FR-HOST-DISC-DEPENDENCY-RESOLVER: Dependency resolution complete. "
            "Validated %d plugins in load order: %s",
            len(ordered),
            ordered,
            extra={"fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLVER"},
        )
        return list(self._load_order)

    def _validate_slots_and_capabilities(self) -> None:
        """Quarantine plugins with unknown slots, missing caps, or slot conflicts."""
        slot_bindings: dict[str, str] = {}
        for plugin_id in sorted(self._records.keys()):
            record = self._records[plugin_id]
            if record.state == PluginState.QUARANTINED:
                continue

            slot_def = self.slot_registry.get_slot(record.manifest.slot)
            if slot_def is None:
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="UNKNOWN_EXTENSION_SLOT",
                    message=(
                        f"Plugin targets unregistered extension slot "
                        f"'{record.manifest.slot}'."
                    ),
                )
                continue

            missing_caps = [
                cap
                for cap in slot_def.required_capabilities
                if cap not in record.manifest.capabilities
            ]
            if missing_caps:
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="MISSING_REQUIRED_CAPABILITIES",
                    message=(
                        f"Slot '{slot_def.slot_id}' requires capabilities "
                        f"{missing_caps}, which are not declared by '{plugin_id}'."
                    ),
                )
                continue

            if not slot_def.allow_multiple and record.enabled:
                if slot_def.slot_id in slot_bindings:
                    existing_owner = slot_bindings[slot_def.slot_id]
                    record.state = PluginState.QUARANTINED
                    self.record_diagnostic(
                        plugin_id=plugin_id,
                        source_path=record.manifest_path,
                        severity="ERROR",
                        code="SLOT_CARDINALITY_CONFLICT",
                        message=(
                            f"Single-instance slot '{slot_def.slot_id}' is "
                            f"already bound by '{existing_owner}'."
                        ),
                    )
                    continue
                slot_bindings[slot_def.slot_id] = plugin_id

    def _validate_dependency_availability(self) -> None:
        """Iteratively quarantine plugins whose required dependencies fail."""
        changed = True
        while changed:
            changed = False
            for plugin_id in sorted(self._records.keys()):
                record = self._records[plugin_id]
                if record.state == PluginState.QUARANTINED:
                    continue
                if not self._check_plugin_dependencies(plugin_id, record):
                    changed = True

    def _check_plugin_dependencies(self, plugin_id: str, record: PluginRecord) -> bool:
        """Check all dependencies of ``record``; return False if quarantined."""
        for dep in record.manifest.dependencies:
            if dep.plugin_id == plugin_id:
                record.state = PluginState.QUARANTINED
                self.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="SELF_DEPENDENCY",
                    message=f"Plugin '{plugin_id}' cannot depend on itself.",
                )
                return False

            target = self._records.get(dep.plugin_id)
            if target is None or target.state == PluginState.QUARANTINED:
                if dep.optional:
                    self.record_diagnostic(
                        plugin_id=plugin_id,
                        source_path=record.manifest_path,
                        severity="WARNING",
                        code="OPTIONAL_DEPENDENCY_UNAVAILABLE",
                        message=(
                            f"Optional dependency '{dep.plugin_id}' is not available."
                        ),
                    )
                    continue
                record.state = PluginState.QUARANTINED
                logger.error(
                    "FR-HOST-DISC-DEPENDENCY-RESOLVER: Plugin '%s' "
                    "missing required dependency '%s'.",
                    plugin_id,
                    dep.plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLVER"},
                )
                self.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="MISSING_REQUIRED_DEPENDENCY",
                    message=(
                        f"Required dependency '{dep.plugin_id}' is "
                        "missing or quarantined."
                    ),
                )
                return False

            if not self._version_satisfies(
                target.manifest.version, dep.min_version, dep.max_version
            ):
                if dep.optional:
                    self.record_diagnostic(
                        plugin_id=plugin_id,
                        source_path=record.manifest_path,
                        severity="WARNING",
                        code="OPTIONAL_DEPENDENCY_VERSION_MISMATCH",
                        message=(
                            f"Optional dependency '{dep.plugin_id}' version "
                            f"'{target.manifest.version}' outside "
                            f"[{dep.min_version}, {dep.max_version}]."
                        ),
                    )
                    continue
                record.state = PluginState.QUARANTINED
                logger.error(
                    "FR-HOST-DISC-DEPENDENCY-RESOLVER: Plugin '%s' "
                    "requires '%s' in [%s, %s], found '%s'.",
                    plugin_id,
                    dep.plugin_id,
                    dep.min_version,
                    dep.max_version,
                    target.manifest.version,
                    extra={"fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLVER"},
                )
                self.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="DEPENDENCY_VERSION_INCOMPATIBLE",
                    message=(
                        f"Dependency '{dep.plugin_id}' version "
                        f"'{target.manifest.version}' does not satisfy "
                        f"min={dep.min_version}, max={dep.max_version}."
                    ),
                )
                return False
        return True

    def _compute_topological_order(self) -> list[str]:
        """Run Kahn's algorithm and quarantine any circular dependency chains."""
        active_ids = sorted(
            pid
            for pid, rec in self._records.items()
            if rec.state != PluginState.QUARANTINED
        )
        in_degree: dict[str, int] = dict.fromkeys(active_ids, 0)
        dependents_map: dict[str, list[str]] = {pid: [] for pid in active_ids}

        for pid in active_ids:
            rec = self._records[pid]
            for dep in rec.manifest.dependencies:
                if dep.plugin_id in in_degree:
                    target_rec = self._records[dep.plugin_id]
                    if self._version_satisfies(
                        target_rec.manifest.version,
                        dep.min_version,
                        dep.max_version,
                    ):
                        in_degree[pid] += 1
                        dependents_map[dep.plugin_id].append(pid)

        ready_queue = sorted([pid for pid, deg in in_degree.items() if deg == 0])
        ordered: list[str] = []

        while ready_queue:
            current = ready_queue.pop(0)
            ordered.append(current)
            for dependent_id in sorted(dependents_map[current]):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    ready_queue.append(dependent_id)
                    ready_queue.sort()

        if len(ordered) < len(active_ids):
            cycle_participants = [pid for pid in active_ids if pid not in ordered]
            for pid in cycle_participants:
                rec = self._records[pid]
                rec.state = PluginState.QUARANTINED
                logger.error(
                    "FR-HOST-DISC-DEPENDENCY-RESOLVER: Circular dependency "
                    "detected involving '%s' (participants=%s).",
                    pid,
                    cycle_participants,
                    extra={"fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLVER"},
                )
                self.record_diagnostic(
                    plugin_id=pid,
                    source_path=rec.manifest_path,
                    severity="ERROR",
                    code="CIRCULAR_DEPENDENCY",
                    message=(
                        f"Plugin '{pid}' is part of a circular dependency chain "
                        f"involving: {', '.join(cycle_participants)}."
                    ),
                )
        return ordered

    @staticmethod
    def _version_satisfies(
        actual: str,
        min_version: str | None,
        max_version: str | None,
    ) -> bool:
        """Return True if ``actual`` falls within ``[min_version, max_version]``."""
        actual_tuple = _parse_semver_tuple(actual)
        if min_version is not None and actual_tuple < _parse_semver_tuple(min_version):
            return False
        return not (
            max_version is not None and actual_tuple > _parse_semver_tuple(max_version)
        )

    def _ensure_default_lifecycle(self) -> PluginLifecycleManager:
        """Lazily initialize a default ``PluginLifecycleManager`` for convenience."""
        if self._default_lifecycle is None:
            default_data_root = (
                self.search_dirs[0].parent / "data" / "plugins"
                if self.search_dirs
                else Path("data/plugins")
            )
            self._default_lifecycle = PluginLifecycleManager(
                discovery_engine=self,
                data_root=default_data_root,
            )
        return self._default_lifecycle

    def get_instance(self, plugin_id: str) -> Any | None:
        """Thread-safe lazy instantiation and caching of a validated plugin."""
        return self._ensure_default_lifecycle().get_instance(plugin_id)

    def get_instances_for_slot(self, slot_id: str) -> list[Any]:
        """Return all active plugin instances registered for ``slot_id``."""
        return self._ensure_default_lifecycle().get_instances_for_slot(slot_id)


# ============================================================================
# Plugin Lifecycle Manager (FR-HOST-DISC-LIFECYCLE-MANAGER)
# ============================================================================


class PluginLifecycleManager:
    """Manages thread-safe plugin loading, lazy caching, enable/disable, and reload."""

    def __init__(
        self,
        discovery_engine: PluginDiscoveryEngine,
        data_root: Path,
        plugin_settings: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the lifecycle manager."""
        self.discovery = discovery_engine
        self.data_root = Path(data_root)
        self.plugin_settings: dict[str, dict[str, Any]] = dict(plugin_settings or {})
        self._contexts: dict[str, PluginHostContext] = {}
        self._loaded_modules: dict[str, list[str]] = {}
        self._lock = threading.RLock()
        self.discovery.bind_lifecycle(self)

    @property
    def contexts(self) -> dict[str, PluginHostContext]:
        """Return active ``PluginHostContext`` instances keyed by plugin ID."""
        with self._lock:
            return dict(self._contexts)

    def load_and_attach_all(self) -> DiscoveryReport:
        """Attach and enable all validated plugins in topological load order."""
        with self._lock:
            if not self.discovery.load_order and self.discovery.registry:
                self.discovery.resolve_dependencies()

            for plugin_id in self.discovery.load_order:
                record = self.discovery.registry.get(plugin_id)
                if record is None:
                    continue
                if not record.enabled:
                    record.state = PluginState.DISABLED
                    logger.info(
                        "FR-HOST-DISC-LIFECYCLE-MANAGER: Plugin '%s' is disabled "
                        "by configuration; skipping boot attachment.",
                        plugin_id,
                        extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                    )
                    continue
                self.attach_plugin(plugin_id)

            return self.build_report()

    def attach_plugin(self, plugin_id: str) -> bool:
        """Dynamically import and attach a single validated plugin."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                logger.error(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: Cannot attach unknown "
                    "plugin '%s'.",
                    plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                return False

            if (
                record.state in (PluginState.ENABLED, PluginState.ATTACHED)
                and record.instance is not None
            ):
                return True

            if record.state not in (
                PluginState.VALIDATED,
                PluginState.DISABLED,
                PluginState.DISCOVERED,
            ):
                logger.error(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: Cannot attach plugin '%s' "
                    "in state '%s'.",
                    plugin_id,
                    record.state.value,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                return False

            if not self._ensure_dependencies_attached(plugin_id, record):
                return False

            return self._execute_plugin_attachment(plugin_id, record)

    def _ensure_dependencies_attached(
        self, plugin_id: str, record: PluginRecord
    ) -> bool:
        """Ensure all required dependencies of ``record`` are attached and ENABLED."""
        for dep in record.manifest.dependencies:
            if dep.optional:
                continue
            dep_record = self.discovery.registry.get(dep.plugin_id)
            if dep_record is None:
                record.state = PluginState.FAILED
                self.discovery.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="DEPENDENCY_NOT_ENABLED",
                    message=(
                        f"Cannot attach '{plugin_id}' because required "
                        f"dependency '{dep.plugin_id}' is missing."
                    ),
                )
                return False

            if (
                dep_record.state in (PluginState.DISCOVERED, PluginState.VALIDATED)
                and dep_record.enabled
            ):
                self.attach_plugin(dep.plugin_id)

            if dep_record.state != PluginState.ENABLED:
                record.state = PluginState.FAILED
                self.discovery.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="ERROR",
                    code="DEPENDENCY_NOT_ENABLED",
                    message=(
                        f"Cannot attach '{plugin_id}' because required "
                        f"dependency '{dep.plugin_id}' is not ENABLED "
                        f"(state={dep_record.state.value})."
                    ),
                )
                return False
        return True

    def _execute_plugin_attachment(self, plugin_id: str, record: PluginRecord) -> bool:
        """Load module, invoke entrypoint in fault boundary, and update record."""
        mod_part, attr_name = record.manifest.entry_point.split(":", 1)
        plugin_data_dir = self.data_root / plugin_id
        ctx = PluginHostContext(
            plugin_id=plugin_id,
            manifest=record.manifest,
            package_dir=record.package_dir,
            data_dir=plugin_data_dir,
            settings=self.plugin_settings.get(plugin_id, {}),
        )

        try:
            module = self._load_plugin_module(plugin_id, record, mod_part)
            target_callable = self._resolve_entrypoint_callable(
                module, mod_part, attr_name, record.manifest.entry_point
            )
            instance = self._invoke_entrypoint(target_callable, ctx)
        except Exception as exc:
            record.state = PluginState.FAILED
            record.instance = None
            self._cleanup_plugin_modules(plugin_id)
            logger.exception(
                "FR-HOST-DISC-LIFECYCLE-MANAGER: Failed to attach plugin '%s'",
                plugin_id,
                extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
            )
            self.discovery.record_diagnostic(
                plugin_id=plugin_id,
                source_path=record.manifest_path,
                severity="ERROR",
                code="ATTACHMENT_RUNTIME_FAILURE",
                message=f"Plugin entrypoint raised exception: {exc}",
            )
            return False

        self._contexts[plugin_id] = ctx
        record.instance = instance if instance is not None else ctx
        record.attached_at = datetime.now(UTC).isoformat()
        record.state = PluginState.ENABLED
        record.enabled = True

        logger.info(
            "FR-HOST-DISC-LIFECYCLE-MANAGER: Attached and enabled plugin '%s' "
            "(v%s) on slot '%s'.",
            plugin_id,
            record.manifest.version,
            record.manifest.slot,
            extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
        )
        return True

    @staticmethod
    def _resolve_entrypoint_callable(
        module: Any, mod_part: str, attr_name: str, entry_point: str
    ) -> Callable[..., Any]:
        """Verify and return the callable entrypoint attribute on ``module``."""
        if not hasattr(module, attr_name):
            raise AttributeError(
                f"Module '{mod_part}' has no entrypoint attribute '{attr_name}'."
            )
        target_callable = getattr(module, attr_name)
        if not callable(target_callable):
            raise TypeError(f"Entrypoint '{entry_point}' is not callable.")
        return target_callable  # type: ignore[no-any-return]

    @staticmethod
    def _invoke_entrypoint(
        target_callable: Callable[..., Any],
        ctx: PluginHostContext,
    ) -> Any:
        """Invoke a plugin entrypoint class or factory with or without ``ctx``."""
        try:
            sig = inspect.signature(target_callable)
        except ValueError, TypeError:
            return target_callable(ctx)

        params = list(sig.parameters.values())
        if not params:
            return target_callable()

        first = params[0]
        if first.kind == inspect.Parameter.VAR_POSITIONAL:
            return target_callable(ctx)

        if first.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            annotation_str = str(first.annotation)
            if (
                first.default is inspect.Parameter.empty
                or first.name in {"ctx", "context", "host_context", "host"}
                or "PluginHostContext" in annotation_str
            ):
                return target_callable(ctx)

        return target_callable()

    def _load_plugin_module(
        self,
        plugin_id: str,
        record: PluginRecord,
        mod_part: str,
    ) -> Any:
        """Load the plugin module into an isolated namespace under ``sys.modules``."""
        safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", plugin_id)
        namespace_prefix = f"_haruquant_plugins.{safe_id}"
        loaded_names: list[str] = []

        if record.is_single_file:
            target_file = record.manifest_path
            full_mod_name = f"{namespace_prefix}.{mod_part}"
            spec = importlib.util.spec_from_file_location(full_mod_name, target_file)
        else:
            pkg_init = record.package_dir / "__init__.py"
            if pkg_init.exists():
                pkg_spec = importlib.util.spec_from_file_location(
                    namespace_prefix,
                    pkg_init,
                    submodule_search_locations=[str(record.package_dir)],
                )
                if pkg_spec and pkg_spec.loader:
                    pkg_mod = importlib.util.module_from_spec(pkg_spec)
                    sys.modules[namespace_prefix] = pkg_mod
                    loaded_names.append(namespace_prefix)
                    pkg_spec.loader.exec_module(pkg_mod)

            rel_mod_path = Path(*mod_part.split("."))
            py_file = record.package_dir / f"{rel_mod_path}.py"
            sub_init = record.package_dir / rel_mod_path / "__init__.py"
            target_file = py_file if py_file.exists() else sub_init
            full_mod_name = f"{namespace_prefix}.{mod_part}"
            spec = importlib.util.spec_from_file_location(
                full_mod_name,
                target_file,
                submodule_search_locations=[str(record.package_dir)],
            )

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Could not create module spec for '{mod_part}' at "
                f"'{record.package_dir}'."
            )

        module = importlib.util.module_from_spec(spec)
        sys.modules[full_mod_name] = module
        loaded_names.append(full_mod_name)
        self._loaded_modules[plugin_id] = loaded_names
        spec.loader.exec_module(module)
        return module

    def _cleanup_plugin_modules(self, plugin_id: str) -> None:
        """Remove dynamically loaded modules for ``plugin_id`` from ``sys.modules``."""
        mod_names = self._loaded_modules.pop(plugin_id, [])
        for name in mod_names:
            sys.modules.pop(name, None)

    def get_instance(self, plugin_id: str) -> Any | None:
        """Thread-safe lazy instantiation and caching of a validated plugin."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                logger.debug(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: get_instance('%s') -> None "
                    "(not registered).",
                    plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                return None

            if record.instance is not None and record.state in (
                PluginState.ENABLED,
                PluginState.ATTACHED,
            ):
                logger.debug(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: Returning cached instance "
                    "for plugin '%s'.",
                    plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                return record.instance

            if not record.enabled or record.state in (
                PluginState.DISABLED,
                PluginState.QUARANTINED,
                PluginState.FAILED,
                PluginState.UNINSTALLED,
            ):
                return None

            if record.state == PluginState.DISCOVERED:
                self.discovery.resolve_dependencies()
                record = self.discovery.registry.get(plugin_id)

            if (
                record is not None
                and record.state == PluginState.VALIDATED
                and self.attach_plugin(plugin_id)
            ):
                logger.info(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: Lazily instantiated "
                    "plugin '%s' on demand.",
                    plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                return record.instance

            return None

    def get_instances_for_slot(self, slot_id: str) -> list[Any]:
        """Return all active plugin instances bound to ``slot_id``."""
        with self._lock:
            has_unvalidated = any(
                rec.manifest.slot == slot_id and rec.state == PluginState.DISCOVERED
                for rec in self.discovery.registry.values()
            )
            if has_unvalidated:
                self.discovery.resolve_dependencies()

            ordered_ids = list(self.discovery.load_order)
            for pid in sorted(self.discovery.registry.keys()):
                if pid not in ordered_ids:
                    ordered_ids.append(pid)

            instances: list[Any] = []
            for pid in ordered_ids:
                record = self.discovery.registry.get(pid)
                if record is None or record.manifest.slot != slot_id:
                    continue
                if not record.enabled:
                    continue
                inst = self.get_instance(pid)
                if inst is not None:
                    instances.append(inst)

            logger.debug(
                "FR-HOST-DISC-LIFECYCLE-MANAGER: Resolved %d active plugin "
                "instances for slot '%s'.",
                len(instances),
                slot_id,
                extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
            )
            return instances

    def disable_plugin(self, plugin_id: str, *, cascade: bool = True) -> bool:
        """Disable an active plugin and invoke its teardown callbacks."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                return False

            if record.state == PluginState.DISABLED:
                return True

            if cascade:
                self._cascade_disable_dependents(plugin_id)

            self._run_teardown_callbacks(plugin_id, record)
            self._cleanup_plugin_modules(plugin_id)
            record.instance = None
            record.state = PluginState.DISABLED
            record.enabled = False
            logger.info(
                "FR-HOST-DISC-LIFECYCLE-MANAGER: Disabled plugin '%s'.",
                plugin_id,
                extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
            )
            return True

    def _cascade_disable_dependents(self, plugin_id: str) -> None:
        """Disable any active plugin that has a required dependency on ``plugin_id``."""
        for other_id, other_rec in self.discovery.registry.items():
            if other_id == plugin_id or other_rec.state != PluginState.ENABLED:
                continue
            for dep in other_rec.manifest.dependencies:
                if dep.plugin_id == plugin_id and not dep.optional:
                    self.disable_plugin(other_id, cascade=True)

    def _run_teardown_callbacks(self, plugin_id: str, record: PluginRecord) -> None:
        """Invoke registered teardown callbacks for ``plugin_id`` in reverse order."""
        ctx = self._contexts.pop(plugin_id, None)
        if ctx is None:
            return
        for callback in reversed(ctx.teardown_callbacks):
            try:
                callback()
            except Exception as exc:
                logger.exception(
                    "FR-HOST-DISC-LIFECYCLE-MANAGER: Teardown callback error for '%s'",
                    plugin_id,
                    extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
                )
                self.discovery.record_diagnostic(
                    plugin_id=plugin_id,
                    source_path=record.manifest_path,
                    severity="WARNING",
                    code="TEARDOWN_CALLBACK_ERROR",
                    message=f"Teardown callback raised exception: {exc}",
                )

    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a previously disabled or validated plugin."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                return False
            if record.state == PluginState.ENABLED:
                return True
            if record.state in (
                PluginState.QUARANTINED,
                PluginState.UNINSTALLED,
            ):
                return False

            slot_def = self.discovery.slot_registry.get_slot(record.manifest.slot)
            if slot_def and not slot_def.allow_multiple:
                for other_id, other_rec in self.discovery.registry.items():
                    if (
                        other_id != plugin_id
                        and other_rec.manifest.slot == slot_def.slot_id
                        and other_rec.state == PluginState.ENABLED
                    ):
                        self.discovery.record_diagnostic(
                            plugin_id=plugin_id,
                            source_path=record.manifest_path,
                            severity="ERROR",
                            code="SLOT_CARDINALITY_CONFLICT",
                            message=(
                                f"Cannot enable '{plugin_id}': single-instance "
                                f"slot '{slot_def.slot_id}' is occupied by "
                                f"'{other_id}'."
                            ),
                        )
                        return False

            record.enabled = True
            return self.attach_plugin(plugin_id)

    def reload_plugin(self, plugin_id: str) -> bool:
        """Disable and re-attach a plugin to pick up code changes."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                return False
            if record.state == PluginState.ENABLED:
                self.disable_plugin(plugin_id, cascade=False)
            record.state = PluginState.VALIDATED
            record.enabled = True
            return self.attach_plugin(plugin_id)

    def uninstall_plugin(self, plugin_id: str) -> bool:
        """Disable and remove a plugin from the runtime registry."""
        with self._lock:
            record = self.discovery.registry.get(plugin_id)
            if record is None:
                return False
            if record.state == PluginState.ENABLED:
                self.disable_plugin(plugin_id, cascade=True)
            record.state = PluginState.UNINSTALLED
            self.discovery.registry.pop(plugin_id, None)
            self.discovery.remove_from_load_order(plugin_id)
            logger.info(
                "FR-HOST-DISC-LIFECYCLE-MANAGER: Unregistered plugin '%s' from "
                "host registry.",
                plugin_id,
                extra={"fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGER"},
            )
            return True

    def build_report(self) -> DiscoveryReport:
        """Build a consolidated ``DiscoveryReport`` of current plugin states."""
        with self._lock:
            records = list(self.discovery.registry.values())
            return DiscoveryReport(
                scanned_dirs=[str(d) for d in self.discovery.search_dirs],
                total_discovered=len(records),
                validated_count=sum(
                    1
                    for r in records
                    if r.state in (PluginState.VALIDATED, PluginState.ENABLED)
                ),
                attached_count=sum(
                    1
                    for r in records
                    if r.state in (PluginState.ATTACHED, PluginState.ENABLED)
                ),
                enabled_count=sum(1 for r in records if r.state == PluginState.ENABLED),
                quarantined_count=sum(
                    1 for r in records if r.state == PluginState.QUARANTINED
                ),
                failed_count=sum(1 for r in records if r.state == PluginState.FAILED),
                load_order=list(self.discovery.load_order),
                diagnostics=self.discovery.diagnostics,
            )


# ============================================================================
# FastAPI Inspection & Control Router (FR-HOST-DISC-INSPECTION-API)
# ============================================================================


def _require_plugin_record(
    lifecycle: PluginLifecycleManager, plugin_id: str
) -> PluginRecord:
    """Look up ``plugin_id`` or raise a 404 ``HTTPException``."""
    record = lifecycle.discovery.registry.get(plugin_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{plugin_id}' not found.",
        )
    return record


def _build_slot_summaries(
    lifecycle: PluginLifecycleManager,
) -> list[dict[str, Any]]:
    """Build JSON-serializable summaries of all slots and their bound plugins."""
    slot_summaries: list[dict[str, Any]] = []
    for s in lifecycle.discovery.slot_registry.list_slots():
        bound = [
            r.manifest.id
            for r in lifecycle.discovery.registry.values()
            if r.manifest.slot == s.slot_id and r.state == PluginState.ENABLED
        ]
        slot_summaries.append(
            {
                "slot_id": s.slot_id,
                "description": s.description,
                "allow_multiple": s.allow_multiple,
                "required_capabilities": list(s.required_capabilities),
                "bound_plugins": sorted(bound),
            }
        )
    return slot_summaries


def create_discovery_router(lifecycle: PluginLifecycleManager) -> APIRouter:
    """Create a FastAPI router exposing plugin discovery and lifecycle controls."""
    router = APIRouter(prefix="/discovery", tags=["plugin-discovery"])
    logger.info(
        "FR-HOST-DISC-INSPECTION-API: Created FastAPI plugin discovery router.",
        extra={"fr_id": "FR-HOST-DISC-INSPECTION-API"},
    )

    @router.get("/plugins")
    def list_plugins() -> dict[str, Any]:
        """List all discovered plugins, their states, and discovery report."""
        report = lifecycle.build_report()
        plugins = [
            rec.to_summary_dict()
            for rec in sorted(
                lifecycle.discovery.registry.values(),
                key=lambda r: (
                    r.load_order if r.load_order is not None else 9999,
                    r.manifest.id,
                ),
            )
        ]
        return {"report": report.model_dump(), "plugins": plugins}

    @router.get("/plugins/{plugin_id}")
    def get_plugin_detail(plugin_id: str) -> dict[str, Any]:
        """Retrieve detailed status and diagnostics for a specific plugin."""
        return _require_plugin_record(lifecycle, plugin_id).to_summary_dict()

    @router.post("/plugins/{plugin_id}/enable")
    def enable_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        """Enable a discovered plugin by ID."""
        record = _require_plugin_record(lifecycle, plugin_id)
        success = lifecycle.enable_plugin(plugin_id)
        logger.info(
            "FR-HOST-DISC-INSPECTION-API: API enable requested for '%s' (success=%s).",
            plugin_id,
            success,
            extra={"fr_id": "FR-HOST-DISC-INSPECTION-API"},
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": f"Failed to enable plugin '{plugin_id}'.",
                    "state": record.state.value,
                    "diagnostics": [d.model_dump() for d in record.diagnostics],
                },
            )
        return record.to_summary_dict()

    @router.post("/plugins/{plugin_id}/disable")
    def disable_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        """Disable an active plugin by ID."""
        record = _require_plugin_record(lifecycle, plugin_id)
        lifecycle.disable_plugin(plugin_id)
        logger.info(
            "FR-HOST-DISC-INSPECTION-API: API disable completed for '%s'.",
            plugin_id,
            extra={"fr_id": "FR-HOST-DISC-INSPECTION-API"},
        )
        return record.to_summary_dict()

    @router.post("/plugins/{plugin_id}/reload")
    def reload_plugin_endpoint(plugin_id: str) -> dict[str, Any]:
        """Reload an existing plugin by ID."""
        record = _require_plugin_record(lifecycle, plugin_id)
        success = lifecycle.reload_plugin(plugin_id)
        logger.info(
            "FR-HOST-DISC-INSPECTION-API: API reload requested for '%s' (success=%s).",
            plugin_id,
            success,
            extra={"fr_id": "FR-HOST-DISC-INSPECTION-API"},
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Failed to reload plugin '{plugin_id}'.",
            )
        return record.to_summary_dict()

    @router.get("/slots")
    def list_slots_endpoint() -> dict[str, Any]:
        """List all registered host extension slots and their bound plugins."""
        return {"slots": _build_slot_summaries(lifecycle)}

    return router


# ============================================================================
# Standalone CLI Entrypoint
# ============================================================================


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint to scan plugin directories and print a discovery report."""
    parser = argparse.ArgumentParser(
        prog="app.host.discovery",
        description="HaruQuant Host Plugin Discovery & Verification CLI",
    )
    parser.add_argument(
        "--scan-dir",
        action="append",
        default=[],
        help="Directory path to scan for plugins (can be specified multiple times).",
    )
    args = parser.parse_args(argv)

    scan_paths = (
        [Path(p) for p in args.scan_dir] if args.scan_dir else [Path("app/plugins")]
    )
    engine = PluginDiscoveryEngine(search_dirs=scan_paths)
    engine.discover()
    engine.resolve_dependencies()

    lifecycle = PluginLifecycleManager(
        discovery_engine=engine,
        data_root=Path("data/plugins"),
    )
    report = lifecycle.build_report()
    print(json.dumps(report.model_dump(), indent=2))
    return 0 if report.quarantined_count == 0 and report.failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

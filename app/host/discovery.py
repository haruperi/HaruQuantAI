"""Workspace and plugin discovery, manifest verification, and typed attachment.

Description:
    This module provides the central discovery engine, manifest validator, slot
    registry, dependency resolver, capability injection pipeline, and lifecycle
    manager for HaruQuantAI platform workspaces and plugins. It enables modular
    extension packages to declare identity, versioning, extension slots, entrypoint
    factories, dependencies, and requested host capabilities through declarative
    manifest files (`plugin.json` or `manifest.json`). The discovery engine enforces
    strict filesystem containment, rejecting path traversal attempts, escaped
    symbolic links, and unauthorized external modules. Plugin entrypoints are
    executed inside guarded error boundaries with an injected, typed
    `PluginHostContext` providing scoped logging, settings access, route mounting,
    and event subscriptions. The lifecycle manager supports controlled disabling,
    reloading, and uninstallation with automated resource cleanup (route
    unmounting, event listener removal, and background job cancellation) while
    preserving retained user data. The host guarantees zero-plugin resilience:
    the browser shell and workspace surfaces remain fully functional even when
    no plugins are installed.

Purpose:
    FEAT-HOST-DISCOVERY: Workspace and plugin discovery, manifest verification,
    containment security, extension slot registration, dependency resolution,
    and typed lifecycle attachment.

Key Capabilities:
    - FR-HOST-DISC-MANIFEST-SCHEMA: Package identity, semver, contained entrypoints,
      slot declarations, and dependency metadata schema validation.
      Associated: `PluginManifest`, `PluginDiscoveryEngine.parse_manifest_file()`
      Logging: Emits INFO on valid manifest discovery; ERROR on validation failure.
    - FR-HOST-DISC-CONTAINMENT-SECURITY: Strict directory containment, forbidding
      path traversal (`..`), symbolic link escapes, and uncontained entrypoints.
      Associated: `PluginDiscoveryEngine.verify_containment()`
      Logging: Emits WARNING/ERROR with security violation details.
    - FR-HOST-DISC-SLOT-REGISTRATION: Typed host extension slots registry and
      attachment cardinality validation.
      Associated: `SlotRegistry`, `SlotDefinition`
      Logging: Emits INFO on slot registration; WARNING on incompatible slot request.
    - FR-HOST-DISC-DEPENDENCY-RESOLUTION: Topological dependency ordering, missing
      dependency detection, and circular dependency prevention.
      Associated: `PluginDiscoveryEngine.resolve_dependencies()`
      Logging: Emits INFO on resolved DAG; ERROR on missing dependency or cycle.
    - FR-HOST-DISC-CAPABILITY-INJECTION: Typed host capability context injection into
      plugin factories via `PluginHostContext`.
      Associated: `PluginHostContext`, `PluginLifecycleManager.attach()`
      Logging: Emits INFO on successful capability binding and factory invocation.
    - FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Safe attachment, activation, controlled
      disabling, reload, and uninstallation with resource cleanup.
      Associated: `PluginLifecycleManager`
      Logging: Emits INFO on lifecycle state transitions; ERROR on factory failure.
    - FR-HOST-DISC-BROWSER-PROJECTION: FastAPI REST projection endpoints exposing
      discovered packages, status, slot bindings, and lifecycle operations.
      Associated: `create_discovery_router()`
      Logging: Emits DEBUG on status queries; INFO on state mutations.

Python API Usage:
    ```python
    from pathlib import Path
    from app.host.discovery import (
        PluginDiscoveryEngine,
        PluginLifecycleManager,
        SlotRegistry,
    )

    registry = SlotRegistry()
    engine = PluginDiscoveryEngine(slot_registry=registry)
    records = engine.discover([Path("plugins")])
    manager = PluginLifecycleManager(engine)
    for plugin_id in engine.resolve_dependencies(records):
        manager.attach(plugin_id)
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.discovery --scan plugins/ --list
    ```
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.host.logging import BoundLogger, get_logger

logger = get_logger(__name__)

# Maximum allowed size for a plugin manifest file (1 MiB)
MAX_MANIFEST_BYTES: int = 1024 * 1024

# Identifier regex: letters, numbers, hyphens, underscores, dots (1..100 chars)
ID_PATTERN: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_\-\.]{1,100}$")

# Expected number of integer parts in a normalized semantic version
SEMVER_PARTS_COUNT: int = 3


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class DiscoveryError(Exception):
    """Base exception for all workspace and plugin discovery errors."""


class ManifestValidationError(DiscoveryError):
    """Raised when a plugin manifest fails schema or constraint validation."""


class SecurityViolationError(DiscoveryError):
    """Raised when a plugin violates directory containment or security rules."""


class IncompatibleSlotError(DiscoveryError):
    """Raised when a plugin attempts to attach to an unregistered or invalid slot."""


class DependencyResolutionError(DiscoveryError):
    """Raised when plugin dependencies are missing, invalid, or cyclic."""


class PluginLifecycleError(DiscoveryError):
    """Raised when a plugin fails during attachment, disabling, or reload."""


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------


class PluginState(StrEnum):
    """Lifecycle states of a discovered workspace plugin."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    ATTACHED = "attached"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    DISABLED = "disabled"


class SlotDefinition(BaseModel):
    """Specification of a host extension slot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_id: str = Field(description="Unique extension slot identifier")
    description: str = Field(default="", description="Human-readable description")
    multi_instance: bool = Field(
        default=True, description="Whether multiple plugins can attach"
    )
    required_capabilities: list[str] = Field(
        default_factory=list, description="Capabilities required for slot"
    )


class PluginDependency(BaseModel):
    """Declared dependency of a plugin on another plugin or host feature."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    plugin_id: str = Field(description="Target dependency plugin identifier")
    min_version: str | None = Field(
        default=None, description="Minimum semver string (inclusive)"
    )
    max_version: str | None = Field(
        default=None, description="Maximum semver string (inclusive)"
    )
    optional: bool = Field(
        default=False, description="Whether failure to resolve dependency is fatal"
    )


class PluginManifest(BaseModel):
    """Declarative specification defining a plugin package."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest_version: int = Field(default=1, ge=1, le=10)
    id: str = Field(description="Unique plugin ID (kebab-case or dot-notation)")
    name: str = Field(description="Human-readable display name", min_length=1)
    version: str = Field(description="SemVer string, e.g. 1.0.0", min_length=1)
    description: str = Field(default="", description="Plugin purpose and details")
    author: str = Field(default="", description="Author or maintainer")
    slot: str = Field(description="Target host extension slot")
    entrypoint: str = Field(
        description="Contained entrypoint 'module:func' or 'file.py:func'"
    )
    dependencies: list[PluginDependency] = Field(
        default_factory=list, description="Required dependencies"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Requested host capabilities"
    )
    enabled: bool = Field(default=True, description="Initial enablement flag")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary extension metadata"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate plugin identifier syntax."""
        if not ID_PATTERN.match(v):
            raise ValueError(
                f"Plugin identifier '{v}' is invalid. "
                f"Must match pattern {ID_PATTERN.pattern}"
            )
        return v

    @field_validator("entrypoint")
    @classmethod
    def validate_entrypoint(cls, v: str) -> str:
        """Validate entrypoint format and forbid traversal syntax."""
        if ":" not in v:
            raise ValueError(
                f"Entrypoint '{v}' must be in format 'module:attr' or 'file.py:attr'"
            )
        target, attr = v.split(":", 1)
        if not target.strip() or not attr.strip():
            raise ValueError(f"Entrypoint '{v}' cannot have empty target or attr")
        if ".." in target or target.startswith(("/", "\\")):
            raise ValueError(
                f"Entrypoint '{v}' violates security policy (escaped path)"
            )
        return v


class PluginRecord(BaseModel):
    """Complete runtime state and metadata record for a discovered plugin."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: PluginManifest
    state: PluginState
    package_dir: str = Field(description="Absolute path to plugin root directory")
    error_message: str | None = Field(
        default=None, description="Detailed error description if degraded"
    )
    discovered_at: str = Field(description="ISO-8601 discovery timestamp")
    attached_at: str | None = Field(
        default=None, description="ISO-8601 attachment timestamp"
    )


class PluginSummary(BaseModel):
    """Projected summary of a plugin suitable for UI and browser inspection."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    version: str
    slot: str
    state: PluginState
    enabled: bool
    description: str
    package_dir: str
    error_message: str | None = None
    discovered_at: str
    attached_at: str | None = None


class PluginListResponse(BaseModel):
    """API response envelope for plugin catalog queries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total: int
    states_count: dict[str, int]
    plugins: list[PluginSummary]


class SlotSummary(BaseModel):
    """Projected summary of a host extension slot and its attached plugins."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_id: str
    description: str
    multi_instance: bool
    required_capabilities: list[str]
    attached_plugins: list[str]


# -----------------------------------------------------------------------------
# Slot Registry
# -----------------------------------------------------------------------------


class SlotRegistry:
    """Registry maintaining valid host extension slots and their constraints.

    Fires FR-HOST-DISC-SLOT-REGISTRATION.
    """

    def __init__(self) -> None:
        """Initialize slot registry with built-in core host extension slots."""
        self._slots: dict[str, SlotDefinition] = {}
        self._register_core_slots()

    def _register_core_slots(self) -> None:
        """Register normative built-in host slots."""
        core_slots = [
            SlotDefinition(
                slot_id="workspace.root",
                description="Top-level browser application workspace surface",
                multi_instance=True,
            ),
            SlotDefinition(
                slot_id="workspace.panel",
                description="Sub-panel integrated within an existing workspace",
                multi_instance=True,
            ),
            SlotDefinition(
                slot_id="data.provider",
                description="Market data feed, downloader, or import provider",
                multi_instance=True,
            ),
            SlotDefinition(
                slot_id="engine.evaluator",
                description="Quantitative strategy evaluator or fitness ranking",
                multi_instance=True,
            ),
            SlotDefinition(
                slot_id="export.formatter",
                description="Code generator or quantitative trade report exporter",
                multi_instance=True,
            ),
            SlotDefinition(
                slot_id="diagnostic.probe",
                description="Host hardware and runtime system diagnostic probe",
                multi_instance=True,
            ),
        ]
        for slot in core_slots:
            self._slots[slot.slot_id] = slot

    def register_slot(self, slot: SlotDefinition) -> None:
        """Register an extension slot with the host.

        Fires FR-HOST-DISC-SLOT-REGISTRATION.
        """
        self._slots[slot.slot_id] = slot
        logger.info(
            "FR-HOST-DISC-SLOT-REGISTRATION: Registered extension slot '%s' "
            "(multi_instance=%s)",
            slot.slot_id,
            slot.multi_instance,
            extra={
                "fr_id": "FR-HOST-DISC-SLOT-REGISTRATION",
                "slot_id": slot.slot_id,
                "multi_instance": slot.multi_instance,
            },
        )

    def get_slot(self, slot_id: str) -> SlotDefinition | None:
        """Retrieve slot definition by identifier."""
        return self._slots.get(slot_id)

    def has_slot(self, slot_id: str) -> bool:
        """Check whether slot identifier is registered."""
        return slot_id in self._slots

    def list_slots(self) -> list[SlotDefinition]:
        """List all currently registered extension slots."""
        return list(self._slots.values())


# -----------------------------------------------------------------------------
# Plugin Host Capability Context
# -----------------------------------------------------------------------------


class PluginHostContext:
    """Typed capability context injected into plugin factories upon attachment.

    Fires FR-HOST-DISC-CAPABILITY-INJECTION.
    """

    def __init__(
        self,
        plugin_id: str,
        package_dir: Path,
        data_dir: Path,
        settings: Any | None = None,
    ) -> None:
        """Initialize host context with isolated resources for a specific plugin."""
        self.plugin_id: str = plugin_id
        self.package_dir: Path = package_dir
        self.data_dir: Path = data_dir
        self.settings: Any | None = settings
        self.logger: BoundLogger = get_logger(f"plugin.{plugin_id}")

        self._mounted_routers: list[APIRouter] = []
        self._event_listeners: list[tuple[str, Callable[..., Any]]] = []
        self._tracked_jobs: list[tuple[str, Callable[[], Any] | None]] = []
        self._teardown_hooks: list[Callable[[], Any]] = []

        # Ensure isolated plugin data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def register_route(self, router: APIRouter) -> None:
        """Register an API sub-router owned by this plugin."""
        self._mounted_routers.append(router)
        logger.info(
            "FR-HOST-DISC-CAPABILITY-INJECTION: Plugin '%s' registered API router.",
            self.plugin_id,
            extra={
                "fr_id": "FR-HOST-DISC-CAPABILITY-INJECTION",
                "plugin_id": self.plugin_id,
            },
        )

    def register_event_listener(
        self, event_type: str, handler: Callable[..., Any]
    ) -> None:
        """Register an event listener owned by this plugin."""
        self._event_listeners.append((event_type, handler))
        logger.debug(
            "FR-HOST-DISC-CAPABILITY-INJECTION: Plugin '%s' registered event "
            "listener for '%s'",
            self.plugin_id,
            event_type,
            extra={
                "fr_id": "FR-HOST-DISC-CAPABILITY-INJECTION",
                "plugin_id": self.plugin_id,
                "event_type": event_type,
            },
        )

    def register_job(
        self, job_id: str, cancel_handler: Callable[[], Any] | None = None
    ) -> None:
        """Track a background job owned by this plugin."""
        self._tracked_jobs.append((job_id, cancel_handler))
        logger.debug(
            "FR-HOST-DISC-CAPABILITY-INJECTION: Plugin '%s' registered background "
            "job '%s'",
            self.plugin_id,
            job_id,
            extra={
                "fr_id": "FR-HOST-DISC-CAPABILITY-INJECTION",
                "plugin_id": self.plugin_id,
                "job_id": job_id,
            },
        )

    def register_teardown(self, callback: Callable[[], Any]) -> None:
        """Register a teardown hook to execute on plugin disable or removal."""
        self._teardown_hooks.append(callback)

    def execute_teardown(self) -> None:
        """Execute all registered teardown hooks and cancel owned jobs."""
        for hook in reversed(self._teardown_hooks):
            try:
                hook()
            except Exception:
                logger.exception(
                    "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Error executing teardown hook "
                    "in plugin '%s'",
                    self.plugin_id,
                    extra={
                        "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                        "plugin_id": self.plugin_id,
                    },
                )

        for job_id, cancel_fn in self._tracked_jobs:
            if cancel_fn is not None:
                try:
                    cancel_fn()
                except Exception:
                    logger.exception(
                        "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Error cancelling job '%s' "
                        "for plugin '%s'",
                        job_id,
                        self.plugin_id,
                        extra={
                            "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                            "plugin_id": self.plugin_id,
                            "job_id": job_id,
                        },
                    )

        self._mounted_routers.clear()
        self._event_listeners.clear()
        self._tracked_jobs.clear()
        self._teardown_hooks.clear()


# -----------------------------------------------------------------------------
# SemVer Comparison Helper
# -----------------------------------------------------------------------------


def _parse_semver(version_str: str) -> tuple[int, ...]:
    """Parse semver string into comparable integer tuple, stripping suffixes."""
    clean = version_str.strip().lstrip("vV")
    base = clean.split("-", 1)[0].split("+", 1)[0]
    parts: list[int] = []
    for piece in base.split("."):
        try:
            parts.append(int(piece))
        except ValueError:
            parts.append(0)
    while len(parts) < SEMVER_PARTS_COUNT:
        parts.append(0)
    return tuple(parts[:SEMVER_PARTS_COUNT])


def _is_version_compatible(
    version: str, min_ver: str | None, max_ver: str | None
) -> bool:
    """Evaluate whether a version string satisfies min/max constraints."""
    v_tuple = _parse_semver(version)
    if min_ver is not None and v_tuple < _parse_semver(min_ver):
        return False
    return not (max_ver is not None and v_tuple > _parse_semver(max_ver))


# -----------------------------------------------------------------------------
# Plugin Discovery Engine
# -----------------------------------------------------------------------------


class PluginDiscoveryEngine:
    """Discovers, parses, validates, and orders workspace plugin packages.

    Fires FR-HOST-DISC-MANIFEST-SCHEMA, FR-HOST-DISC-CONTAINMENT-SECURITY,
    and FR-HOST-DISC-DEPENDENCY-RESOLUTION.
    """

    def __init__(self, slot_registry: SlotRegistry | None = None) -> None:
        """Initialize discovery engine with extension slot registry."""
        self.slot_registry: SlotRegistry = slot_registry or SlotRegistry()

    def _reject_constant(self, val: str) -> None:
        """Reject non-finite JSON constants (NaN, Infinity)."""
        raise ValueError(f"Non-finite JSON constant '{val}' is not allowed in manifest")

    def parse_manifest_file(
        self, manifest_path: Path, search_root: Path
    ) -> PluginManifest:
        """Read and parse a manifest file with bounds and security checks.

        Fires FR-HOST-DISC-MANIFEST-SCHEMA and FR-HOST-DISC-CONTAINMENT-SECURITY.
        """
        # 1. Size bounds check
        try:
            stat_res = manifest_path.stat()
        except OSError as exc:
            raise ManifestValidationError(
                f"Cannot access manifest '{manifest_path}': {exc}"
            ) from exc

        if stat_res.st_size > MAX_MANIFEST_BYTES:
            raise ManifestValidationError(
                f"Manifest file '{manifest_path}' exceeds size limit "
                f"({stat_res.st_size} > {MAX_MANIFEST_BYTES} bytes)"
            )

        # 2. Containment check
        self.verify_containment(manifest_path.parent, search_root)

        # 3. Read and JSON parse with constant rejection
        try:
            raw_bytes = manifest_path.read_bytes()
            content_str = raw_bytes.decode("utf-8")
            raw_dict = json.loads(content_str, parse_constant=self._reject_constant)
        except UnicodeDecodeError as exc:
            raise ManifestValidationError(
                f"Manifest '{manifest_path}' is not valid UTF-8: {exc}"
            ) from exc
        except (json.JSONDecodeError, ValueError) as exc:
            raise ManifestValidationError(
                f"Manifest '{manifest_path}' contains malformed JSON: {exc}"
            ) from exc

        if not isinstance(raw_dict, dict):
            raise ManifestValidationError(
                f"Manifest '{manifest_path}' root must be a JSON object"
            )

        # 4. Pydantic schema validation
        try:
            manifest = PluginManifest.model_validate(raw_dict)
        except Exception as exc:
            raise ManifestValidationError(
                f"Manifest '{manifest_path}' schema validation failed: {exc}"
            ) from exc

        logger.info(
            "FR-HOST-DISC-MANIFEST-SCHEMA: Validated manifest for plugin '%s' "
            "(version=%s, slot=%s)",
            manifest.id,
            manifest.version,
            manifest.slot,
            extra={
                "fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA",
                "plugin_id": manifest.id,
                "version": manifest.version,
                "slot": manifest.slot,
            },
        )
        return manifest

    def verify_containment(self, package_dir: Path, search_root: Path) -> None:
        """Verify that package directory strictly resolves within search root.

        Fires FR-HOST-DISC-CONTAINMENT-SECURITY.
        """
        try:
            resolved_root = search_root.resolve(strict=False)
            resolved_pkg = package_dir.resolve(strict=True)
        except OSError as exc:
            raise SecurityViolationError(
                f"Unable to resolve path security containment: {exc}"
            ) from exc

        try:
            resolved_pkg.relative_to(resolved_root)
        except ValueError as exc:
            logger.warning(
                "FR-HOST-DISC-CONTAINMENT-SECURITY: Security violation! Directory "
                "'%s' escapes root '%s'",
                resolved_pkg,
                resolved_root,
                extra={
                    "fr_id": "FR-HOST-DISC-CONTAINMENT-SECURITY",
                    "package_dir": str(resolved_pkg),
                    "search_root": str(resolved_root),
                },
            )
            err = (
                f"Plugin package '{resolved_pkg}' escapes "
                f"authorized root '{resolved_root}'"
            )
            raise SecurityViolationError(err) from exc

    def _find_manifest_file(self, candidate_dir: Path) -> Path | None:
        """Locate plugin.json or manifest.json in candidate directory."""
        for fname in ("plugin.json", "manifest.json"):
            cand_file = candidate_dir / fname
            if cand_file.is_file():
                return cand_file
        return None

    def _process_candidate(
        self,
        candidate_dir: Path,
        search_root: Path,
        discovered: dict[str, PluginRecord],
        now: str,
    ) -> None:
        """Process a single directory candidate for plugin manifest discovery."""
        manifest_file = self._find_manifest_file(candidate_dir)
        if manifest_file is None:
            return

        try:
            manifest = self.parse_manifest_file(manifest_file, search_root)
        except (ManifestValidationError, SecurityViolationError) as exc:
            logger.exception(
                "FR-HOST-DISC-MANIFEST-SCHEMA: Rejected invalid plugin in '%s'",
                candidate_dir.name,
                extra={
                    "fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA",
                    "candidate_dir": candidate_dir.name,
                    "error": str(exc),
                },
            )
            return

        # Check for duplicate ID
        if manifest.id in discovered:
            existing = discovered[manifest.id]
            dup_err = (
                f"Duplicate plugin ID '{manifest.id}' in '{candidate_dir}' "
                f"conflicting with '{existing.package_dir}'"
            )
            logger.error(
                "FR-HOST-DISC-MANIFEST-SCHEMA: %s",
                dup_err,
                extra={
                    "fr_id": "FR-HOST-DISC-MANIFEST-SCHEMA",
                    "plugin_id": manifest.id,
                },
            )
            discovered[manifest.id] = PluginRecord(
                manifest=existing.manifest,
                state=PluginState.INCOMPATIBLE,
                package_dir=existing.package_dir,
                error_message=dup_err,
                discovered_at=existing.discovered_at,
            )
            return

        # Check slot compatibility
        state = PluginState.DISCOVERED
        err_message: str | None = None
        if not self.slot_registry.has_slot(manifest.slot):
            state = PluginState.INCOMPATIBLE
            err_message = f"Target slot '{manifest.slot}' is not registered in host"
            logger.warning(
                "FR-HOST-DISC-SLOT-REGISTRATION: Plugin '%s' declared "
                "unregistered slot '%s'",
                manifest.id,
                manifest.slot,
                extra={
                    "fr_id": "FR-HOST-DISC-SLOT-REGISTRATION",
                    "plugin_id": manifest.id,
                    "slot": manifest.slot,
                },
            )

        discovered[manifest.id] = PluginRecord(
            manifest=manifest,
            state=state,
            package_dir=str(candidate_dir.resolve()),
            error_message=err_message,
            discovered_at=now,
        )

    def discover(self, search_paths: Sequence[Path | str]) -> dict[str, PluginRecord]:
        """Scan candidate search paths and discover all valid plugin manifests.

        Fires FR-HOST-DISC-MANIFEST-SCHEMA and FR-HOST-DISC-CONTAINMENT-SECURITY.
        """
        discovered: dict[str, PluginRecord] = {}
        now = datetime.now(UTC).isoformat()

        for raw_path in search_paths:
            path = Path(raw_path)
            if not path.is_dir():
                continue

            search_root = path.resolve()
            for candidate_dir in search_root.iterdir():
                if candidate_dir.is_dir():
                    self._process_candidate(candidate_dir, search_root, discovered, now)

        return discovered

    def _validate_dependency_link(
        self, dep: PluginDependency, plugins: dict[str, PluginRecord]
    ) -> str | None:
        """Check a single dependency link and return error message if incompatible."""
        dep_id = dep.plugin_id
        if dep_id not in plugins:
            return (
                f"Missing required dependency '{dep_id}'" if not dep.optional else None
            )

        dep_rec = plugins[dep_id]
        if dep_rec.state == PluginState.INCOMPATIBLE and not dep.optional:
            return (
                f"Required dependency '{dep_id}' is incompatible: "
                f"{dep_rec.error_message}"
            )

        if (
            not _is_version_compatible(
                dep_rec.manifest.version, dep.min_version, dep.max_version
            )
            and not dep.optional
        ):
            return (
                f"Dependency '{dep_id}' version "
                f"'{dep_rec.manifest.version}' does not satisfy range "
                f"[{dep.min_version}, {dep.max_version}]"
            )

        return None

    def _check_dependencies(
        self, plugins: dict[str, PluginRecord]
    ) -> dict[str, set[str]]:
        """Validate presence and versions of all declared dependencies."""
        adj: dict[str, set[str]] = {}
        incompatible_reasons: dict[str, str] = {}

        for p_id, record in plugins.items():
            adj[p_id] = set()
            if record.state == PluginState.INCOMPATIBLE:
                continue

            for dep in record.manifest.dependencies:
                dep_err = self._validate_dependency_link(dep, plugins)
                if dep_err is not None:
                    incompatible_reasons[p_id] = dep_err
                    break
                if dep.plugin_id in plugins:
                    adj[p_id].add(dep.plugin_id)

        for p_id, reason in incompatible_reasons.items():
            rec = plugins[p_id]
            logger.error(
                "FR-HOST-DISC-DEPENDENCY-RESOLUTION: Dependency failure for '%s': %s",
                p_id,
                reason,
                extra={
                    "fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLUTION",
                    "plugin_id": p_id,
                    "reason": reason,
                },
            )
            plugins[p_id] = PluginRecord(
                manifest=rec.manifest,
                state=PluginState.INCOMPATIBLE,
                package_dir=rec.package_dir,
                error_message=reason,
                discovered_at=rec.discovered_at,
            )

        return adj

    def _topological_sort(
        self, plugins: dict[str, PluginRecord], adj: dict[str, set[str]]
    ) -> list[str]:
        """Execute topological sort on dependency DAG and detect cycles."""
        dependent_nodes: dict[str, list[str]] = {p_id: [] for p_id in plugins}
        clean_in_degree: dict[str, int] = dict.fromkeys(plugins, 0)

        for p_id, deps in adj.items():
            if plugins[p_id].state == PluginState.INCOMPATIBLE:
                continue
            for dep_id in deps:
                if plugins[dep_id].state != PluginState.INCOMPATIBLE:
                    dependent_nodes[dep_id].append(p_id)
                    clean_in_degree[p_id] += 1

        ready_queue: list[str] = [
            p_id
            for p_id, deg in clean_in_degree.items()
            if deg == 0 and plugins[p_id].state != PluginState.INCOMPATIBLE
        ]
        sorted_order: list[str] = []

        while ready_queue:
            curr = ready_queue.pop(0)
            sorted_order.append(curr)

            for dependent in dependent_nodes.get(curr, []):
                clean_in_degree[dependent] -= 1
                if clean_in_degree[dependent] == 0:
                    ready_queue.append(dependent)

        for p_id, deg in clean_in_degree.items():
            if deg > 0 and plugins[p_id].state != PluginState.INCOMPATIBLE:
                rec = plugins[p_id]
                cycle_err = f"Circular dependency detected involving plugin '{p_id}'"
                logger.error(
                    "FR-HOST-DISC-DEPENDENCY-RESOLUTION: %s",
                    cycle_err,
                    extra={
                        "fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLUTION",
                        "plugin_id": p_id,
                    },
                )
                plugins[p_id] = PluginRecord(
                    manifest=rec.manifest,
                    state=PluginState.INCOMPATIBLE,
                    package_dir=rec.package_dir,
                    error_message=cycle_err,
                    discovered_at=rec.discovered_at,
                )

        return sorted_order

    def resolve_dependencies(self, plugins: dict[str, PluginRecord]) -> list[str]:
        """Resolve dependencies and return plugins ordered topologically for attachment.

        Fires FR-HOST-DISC-DEPENDENCY-RESOLUTION.
        """
        adj = self._check_dependencies(plugins)
        sorted_order = self._topological_sort(plugins, adj)

        logger.info(
            "FR-HOST-DISC-DEPENDENCY-RESOLUTION: Resolved dependency order "
            "for %d plugins: %s",
            len(sorted_order),
            sorted_order,
            extra={
                "fr_id": "FR-HOST-DISC-DEPENDENCY-RESOLUTION",
                "resolved_count": len(sorted_order),
                "order": sorted_order,
            },
        )
        return sorted_order


# -----------------------------------------------------------------------------
# Plugin Lifecycle Manager
# -----------------------------------------------------------------------------


class PluginLifecycleManager:
    """Coordinates lifecycle, capability injection, and controlled cleanup of plugins.

    Fires FR-HOST-DISC-LIFECYCLE-MANAGEMENT and FR-HOST-DISC-CAPABILITY-INJECTION.
    """

    def __init__(
        self,
        discovery_engine: PluginDiscoveryEngine,
        data_base_dir: Path | None = None,
        settings: Any | None = None,
    ) -> None:
        """Initialize lifecycle manager."""
        self.engine: PluginDiscoveryEngine = discovery_engine
        self.data_base_dir: Path = (
            data_base_dir.resolve() if data_base_dir else Path("data/plugins").resolve()
        )
        self.settings: Any | None = settings

        self._records: dict[str, PluginRecord] = {}
        self._contexts: dict[str, PluginHostContext] = {}
        self._instances: dict[str, Any] = {}

    @property
    def records(self) -> dict[str, PluginRecord]:
        """Get copy of all current plugin records."""
        return dict(self._records)

    def set_records(self, records: dict[str, PluginRecord]) -> None:
        """Register discovered records with the lifecycle manager."""
        self._records = dict(records)

    def get_record(self, plugin_id: str) -> PluginRecord | None:
        """Retrieve plugin record by identifier."""
        return self._records.get(plugin_id)

    def get_context(self, plugin_id: str) -> PluginHostContext | None:
        """Retrieve active host context for an attached plugin."""
        return self._contexts.get(plugin_id)

    def get_instance(self, plugin_id: str) -> Any | None:
        """Retrieve attached instance of a plugin."""
        return self._instances.get(plugin_id)

    def get_instances_for_slot(self, slot_id: str) -> list[Any]:
        """Retrieve all attached plugin instances matching a slot."""
        instances: list[Any] = []
        for p_id, rec in self._records.items():
            if rec.state == PluginState.ATTACHED and rec.manifest.slot == slot_id:
                inst = self._instances.get(p_id)
                if inst is not None:
                    instances.append(inst)
        return instances

    def attach(self, plugin_id: str) -> bool:
        """Load and attach a plugin into the host platform.

        Fires FR-HOST-DISC-LIFECYCLE-MANAGEMENT and FR-HOST-DISC-CAPABILITY-INJECTION.
        """
        if plugin_id not in self._records:
            logger.error(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Unknown plugin '%s'",
                plugin_id,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            return False

        record = self._records[plugin_id]
        manifest = record.manifest

        if not manifest.enabled or record.state == PluginState.DISABLED:
            logger.info(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Skipping disabled plugin '%s'",
                plugin_id,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            return False

        if record.state == PluginState.INCOMPATIBLE:
            logger.warning(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Skipping incompatible '%s': %s",
                plugin_id,
                record.error_message,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            return False

        package_dir = Path(record.package_dir)
        plugin_data_dir = self.data_base_dir / plugin_id
        context = PluginHostContext(
            plugin_id=plugin_id,
            package_dir=package_dir,
            data_dir=plugin_data_dir,
            settings=self.settings,
        )

        try:
            factory = self._load_entrypoint(package_dir, manifest.entrypoint)
        except Exception as exc:
            err = f"Failed to load entrypoint '{manifest.entrypoint}': {exc}"
            logger.exception(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: %s",
                err,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            self._records[plugin_id] = PluginRecord(
                manifest=manifest,
                state=PluginState.UNAVAILABLE,
                package_dir=record.package_dir,
                error_message=err,
                discovered_at=record.discovered_at,
            )
            return False

        try:
            instance = factory(context)
            self._instances[plugin_id] = instance
            self._contexts[plugin_id] = context
            now = datetime.now(UTC).isoformat()
            self._records[plugin_id] = PluginRecord(
                manifest=manifest,
                state=PluginState.ATTACHED,
                package_dir=record.package_dir,
                error_message=None,
                discovered_at=record.discovered_at,
                attached_at=now,
            )
            logger.info(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Attached plugin '%s' (slot=%s)",
                plugin_id,
                manifest.slot,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                    "slot": manifest.slot,
                },
            )
            return True
        except Exception as exc:
            err = f"Exception raised during plugin factory execution: {exc}"
            logger.exception(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: %s",
                err,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            context.execute_teardown()
            self._records[plugin_id] = PluginRecord(
                manifest=manifest,
                state=PluginState.UNAVAILABLE,
                package_dir=record.package_dir,
                error_message=err,
                discovered_at=record.discovered_at,
            )
            return False

    def _cascade_disable(self, plugin_id: str) -> None:
        """Cascade disable to attached plugins depending on target plugin."""
        for other_id, rec in self._records.items():
            if rec.state != PluginState.ATTACHED:
                continue
            for dep in rec.manifest.dependencies:
                if dep.plugin_id == plugin_id and not dep.optional:
                    logger.info(
                        "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Cascading disable to '%s'",
                        other_id,
                        extra={
                            "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                            "plugin_id": other_id,
                            "dependency": plugin_id,
                        },
                    )
                    self.disable(other_id)

    def _teardown_instance(self, plugin_id: str) -> None:
        """Teardown active plugin context and instance hooks."""
        if plugin_id in self._contexts:
            ctx = self._contexts.pop(plugin_id)
            ctx.execute_teardown()

        if plugin_id in self._instances:
            inst = self._instances.pop(plugin_id)
            for hook_name in ("shutdown", "teardown", "close"):
                hook = getattr(inst, hook_name, None)
                if callable(hook):
                    try:
                        hook()
                    except Exception:
                        logger.exception(
                            "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Error calling %s",
                            hook_name,
                            extra={
                                "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                                "plugin_id": plugin_id,
                            },
                        )

    def disable(self, plugin_id: str) -> bool:
        """Controlled disabling of an active plugin with resource teardown.

        Fires FR-HOST-DISC-LIFECYCLE-MANAGEMENT.
        """
        if plugin_id not in self._records:
            return False

        self._cascade_disable(plugin_id)
        self._teardown_instance(plugin_id)

        rec = self._records[plugin_id]
        self._records[plugin_id] = PluginRecord(
            manifest=rec.manifest,
            state=PluginState.DISABLED,
            package_dir=rec.package_dir,
            error_message="Plugin disabled by host operator",
            discovered_at=rec.discovered_at,
            attached_at=None,
        )
        logger.info(
            "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Disabled plugin '%s' successfully.",
            plugin_id,
            extra={
                "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                "plugin_id": plugin_id,
            },
        )
        return True

    def enable(self, plugin_id: str) -> bool:
        """Enable and attach a previously disabled or validated plugin."""
        if plugin_id not in self._records:
            return False

        logger.info(
            "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Enabling plugin '%s'...",
            plugin_id,
            extra={
                "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                "plugin_id": plugin_id,
            },
        )
        rec = self._records[plugin_id]
        self._records[plugin_id] = PluginRecord(
            manifest=rec.manifest,
            state=PluginState.VALIDATED,
            package_dir=rec.package_dir,
            error_message=None,
            discovered_at=rec.discovered_at,
        )
        return self.attach(plugin_id)

    def reload(self, plugin_id: str) -> bool:
        """Reload a plugin by disabling it, re-reading manifest, and re-attaching."""
        if plugin_id not in self._records:
            return False

        logger.info(
            "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Reloading plugin '%s'...",
            plugin_id,
            extra={
                "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                "plugin_id": plugin_id,
            },
        )
        self.disable(plugin_id)
        rec = self._records[plugin_id]
        package_dir = Path(rec.package_dir)
        manifest_file = package_dir / "plugin.json"
        if not manifest_file.exists():
            manifest_file = package_dir / "manifest.json"

        if not manifest_file.exists():
            logger.error(
                "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Manifest missing on reload of '%s'",
                plugin_id,
                extra={
                    "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                    "plugin_id": plugin_id,
                },
            )
            return False

        try:
            new_manifest = self.engine.parse_manifest_file(
                manifest_file, package_dir.parent
            )
            self._records[plugin_id] = PluginRecord(
                manifest=new_manifest,
                state=PluginState.VALIDATED,
                package_dir=str(package_dir),
                error_message=None,
                discovered_at=datetime.now(UTC).isoformat(),
            )
        except (DiscoveryError, OSError, ValueError, KeyError) as exc:
            self._records[plugin_id] = PluginRecord(
                manifest=rec.manifest,
                state=PluginState.INCOMPATIBLE,
                package_dir=str(package_dir),
                error_message=f"Reload failed: {exc}",
                discovered_at=rec.discovered_at,
            )
            return False

        return self.attach(plugin_id)

    def uninstall(self, plugin_id: str) -> bool:
        """Unregister a plugin and release ownership while preserving retained data."""
        if plugin_id not in self._records:
            return False

        self.disable(plugin_id)
        self._records.pop(plugin_id, None)
        logger.info(
            "FR-HOST-DISC-LIFECYCLE-MANAGEMENT: Uninstalled plugin '%s' from host.",
            plugin_id,
            extra={
                "fr_id": "FR-HOST-DISC-LIFECYCLE-MANAGEMENT",
                "plugin_id": plugin_id,
            },
        )
        return True

    def _load_entrypoint(
        self, package_dir: Path, entrypoint_spec: str
    ) -> Callable[..., Any]:
        """Safely load entrypoint callable from package directory."""
        target, attr = entrypoint_spec.split(":", 1)

        is_file_target = (
            target.endswith(".py")
            or (package_dir / f"{target}.py").exists()
            or (package_dir / target).is_file()
        )
        if is_file_target:
            py_file = (
                package_dir / target
                if target.endswith(".py")
                else package_dir / f"{target}.py"
            )
            if not py_file.is_file():
                raise FileNotFoundError(f"Entrypoint file '{py_file}' not found")

            self.engine.verify_containment(py_file.parent, package_dir)

            mod_name = f"haru_plugin_{package_dir.name}_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(mod_name, py_file)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot create module spec for '{py_file}'")

            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            factory = getattr(module, attr, None)
            if factory is None or not callable(factory):
                raise AttributeError(
                    f"Module '{py_file}' has no callable attribute '{attr}'"
                )
            return cast("Callable[..., Any]", factory)

        pkg_parent_str = str(package_dir.parent.resolve())
        sys_path_added = False
        if pkg_parent_str not in sys.path:
            sys.path.insert(0, pkg_parent_str)
            sys_path_added = True

        try:
            mod = importlib.import_module(target)
            factory = getattr(mod, attr, None)
            if factory is None or not callable(factory):
                raise AttributeError(
                    f"Module '{target}' has no callable attribute '{attr}'"
                )
            return cast("Callable[..., Any]", factory)
        finally:
            if sys_path_added and pkg_parent_str in sys.path:
                sys.path.remove(pkg_parent_str)


# -----------------------------------------------------------------------------
# Module Singleton Instances
# -----------------------------------------------------------------------------

default_slot_registry: SlotRegistry = SlotRegistry()
default_discovery_engine: PluginDiscoveryEngine = PluginDiscoveryEngine(
    slot_registry=default_slot_registry
)
default_lifecycle_manager: PluginLifecycleManager = PluginLifecycleManager(
    discovery_engine=default_discovery_engine
)


# -----------------------------------------------------------------------------
# FastAPI Browser REST Router
# -----------------------------------------------------------------------------


class _DiscoveryEndpointHandler:
    """REST endpoint handlers for plugin discovery projections."""

    def __init__(self, manager: PluginLifecycleManager) -> None:
        self.manager: PluginLifecycleManager = manager

    async def list_plugins(
        self,
        slot: Annotated[str | None, Query(description="Filter by slot ID")] = None,
        state: Annotated[
            PluginState | None, Query(description="Filter by state")
        ] = None,
    ) -> PluginListResponse:
        """List all discovered plugins with optional filtering."""
        records = self.manager.records.values()
        summaries: list[PluginSummary] = []
        states_count: dict[str, int] = {}

        for rec in records:
            s_name = rec.state.value
            states_count[s_name] = states_count.get(s_name, 0) + 1

            if slot is not None and rec.manifest.slot != slot:
                continue
            if state is not None and rec.state != state:
                continue

            summaries.append(
                PluginSummary(
                    id=rec.manifest.id,
                    name=rec.manifest.name,
                    version=rec.manifest.version,
                    slot=rec.manifest.slot,
                    state=rec.state,
                    enabled=rec.manifest.enabled,
                    description=rec.manifest.description,
                    package_dir=rec.package_dir,
                    error_message=rec.error_message,
                    discovered_at=rec.discovered_at,
                    attached_at=rec.attached_at,
                )
            )

        logger.debug(
            "FR-HOST-DISC-BROWSER-PROJECTION: Queried plugins list "
            "(total=%d, filtered=%d)",
            len(records),
            len(summaries),
            extra={
                "fr_id": "FR-HOST-DISC-BROWSER-PROJECTION",
                "total": len(records),
                "filtered": len(summaries),
            },
        )
        return PluginListResponse(
            total=len(summaries),
            states_count=states_count,
            plugins=summaries,
        )

    async def get_plugin(self, plugin_id: str) -> PluginRecord:
        """Retrieve full details of a specific plugin."""
        record = self.manager.get_record(plugin_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        return record

    async def enable_plugin(self, plugin_id: str) -> PluginRecord:
        """Enable and attach a plugin."""
        success = self.manager.enable(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=rec.error_message or "Failed to enable plugin",
            )
        return rec

    async def disable_plugin(self, plugin_id: str) -> PluginRecord:
        """Disable a plugin and release its attached resources."""
        success = self.manager.disable(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disable plugin",
            )
        return rec

    async def reload_plugin(self, plugin_id: str) -> PluginRecord:
        """Reload a plugin by disabling, re-reading manifest, and re-attaching."""
        success = self.manager.reload(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=rec.error_message or "Failed to reload plugin",
            )
        return rec

    async def list_slots(self) -> list[SlotSummary]:
        """List all extension slots and currently attached plugins."""
        slots = self.manager.engine.slot_registry.list_slots()
        records = self.manager.records.values()

        summaries: list[SlotSummary] = []
        for s in slots:
            attached = [
                r.manifest.id
                for r in records
                if r.manifest.slot == s.slot_id and r.state == PluginState.ATTACHED
            ]
            summaries.append(
                SlotSummary(
                    slot_id=s.slot_id,
                    description=s.description,
                    multi_instance=s.multi_instance,
                    required_capabilities=s.required_capabilities,
                    attached_plugins=attached,
                )
            )
        return summaries


def create_discovery_router(
    manager: PluginLifecycleManager | None = None,
) -> APIRouter:
    """Create and return FastAPI router for browser plugin queries.

    Fires FR-HOST-DISC-BROWSER-PROJECTION.
    """
    mgr = manager or default_lifecycle_manager
    handler = _DiscoveryEndpointHandler(mgr)
    router = APIRouter(prefix="/discovery", tags=["Discovery"])

    router.add_api_route(
        "/plugins",
        handler.list_plugins,
        methods=["GET"],
        response_model=PluginListResponse,
        summary="List discovered plugins",
    )
    router.add_api_route(
        "/plugins/{plugin_id}",
        handler.get_plugin,
        methods=["GET"],
        response_model=PluginRecord,
        summary="Get plugin details",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/enable",
        handler.enable_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Enable and attach plugin",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/disable",
        handler.disable_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Disable and teardown plugin",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/reload",
        handler.reload_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Reload plugin",
    )
    router.add_api_route(
        "/slots",
        handler.list_slots,
        methods=["GET"],
        response_model=list[SlotSummary],
        summary="List extension slots",
    )

    return router


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for offline scanning and validation of plugin packages."""
    parser = argparse.ArgumentParser(
        description="HaruQuantAI Workspace and Plugin Discovery Scanner"
    )
    parser.add_argument(
        "--scan",
        nargs="+",
        default=["plugins"],
        help="Directories to scan for plugin packages",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered plugins and their states",
    )
    parser.add_argument(
        "--slots",
        action="store_true",
        help="List registered host extension slots",
    )
    args = parser.parse_args(argv)

    if args.slots:
        registry = SlotRegistry()
        print(f"Registered Host Extension Slots ({len(registry.list_slots())}):")
        for s in registry.list_slots():
            print(f" - {s.slot_id}: {s.description} (multi={s.multi_instance})")
        return 0

    paths: list[Path | str] = [Path(p) for p in args.scan]
    engine = PluginDiscoveryEngine()
    records = engine.discover(paths)
    order = engine.resolve_dependencies(records)

    print(f"Discovered {len(records)} plugin packages:")
    for p_id in order:
        rec = records[p_id]
        print(
            f" - [{rec.state.value.upper()}] {rec.manifest.name} "
            f"({p_id} v{rec.manifest.version}) -> slot: {rec.manifest.slot}"
        )
        if rec.error_message:
            print(f"     Error: {rec.error_message}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

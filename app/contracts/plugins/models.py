"""Domain models and DTOs for plugin manifests and packages."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PluginType(StrEnum):
    """Supported plugin contribution types."""

    BLOCK = "BLOCK"
    INDICATOR = "INDICATOR"
    METRIC = "METRIC"
    FILTER = "FILTER"
    FITNESS = "FITNESS"
    RESEARCH_METHOD = "RESEARCH_METHOD"
    DATA_CONNECTOR = "DATA_CONNECTOR"
    PROJECT_TASK = "PROJECT_TASK"
    SOURCE_EMITTER = "SOURCE_EMITTER"
    RESULT_PANEL = "RESULT_PANEL"


@dataclass(frozen=True, slots=True)
class PluginPermission:
    """Declared execution permissions for a plugin."""

    filesystem_read: tuple[str, ...] = ()
    filesystem_write: tuple[str, ...] = ()
    network_endpoints: tuple[str, ...] = ()
    subprocess_allow: bool = False
    secrets: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginResourceLimits:
    """Declared execution resource limits for a plugin."""

    cpu_limit_cores: float = 1.0
    memory_limit_mb: int = 512
    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class PluginFileEntry:
    """Metadata for an individual file contained in a plugin package."""

    path: str
    sha256: str
    size_bytes: int = 0


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Authoritative manifest declaring plugin metadata and capabilities."""

    id: str
    version: str
    api_range: str
    types: tuple[PluginType, ...] = ()
    entry_point: str = "main.py"
    schemas: dict[str, Any] = field(default_factory=dict)
    capabilities: tuple[str, ...] = ()
    permissions: PluginPermission = field(default_factory=PluginPermission)
    resources: PluginResourceLimits = field(default_factory=PluginResourceLimits)
    sha256_by_file: dict[str, str] = field(default_factory=dict)
    signature: str | None = None


@dataclass(frozen=True, slots=True)
class PluginPackageValidation:
    """Result of validating a plugin package zip file and its manifest."""

    manifest: PluginManifest
    package_hash: str
    files: tuple[PluginFileEntry, ...] = ()
    is_valid: bool = True
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PluginPackageRef:
    """Reference descriptor for a validated plugin package."""

    plugin_id: str
    version: str
    package_path: str
    package_hash: str

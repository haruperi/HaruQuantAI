"""Contracts and document models for project configurations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType

from app.core.lib.errors import JSONValue, copy_json


@dataclass(frozen=True, slots=True)
class TaskDocument:
    """Document model representing a single task in a project pipeline."""

    task_id: str
    task_type: str
    settings: dict[str, JSONValue] = field(default_factory=dict)
    name: str = ""
    enabled: bool = True
    databank_target: str = ""
    dependencies: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert task document to dictionary suitable for JSON serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "name": self.name,
            "enabled": self.enabled,
            "databank_target": self.databank_target,
            "dependencies": [str(d) for d in self.dependencies],
            "settings": copy_json(self.settings),
        }

    @classmethod
    def from_dict(cls, task_id: str, data: dict[str, JSONValue]) -> TaskDocument:
        """Create a TaskDocument instance from a raw dictionary."""
        t_id = str(data.get("task_id") or task_id)
        t_type = str(data.get("task_type") or "generic")
        name = str(data.get("name") or "")
        enabled = bool(data.get("enabled", True))
        databank_target = str(data.get("databank_target") or "")
        deps_raw = data.get("dependencies", [])
        deps = (
            tuple(str(item) for item in deps_raw) if isinstance(deps_raw, list) else ()
        )
        settings_raw = data.get("settings", {})
        settings = copy_json(settings_raw) if isinstance(settings_raw, dict) else {}
        return cls(
            task_id=t_id,
            task_type=t_type,
            settings=settings if isinstance(settings, dict) else {},
            name=name,
            enabled=enabled,
            databank_target=databank_target,
            dependencies=deps,
        )


@dataclass(frozen=True, slots=True)
class ProjectManifest:
    """Identity and metadata manifest for a Haru project."""

    project_id: str
    name: str
    app_name: str = "HaruQuantAI"
    schema_version: int = 1
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, JSONValue]:
        """Convert manifest to JSON-compatible dictionary."""
        return {
            "app_name": self.app_name,
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, JSONValue]) -> ProjectManifest:
        """Create a ProjectManifest from dictionary."""
        raw_schema = data.get("schema_version", 1)
        schema_version = (
            int(raw_schema)
            if isinstance(raw_schema, (int, float, str))
            and not isinstance(raw_schema, bool)
            else 1
        )
        return cls(
            project_id=str(data.get("project_id", "")),
            name=str(data.get("name", "")),
            app_name=str(data.get("app_name", "HaruQuantAI")),
            schema_version=schema_version,
            description=str(data.get("description", "")),
            created_at=str(data.get("created_at", "")),
            updated_at=str(data.get("updated_at", "")),
        )


@dataclass(frozen=True, slots=True)
class ProjectDocument:
    """Complete in-memory document representing a Haru strategy project."""

    manifest: ProjectManifest
    pipeline: tuple[str, ...] = ()
    databanks: Mapping[str, str] = field(default_factory=dict)
    tasks: Mapping[str, TaskDocument] = field(default_factory=dict)
    metadata: Mapping[str, JSONValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce immutable mapping proxies."""
        object.__setattr__(self, "databanks", MappingProxyType(dict(self.databanks)))
        object.__setattr__(self, "tasks", MappingProxyType(dict(self.tasks)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

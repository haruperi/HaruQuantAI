"""Typed owner-scoped host services; no provider registry or peer business APIs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, cast

from app.host.jobs import Budget, Job, JobManager
from app.host.resource_store import ResourceRef, ResourceStore


@dataclass(frozen=True)
class ResourceAccess:
    """Host resource custody scoped to one principal and producer version."""

    owner: str
    version: str
    _store: ResourceStore

    def list(self) -> tuple[ResourceRef, ...]:
        """List revisions readable by this owner."""
        return self._store.list(self.owner)

    def read(self, reference: ResourceRef) -> tuple[bytes, str]:
        """Read immutable bytes/schema with access checks and digest verification."""
        return self._store.read(self.owner, reference)

    def publish(
        self,
        content: bytes,
        *,
        schema_id: str,
        schema_version: str,
        schema_json: str,
        media_type: str,
        readers: tuple[str, ...] = (),
        previous: ResourceRef | None = None,
    ) -> ResourceRef:
        """Publish without allowing the caller to impersonate another producer."""
        return self._store.publish(
            self.owner,
            self.version,
            content,
            schema_id=schema_id,
            schema_version=schema_version,
            schema_json=schema_json,
            media_type=media_type,
            readers=readers,
            previous=previous,
        )


@dataclass(frozen=True)
class JobAccess:
    """Scoped admission and observation for one owner's task bodies."""

    owner: str
    _manager: JobManager

    def submit(self, budget: Budget, operation: Callable[[], Awaitable[None]]) -> Job:
        """Reserve host capacity for this owner only."""
        return self._manager.submit(self.owner, budget, operation)

    def status(self, job_id: str) -> Job:
        """Read an owned job."""
        return self._manager.status(self.owner, job_id)

    def cancel(self, job_id: str) -> None:
        """Cancel an owned job."""
        self._manager.cancel(self.owner, job_id)


@dataclass(frozen=True)
class SettingsAccess:
    """Host private settings custody scoped to one owner."""

    owner: str
    _store: Any

    def get(self, key: str) -> dict[str, Any] | None:
        """Read a private settings record for this owner."""
        if hasattr(self._store, "get_private"):
            result = self._store.get_private(self.owner, key)
            return cast("dict[str, Any] | None", result)
        if hasattr(self._store, "get"):
            result = self._store.get(f"{self.owner}:{key}")
            return cast("dict[str, Any] | None", result)
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set a private settings record for this owner."""
        if hasattr(self._store, "set_private"):
            self._store.set_private(self.owner, key, value)
        elif hasattr(self._store, "__setitem__"):
            self._store[f"{self.owner}:{key}"] = dict(value)


@dataclass(frozen=True)
class HostCapabilities:
    """Explicit immutable bundle, constructed by the composition root for an owner."""

    resources: ResourceAccess | None
    jobs: JobAccess | None
    log: Callable[[str], None] | None
    settings: SettingsAccess | None = None

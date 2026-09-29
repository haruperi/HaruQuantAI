"""Typed Owner-Scoped Capability Slot Facades and Isolation Boundary.

Description:
    This module defines the typed, owner-scoped capability facades injected into
    workspaces and plugins. It exists to enforce the Second and Third Laws of
    Spatial Composability (Orthogonality and Explicit Typed Capability Slots),
    guaranteeing that quantitative and workspace code cannot access ambient
    registries, issue raw unrestricted database queries, bypass hardware capacity
    budgets, or execute un-sandboxed network and filesystem operations. Externally,
    it interacts with `Composition` in `app.host.packages`, which inspects package
    manifest requirements (`requires: ["host.resources", "host.jobs", ...]`) and
    constructs an immutable `HostCapabilities` bundle passed to the package's
    `prepare()` hook. Quantitative workspaces and plugins consume these facades
    during analysis and execution workflows. Internally, each access class
    (`ResourceAccess`, `JobAccess`, `SettingsAccess`, `MarketAccess`, `NetworkAccess`)
    binds an immutable `owner` identity, mediating all interactions with underlying
    stores while enforcing strict ownership authorization.

Purpose:
    FEAT-HOST-CAPABILITIES: Typed Capability Slot Facades and Isolation Boundary.
    Provides typed, owner-scoped capability facades injected into workspaces
    and plugins, preventing ambient authority and isolating resource custody.

Key Capabilities:
    - FR-HOST-CAPABILITIES-RESOURCE-CUSTODY: Scoped Shared Resource Custody
      Associated: `ResourceAccess.read()`, `ResourceAccess.publish()`,
      `ResourceAccess.list()`
      Logging: Emits debug log on resource read and info log on immutable
      resource publishing.
    - FR-HOST-CAPABILITIES-JOB-OFFLOAD: Hardware Budgeted Job Admission
      Associated: `JobAccess.submit()`, `JobAccess.status()`,
      `JobAccess.cancel()`
      Logging: Emits info log on task submission and cancellation under the
      owner's compute budget.
    - FR-HOST-CAPABILITIES-SETTINGS-CUSTODY: Private Settings Custody
      Associated: `SettingsAccess.get()`, `SettingsAccess.set()`
      Logging: Emits debug log on settings read and info log on private
      setting update.
    - FR-HOST-CAPABILITIES-MARKET-CUSTODY: Historical Market Data Storage
      Associated: `MarketAccess.register_dataset()`, `MarketAccess.publish()`,
      `MarketAccess.delete_dataset()`
      Logging: Emits info logs when datasets are registered, updated,
      cleared, or purged.
    - FR-HOST-CAPABILITIES-NETWORK-RETRIEVAL: Allowlisted Network Access
      Associated: `NetworkAccess.get()`
      Logging: Emits debug log with target URL upon historical data retrieval.

Python API Usage:
    ```python
    from app.host.capabilities import HostCapabilities, JobAccess, ResourceAccess
    from app.host.jobs import Budget, JobManager
    from app.persistence.resources import ResourceStore

    # 1. Host runtime constructs scoped capabilities during composition
    resources = ResourceAccess("plugin.example", "1.0.0", store)
    jobs = JobAccess("plugin.example", job_manager)
    caps = HostCapabilities(resources=resources, jobs=jobs, log=logger.info)

    # 2. Plugin receives caps in prepare() without global dependencies
    # async def prepare(caps: HostCapabilities) -> PreparedContribution: ...
    ```

CLI Usage:
    Capability boundaries and slot compatibility are verified via test
    suites and the architecture checker:
    ```bash
    # Verify capability isolation and typing
    uv run pytest tests/host/test_capabilities.py

    # Verify absence of ambient dependencies or forbidden imports
    uv run python scripts/architecture_check.py
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, cast

from app.host.jobs import Budget, Job, JobManager
from app.host.logging import get_logger
from app.host.network import HistoricalNetwork, NetworkResult
from app.persistence.market import (
    DefinitionRequest,
    Kind,
    MarketBroker,
    MarketDataset,
    MarketDataStore,
)
from app.persistence.resources import ResourceRef, ResourceStore

logger = get_logger(__name__)


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
        logger.info(
            "ResourceAccess reading resource %s (owner=%s)",
            reference.id,
            self.owner,
        )
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
        ref = self._store.publish(
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
        logger.info(
            "ResourceAccess published resource %s revision %d (schema=%s, owner=%s)",
            ref.id,
            ref.revision,
            schema_id,
            self.owner,
        )
        return ref


@dataclass(frozen=True)
class JobAccess:
    """Scoped admission and observation for one owner's task bodies."""

    owner: str
    _manager: JobManager

    def submit(self, budget: Budget, operation: Callable[[], Awaitable[None]]) -> Job:
        """Reserve host capacity for this owner only."""
        job = self._manager.submit(self.owner, budget, operation)
        logger.info("Job submitted: owner=%s job_id=%s", self.owner, job.id)
        return job

    def status(self, job_id: str) -> Job:
        """Read an owned job."""
        return self._manager.status(self.owner, job_id)

    def cancel(self, job_id: str) -> None:
        """Cancel an owned job."""
        self._manager.cancel(self.owner, job_id)
        logger.info("Job cancelled: owner=%s job_id=%s", self.owner, job_id)


@dataclass(frozen=True)
class SettingsAccess:
    """Host private settings custody scoped to one owner."""

    owner: str
    _store: Any

    def get(self, key: str) -> dict[str, Any] | None:
        """Read a private settings record for this owner."""
        logger.info("Settings accessed: owner=%s key=%s", self.owner, key)
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
        logger.info("Settings set: owner=%s key=%s", self.owner, key)


@dataclass(frozen=True)
class HostCapabilities:
    """Explicit immutable bundle, constructed by the composition root for an owner."""

    resources: ResourceAccess | None
    jobs: JobAccess | None
    log: Callable[[str], None] | None
    settings: SettingsAccess | None = None
    market_data: MarketAccess | None = field(default=None, kw_only=True)
    network: NetworkAccess | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class MarketAccess:
    """Owner-scoped market custody with no raw SQL or filesystem authority."""

    owner: str
    _store: MarketDataStore

    def available(self) -> bool:
        """Check whether market storage has an approved schema."""
        return self._store.available()

    def list_brokers(self) -> tuple[MarketBroker, ...]:
        """Read eligible broker summaries for this data-source owner only."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Broker catalog ownership denied")
        return self._store.list_brokers()

    def definitions_available(self) -> bool:
        """Check the owner's definition catalog."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        return self._store.definitions_available()

    def register_definitions(
        self, requests: tuple[DefinitionRequest, ...]
    ) -> tuple[MarketDataset, ...]:
        """Register an owned batch through host custody."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        logger.info(
            "Market definitions registered: owner=%s count=%d",
            self.owner,
            len(requests),
        )
        return self._store.register_definitions(requests)

    def register_dataset(self, symbol: str, kind: str, instrument: str) -> Any:
        """Create only an owned Dukascopy definition, without SQL authority."""
        if self.owner != "plugin.data_manager.dukascopy" or kind not in ("ticks", "m1"):
            raise PermissionError("Market source ownership denied")
        logger.info(
            "Market dataset registered: owner=%s symbol=%s",
            self.owner,
            symbol,
        )
        return self._store.register_dataset(
            source="dukascopy",
            symbol=symbol,
            kind=cast("Kind", kind),
            instrument=instrument,
        )

    def get_dataset(self, dataset_id: str) -> Any:
        """Resolve only an owned Dukascopy dataset ID."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        return self._store.get_dataset(dataset_id)

    def list_datasets(self) -> tuple[dict[str, Any], ...]:
        """Read committed Dukascopy definitions and file-backed summaries."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        return self._store.list_datasets("dukascopy")

    def delete_dataset(self, symbol: str) -> bool:
        """Purge files and delete dataset definition for an owned symbol."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        logger.info("Market dataset deleted: owner=%s symbol=%s", self.owner, symbol)
        return self._store.delete_dataset(symbol)

    def clear_dataset(self, symbol: str) -> bool:
        """Purge files and reset dataset coverage for an owned symbol."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        logger.info("Market dataset cleared: owner=%s symbol=%s", self.owner, symbol)
        return self._store.clear_dataset(symbol)

    def list_files(self, source: str, kind: str, symbol: str) -> tuple[Any, ...]:
        """List committed revisions for a validated identity."""
        if source != "dukascopy" or self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        if kind not in ("ticks", "m1"):
            raise ValueError("Invalid market kind")
        return self._store.list_files(source, cast("Kind", kind), symbol)

    def publish(
        self,
        *,
        kind: str,
        symbol: str,
        period: str,
        table: Any,
        coverage: tuple[tuple[int, int], ...],
        mode: str,
    ) -> Any:
        """Publish only this plugin's source under host custody."""
        if self.owner != "plugin.data_manager.dukascopy" or kind not in ("ticks", "m1"):
            raise PermissionError("Market source ownership denied")
        clean_kind = cast("Kind", kind)
        return self._store.publish(
            source="dukascopy",
            kind=clean_kind,
            symbol=symbol,
            period=period,
            table=table,
            coverage=coverage,
            provider_mode=mode,
        )

    def replace_interval(
        self,
        *,
        kind: str,
        symbol: str,
        period: str,
        incoming: Any,
        start_ms: int,
        end_ms: int,
        mode: str,
    ) -> Any:
        """Replace one owned interval without exposing a writable path or SQL."""
        if self.owner != "plugin.data_manager.dukascopy" or kind not in ("ticks", "m1"):
            raise PermissionError("Market source ownership denied")
        clean_kind = cast("Kind", kind)
        return self._store.replace_interval(
            source="dukascopy",
            kind=clean_kind,
            symbol=symbol,
            period=period,
            incoming=incoming,
            start_ms=start_ms,
            end_ms=end_ms,
            provider_mode=mode,
        )


@dataclass(frozen=True)
class NetworkAccess:
    """A declared owner's bounded public historical-data transport."""

    owner: str
    _network: HistoricalNetwork

    async def get(self, url: str) -> NetworkResult:
        """Fetch one allowlisted provider object."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Historical transport ownership denied")
        logger.info("Historical network request: owner=%s url=%s", self.owner, url)
        return await self._network.get(url)

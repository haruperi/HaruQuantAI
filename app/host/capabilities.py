"""Typed owner-scoped host services; no provider registry or peer business APIs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, cast

from app.host.jobs import Budget, Job, JobManager
from app.host.market_data import (
    DefinitionRequest,
    MarketBroker,
    MarketDataset,
    MarketDataStore,
)
from app.host.network import HistoricalNetwork, NetworkResult
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
        return self._store.register_definitions(requests)

    def register_dataset(self, symbol: str, kind: str, instrument: str) -> Any:
        """Create only an owned Dukascopy definition, without SQL authority."""
        if self.owner != "plugin.data_manager.dukascopy" or kind not in ("ticks", "m1"):
            raise PermissionError("Market source ownership denied")
        return self._store.register_dataset(
            source="dukascopy", symbol=symbol, kind=kind, instrument=instrument
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

    def list_files(self, source: str, kind: str, symbol: str) -> tuple[Any, ...]:
        """List committed revisions for a validated identity."""
        if source != "dukascopy" or self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        if kind not in ("ticks", "m1"):
            raise ValueError("Invalid market kind")
        return self._store.list_files(source, kind, symbol)

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
        return self._store.publish(
            source="dukascopy",
            kind=kind,
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
        return self._store.replace_interval(
            source="dukascopy",
            kind=kind,
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
        return await self._network.get(url)

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

import asyncio
import json
import re
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar, cast

from app.host.jobs import Budget, Job, JobManager
from app.host.logging import get_logger
from app.host.network import HistoricalNetwork, NetworkResult, SourceNetwork
from app.persistence.market import (
    DefinitionRequest,
    Kind,
    MarketBroker,
    MarketDataset,
    MarketDataStore,
)
from app.persistence.resources import ResourceRef, ResourceStore

ComputeResult = TypeVar("ComputeResult")

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

    async def offload(
        self, operation: Callable[..., ComputeResult], *arguments: Any
    ) -> ComputeResult:
        """Run bounded pure source computations inside this owner's admitted job."""
        return await self._manager.offload(self.owner, operation, *arguments)

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

    async def close(self) -> None:
        """Cancel and await this owner's jobs before releasing its dependencies."""
        await self._manager.close(self.owner)


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
    terminal: TerminalAccess | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class MarketAccess:
    """Owner-scoped market custody with no raw SQL or filesystem authority."""

    owner: str
    _store: MarketDataStore

    def available(self) -> bool:
        """Check whether market storage has an approved schema."""
        return self._store.available()

    def source_available(self) -> bool:
        """Report whether the script-backed catalog has been explicitly provisioned."""
        return self._store.source_available()

    def inventory(self) -> tuple[dict[str, Any], ...]:
        """Let the explicitly bound workspace inspect all source definitions."""
        if self.owner != "workspace.data_manager":
            raise PermissionError("Workspace inventory access denied")
        return self._store.inventory()

    def retained_source(self, dataset_id: str) -> dict[str, Any]:
        """Read retained metadata through the workspace or source owner boundary."""
        row = self._store.retained_source(dataset_id)
        if self.owner not in (row["owner"], "workspace.data_manager"):
            raise PermissionError("Retained dataset access denied")
        return row

    def read_source(self, dataset_id: str) -> Any:
        """Read immutable published data without needing a live producer."""
        self.retained_source(dataset_id)
        return self._store.read_source(dataset_id)

    def update_source_broker(
        self, dataset_id: str, broker: str, broker_name: str
    ) -> None:
        """Apply explicit workspace broker metadata without granting peer SQL access."""
        if self.owner != "workspace.data_manager":
            raise PermissionError("Workspace broker update denied")
        self._store.update_source_broker(dataset_id, broker, broker_name)

    def retained_revisions(self, dataset_id: str) -> dict[str, int]:
        """Read the revision map for a checked snapshot replacement."""
        self.retained_source(dataset_id)
        return {
            row["period"]: row["revision"]
            for row in self._store.source_partitions(dataset_id)
        }

    def replace_source(
        self,
        dataset_id: str,
        tables: dict[str, Any],
        *,
        expected_revisions: dict[str, int],
    ) -> None:
        """Replace a selected snapshot through host transactions."""
        definition = self.retained_source(dataset_id)
        if definition["storage_backend"] != "source_partitions":
            raise ValueError(
                "Legacy source editing requires an explicit storage migration"
            )
        self._store.replace_source(
            definition["owner"],
            dataset_id,
            tables,
            expected_revisions=expected_revisions,
        )

    def export_definition(self, dataset_id: str) -> dict[str, Any]:
        """Read producer-independent definition metadata through workspace authority."""
        if self.owner != "workspace.data_manager":
            raise PermissionError("Definition transfer access denied")
        return self._store.export_source_definition(dataset_id)

    def remove_source(self, dataset_id: str, *, clear_only: bool) -> None:
        """Execute a workspace or owning producer's explicit delete/clear request."""
        self.retained_source(dataset_id)
        self._store.remove_source(dataset_id, clear_only=clear_only)

    def import_definition(self, record: dict[str, Any]) -> str:
        """Restore opaque provider metadata without granting source execution."""
        if self.owner != "workspace.data_manager":
            raise PermissionError("Definition transfer access denied")
        owner = record.get("owner", "")
        if not isinstance(owner, str) or not re.fullmatch(
            r"(?:plugin\.data_manager\.[a-z_]+|workspace\.data_manager)", owner
        ):
            raise ValueError("Invalid definition owner")
        if (
            owner == "plugin.data_manager.dukascopy"
            and record.get("storage_backend") == "market_files"
        ):
            for existing in self._store.inventory():
                if all(
                    existing[key] == record[key]
                    for key in (
                        "source",
                        "symbol",
                        "underlying",
                        "instrument",
                        "timeframe",
                        "timezone",
                        "broker",
                    )
                ):
                    return str(existing["id"])
            symbol = str(record["underlying"]).upper()
            display = str(record["symbol"])
            if (
                not display.startswith(symbol)
                or record["timeframe"] not in ("M1", "TICK")
                or record["timezone"] != "UTC"
            ):
                raise ValueError("Unsupported legacy definition identity")
            kind: Literal["ticks", "m1"] = (
                "ticks" if record["timeframe"] == "TICK" else "m1"
            )
            datasets = self._store.register_definitions(
                (
                    DefinitionRequest(
                        symbol=symbol,
                        kind=kind,
                        broker=str(record["broker"]),
                        postfix=display[len(symbol) :],
                        instrument=str(record["instrument"]),
                    ),
                )
            )
            return datasets[0].id
        return self._store.register_source(
            owner,
            source=str(record["source"]),
            symbol=str(record["symbol"]),
            underlying=str(record["underlying"]),
            instrument=str(record["instrument"]),
            timeframe=str(record["timeframe"]),
            timezone=str(record.get("timezone", "UTC")),
            broker=str(record.get("broker", "-1")),
            options=record.get("options", {}),
        )

    def register_source(
        self,
        *,
        source: str,
        symbol: str,
        underlying: str,
        instrument: str,
        timeframe: str,
        timezone: str = "UTC",
        broker: str = "-1",
        options: dict[str, Any] | None = None,
    ) -> str:
        """Register a definition scoped to the immutable caller identity."""
        return self._store.register_source(
            self.owner,
            source=source,
            symbol=symbol,
            underlying=underlying,
            instrument=instrument,
            timeframe=timeframe,
            timezone=timezone,
            broker=broker,
            options=options or {},
        )

    def source_definition(self, dataset_id: str) -> dict[str, Any]:
        """Read this provider's options without granting peer dataset authority."""
        return self._store.source_definition(self.owner, dataset_id)

    def source_definitions(self) -> tuple[dict[str, Any], ...]:
        """List the caller's durable definitions."""
        return self._store.source_definitions(self.owner)

    def source_partitions(self, dataset_id: str) -> tuple[dict[str, Any], ...]:
        """List this provider's current partition revisions before an update."""
        self.source_definition(dataset_id)
        return self._store.source_partitions(dataset_id)

    def read_source_partition(self, dataset_id: str, period: str) -> Any:
        """Read a verified owned partition selected by identity, never a caller path."""
        records = self.source_partitions(dataset_id)
        record = next((item for item in records if item["period"] == period), None)
        if record is None:
            raise ValueError("Source partition unavailable")
        return self._store.read_source_partition(record)

    def publish_source(
        self,
        dataset_id: str,
        period: str,
        table: Any,
        *,
        expected_revision: int = 0,
    ) -> dict[str, Any]:
        """Publish lossless source data under host revision and catalog custody."""
        return self._store.publish_source(
            self.owner,
            dataset_id,
            period,
            table,
            expected_revision=expected_revision,
        )

    def list_brokers(self) -> tuple[MarketBroker, ...]:
        """Read eligible broker summaries for authorized owners."""
        if self.owner not in (
            "plugin.data_manager.dukascopy",
            "plugin.data_manager.meta_trader",
            "workspace.data_manager",
        ):
            raise PermissionError("Broker catalog ownership denied")
        return self._store.list_brokers()

    def list_all_brokers(self) -> tuple[dict[str, Any], ...]:
        """Read full broker profile records for authorized owners."""
        if self.owner not in (
            "plugin.data_manager.dukascopy",
            "plugin.data_manager.meta_trader",
            "workspace.data_manager",
        ):
            raise PermissionError("Broker catalog ownership denied")
        return self._store.list_all_brokers()

    def definitions_available(self) -> bool:
        """Check the owner's definition catalog."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        return self._store.definitions_available()

    def register_definitions(
        self, requests: tuple[DefinitionRequest, ...], *, idempotent: bool = False
    ) -> tuple[MarketDataset, ...]:
        """Register an owned batch through host custody."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        logger.info(
            "Market definitions registered: owner=%s count=%d",
            self.owner,
            len(requests),
        )
        return self._store.register_definitions(requests, idempotent=idempotent)

    def read_market_rows(
        self,
        dataset_id: str,
        *,
        start_ms: int,
        end_ms: int,
        offset: int = 0,
        limit: int = 2000,
    ) -> Any:
        """Read a bounded owned page without exposing mutable stores or paths."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        return self._store.read_market_rows(
            dataset_id,
            start_ms=start_ms,
            end_ms=end_ms,
            offset=offset,
            limit=limit,
        )

    def market_root(self) -> str:
        """Describe this provider's configured custody root to a local client."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Market source ownership denied")
        logger.info("Described market custody root: owner=%s", self.owner)
        return str((self._store.data_root / "market").resolve())

    def market_path(self, kind: str, symbol: str, period: str) -> str:
        """Describe an owned canonical path without delegating filesystem access."""
        if self.owner != "plugin.data_manager.dukascopy" or kind not in ("m1", "ticks"):
            raise PermissionError("Market source ownership denied")
        logger.info("Described canonical market path: owner=%s", self.owner)
        return str(self._store.path("dukascopy", cast("Kind", kind), symbol, period))

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
        received_intervals: tuple[tuple[int, int], ...] | None = None,
        merge_timestamps: bool = False,
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
            received_intervals=received_intervals,
            merge_timestamps=merge_timestamps,
        )


@dataclass(frozen=True)
class NetworkAccess:
    """A declared owner's bounded public historical-data transport."""

    owner: str
    _network: HistoricalNetwork

    def source_session(self, origins: tuple[str, ...]) -> SourceNetwork:
        """Bind explicit provider origins to an isolated host-owned session."""
        logger.info("Historical source session: owner=%s", self.owner)
        return self._network.source_session(origins, owner=self.owner)

    async def get(self, url: str) -> NetworkResult:
        """Fetch one allowlisted provider object."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Historical transport ownership denied")
        logger.info("Historical network request: owner=%s url=%s", self.owner, url)
        return await self._network.get(url)

    async def head(self, url: str) -> NetworkResult:
        """Probe an allowlisted historical origin without granting peer authority."""
        if self.owner != "plugin.data_manager.dukascopy":
            raise PermissionError("Historical transport ownership denied")
        logger.info("Historical network probe: owner=%s url=%s", self.owner, url)
        return await self._network.head(url)


# The worker has no trading operations. A process boundary makes blocked native
# terminal calls cancellable without abandoning a thread or unloading a live DLL.
_TERMINAL_WORKER = """
import datetime, json, os, sys
import MetaTrader5 as terminal

CANDIDATES = [
    r"C:\\Program Files\\MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\Darwinex MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\Pepperstone MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\IC Markets Global MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\RoboForex MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\FTMO MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files\\MetaQuotes\\MetaTrader 5\\terminal64.exe",
    r"C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
]

for line in sys.stdin:
    try:
        request = json.loads(line)
        operation = request['operation']
        args = request['arguments']
        if operation == 'connect':
            options = {'timeout': 30000}
            path = args.get('path')
            if not path or not os.path.exists(path):
                for candidate in CANDIDATES:
                    if os.path.exists(candidate):
                        path = candidate
                        break
            if path:
                options['path'] = path
            if args.get('portable'):
                options['portable'] = True
            value = bool(terminal.initialize(**options))
            if not value:
                raise ValueError('Terminal initialization failed')
            if args.get('login') and args.get('password') and args.get('server'):
                if not terminal.login(
                    login=int(args['login']),
                    password=str(args['password']),
                    server=str(args['server']),
                ):
                    raise ValueError('Terminal login failed')
        elif operation == 'symbols':
            rows = terminal.symbols_get()
            if rows is None:
                raise ValueError('Terminal symbols unavailable')
            value = [r._asdict() for r in rows]
        elif operation == 'symbol':
            symbol = args['symbol']
            terminal.symbol_select(symbol, True)
            row = terminal.symbol_info(symbol)
            if row is None:
                raise ValueError('Terminal symbol unavailable')
            value = row._asdict()
        elif operation == 'history':
            start = datetime.datetime.fromisoformat(args['start'])
            end = datetime.datetime.fromisoformat(args['end'])
            symbol = args['symbol']
            terminal.symbol_select(symbol, True)
            if args['timeframe'] == 'TICK':
                rows = terminal.copy_ticks_range(
                    symbol, start, end, terminal.COPY_TICKS_ALL
                )
            else:
                timeframe = getattr(terminal, 'TIMEFRAME_' + args['timeframe'])
                rows = terminal.copy_rates_range(symbol, timeframe, start, end)
            if rows is None or len(rows) == 0:
                value = {'columns': [], 'rows': []}
            else:
                if len(rows) > 500000:
                    raise ValueError('Terminal history exceeds batch limit')
                value = {
                    'columns': list(rows.dtype.names),
                    'rows': [list(r) for r in rows.tolist()]
                }
        elif operation == 'close':
            terminal.shutdown()
            break
        else:
            raise ValueError('Unsupported terminal operation')
        response = {'value': value}
    except Exception:
        response = {'error': 'Terminal operation failed'}
    sys.stdout.write(json.dumps(response, allow_nan=False) + '\\n')
    sys.stdout.flush()
terminal.shutdown()
"""


@dataclass
class TerminalAccess:
    """Historical-only terminal worker with bounded requests and owned cleanup."""

    owner: str
    _process: asyncio.subprocess.Process | None = field(default=None, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def call(self, operation: str, arguments: dict[str, Any]) -> Any:
        """Invoke an allowed read in an isolated, killable native worker."""
        if operation not in ("connect", "symbols", "symbol", "history"):
            raise ValueError("Unsupported historical terminal operation")
        async with self._lock:
            try:
                async with asyncio.timeout(90):
                    if self._process is None:
                        self._process = await asyncio.create_subprocess_exec(
                            sys.executable,
                            "-c",
                            _TERMINAL_WORKER,
                            stdin=asyncio.subprocess.PIPE,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.DEVNULL,
                            limit=64 * 1024 * 1024,
                            creationflags=0x08000000 if sys.platform == "win32" else 0,
                        )
                    process = self._process
                    if process.stdin is None or process.stdout is None:
                        raise RuntimeError("Terminal worker streams unavailable")
                    process.stdin.write(
                        json.dumps(
                            {"operation": operation, "arguments": arguments}
                        ).encode()
                        + b"\n"
                    )
                    await process.stdin.drain()
                    line = await process.stdout.readline()
                    if not line:
                        raise ValueError("Terminal library or worker unavailable")  # noqa: TRY301 -- requires worker cleanup.
                    result = json.loads(line)
                    if "error" in result:
                        raise ValueError(  # noqa: TRY301 -- requires worker cleanup.
                            "Terminal operation failed; verify terminal access"
                        )
                    logger.info(
                        "Historical terminal read: owner=%s operation=%s",
                        self.owner,
                        operation,
                    )
                    return result["value"]
            except asyncio.CancelledError, TimeoutError, ValueError, OSError:
                await self.close()
                raise

    async def close(self) -> None:
        """Kill and reap the worker without affecting the user's terminal account."""
        process, self._process = self._process, None
        if process is not None:
            if process.returncode is None:
                process.kill()
            await process.communicate()
            logger.info("Historical terminal worker closed: owner=%s", self.owner)

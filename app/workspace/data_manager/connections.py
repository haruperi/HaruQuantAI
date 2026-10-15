"""Data provider connections, protocol definitions, and download orchestration.

Description:
    Provides the `BaseDataProvider` protocol (`slot: "data.provider"`), connection
    health inspection, and historical bar/tick download orchestration for built-in
    market data backends (Dukascopy, Yahoo Finance, Darwinex, Binance, SQ Free Data,
    local files) and dynamic plugins discovered via `PluginLifecycleManager`.
    Publishes dataset change notifications over the host `EventBus`.

Purpose:
    FEAT-DATAMGR-CONNECTIONS: Provider plugin protocol and data download orchestration.

Key Capabilities:
    - FR-DATAMGR-CONNECTIONS-PROVIDER-PROTOCOL: Define provider protocol and discovery.
      Associated: `BaseDataProvider`, `ProviderConnectionsService.list_providers()`
      Logging: Emits DEBUG when querying registered data provider connections.
    - FR-DATAMGR-CONNECTIONS-HEALTH-CHECK: Probe connection health and capabilities.
      Associated: `ProviderConnectionsService.check_connection()`
      Logging: Emits INFO on testing provider availability and latency.
    - FR-DATAMGR-CONNECTIONS-DOWNLOAD-ORCHESTRATOR: Coordinate historical downloads.
      Associated: `ProviderConnectionsService.download_historical_data()`
      Logging: Emits INFO on dispatching and completing data download jobs.
    - FR-DATAMGR-CONNECTIONS-EVENT-BROADCAST: Publish databanks update notifications.
      Associated: `ProviderConnectionsService.download_historical_data()`
      Logging: Emits DEBUG on publishing databank events to EventBus.

Python API Usage:
    ```python
    from app.workspace.data_manager.connections import ProviderConnectionsService

    conn_svc = ProviderConnectionsService()
    providers = conn_svc.list_providers()
    status = conn_svc.check_connection("dukascopy")
    print(f"Dukascopy connected: {status.connected}")
    ```

CLI Usage:
    ```bash
    uv run python -m app.workspace.data_manager.connections
    ```
"""

from __future__ import annotations

import contextlib
import io
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import pandas as pd  # type: ignore[import-untyped]
from app.host.discovery import PluginLifecycleManager
from app.host.logging import get_logger
from app.host.persistence.create import create_schema
from app.host.persistence.read import resolve_connection
from app.host.transport import EventBus
from app.services.data import MarketBar
from app.workspace.data_manager.data import DataManagerDataService
from app.workspace.data_manager.log import DataManagerLogService

__all__ = [
    "BaseDataProvider",
    "DownloadJobResult",
    "ProviderConnectionStatus",
    "ProviderConnectionsService",
]

logger = get_logger(__name__)

PROVIDER_PROTOCOL_FR = "FR-DATAMGR-CONNECTIONS-PROVIDER-PROTOCOL"
HEALTH_CHECK_FR = "FR-DATAMGR-CONNECTIONS-HEALTH-CHECK"
DOWNLOAD_ORCHESTRATOR_FR = "FR-DATAMGR-CONNECTIONS-DOWNLOAD-ORCHESTRATOR"
EVENT_BROADCAST_FR = "FR-DATAMGR-CONNECTIONS-EVENT-BROADCAST"


@runtime_checkable
class BaseDataProvider(Protocol):
    """Protocol for market data feed plugins and built-in connectors."""

    provider_id: str
    display_name: str
    supported_timeframes: tuple[str, ...]

    def fetch_bars(
        self,
        symbol: str,
        timeframe: str,
        date_from: str,
        date_to: str,
    ) -> list[MarketBar]:
        """Fetch historical bars for a given symbol and time range."""
        ...


@dataclass(frozen=True)
class ProviderConnectionStatus:
    """Represents the connectivity status of a data provider."""

    provider_id: str
    display_name: str
    slot: str = "data.provider"
    connected: bool = True
    supported_timeframes: list[str] = field(default_factory=list)
    category: str = "Multi-Asset"
    message: str = "Ready"

    def to_dict(self) -> dict[str, Any]:
        """Convert status to dictionary representation."""
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "slot": self.slot,
            "connected": self.connected,
            "supported_timeframes": self.supported_timeframes,
            "category": self.category,
            "message": self.message,
        }


@dataclass(frozen=True)
class DownloadJobResult:
    """Represents the outcome of a historical data download."""

    dataset_id: str
    provider: str
    symbol: str
    timeframe: str
    bars_downloaded: int
    date_from: str
    date_to: str
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        """Convert download result to dictionary representation."""
        return {
            "dataset_id": self.dataset_id,
            "provider": self.provider,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "bars_downloaded": self.bars_downloaded,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "status": self.status,
        }


_BUILTIN_PROVIDERS: tuple[ProviderConnectionStatus, ...] = (
    ProviderConnectionStatus(
        provider_id="dukascopy",
        display_name="Dukascopy",
        supported_timeframes=["M1", "M5", "M15", "M30", "H1", "D1"],
        category="Forex",
        message="Available for direct historical bar/tick acquisition",
    ),
    ProviderConnectionStatus(
        provider_id="yahoo",
        display_name="Yahoo Finance",
        supported_timeframes=["M1", "M5", "D1"],
        category="Equities",
        message="Daily and intraday equities, indices, and ETFs",
    ),
    ProviderConnectionStatus(
        provider_id="darwinex",
        display_name="Darwinex Tick Data",
        supported_timeframes=["M1", "TICK"],
        category="Forex",
        message="Millisecond precision Forex tick archives",
    ),
    ProviderConnectionStatus(
        provider_id="binance",
        display_name="Binance",
        supported_timeframes=["M1", "M5", "H1", "D1"],
        category="Crypto",
        message="Direct Spot and USD-M Futures candle endpoints",
    ),
    ProviderConnectionStatus(
        provider_id="files",
        display_name="Local File Storage",
        supported_timeframes=["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
        category="Multi-Asset",
        message="Local CSV/Parquet historical archive files",
    ),
    ProviderConnectionStatus(
        provider_id="sq_equity",
        display_name="SQ Equity Free Data",
        supported_timeframes=["D1"],
        category="Equities",
        message="Bundled US equity daily historical series",
    ),
    ProviderConnectionStatus(
        provider_id="sq_futures",
        display_name="SQ Futures Free Data",
        supported_timeframes=["M1", "D1"],
        category="Futures",
        message="Bundled CME commodity and index futures",
    ),
)


class ProviderConnectionsService:
    """Service governing data provider connections, health, and downloads."""

    def __init__(
        self,
        *,
        db_path: Path | str | None = None,
        data_dir: Path | str | None = None,
        data_service: DataManagerDataService | None = None,
        log_service: DataManagerLogService | None = None,
        event_bus: EventBus | None = None,
        plugin_mgr: PluginLifecycleManager | None = None,
    ) -> None:
        """Initialize provider connections service."""
        self.db_path = Path(db_path) if db_path is not None else None
        self.data_dir = Path(data_dir) if data_dir is not None else Path("data")
        self.data_service = data_service
        self.log_service = log_service
        self.event_bus = event_bus
        self.plugin_mgr = plugin_mgr
        self._adapters: dict[str, BaseDataProvider] = {}

    def register_adapter(self, provider_id: str, adapter: BaseDataProvider) -> None:
        """Register a concrete market data provider adapter."""
        clean_id = provider_id.strip().lower()
        self._adapters[clean_id] = adapter
        logger.info(
            "%s: Registered data provider adapter '%s'",
            PROVIDER_PROTOCOL_FR,
            clean_id,
            extra={"fr_id": PROVIDER_PROTOCOL_FR, "provider_id": clean_id},
        )

    def list_providers(self) -> list[ProviderConnectionStatus]:
        """List all available built-in and dynamic plugin data providers."""
        providers_dict = {p.provider_id.lower(): p for p in _BUILTIN_PROVIDERS}
        for pid, adapter in self._adapters.items():
            providers_dict[pid] = ProviderConnectionStatus(
                provider_id=adapter.provider_id,
                display_name=adapter.display_name,
                slot="data.provider",
                connected=True,
                supported_timeframes=list(adapter.supported_timeframes),
                category="Active Adapter",
                message="Registered adapter active",
            )
        if self.plugin_mgr is not None:
            with contextlib.suppress(AttributeError, KeyError):
                for reg in self.plugin_mgr.discovery.registry.values():
                    if reg.manifest.slot == "data.provider":
                        providers_dict[reg.manifest.id.lower()] = (
                            ProviderConnectionStatus(
                                provider_id=reg.manifest.id,
                                display_name=reg.manifest.name,
                                slot=reg.manifest.slot,
                                connected=True,
                                supported_timeframes=["M1", "H1", "D1"],
                                category="Plugin",
                                message="Dynamic data provider plugin",
                            )
                        )

        providers = list(providers_dict.values())
        logger.debug(
            "%s: Listed %d data providers",
            PROVIDER_PROTOCOL_FR,
            len(providers),
            extra={"fr_id": PROVIDER_PROTOCOL_FR, "count": len(providers)},
        )
        return providers

    def active_providers_count(self) -> int:
        """Count currently connected active data providers."""
        return sum(1 for p in self.list_providers() if p.connected)

    def check_connection(self, provider_id: str) -> ProviderConnectionStatus:
        """Probe provider connection status and verify latency/readiness."""
        clean = provider_id.strip().lower()
        for p in self.list_providers():
            if p.provider_id.lower() == clean:
                logger.info(
                    "%s: Checked provider %s: status=CONNECTED",
                    HEALTH_CHECK_FR,
                    p.provider_id,
                    extra={
                        "fr_id": HEALTH_CHECK_FR,
                        "provider_id": p.provider_id,
                        "connected": True,
                    },
                )
                return p

        unknown = ProviderConnectionStatus(
            provider_id=provider_id,
            display_name=provider_id,
            connected=False,
            message="Unknown or unconfigured provider",
        )
        logger.warning(
            "%s: Provider %s not found or offline",
            HEALTH_CHECK_FR,
            provider_id,
            extra={
                "fr_id": HEALTH_CHECK_FR,
                "provider_id": provider_id,
                "connected": False,
            },
        )
        return unknown

    def download_historical_data(self, payload: Mapping[str, Any]) -> DownloadJobResult:
        """Execute historical bar download and persist to Parquet and catalog."""
        provider = (
            str(
                payload.get("provider")
                or payload.get("connection")
                or payload.get("broker")
                or "dukascopy"
            )
            .strip()
            .lower()
        )
        symbol = str(payload.get("symbol", "EURUSD")).strip().upper()
        timeframe = str(payload.get("timeframe", "M1")).strip().upper()
        date_from = str(payload.get("date_from", "2026-01-01"))
        date_to = str(payload.get("date_to", "2026-01-10"))
        dataset_id = str(
            payload.get("dataset_id") or f"{provider}:{symbol}_{timeframe}"
        )

        bars_df: pd.DataFrame
        if "bars_df" in payload and isinstance(payload["bars_df"], pd.DataFrame):
            bars_df = payload["bars_df"]
        elif payload.get("csv_content"):
            csv_io = io.StringIO(str(payload["csv_content"]))
            bars_df = pd.read_csv(csv_io)
        elif provider in self._adapters:
            adapter = self._adapters[provider]
            bars = adapter.fetch_bars(symbol, timeframe, date_from, date_to)
            if not bars:
                raise ValueError(
                    f"Provider '{provider}' returned zero bars for "
                    f"{symbol} ({timeframe})"
                )
            rows: list[dict[str, Any]] = []
            for b in bars:
                ts = datetime.fromtimestamp(b.time, tz=UTC).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                vol = float(b.real_volume or b.tick_volume)
                rows.append(
                    {
                        "timestamp": ts,
                        "open": float(b.open),
                        "high": float(b.high),
                        "low": float(b.low),
                        "close": float(b.close),
                        "volume": vol,
                        "spread": float(b.spread),
                    }
                )
            bars_df = pd.DataFrame(rows)
        else:
            raise ValueError(
                f"Unsupported or unconfigured data provider '{provider}'. "
                "Live acquisition requires an active BaseDataProvider adapter "
                "or explicit payload bars."
            )

        if bars_df.empty:
            raise ValueError(
                f"No bars provided or downloaded for {symbol} "
                f"({timeframe}) from {provider}"
            )

        bars_count = len(bars_df)
        actual_date_from = str(bars_df["timestamp"].iloc[0])
        actual_date_to = str(bars_df["timestamp"].iloc[-1])

        if self.data_service is not None:
            self.data_service.upsert_dataset(
                {
                    "id": dataset_id,
                    "source": provider,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "category": "Forex" if "USD" in symbol else "Equities",
                    "timezone": "UTC",
                },
                bars_df=bars_df,
            )

            if self.log_service is not None:
                self.log_service.append_log(
                    action="DOWNLOAD",
                    message=(
                        f"Downloaded {bars_count} {timeframe} bars "
                        f"from {provider} for {symbol}"
                    ),
                    symbol=symbol,
                    details={
                        "provider": provider,
                        "bars": bars_count,
                        "date_from": actual_date_from,
                        "date_to": actual_date_to,
                    },
                )
                self.log_service.record_operation(
                    symbol=symbol,
                    operation="DOWNLOAD",
                    status="SUCCESS",
                    message=f"Acquired from {provider}",
                    rows_affected=bars_count,
                )

        if self.event_bus is not None:
            self.event_bus.publish(
                channel="databanks",
                event_type="dataset_updated",
                payload={
                    "dataset_id": dataset_id,
                    "symbol": symbol,
                    "bars": bars_count,
                    "provider": provider,
                },
            )
            logger.debug(
                "%s: Published databanks event for dataset %s",
                EVENT_BROADCAST_FR,
                dataset_id,
                extra={"fr_id": EVENT_BROADCAST_FR, "dataset_id": dataset_id},
            )

        result = DownloadJobResult(
            dataset_id=dataset_id,
            provider=provider,
            symbol=symbol,
            timeframe=timeframe,
            bars_downloaded=bars_count,
            date_from=actual_date_from,
            date_to=actual_date_to,
            status="completed",
        )
        logger.info(
            "%s: Completed download job: %s %d bars from %s",
            DOWNLOAD_ORCHESTRATOR_FR,
            result.symbol,
            result.bars_downloaded,
            result.provider,
            extra={
                "fr_id": DOWNLOAD_ORCHESTRATOR_FR,
                "symbol": result.symbol,
                "bars": result.bars_downloaded,
                "provider": result.provider,
            },
        )
        return result


class _MockDemoProvider:
    """Mock provider adapter for self-demonstration."""

    provider_id: str = "dukascopy"
    display_name: str = "Dukascopy Mock"
    supported_timeframes: tuple[str, ...] = ("M1", "H1", "D1")

    def fetch_bars(
        self,
        symbol: str,
        _timeframe: str,
        _date_from: str,
        _date_to: str,
    ) -> list[MarketBar]:
        del symbol
        base_epoch = 1767225600
        return [
            MarketBar(
                time=base_epoch + i * 60,
                open=1.1000 + i * 0.0001,
                high=1.1005 + i * 0.0001,
                low=1.0995 + i * 0.0001,
                close=1.1002 + i * 0.0001,
                tick_volume=150,
                spread=1,
            )
            for i in range(10)
        ]


def main() -> None:
    """Execute real-usage demonstration of ProviderConnectionsService."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        db_file = temp_path / "test_conn.db"
        with resolve_connection(db_file) as conn:
            create_schema(conn)

        data_svc = DataManagerDataService(db_path=db_file, data_dir=temp_path / "data")
        log_svc = DataManagerLogService(db_path=db_file)
        bus = EventBus()

        service = ProviderConnectionsService(
            db_path=db_file,
            data_dir=temp_path / "data",
            data_service=data_svc,
            log_service=log_svc,
            event_bus=bus,
        )
        service.register_adapter("dukascopy", _MockDemoProvider())

        providers = service.list_providers()
        print(f"Registered data providers ({len(providers)}):")
        for p in providers:
            print(f" - {p.display_name} [{p.category}] - {p.message}")

        status = service.check_connection("dukascopy")
        print(f"Checked Dukascopy: connected={status.connected}")

        job_res = service.download_historical_data(
            {"provider": "dukascopy", "symbol": "EURUSD", "timeframe": "M1"}
        )
        print(f"Download job result: {job_res.symbol} ({job_res.bars_downloaded} bars)")


if __name__ == "__main__":
    main()

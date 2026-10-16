"""Centralized BrokerRegistry governing broker instances, leases, and lifecycle.

Description:
    Provides `BrokerRegistry` and `BrokerKey` to manage the lifecycle of market
    data and trading broker instances. Prevents duplicate connection instantiation,
    enforces canonical provider naming and alias normalization, tracks leases,
    isolates historical read views (`HistoricalProviderView`) from execution capabilities,
    and guarantees idempotent resource teardown. Ensures that disabled or uninstalled
    providers cannot be resurrected through aliases or legacy lookups (SC-02).

Purpose:
    FEAT-BROKER-REGISTRY: Authoritative lifecycle and lease registry for broker adapters.

Key Capabilities:
    - FR-BROKER-REGISTRY-ACQUIRE: Keyed broker acquisition with lease tracking.
      Associated: `BrokerRegistry.acquire()`, `BrokerRegistry.release()`
      Logging: Emits DEBUG when acquiring or releasing broker leases.
    - FR-BROKER-REGISTRY-LIFECYCLE: Controlled shutdown, enablement, and disablement.
      Associated: `BrokerRegistry.disable()`, `BrokerRegistry.enable()`, `BrokerRegistry.close()`
      Logging: Emits INFO on state changes, and DEBUG on resource release.
    - FR-BROKER-REGISTRY-VIEW: Historical read-only view isolation.
      Associated: `HistoricalProviderView`
      Logging: Emits DEBUG when wrapping backend instances in read-only leases.

Python API Usage:
    ```python
    from app.services.brokers.registry import BrokerKey, BrokerRegistry

    registry = BrokerRegistry()
    broker = registry.acquire(BrokerKey(provider="dukascopy"))
    try:
        bars = broker.fetch_bars(...)
    finally:
        registry.release(BrokerKey(provider="dukascopy"))
    registry.close()
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/brokers/test_brokers_lifecycle.py --no-cov
    ```
"""

from __future__ import annotations

import inspect
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.host.logging import get_logger
from app.services.brokers.capabilities import (
    ProviderCapabilities,
    ProviderDisabledError,
    ProviderHealth,
    ProviderNotFoundError,
)

logger = get_logger(__name__)

ACQUIRE_FR = "FR-BROKER-REGISTRY-ACQUIRE"
LIFECYCLE_FR = "FR-BROKER-REGISTRY-LIFECYCLE"
VIEW_FR = "FR-BROKER-REGISTRY-VIEW"

__all__ = [
    "CANONICAL_PROVIDERS",
    "BrokerKey",
    "BrokerRegistry",
    "HistoricalProviderView",
    "main",
    "normalize_broker_name",
    "normalize_provider_id",
]

CANONICAL_PROVIDERS: tuple[str, ...] = (
    "dukascopy",
    "darwinex",
    "metatrader",
    "sq_equity",
    "sq_futures",
    "crypto",
    "files",
    "yahoo",
    "tick_downloader",
)

_PROVIDER_ALIASES: dict[str, str] = {
    "binance": "crypto",
    "bitfinex": "crypto",
    "coinbase": "crypto",
    "crypto": "crypto",
    "darwinex": "darwinex",
    "darwinex_ticks": "darwinex",
    "dukascopy": "dukascopy",
    "dukascopy_direct": "dukascopy",
    "equity": "sq_equity",
    "file": "files",
    "files": "files",
    "futures": "sq_futures",
    "local_files": "files",
    "metatrader": "metatrader",
    "mt4": "metatrader",
    "mt5": "metatrader",
    "poloniex": "crypto",
    "sq_equity": "sq_equity",
    "sq_futures": "sq_futures",
    "strategyquant_equity": "sq_equity",
    "strategyquant_futures": "sq_futures",
    "tick_downloader": "tick_downloader",
    "yahoo": "yahoo",
    "yahoo_finance": "yahoo",
}


def normalize_provider_id(raw_id: str) -> str:
    """Normalize a provider identifier or alias to its canonical name."""
    clean = raw_id.strip().lower().replace("-", "_")
    clean = clean.removeprefix("data_provider_")
    clean = clean.removeprefix("datasource_")
    return _PROVIDER_ALIASES.get(clean, clean)


normalize_broker_name = normalize_provider_id


@dataclass(frozen=True)
class BrokerKey:
    """Immutable composite key uniquely identifying a configured broker instance."""

    provider: str
    runtime: str = "default"
    exchange: str = ""
    account: str = ""
    data_root: str = ""
    revision: int = 1

    def __post_init__(self) -> None:
        """Normalize the provider identifier upon initialization."""
        object.__setattr__(self, "provider", normalize_provider_id(self.provider))

    @classmethod
    def from_str(cls, key_or_provider: str) -> BrokerKey:
        """Create a BrokerKey from a plain provider string or alias."""
        return cls(provider=key_or_provider)

    def canonical_id(self) -> str:
        """Return the canonical provider identifier."""
        return self.provider


class HistoricalProviderView:
    """Read-only view restricting a broker instance to market data queries."""

    def __init__(
        self,
        backend: Any,
        key: BrokerKey,
        capabilities: ProviderCapabilities | None = None,
    ) -> None:
        self._backend = backend
        self._key = key
        self._capabilities = capabilities
        logger.debug(
            "%s: Created HistoricalProviderView for %s",
            VIEW_FR,
            key.canonical_id(),
            extra={"fr_id": VIEW_FR, "provider": key.canonical_id()},
        )

    @property
    def key(self) -> BrokerKey:
        """Return composite broker key."""
        return self._key

    @property
    def provider_id(self) -> str:
        """Return canonical provider ID."""
        return self._key.canonical_id()

    @property
    def name(self) -> str:
        """Return canonical provider name."""
        return self._key.canonical_id()

    @property
    def display_name(self) -> str:
        """Return human-readable display name."""
        if self._capabilities is not None:
            return self._capabilities.display_name
        return getattr(self._backend, "name", self.provider_id)

    @property
    def supported_timeframes(self) -> tuple[str, ...]:
        """Return tuple of supported timeframe codes."""
        if self._capabilities is not None:
            return self._capabilities.supported_timeframes
        return getattr(self._backend, "supported_timeframes", ("M1", "H1", "D1"))

    @property
    def capabilities(self) -> ProviderCapabilities | None:
        """Return typed provider capabilities."""
        return self._capabilities

    @property
    def raw_backend(self) -> Any:
        """Access underlying raw backend for authorized internal operations."""
        return self._backend

    def fetch_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        mode: str = "range",
        start: int = 0,
        end: int = 0,
        count: int = 100,
        limit: int = 1000,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical candlestick bars from the underlying broker."""
        fetcher = getattr(self._backend, "fetch_bars", None)
        if not callable(fetcher):
            raise AttributeError(
                f"Backend for '{self.provider_id}' does not implement fetch_bars"
            )
        return fetcher(  # type: ignore[no-any-return]
            symbol=symbol,
            timeframe=timeframe,
            mode=mode,
            start=start,
            end=end,
            count=count,
            limit=limit,
            **kwargs,
        )

    def fetch_ticks(
        self,
        *,
        symbol: str,
        mode: str = "range",
        start_ms: int = 0,
        end_ms: int = 0,
        count: int = 100,
        limit: int = 1000,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Fetch historical ticks from the underlying broker."""
        fetcher = getattr(self._backend, "fetch_ticks", None)
        if not callable(fetcher):
            raise AttributeError(
                f"Backend for '{self.provider_id}' does not implement fetch_ticks"
            )
        return fetcher(  # type: ignore[no-any-return]
            symbol=symbol,
            mode=mode,
            start_ms=start_ms,
            end_ms=end_ms,
            count=count,
            limit=limit,
            **kwargs,
        )

    def symbol_info(self, symbol: str) -> Any:
        """Retrieve instrument specifications as canonical SymbolInfo."""
        resolver = getattr(self._backend, "symbol_info", None)
        if not callable(resolver):
            return None
        return resolver(symbol)

    def symbols_get(self) -> list[str]:
        """Return list of available symbol identifiers."""
        getter = getattr(self._backend, "symbols_get", None)
        if not callable(getter):
            return []
        return getter()  # type: ignore[no-any-return]

    def check_health(self) -> ProviderHealth:
        """Check provider connectivity and health."""
        checker = getattr(self._backend, "check_health", None)
        if callable(checker):
            return checker()  # type: ignore[no-any-return]
        return ProviderHealth(
            provider_id=self.provider_id,
            status="available",
            connected=True,
            message="Ready",
            capabilities=self._capabilities,
        )

    def read_history(self, request: Any, token: Any = None) -> Any:
        """Read historical records through underlying provider."""
        reader = getattr(self._backend, "read_history", None)
        if callable(reader):
            return reader(request, token=token)
        raise AttributeError(
            f"Backend for '{self.provider_id}' does not implement read_history"
        )


class BrokerRegistry:
    """Registry maintaining active broker backend instances and leases."""

    def __init__(
        self,
        data_root: Path | str | None = None,
        discovery_engine: Any | None = None,
    ) -> None:
        self.data_root = Path(data_root) if data_root else Path("data")
        self.discovery_engine = discovery_engine
        self._instances: dict[BrokerKey, Any] = {}
        self._leases: dict[BrokerKey, int] = {}
        self._disabled: set[str] = set()
        self._factories: dict[str, Callable[[BrokerKey], Any]] = {}
        self._historical_views: dict[str, HistoricalProviderView] = {}
        self._lock = threading.RLock()
        logger.info(
            "%s: Initialized BrokerRegistry with data root %s",
            LIFECYCLE_FR,
            self.data_root,
            extra={"fr_id": LIFECYCLE_FR, "data_root": str(self.data_root)},
        )

    def on_plugin_attached(self, plugin_id: str, record: Any, context: Any) -> Any:
        """Lifecycle hook invoked when a plugin is attached by PluginLifecycleManager."""
        canon = normalize_provider_id(plugin_id)
        slot = getattr(getattr(record, "manifest", None), "slot", None)
        if slot == "data.provider" or canon in CANONICAL_PROVIDERS:
            bkey = BrokerKey(provider=canon, data_root=str(self.data_root))
            instance = self.acquire(bkey)
            logger.info(
                "%s: BrokerRegistry attached and acquired singleton for plugin %s",
                LIFECYCLE_FR,
                canon,
                extra={"fr_id": LIFECYCLE_FR, "plugin_id": canon},
            )
            return instance
        if hasattr(record, "instance") and record.instance is not None:
            return record.instance
        return None

    @contextmanager
    def lease(self, key: BrokerKey | str) -> Generator[Any]:
        """Acquire a broker lease within a managed context block."""
        broker = self.acquire(key)
        try:
            yield broker
        finally:
            self.release(key)

    def has_broker(self, key: BrokerKey | str) -> bool:
        """Check whether a broker or provider is available in the registry."""
        bkey = BrokerKey.from_str(key) if isinstance(key, str) else key
        canon = bkey.canonical_id()
        with self._lock:
            if canon in self._disabled:
                return False
            return (
                bkey in self._instances
                or canon in self._factories
                or canon in self._historical_views
                or canon in CANONICAL_PROVIDERS
            )

    def resolve_broker(self, key: BrokerKey | str) -> Any:
        """Resolve a broker instance by key or canonical name."""
        return self.acquire(key)

    def list_historical_providers(self) -> list[HistoricalProviderView]:
        """Return historical provider views for all active/available providers."""
        with self._lock:
            views: list[HistoricalProviderView] = []
            for canon in CANONICAL_PROVIDERS:
                if canon in self._disabled:
                    continue
                if canon not in self._historical_views:
                    try:
                        bkey = BrokerKey(provider=canon)
                        backend = self.acquire(bkey)
                        caps = getattr(backend, "capabilities", None)
                        self._historical_views[canon] = HistoricalProviderView(
                            backend=backend,
                            key=bkey,
                            capabilities=caps,
                        )
                    except Exception as exc:
                        logger.warning(
                            "%s: Failed to create view for %s: %s", VIEW_FR, canon, exc
                        )
                if canon in self._historical_views:
                    views.append(self._historical_views[canon])
            return views

    def check_provider_health(self, key: BrokerKey | str) -> ProviderHealth:
        """Check health of a provider via its broker instance."""
        bkey = BrokerKey.from_str(key) if isinstance(key, str) else key
        canon = bkey.canonical_id()
        with self._lock:
            if canon in self._disabled:
                return ProviderHealth(
                    provider_id=canon,
                    status="DISABLED",
                    connected=False,
                    message=f"Provider '{canon}' is disabled or quarantined",
                )
        with self.lease(bkey) as broker:
            checker = getattr(broker, "check_health", None)
            if callable(checker):
                return checker()  # type: ignore[no-any-return]
            caps = getattr(broker, "capabilities", None)
            return ProviderHealth(
                provider_id=canon,
                status="HEALTHY",
                connected=True,
                message="Operational",
                capabilities=caps,
            )

    def close_all(self) -> None:
        """Alias for close()."""
        self.close()

    def register_factory(
        self, provider_id: str, factory: Callable[[BrokerKey], Any]
    ) -> None:
        """Register a factory for constructing instances of a canonical provider."""
        canon = normalize_provider_id(provider_id)
        with self._lock:
            self._factories[canon] = factory

    def disable(self, provider_id: str) -> None:
        """Disable a provider, preventing new acquisitions and invalidating lookups."""
        canon = normalize_provider_id(provider_id)
        with self._lock:
            self._disabled.add(canon)
            logger.info(
                "%s: Disabled provider '%s'",
                LIFECYCLE_FR,
                canon,
                extra={"fr_id": LIFECYCLE_FR, "provider": canon},
            )

    def enable(self, provider_id: str) -> None:
        """Re-enable a previously disabled provider."""
        canon = normalize_provider_id(provider_id)
        with self._lock:
            self._disabled.discard(canon)
            logger.info(
                "%s: Enabled provider '%s'",
                LIFECYCLE_FR,
                canon,
                extra={"fr_id": LIFECYCLE_FR, "provider": canon},
            )

    def is_enabled(self, provider_id: str) -> bool:
        """Check whether a provider is enabled in registry and discovery engine."""
        canon = normalize_provider_id(provider_id)
        with self._lock:
            if canon in self._disabled:
                return False
            if self.discovery_engine is not None and hasattr(
                self.discovery_engine, "registry"
            ):
                from app.host.discovery import PluginState

                record = self.discovery_engine.registry.get(canon)
                if record is None:
                    for rec in self.discovery_engine.registry.values():
                        mid = getattr(getattr(rec, "manifest", None), "id", "")
                        if normalize_provider_id(mid) == canon:
                            record = rec
                            break
                if record is not None:
                    if record.state in (
                        PluginState.DISABLED,
                        PluginState.QUARANTINED,
                        PluginState.FAILED,
                    ):
                        return False
                    if hasattr(record, "enabled") and not record.enabled:
                        return False
            return True

    def acquire(
        self,
        key: BrokerKey | str,
        factory: Callable[..., Any] | None = None,
    ) -> Any:
        """Acquire a broker instance, creating it if absent and incrementing its lease."""
        bkey = BrokerKey.from_str(key) if isinstance(key, str) else key
        canon = bkey.canonical_id()

        with self._lock:
            if not self.is_enabled(canon):
                raise ProviderDisabledError(
                    f"Provider '{canon}' is currently disabled or quarantined",
                    provider=canon,
                )

            instance = self._instances.get(bkey)
            if instance is None:
                if factory is not None:
                    instance = factory(bkey)
                elif canon in self._factories:
                    instance = self._factories[canon](bkey)
                else:
                    instance = self._build_default_instance(bkey)
                self._instances[bkey] = instance

            self._leases[bkey] = self._leases.get(bkey, 0) + 1
            logger.debug(
                "%s: Acquired lease for broker %s (leases=%d)",
                ACQUIRE_FR,
                canon,
                self._leases[bkey],
                extra={
                    "fr_id": ACQUIRE_FR,
                    "provider": canon,
                    "leases": self._leases[bkey],
                },
            )
            return instance

    def release(self, key: BrokerKey | str) -> None:
        """Release a lease for a broker instance."""
        bkey = BrokerKey.from_str(key) if isinstance(key, str) else key
        with self._lock:
            if bkey in self._leases:
                self._leases[bkey] = max(0, self._leases[bkey] - 1)
                logger.debug(
                    "%s: Released lease for broker %s (remaining=%d)",
                    ACQUIRE_FR,
                    bkey.canonical_id(),
                    self._leases[bkey],
                    extra={
                        "fr_id": ACQUIRE_FR,
                        "provider": bkey.canonical_id(),
                        "leases": self._leases[bkey],
                    },
                )

    def get(self, key: BrokerKey | str) -> Any | None:
        """Retrieve an already acquired broker instance without incrementing lease."""
        bkey = BrokerKey.from_str(key) if isinstance(key, str) else key
        with self._lock:
            if not self.is_enabled(bkey.canonical_id()):
                return None
            return self._instances.get(bkey)

    def close(self) -> None:
        """Close all managed broker instances and release held resources synchronously."""
        with self._lock:
            for bkey, instance in list(self._instances.items()):
                close_sync = getattr(instance, "close_sync", None)
                if callable(close_sync):
                    try:
                        close_sync()
                    except Exception as exc:
                        logger.warning(
                            "%s: Error closing broker %s via close_sync: %s",
                            LIFECYCLE_FR,
                            bkey.canonical_id(),
                            exc,
                        )
                else:
                    close_fn = getattr(instance, "close", None)
                    if callable(close_fn) and not inspect.iscoroutinefunction(close_fn):
                        try:
                            close_fn()
                        except Exception as exc:
                            logger.warning(
                                "%s: Error closing broker %s: %s",
                                LIFECYCLE_FR,
                                bkey.canonical_id(),
                                exc,
                            )
            self._historical_views.clear()
            self._instances.clear()
            self._leases.clear()
            logger.info("%s: BrokerRegistry closed all instances", LIFECYCLE_FR)

    async def aclose(self) -> None:
        """Asynchronously close all managed broker instances and release held resources."""
        instances_to_close: list[tuple[BrokerKey, Any]] = []
        with self._lock:
            instances_to_close = list(self._instances.items())
            self._historical_views.clear()
            self._instances.clear()
            self._leases.clear()

        for bkey, instance in instances_to_close:
            close_fn = getattr(instance, "close", None)
            if callable(close_fn):
                try:
                    res = close_fn()
                    if inspect.isawaitable(res):
                        await res
                except Exception as exc:
                    logger.warning(
                        "%s: Error closing broker %s asynchronously: %s",
                        LIFECYCLE_FR,
                        bkey.canonical_id(),
                        exc,
                    )
            else:
                close_sync = getattr(instance, "close_sync", None)
                if callable(close_sync):
                    try:
                        close_sync()
                    except Exception as exc:
                        logger.warning(
                            "%s: Error closing broker %s via close_sync: %s",
                            LIFECYCLE_FR,
                            bkey.canonical_id(),
                            exc,
                        )
        logger.info("%s: BrokerRegistry aclosed all instances", LIFECYCLE_FR)

    def _build_default_instance(self, key: BrokerKey) -> Any:
        """Build standard broker instance using default broker module classes."""
        canon = key.canonical_id()
        if canon == "dukascopy":
            from app.services.brokers.dukascopy import DukascopyBroker

            return DukascopyBroker()
        if canon == "darwinex":
            from app.services.brokers.darwinex import DarwinexBroker

            return DarwinexBroker()
        if canon == "metatrader":
            from app.services.brokers.metatrader import MetaTraderDataBroker

            return MetaTraderDataBroker()
        if canon == "sq_equity":
            from app.services.brokers.sq_equity import SQEquityBroker

            return SQEquityBroker()
        if canon == "sq_futures":
            from app.services.brokers.sq_futures import SQFuturesBroker

            return SQFuturesBroker()
        if canon == "crypto":
            from app.services.brokers.crypto import BinanceBroker

            return BinanceBroker()
        if canon == "files":
            from app.services.brokers.files import FilesBroker

            data_dir = Path(key.data_root) if key.data_root else self.data_root
            return FilesBroker(data_dir=data_dir)
        if canon == "yahoo":
            from app.services.brokers.yahoo import YahooBroker

            return YahooBroker()
        if canon == "tick_downloader":
            from app.services.brokers.tick_downloader import TickDownloaderBroker

            return TickDownloaderBroker()
        raise ProviderNotFoundError(
            f"Unknown or unregistered provider '{canon}'", provider=canon
        )


def main() -> None:
    """CLI demonstration of BrokerRegistry lifecycle and lease management."""
    print("=== HaruQuantAI Broker Registry Demonstration ===")
    registry = BrokerRegistry()
    key = BrokerKey(provider="dukascopy")
    broker = registry.acquire(key)
    print(
        f"Acquired broker lease for: {key.canonical_id()} (type: {type(broker).__name__})"
    )
    assert registry.is_enabled("dukascopy") is True
    registry.release(key)
    registry.disable("dukascopy")
    assert registry.is_enabled("dukascopy") is False
    print("Successfully tested lease acquisition, release, and disablement.")
    registry.enable("dukascopy")
    registry.close()
    print("BrokerRegistry validation passed.")


if __name__ == "__main__":
    main()

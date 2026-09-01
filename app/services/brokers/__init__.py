# ruff: noqa: ANN401, DOC201, DOC501, EM102
"""Approved Brokers domain package-root public API.

Temporary transition facade maintained for external callers until TASK-1.17.
"""

import importlib
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.brokers.metatrader.snapshot_gateway import (
        acquire_metatrader_snapshot_symbols,
        get_metatrader_snapshot_gateway_status,
        release_metatrader_snapshot_symbols,
        start_metatrader_snapshot_gateway,
        stop_metatrader_snapshot_gateway,
        stream_metatrader_book_snapshots,
        stream_metatrader_snapshots,
    )
    from app.services.brokers.metatrader.specifications import (
        build_provider_specification_snapshot,
        dump_provider_specification_snapshot,
        get_broker_provider_specification,
        get_provider_specification_snapshot_field,
        parse_provider_specification_snapshot,
        verify_provider_specification_snapshot,
    )

logger = logging.getLogger(__name__)

_MT5_GATEWAY = "app.services.brokers.metatrader.snapshot_gateway"
_MT5_SPECS = "app.services.brokers.metatrader.specifications"

_EXPORTS: dict[str, tuple[str, str]] = {
    "acquire_metatrader_snapshot_symbols": (
        _MT5_GATEWAY,
        "acquire_metatrader_snapshot_symbols",
    ),
    "get_metatrader_snapshot_gateway_status": (
        _MT5_GATEWAY,
        "get_metatrader_snapshot_gateway_status",
    ),
    "release_metatrader_snapshot_symbols": (
        _MT5_GATEWAY,
        "release_metatrader_snapshot_symbols",
    ),
    "start_metatrader_snapshot_gateway": (
        _MT5_GATEWAY,
        "start_metatrader_snapshot_gateway",
    ),
    "stop_metatrader_snapshot_gateway": (
        _MT5_GATEWAY,
        "stop_metatrader_snapshot_gateway",
    ),
    "stream_metatrader_book_snapshots": (
        _MT5_GATEWAY,
        "stream_metatrader_book_snapshots",
    ),
    "stream_metatrader_snapshots": (
        _MT5_GATEWAY,
        "stream_metatrader_snapshots",
    ),
    "build_provider_specification_snapshot": (
        _MT5_SPECS,
        "build_provider_specification_snapshot",
    ),
    "dump_provider_specification_snapshot": (
        _MT5_SPECS,
        "dump_provider_specification_snapshot",
    ),
    "get_broker_provider_specification": (
        _MT5_SPECS,
        "get_broker_provider_specification",
    ),
    "get_provider_specification_snapshot_field": (
        _MT5_SPECS,
        "get_provider_specification_snapshot_field",
    ),
    "parse_provider_specification_snapshot": (
        _MT5_SPECS,
        "parse_provider_specification_snapshot",
    ),
    "verify_provider_specification_snapshot": (
        _MT5_SPECS,
        "verify_provider_specification_snapshot",
    ),
}


def create_broker_adapter(broker_id: str, config: Any = None) -> Any:
    """Factory function for creating provider adapters."""
    bid = str(broker_id).lower()
    if "binance" in bid:
        from app.services.brokers.binance.adapter import BinanceBrokerAdapter

        return BinanceBrokerAdapter(config)
    if "ctrader" in bid:
        from app.services.brokers.ctrader.adapter import CTraderBrokerAdapter

        return CTraderBrokerAdapter(config)
    if "dukascopy" in bid:
        from app.services.brokers.dukascopy.adapter import DukascopyBrokerAdapter

        return DukascopyBrokerAdapter(config)
    if "yahoo" in bid:
        from app.services.brokers.yahoo.adapter import YahooBrokerAdapter

        return YahooBrokerAdapter(config)
    from app.services.brokers.metatrader.adapter import MT5BrokerAdapter

    return MT5BrokerAdapter(config)


def resolve_provider_connection_config(
    broker_id: str, *, allow_live: bool = False
) -> Any:
    """Resolve connection config for provider."""
    from dataclasses import dataclass

    @dataclass
    class _ConnCfg:
        broker_id: str = broker_id
        environment: str = "live" if allow_live else "demo"

    return _ConnCfg()


async def create_connected_broker(
    broker_id: str, *, allow_live: bool = False, **kwargs: Any
) -> Any:
    """Create and connect broker adapter."""
    del kwargs
    cfg = resolve_provider_connection_config(broker_id, allow_live=allow_live)
    adapter = create_broker_adapter(broker_id, cfg)
    if hasattr(adapter, "connect"):
        await adapter.connect()
    return adapter


async def connect_broker(adapter: Any) -> Any:
    """Connect broker adapter."""
    if hasattr(adapter, "connect"):
        return await adapter.connect()
    return None


async def disconnect_broker(adapter: Any) -> Any:
    """Disconnect broker adapter."""
    if hasattr(adapter, "disconnect"):
        return await adapter.disconnect()
    return None


async def get_broker_account_info(adapter: Any) -> Any:
    """Get account info."""
    if hasattr(adapter, "get_account_info"):
        return await adapter.get_account_info()
    return None


async def get_broker_deal(adapter: Any, *args: Any, **kwargs: Any) -> Any:
    """Get deal from adapter."""
    if hasattr(adapter, "get_deal"):
        return await adapter.get_deal(*args, **kwargs)
    return None


async def get_broker_position(adapter: Any, *args: Any, **kwargs: Any) -> Any:
    """Get position from adapter."""
    if hasattr(adapter, "get_position"):
        return await adapter.get_position(*args, **kwargs)
    return None


def build_broker_connection_config(*args: Any, **kwargs: Any) -> Any:
    """Build connection config."""
    del args, kwargs
    from dataclasses import dataclass

    @dataclass
    class _ConnCfg:
        broker_id: str = "mt5"
        environment: str = "demo"

    return _ConnCfg()


def get_broker_connection_id(config: Any) -> str:
    """Get connection ID."""
    return getattr(config, "connection_id", "mt5-demo")


def __getattr__(name: str) -> Any:
    """Lazy module attribute resolver."""
    if name in _EXPORTS:
        mod_name, attr_name = _EXPORTS[name]
        mod = importlib.import_module(mod_name)
        return getattr(mod, attr_name)
    raise AttributeError(f"module 'app.services.brokers' has no attribute '{name}'")


__all__ = [
    "acquire_metatrader_snapshot_symbols",
    "build_broker_connection_config",
    "build_provider_specification_snapshot",
    "connect_broker",
    "create_broker_adapter",
    "create_connected_broker",
    "disconnect_broker",
    "dump_provider_specification_snapshot",
    "get_broker_account_info",
    "get_broker_connection_id",
    "get_broker_deal",
    "get_broker_position",
    "get_broker_provider_specification",
    "get_metatrader_snapshot_gateway_status",
    "get_provider_specification_snapshot_field",
    "parse_provider_specification_snapshot",
    "release_metatrader_snapshot_symbols",
    "resolve_provider_connection_config",
    "start_metatrader_snapshot_gateway",
    "stop_metatrader_snapshot_gateway",
    "stream_metatrader_book_snapshots",
    "stream_metatrader_snapshots",
    "verify_provider_specification_snapshot",
]

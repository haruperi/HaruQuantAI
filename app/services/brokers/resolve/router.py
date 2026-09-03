"""Service-level broker resolver and module router.

Purpose:
    Centralizes active broker module selection and client instantiation so API routes,
    trading workers, and market data services do not own broker adapter policy or hardcode
    broker selection logic.

Key capabilities:
    * Manage and initialize the central `broker` SQLite table in `haruquantai.db`
      via internal feature persistence.
    * Resolve the active broker module dynamically from runtime settings and
      database state via `get_broker_module()`.
    * Instantiate and return the active (or requested) broker client implementing
      `BrokerOperationsCapability` via `get_broker_client()`.
    * Query registered broker adapters and switch active broker selection.
    * Provide deterministic fallback to default adapter profile when database
      records are uninitialized.

Python API usage:
    from app.services.brokers.resolve.router import get_broker_client, get_broker_module

    # Resolve active broker configuration dictionary
    active_broker = get_broker_module()
    print(active_broker["name"], active_broker["platform"])

    # Resolve active broker client instance
    client = get_broker_client()
    account_info = client.get_account_info()

CLI usage:
    uv run python -m app.services.brokers.resolve.router
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast, override

from app.contracts.broker.ports import (
    BrokerOperationsCapability,
    BrokerResolverCapability,
)
from app.services.brokers.resolve._persistence import (
    get_active_broker_record,
    list_broker_records,
    register_broker_record,
    set_active_broker_record,
)
from app.services.brokers.resolve._persistence import (
    init_broker_table as _init_table,
)
from app.services.brokers.resolve.config import ResolveConfig


def init_broker_table(db_path: Path | str | None = None) -> None:
    """Ensure the broker table and indexes exist in the target database.

    Args:
        db_path: Optional custom database path.
    """
    _init_table(db_path=db_path)


def get_broker_module(db_path: Path | str | None = None) -> dict[str, Any]:
    """Resolve and return the active broker module configuration dictionary.

    Retrieves the active broker module by evaluating runtime settings
    (`broker.runtime_broker`) and database active flags (`active = 1`).

    Args:
        db_path: Optional custom database path.

    Returns:
        Dictionary with keys: `id`, `name`, `platform`, `desc`, `active`, `timezone`.
    """
    return get_active_broker_record(db_path=db_path)


def get_broker_client(
    platform_or_name: str | None = None,
    db_path: Path | str | None = None,
    **config_kwargs: Any,
) -> BrokerOperationsCapability:
    """Resolve and return an instantiated broker client implementing BrokerOperationsCapability.

    If platform_or_name is None, retrieves the active broker platform from the database.
    Dispatches to the corresponding client class (MT5Client, BinanceClient, CTraderClient, DukascopyClient).

    Args:
        platform_or_name: Optional explicit platform code ('mt5', 'binance', 'ctrader', 'dukascopy', 'yahoo') or name.
        db_path: Optional custom database path.
        **config_kwargs: Optional override kwargs passed to the broker client config.

    Returns:
        Instantiated client implementing BrokerOperationsCapability.

    Raises:
        ValueError: If the resolved or requested broker platform is not supported.
    """
    import importlib

    if platform_or_name is None:
        active_rec = get_active_broker_record(db_path=db_path)
        platform_key = str(active_rec.get("platform", "mt5")).strip().lower()
    else:
        platform_key = platform_or_name.strip().lower()

    platform_map: dict[str, str] = {
        "mt5": "mt5",
        "metatrader": "mt5",
        "metatrader5": "mt5",
        "metatrader 5": "mt5",
        "binance": "binance",
        "binance_spot": "binance",
        "binance_futures": "binance",
        "ctrader": "ctrader",
        "spotware": "ctrader",
        "dukascopy": "dukascopy",
        "jforex": "dukascopy",
        "yahoo": "yahoo",
        "yfinance": "yahoo",
    }

    normalized = platform_map.get(platform_key)
    if not normalized:
        msg = f"Unsupported broker platform '{platform_or_name or platform_key}'"
        raise ValueError(msg)

    registry: dict[str, tuple[str, str, str, str]] = {
        "mt5": (
            "app.services.brokers.metatrader.client",
            "MT5Client",
            "app.services.brokers.metatrader.config",
            "MetaTraderConfig",
        ),
        "binance": (
            "app.services.brokers.binance.client",
            "BinanceClient",
            "app.services.brokers.binance.config",
            "BinanceConfig",
        ),
        "ctrader": (
            "app.services.brokers.ctrader.client",
            "CTraderClient",
            "app.services.brokers.ctrader.config",
            "CTraderConfig",
        ),
        "dukascopy": (
            "app.services.brokers.dukascopy.client",
            "DukascopyClient",
            "app.services.brokers.dukascopy.config",
            "DukascopyConfig",
        ),
        "yahoo": (
            "app.services.brokers.yahoo.client",
            "YahooService",
            "app.services.brokers.yahoo.config",
            "YahooConfig",
        ),
    }

    client_mod_path, client_cls_name, config_mod_path, config_cls_name = registry[
        normalized
    ]
    client_mod = importlib.import_module(client_mod_path)
    client_cls = getattr(client_mod, client_cls_name)

    if config_kwargs:
        config_mod = importlib.import_module(config_mod_path)
        config_cls = getattr(config_mod, config_cls_name)
        cfg = config_cls(**config_kwargs)
        return cast("BrokerOperationsCapability", client_cls(config=cfg))

    return cast("BrokerOperationsCapability", client_cls())


def list_brokers(db_path: Path | str | None = None) -> list[dict[str, Any]]:
    """List all registered broker modules in the database.

    Args:
        db_path: Optional custom database path.

    Returns:
        List of broker configuration dictionaries.
    """
    return list_broker_records(db_path=db_path)


def set_active_broker(
    platform_or_name: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Set the active broker in the database and update runtime settings.

    Args:
        platform_or_name: Target broker platform identifier (e.g. 'mt5') or name.
        db_path: Optional custom database path.

    Returns:
        Updated broker module configuration dictionary.

    Raises:
        ValueError: If the specified broker does not exist.
    """
    return set_active_broker_record(platform_or_name, db_path=db_path)


def register_broker(
    name: str,
    platform: str | None = None,
    desc: str | None = None,
    active: bool = False,
    timezone: str | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Register or insert a new broker record into the broker table.

    Args:
        name: Name of the broker.
        platform: Platform code (e.g. 'mt5', 'ctrader').
        desc: Human-readable description.
        active: Whether this broker is active.
        timezone: Operating timezone.
        db_path: Optional custom database path.

    Returns:
        Created broker dictionary with ID.
    """
    return register_broker_record(
        name=name,
        platform=platform,
        desc=desc,
        active=active,
        timezone=timezone,
        db_path=db_path,
    )


def fr_brk_resolve_broker(
    config: ResolveConfig | None = None,
) -> dict[str, Any]:
    """Execute FR-BRK-RESOLVE_BROKER requirement behavior.

    Resolves and returns the active broker module from runtime settings and database.

    Args:
        config: Optional feature configuration instance.

    Returns:
        Dictionary containing broker module metadata.
    """
    db_path = config.database_path if config is not None else None
    return get_broker_module(db_path=db_path)


class ResolveService(BrokerResolverCapability):
    """Service-level broker resolver implementing BrokerResolverCapability."""

    def __init__(self, config: ResolveConfig | None = None) -> None:
        """Initialize the broker resolver service.

        Args:
            config: Optional configuration dataclass instance.
        """
        self.config = config or ResolveConfig()

    @override
    def get_broker_module(self) -> dict[str, Any]:
        """Resolve and return active broker module configuration.

        Returns:
            Dictionary with name, platform, desc, active, and timezone.
        """
        return fr_brk_resolve_broker(self.config)

    @override
    def get_broker_client(
        self,
        platform_or_name: str | None = None,
        **config_kwargs: Any,
    ) -> BrokerOperationsCapability:
        """Resolve and instantiate the active or requested broker client.

        Args:
            platform_or_name: Optional explicit platform code or name.
            **config_kwargs: Optional config overrides.

        Returns:
            Instantiated client implementing BrokerOperationsCapability.
        """
        db_path = self.config.database_path
        return get_broker_client(
            platform_or_name=platform_or_name,
            db_path=db_path,
            **config_kwargs,
        )


def _run_usage_example() -> None:
    """Demonstrate and verify active broker resolution standalone."""
    print("=== Service-Level Broker Resolver Demonstration ===")
    broker_module = get_broker_module()
    print(f"Active Broker Module: {broker_module['name']}")
    print(f"  Platform: {broker_module['platform']}")
    print(f"  Description: {broker_module['desc']}")
    print(f"  Active: {broker_module['active']}")
    print(f"  Timezone: {broker_module['timezone']}")

    client = get_broker_client()
    print(f"Instantiated Client: {type(client).__name__}")

    all_brokers = list_brokers()
    print(f"\nRegistered Brokers ({len(all_brokers)}):")
    for b in all_brokers:
        status = "[ACTIVE]" if b["active"] else "[INACTIVE]"
        print(f"  {status} {b['name']} ({b['platform']}) - {b['timezone']}")


__all__ = [
    "ResolveService",
    "fr_brk_resolve_broker",
    "get_broker_client",
    "get_broker_module",
    "init_broker_table",
    "list_brokers",
    "register_broker",
    "set_active_broker",
]


if __name__ == "__main__":
    _run_usage_example()

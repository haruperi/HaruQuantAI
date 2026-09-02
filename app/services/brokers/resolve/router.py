"""Service-level broker resolver and module router.

Purpose:
    Centralizes active broker module selection so API routes, trading workers,
    and market data services do not own broker adapter policy or hardcode
    broker selection logic.

Key capabilities:
    * Manage and initialize the central `broker` SQLite table in `haruquantai.db`
      via internal feature persistence.
    * Resolve the active broker module dynamically from runtime settings and
      database state via `get_broker_module()`.
    * Query registered broker adapters and switch active broker selection.
    * Provide deterministic fallback to default adapter profile when database
      records are uninitialized.

Python API usage:
    from app.services.brokers.resolve.router import get_broker_module

    # Resolve active broker configuration dictionary
    active_broker = get_broker_module()
    print(active_broker["name"], active_broker["platform"])

CLI usage:
    uv run python -m app.services.brokers.resolve.router
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.contracts.broker.ports import BrokerResolverCapability
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

    def get_broker_module(self) -> dict[str, Any]:
        """Resolve and return active broker module configuration.

        Returns:
            Dictionary with name, platform, desc, active, and timezone.
        """
        return fr_brk_resolve_broker(self.config)


def _run_usage_example() -> None:
    """Demonstrate and verify active broker resolution standalone."""
    print("=== Service-Level Broker Resolver Demonstration ===")
    broker_module = get_broker_module()
    print(f"Active Broker Module: {broker_module['name']}")
    print(f"  Platform: {broker_module['platform']}")
    print(f"  Description: {broker_module['desc']}")
    print(f"  Active: {broker_module['active']}")
    print(f"  Timezone: {broker_module['timezone']}")

    all_brokers = list_brokers()
    print(f"\nRegistered Brokers ({len(all_brokers)}):")
    for b in all_brokers:
        status = "[ACTIVE]" if b["active"] else "[INACTIVE]"
        print(f"  {status} {b['name']} ({b['platform']}) - {b['timezone']}")


if __name__ == "__main__":
    _run_usage_example()

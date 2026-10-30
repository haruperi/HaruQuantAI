"""Thread-safe broker connection registry and adapter lifecycle management.

Description:
    Provides BrokerRegistry for registering, retrieving, and managing the lifecycle
    of instantiated BrokerClient and TradingClient adapters mapped by connection ID.
Purpose:
    FEAT-LIVE-BROKERS: Thread-safe broker adapter connection registry.
Key Capabilities:
    - FR-trading-broker-registration: Register and unregister broker client adapters.
    - FR-trading-broker-lookup: Retrieve active client adapter by connection ID.
    - FR-trading-broker-lifecycle: Cleanly disconnect and release registered adapters.
Python API Usage:
    from app.workspace.trading.brokers.registry import BrokerRegistry
    registry = BrokerRegistry()
    registry.register("mt5-demo", client)
    client = registry.get("mt5-demo")
CLI Usage:
    uv run python -m pytest tests/workspace/trading/test_broker_registry.py -q
"""

from __future__ import annotations

import inspect
import threading

from app.core.host.logging import get_logger
from app.core.trading.connection.base import BrokerClient, TradingClient

logger = get_logger(__name__)


class BrokerRegistry:
    """Thread-safe registry mapping connection IDs to active broker adapters."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._clients: dict[str, BrokerClient] = {}

    def register(self, connection_id: str, client: BrokerClient) -> None:
        """Register a broker client instance under a unique connection ID."""
        with self._lock:
            if connection_id in self._clients:
                existing = self._clients[connection_id]
                if existing is not client:
                    logger.info(
                        "FR-trading-broker-registration: replacing client for %s",
                        connection_id,
                    )
                    existing.disconnect()
            self._clients[connection_id] = client
            logger.info(
                "FR-trading-broker-registration: registered connection %s (%s)",
                connection_id,
                client.name,
            )

    def get(self, connection_id: str) -> BrokerClient | None:
        """Retrieve a registered client by connection ID, or None if not found."""
        with self._lock:
            client = self._clients.get(connection_id)
            logger.debug(
                "FR-trading-broker-lookup: lookup %s found=%s",
                connection_id,
                client is not None,
            )
            return client

    def get_trading_client(self, connection_id: str) -> TradingClient | None:
        """Retrieve a client verified to be a TradingClient instance."""
        client = self.get(connection_id)
        if isinstance(client, TradingClient):
            return client
        return None

    def remove(self, connection_id: str) -> BrokerClient | None:
        """Unregister and return the client instance without disconnecting it."""
        with self._lock:
            client = self._clients.pop(connection_id, None)
            if client is not None:
                logger.info(
                    "FR-trading-broker-registration: removed connection %s",
                    connection_id,
                )
            return client

    def list_active(self) -> list[tuple[str, BrokerClient]]:
        """Return a snapshot list of (connection_id, client) pairs."""
        with self._lock:
            return list(self._clients.items())

    def list_connection_ids(self) -> list[str]:
        """Return a list of registered connection IDs."""
        with self._lock:
            return list(self._clients.keys())

    def close_all(self) -> None:
        """Disconnect all registered broker clients and clear the registry."""
        with self._lock:
            logger.info(
                "FR-trading-broker-lifecycle: closing %d connections",
                len(self._clients),
            )
            for cid, client in self._clients.items():
                try:
                    client.disconnect()
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "FR-trading-broker-lifecycle: error closing %s: %s", cid, exc
                    )
            self._clients.clear()

    async def aclose_all(self) -> None:
        """Asynchronously disconnect and await closure of all clients."""
        with self._lock:
            items = list(self._clients.items())
            self._clients.clear()

        logger.info(
            "FR-trading-broker-lifecycle: async closing %d connections", len(items)
        )
        for cid, client in items:
            try:
                res = client.close()
                if inspect.isawaitable(res):
                    await res
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "FR-trading-broker-lifecycle: error closing %s: %s", cid, exc
                )


# Global default broker registry singleton for live trading workspace
default_broker_registry = BrokerRegistry()

__all__ = ["BrokerRegistry", "default_broker_registry"]

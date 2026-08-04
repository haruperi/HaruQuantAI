"""Non-production broker adapter lifecycle composition."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from app.services.api.composition.broker_config import build_broker_connection_config
from app.services.brokers import (
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    get_broker_id,
)

_NON_PRODUCTION_ENVIRONMENTS = frozenset({"dev", "demo", "paper", "sandbox", "test"})


async def create_non_production_broker_session(
    *,
    credential_reference: str,
    owner_id: str,
    key_set: Mapping[str, bytes],
    request_id: str,
    broker_id: str,
    environment: str,
    account_reference: str | None = None,
) -> tuple[object, object]:
    """Resolve, construct, and connect one non-production broker adapter.

    Returns:
        Brokers-owned connection configuration and connected adapter.

    Raises:
        ValueError: If environment, construction, or connection fails closed.
    """
    if environment not in _NON_PRODUCTION_ENVIRONMENTS:
        raise ValueError("production broker environments are excluded")
    connection = build_broker_connection_config(
        credential_reference=credential_reference,
        owner_id=owner_id,
        key_set=key_set,
        request_id=request_id,
        broker_id=broker_id,
        environment=environment,
        account_reference=account_reference,
    )
    response = create_broker_adapter(
        cast("Any", get_broker_id(broker_id)),
        cast("Any", connection),
    )
    if response.error is not None or response.data is None:
        raise ValueError("broker adapter construction failed")
    adapter = response.data
    connected = await connect_broker(adapter)
    if connected.error is not None:
        await disconnect_broker(adapter)
        raise ValueError("broker connection failed")
    return connection, adapter


async def close_broker_session(adapter: object) -> None:
    """Disconnect one caller-owned broker adapter."""
    await disconnect_broker(cast("Any", adapter))


__all__ = ("close_broker_session", "create_non_production_broker_session")

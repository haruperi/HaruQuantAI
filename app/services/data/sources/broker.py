"""Read-only normalization of caller-owned broker account evidence."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.services.data.contracts.broker import (
    AccountBalance,
    AccountOrder,
    AccountPosition,
    AccountSnapshotRequest,
    AccountStateSnapshot,
)
from app.services.data.contracts.errors import DataError
from app.utils import Clock, logger, utc_now

if TYPE_CHECKING:
    from app.services.brokers import (
        BrokerAccountInfo,
        BrokerAdapter,
        BrokerBalance,
        BrokerOrder,
        BrokerPermissions,
        BrokerPosition,
    )


def _failure(
    request_id: str,
    operation: str,
    code: str = "STALE_EVIDENCE",
) -> DataError:
    """Build a secret-free canonical error for one broker read."""
    logger.warning("Broker account evidence is unavailable for %s", operation)
    return DataError(
        code,
        safe_details={"operation": operation},
        request_id=request_id,
    )


async def _fetch_from_adapter(
    adapter: BrokerAdapter,
    request_id: str,
) -> tuple[
    BrokerAccountInfo,
    tuple[BrokerBalance, ...],
    tuple[BrokerPosition, ...],
    tuple[BrokerOrder, ...],
    BrokerPermissions,
    bool,
]:
    """Read account evidence without owning adapter connection lifecycle."""
    logger.info("Reading account evidence from an injected broker adapter")
    info_result = await adapter.get_account_info()
    balance_result = await adapter.get_balances()
    position_result = await adapter.get_positions()
    order_result = await adapter.get_orders()
    permission_result = await adapter.get_permissions()
    connection_result = await adapter.is_connected()

    if info_result.error is not None or info_result.data is None:
        raise _failure(request_id, "account_info", "SOURCE_UNAVAILABLE")
    if balance_result.error is not None or balance_result.data is None:
        raise _failure(request_id, "balances", "SOURCE_UNAVAILABLE")
    if position_result.error is not None or position_result.data is None:
        raise _failure(request_id, "positions", "SOURCE_UNAVAILABLE")
    if order_result.error is not None or order_result.data is None:
        raise _failure(request_id, "orders", "SOURCE_UNAVAILABLE")
    if permission_result.error is not None or permission_result.data is None:
        raise _failure(request_id, "permissions", "SOURCE_UNAVAILABLE")
    if connection_result.error is not None or connection_result.data is None:
        raise _failure(request_id, "connection_status", "SOURCE_UNAVAILABLE")

    return (
        info_result.data,
        balance_result.data,
        position_result.data.items,
        order_result.data.items,
        permission_result.data,
        connection_result.data,
    )


def _required_decimal(
    value: Decimal | None,
    *,
    field: str,
    request_id: str,
) -> Decimal:
    """Return required finite broker numeric evidence or fail closed."""
    logger.debug("Validating required broker numeric evidence for %s", field)
    if value is None or not value.is_finite():
        raise _failure(request_id, field)
    return value


def _map_balances(
    balances: tuple[BrokerBalance, ...],
    request_id: str,
) -> tuple[AccountBalance, ...]:
    """Map exact broker balances without manufacturing missing amounts."""
    logger.debug("Normalizing %d broker balances", len(balances))
    return tuple(
        AccountBalance(
            asset=balance.asset,
            total=_required_decimal(
                balance.total,
                field="balance.total",
                request_id=request_id,
            ),
            available=_required_decimal(
                balance.available,
                field="balance.available",
                request_id=request_id,
            ),
        )
        for balance in balances
    )


def _map_positions(
    positions: tuple[BrokerPosition, ...],
    request_id: str,
) -> tuple[AccountPosition, ...]:
    """Map exact broker positions and reject unknown direction evidence."""
    logger.debug("Normalizing %d broker positions", len(positions))
    normalized: list[AccountPosition] = []
    for position in positions:
        if position.side not in ("LONG", "SHORT"):
            raise _failure(request_id, "position.side")
        normalized.append(
            AccountPosition(
                position_id=position.position_id,
                symbol=position.symbol,
                side=position.side,
                quantity=position.quantity,
                entry_price=position.open_price,
            )
        )
    return tuple(normalized)


def _map_orders(
    orders: tuple[BrokerOrder, ...],
    request_id: str,
) -> tuple[AccountOrder, ...]:
    """Map exact broker orders and reject unknown direction evidence."""
    logger.debug("Normalizing %d broker orders", len(orders))
    normalized: list[AccountOrder] = []
    for order in orders:
        if order.side not in ("BUY", "SELL"):
            raise _failure(request_id, "order.side")
        normalized.append(
            AccountOrder(
                order_id=order.order_id,
                symbol=order.symbol,
                side=order.side,
                state=order.state,
                quantity=order.quantity,
                price=order.price,
            )
        )
    return tuple(normalized)


def _validate_freshness(
    observed_at: datetime,
    retrieved_at: datetime,
    max_age_seconds: int,
    request_id: str,
) -> None:
    """Fail closed when broker evidence is future-dated or stale."""
    logger.debug("Validating broker account evidence freshness")
    age = observed_at - retrieved_at
    if age < timedelta(0) or age > timedelta(seconds=max_age_seconds):
        raise _failure(request_id, "account_info.retrieved_at")


def get_account_state_snapshot(
    request: AccountSnapshotRequest,
    adapter: BrokerAdapter,
    *,
    clock: Clock | None = None,
) -> AccountStateSnapshot:
    """Normalize a fresh snapshot from an already configured caller-owned adapter.

    Args:
        request: Account identity and freshness boundary.
        adapter: Caller-owned, already connected canonical broker adapter.
        clock: Optional injected UTC clock for deterministic verification.

    Returns:
        Immutable normalized account-state evidence.

    Raises:
        DataError: If mandatory broker evidence is missing, stale, or inconsistent.
    """
    logger.info(
        "Retrieving account snapshot from injected source %s", request.source_id
    )
    try:
        info, balances, positions, orders, permissions, connected = asyncio.run(
            _fetch_from_adapter(adapter, request.request_id)
        )
    except DataError:
        raise
    except Exception as error:
        logger.error("Injected broker adapter account read failed")
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "account_snapshot"},
            request_id=request.request_id,
        ) from error

    if info.account_id != request.account_id:
        raise _failure(request.request_id, "account_info.account_id")
    if info.currency is None:
        raise _failure(request.request_id, "account_info.currency")
    if permissions.trade_write is None:
        raise _failure(request.request_id, "permissions.trade_write")

    observed_at = utc_now(clock)
    _validate_freshness(
        observed_at,
        info.retrieved_at,
        request.max_age_seconds,
        request.request_id,
    )
    equity = _required_decimal(
        info.equity,
        field="account_info.equity",
        request_id=request.request_id,
    )

    return AccountStateSnapshot(
        account_id=request.account_id,
        currency=info.currency,
        balances=_map_balances(balances, request.request_id),
        equity=equity,
        margin_used=info.margin,
        margin_available=info.free_margin,
        positions=_map_positions(positions, request.request_id),
        orders=_map_orders(orders, request.request_id),
        connected=connected,
        trading_allowed=permissions.trade_write and connected,
        source_id=request.source_id,
        snapshot_at=info.retrieved_at,
        expires_at=info.retrieved_at + timedelta(seconds=request.max_age_seconds),
        request_id=request.request_id,
    )


__all__ = ["get_account_state_snapshot"]

# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""MT5 execution-history read operations."""

# ruff: noqa: A002 - public protocol signatures are normative.

from datetime import datetime
from typing import cast

from app.services.brokers.contracts import (
    BrokerAccountTransaction,
    BrokerCapabilityId,
    BrokerDeal,
    BrokerErrorCode,
    BrokerOrder,
    BrokerOrderFilter,
    BrokerPage,
    BrokerPosition,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import (
    _RequestValidationError,
)
from app.services.brokers.mt5_account.mapping import (
    _field,
    _map_deal,
    _map_order,
    _map_position,
    _map_transaction,
)


def _provider_ticket(value: str) -> int:
    """Parse one caller-supplied MT5 ticket before any provider transmission.

    Args:
        value: Caller-supplied provider order or position identifier.

    Returns:
        The exact integral MT5 ticket.

    Raises:
        _RequestValidationError: If the identifier is not a valid MT5 ticket.
            Raised before transmission so a malformed caller identifier is never
            reported as an uncertain mutation outcome.
    """
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise _RequestValidationError("MT5 ticket must be an integer") from error


class _MT5ExecutionHistoryMixin:
    """Private provider operations owned by this feature."""

    async def get_position(self, position_id: str) -> BrokerResult[BrokerPosition]:
        """Return one exact MT5 position by ticket.

        Args:
            position_id: Provider position ticket.

        Returns:
            Canonical open position or a not-found error.
        """
        values = await self._transport.call(
            "positions_get", ticket=_provider_ticket(position_id)
        )
        if not values:
            return self._error(
                BrokerCapabilityId.GET_POSITION,
                BrokerErrorCode.BROKER_POSITION_NOT_FOUND,
            )
        return self._result(
            BrokerCapabilityId.GET_POSITION, data=_map_position(values[0])
        )

    async def get_orders(
        self,
        filter: BrokerOrderFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded current MT5 orders.

        Returns:
            Canonical current-order page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        if cursor is not None:
            raise ValueError("MT5 order cursors are unsupported")
        if limit is None or limit <= 0:
            raise ValueError("positive order limit is required")
        kwargs = {"symbol": filter.symbol} if filter and filter.symbol else {}
        values = await self._transport.call("orders_get", **kwargs)
        mapped = tuple(_map_order(value) for value in (values or ()))
        if filter and filter.status:
            mapped = tuple(item for item in mapped if item.state == filter.status)
        if filter and filter.side:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        return self._result(
            BrokerCapabilityId.GET_ORDERS,
            data=BrokerPage(
                items=mapped[:limit],
                limit=limit,
                truncated=len(mapped) > limit,
            ),
        )

    async def get_order(self, order_id: str) -> BrokerResult[BrokerOrder]:
        """Return one active MT5 order by ticket.

        Args:
            order_id: Provider order ticket.

        Returns:
            Canonical current order or a not-found error.
        """
        values = await self._transport.call("orders_get", ticket=int(order_id))
        if not values:
            return self._error(
                BrokerCapabilityId.GET_ORDER,
                BrokerErrorCode.BROKER_ORDER_NOT_FOUND,
            )
        return self._result(BrokerCapabilityId.GET_ORDER, data=_map_order(values[0]))

    async def list_order_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded MT5 order history for one explicit UTC range.

        Returns:
            Canonical historical-order page.

        Raises:
            ValueError: If the range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        kwargs = {"group": symbol} if symbol else {}
        values = await self._transport.call("history_orders_get", start, end, **kwargs)
        mapped = tuple(_map_order(value) for value in (values or ()))
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.LIST_ORDER_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def list_deal_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerDeal]]:
        """Return bounded MT5 execution deals for one explicit UTC range.

        Returns:
            Canonical deal page.

        Raises:
            ValueError: If the range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        kwargs = {"group": symbol} if symbol else {}
        values = await self._transport.call("history_deals_get", start, end, **kwargs)
        mapped = tuple(
            _map_deal(value)
            for value in (values or ())
            if int(_field(value, "type")) in {0, 1}
        )
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.LIST_DEAL_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def get_deal(self, deal_id: str) -> BrokerResult[BrokerDeal]:
        """Return one MT5 deal by ticket.

        Args:
            deal_id: Provider deal ticket.

        Returns:
            Canonical deal or a not-found error.
        """
        values = await self._transport.call("history_deals_get", ticket=int(deal_id))
        if not values:
            return self._error(
                BrokerCapabilityId.GET_DEAL,
                BrokerErrorCode.BROKER_DEAL_NOT_FOUND,
            )
        return self._result(BrokerCapabilityId.GET_DEAL, data=_map_deal(values[0]))

    async def list_account_transactions(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerAccountTransaction]]:
        """Return bounded non-trade MT5 account transactions.

        Returns:
            Canonical account-transaction page.

        Raises:
            ValueError: If the range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        account = await self._transport.call("account_info")
        if account is None:
            return self._error(
                BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS,
                BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND,
            )
        values = await self._transport.call("history_deals_get", start, end)
        currency = str(_field(account, "currency"))
        mapped = tuple(
            _map_transaction(value, currency)
            for value in (values or ())
            if int(_field(value, "type")) not in {0, 1}
        )
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

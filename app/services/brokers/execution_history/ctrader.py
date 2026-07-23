# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""cTrader execution-history read operations."""

# ruff: noqa: A002 - public protocol signatures are normative.

from datetime import datetime
from typing import cast

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerDeal,
    BrokerOrder,
    BrokerOrderFilter,
    BrokerPage,
    BrokerPosition,
    BrokerPositionFilter,
    BrokerResult,
)
from app.services.brokers.ctrader_session.mapping import (
    _field,
    _map_deal,
    _map_order,
    _map_position,
    _optional,
)


class _CTraderExecutionHistoryMixin:
    """Private provider operations owned by this feature."""

    async def get_positions(
        self,
        filter: BrokerPositionFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerPosition]]:
        """Return bounded reconciled cTrader positions.

        Returns:
            Canonical position page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        self._validate_page(cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        mapped = tuple(
            _map_position(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "position")
        )
        if filter and filter.symbol:
            mapped = tuple(item for item in mapped if item.symbol == filter.symbol)
        if filter and filter.side:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.GET_POSITIONS,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def get_orders(
        self,
        filter: BrokerOrderFilter | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded reconciled cTrader orders.

        Returns:
            Canonical order page.

        Raises:
            ValueError: If cursor or limit is invalid.
        """
        self._validate_page(cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        mapped = tuple(
            _map_order(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "order")
        )
        if filter and filter.symbol:
            mapped = tuple(item for item in mapped if item.symbol == filter.symbol)
        if filter and filter.side:
            mapped = tuple(item for item in mapped if item.side == filter.side)
        if filter and filter.status:
            mapped = tuple(item for item in mapped if item.state == filter.status)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.GET_ORDERS,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=len(mapped) > bounded_limit,
            ),
        )

    async def list_order_history(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        symbol: str | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> BrokerResult[BrokerPage[BrokerOrder]]:
        """Return bounded cTrader historical orders.

        Returns:
            Canonical historical-order page.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        await self._ensure_lot_sizes()
        response = await self._request(
            "ProtoOAOrderListReq",
            "ProtoOAOrderListRes",
            fromTimestamp=int(cast("datetime", start).timestamp() * 1000),
            toTimestamp=int(cast("datetime", end).timestamp() * 1000),
        )
        mapped = tuple(
            _map_order(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "order")
        )
        if symbol is not None:
            mapped = tuple(item for item in mapped if item.symbol == symbol)
        bounded_limit = cast("int", limit)
        return self._result(
            BrokerCapabilityId.LIST_ORDER_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=bool(_optional(response, "hasMore"))
                or len(mapped) > bounded_limit,
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
        """Return bounded cTrader execution deals.

        Returns:
            Canonical deal page.

        Raises:
            ValueError: If range, cursor, or limit is invalid.
        """
        self._validate_history(start, end, cursor, limit)
        await self._ensure_lot_sizes()
        bounded_limit = cast("int", limit)
        response = await self._request(
            "ProtoOADealListReq",
            "ProtoOADealListRes",
            fromTimestamp=int(cast("datetime", start).timestamp() * 1000),
            toTimestamp=int(cast("datetime", end).timestamp() * 1000),
            maxRows=bounded_limit,
        )
        mapped = tuple(
            _map_deal(value, self._symbol_names, self._symbol_lot_sizes)
            for value in _field(response, "deal")
        )
        if symbol is not None:
            mapped = tuple(item for item in mapped if item.symbol == symbol)
        return self._result(
            BrokerCapabilityId.LIST_DEAL_HISTORY,
            data=BrokerPage(
                items=mapped[:bounded_limit],
                limit=bounded_limit,
                truncated=bool(_optional(response, "hasMore"))
                or len(mapped) > bounded_limit,
            ),
        )

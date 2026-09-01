# mypy: ignore-errors

"""MT5 provider-native calculation operations."""

from __future__ import annotations

from decimal import Decimal

from app.services.brokers.metatrader._legacy_types import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerMarginRequest,
    BrokerProfitRequest,
    StandardResponse,
    _UnsupportedAdapterBase,
)


class _MT5CalculationsMixin(_UnsupportedAdapterBase):
    """Private provider operations owned by this feature."""

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> StandardResponse[Decimal]:
        """Return MT5's provider-native margin calculation.

        Args:
            request: Value supplied to the operation.

        Returns:
            Canonical margin amount.
        """
        order_type = await self._transport.constant(f"ORDER_TYPE_{request.side}")
        value = await self._transport.call(
            "order_calc_margin",
            order_type,
            request.symbol,
            float(request.quantity),
            float(request.price or 0),
        )
        if value is None:
            return self._error(
                BrokerCapabilityId.CALCULATE_MARGIN,
                BrokerErrorCode.BROKER_PROVIDER_ERROR,
            )
        return self._result(
            BrokerCapabilityId.CALCULATE_MARGIN, data=Decimal(str(value))
        )

    async def calculate_profit(
        self, request: BrokerProfitRequest
    ) -> StandardResponse[Decimal]:
        """Return MT5's provider-native profit calculation.

        Args:
            request: Value supplied to the operation.

        Returns:
            Canonical profit amount.
        """
        order_type = await self._transport.constant(f"ORDER_TYPE_{request.side}")
        value = await self._transport.call(
            "order_calc_profit",
            order_type,
            request.symbol,
            float(request.quantity),
            float(request.open_price),
            float(request.close_price),
        )
        if value is None:
            return self._error(
                BrokerCapabilityId.CALCULATE_PROFIT,
                BrokerErrorCode.BROKER_PROVIDER_ERROR,
            )
        return self._result(
            BrokerCapabilityId.CALCULATE_PROFIT, data=Decimal(str(value))
        )

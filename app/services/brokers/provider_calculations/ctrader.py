# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""cTrader provider-native calculation operations."""

from decimal import Decimal

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerMarginRequest,
    BrokerProfitRequest,
    BrokerResult,
)
from app.services.brokers.ctrader_session.mapping import (
    _field,
    _optional,
)


class _CTraderCalculationsMixin:
    """Private provider operations owned by this feature."""

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> BrokerResult[Decimal]:
        """Return cTrader's expected margin for one candidate volume.

        Returns:
            Canonical account-currency margin.
        """
        symbol_id, _digits = await self._symbol_identity(request.symbol)
        response = await self._request(
            "ProtoOAExpectedMarginReq",
            "ProtoOAExpectedMarginRes",
            symbolId=symbol_id,
            volume=(await self._provider_volume(request.symbol, request.quantity),),
        )
        margins = tuple(_field(response, "margin"))
        if not margins:
            return self._error(
                BrokerCapabilityId.CALCULATE_MARGIN,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        value = _field(
            margins[0], "buyMargin" if request.side == "BUY" else "sellMargin"
        )
        divisor = Decimal(10) ** int(_field(response, "moneyDigits"))
        return self._result(
            BrokerCapabilityId.CALCULATE_MARGIN,
            data=Decimal(str(value)) / divisor,
        )

    async def calculate_profit(
        self, request: BrokerProfitRequest
    ) -> BrokerResult[Decimal]:
        """Calculate profit from provider lot-size and exact request prices.

        Returns:
            Canonical quote-currency profit evidence.
        """
        spec = await self._symbol_spec(request.symbol)
        lot_size = _optional(spec, "lotSize")
        if lot_size is None:
            return self._error(
                BrokerCapabilityId.CALCULATE_PROFIT,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        difference = (
            request.close_price - request.open_price
            if request.side == "BUY"
            else request.open_price - request.close_price
        )
        return self._result(
            BrokerCapabilityId.CALCULATE_PROFIT,
            data=difference * request.quantity * Decimal(str(lot_size)),
        )

# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""MT5 provider-native calculation operations."""

from decimal import Decimal

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerMarginRequest,
    BrokerProfitRequest,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import (
    _RequestValidationError,
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


class _MT5CalculationsMixin:
    """Private provider operations owned by this feature."""

    async def calculate_margin(
        self, request: BrokerMarginRequest
    ) -> BrokerResult[Decimal]:
        """Return MT5's provider-native margin calculation.

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
    ) -> BrokerResult[Decimal]:
        """Return MT5's provider-native profit calculation.

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

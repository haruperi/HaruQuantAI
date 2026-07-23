# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""MT5 mutation implementations behind unreleased public policy."""

from collections.abc import Mapping

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerOrderCheck,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    BrokerResult,
)
from app.services.brokers.contracts.protocols import (
    _RequestValidationError,
)
from app.services.brokers.mt5_account.mapping import (
    _field,
    _map_error_code,
    _map_order_check,
    _map_order_result,
    _map_position,
    _optional,
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


class _MT5MutationsMixin:
    """Private provider operations owned by this feature."""

    _last_error: BrokerError | None

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderCheck]:
        """Ask MT5 to validate one order without submitting it.

        Returns:
            Canonical non-final order-check response.
        """
        response = await self._transport.call(
            "order_check", await self._native_order_request(request)
        )
        if response is None:
            return self._error(
                BrokerCapabilityId.CHECK_ORDER,
                BrokerErrorCode.BROKER_PROVIDER_ERROR,
            )
        return self._result(
            BrokerCapabilityId.CHECK_ORDER, data=_map_order_check(response)
        )

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Submit exactly one MT5 order without retry.

        Returns:
            Canonical acknowledged order outcome.
        """
        return await self._send_mutation(
            BrokerCapabilityId.PLACE_ORDER,
            await self._native_order_request(request),
        )

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Modify exactly one pending MT5 order without retry.

        Returns:
            Canonical acknowledged order outcome.
        """
        native: dict[str, object] = {
            "action": await self._transport.constant("TRADE_ACTION_MODIFY"),
            "order": int(request.order_id),
        }
        self._copy_prices(native, request)
        if request.quantity is not None:
            native["volume"] = float(request.quantity)
        if request.expiration is not None:
            native["expiration"] = int(request.expiration.timestamp())
        return await self._send_mutation(BrokerCapabilityId.MODIFY_ORDER, native)

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> BrokerResult[BrokerOrderResult]:
        """Cancel exactly one pending MT5 order without retry.

        Returns:
            Canonical acknowledged cancellation outcome.
        """
        del client_request_id
        native = {
            "action": await self._transport.constant("TRADE_ACTION_REMOVE"),
            "order": _provider_ticket(order_id),
        }
        return await self._send_mutation(BrokerCapabilityId.CANCEL_ORDER, native)

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> BrokerResult[BrokerPosition]:
        """Modify stop fields for exactly one MT5 position without retry.

        Returns:
            Refreshed canonical position after provider acknowledgement.
        """
        native: dict[str, object] = {
            "action": await self._transport.constant("TRADE_ACTION_SLTP"),
            "position": _provider_ticket(request.position_id),
        }
        self._copy_prices(native, request)
        response = await self._transport.call("order_send", native)
        if response is None:
            return self._error(
                BrokerCapabilityId.MODIFY_POSITION,
                BrokerErrorCode.BROKER_UNKNOWN_OUTCOME,
            )
        result = _map_order_result(response)
        if result.outcome not in {"ACCEPTED", "PARTIAL"}:
            return self._native_rejection(BrokerCapabilityId.MODIFY_POSITION, response)
        values = await self._transport.call(
            "positions_get", ticket=_provider_ticket(request.position_id)
        )
        if not values:
            return self._error(
                BrokerCapabilityId.MODIFY_POSITION,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        return self._result(
            BrokerCapabilityId.MODIFY_POSITION, data=_map_position(values[0])
        )

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Close or reduce exactly one MT5 position without retry.

        Returns:
            Canonical acknowledged close outcome.
        """
        positions = await self._transport.call(
            "positions_get", ticket=_provider_ticket(request.position_id)
        )
        if not positions:
            return self._error(
                BrokerCapabilityId.CLOSE_POSITION,
                BrokerErrorCode.BROKER_POSITION_NOT_FOUND,
            )
        position = positions[0]
        side = "SELL" if int(_field(position, "type")) == 0 else "BUY"
        native = {
            "action": await self._transport.constant("TRADE_ACTION_DEAL"),
            "position": _provider_ticket(request.position_id),
            "symbol": str(_field(position, "symbol")),
            "volume": float(request.quantity),
            "type": await self._transport.constant(f"ORDER_TYPE_{side}"),
        }
        return await self._send_mutation(BrokerCapabilityId.CLOSE_POSITION, native)

    async def _native_order_request(  # noqa: C901, PLR0912
        self, request: BrokerOrderRequest
    ) -> dict[str, object]:
        """Translate one canonical order request through documented constants.

        Returns:
            Documented MT5 order-request fields.
        """
        suffix: str = request.side
        if request.order_type != "MARKET":
            suffix = f"{suffix}_{request.order_type}"
        native: dict[str, object] = {
            "action": await self._transport.constant(
                "TRADE_ACTION_DEAL"
                if request.order_type == "MARKET"
                else "TRADE_ACTION_PENDING"
            ),
            "symbol": request.symbol,
            "volume": float(request.quantity),
            "type": await self._transport.constant(f"ORDER_TYPE_{suffix}"),
        }
        if request.order_type == "LIMIT":
            if request.limit_price is not None:
                native["price"] = float(request.limit_price)
        elif request.order_type == "STOP":
            if request.stop_price is not None:
                native["price"] = float(request.stop_price)
        elif request.order_type == "STOP_LIMIT":
            if request.stop_price is not None:
                native["price"] = float(request.stop_price)
            if request.limit_price is not None:
                native["stoplimit"] = float(request.limit_price)
        if request.stop_loss is not None:
            native["sl"] = float(request.stop_loss)
        if request.take_profit is not None:
            native["tp"] = float(request.take_profit)
        if request.deviation_points is not None:
            native["deviation"] = request.deviation_points
        if request.magic is not None:
            native["magic"] = request.magic
        if request.comment is not None:
            native["comment"] = request.comment
        if request.expiration is not None:
            native["expiration"] = int(request.expiration.timestamp())
        return native

    async def _send_mutation(
        self,
        operation: BrokerCapabilityId,
        native: Mapping[str, object],
    ) -> BrokerResult[BrokerOrderResult]:
        """Send one mutation once and classify its explicit response.

        Returns:
            Canonical mutation result or error.
        """
        response = await self._transport.call("order_send", dict(native))
        if response is None:
            return self._error(operation, BrokerErrorCode.BROKER_UNKNOWN_OUTCOME)
        result = _map_order_result(response)
        if result.outcome not in {"ACCEPTED", "PARTIAL"}:
            return self._native_rejection(operation, response)
        return self._result(operation, data=result)

    def _native_rejection[T](
        self, operation: BrokerCapabilityId, response: object
    ) -> BrokerResult[T]:
        """Map one explicit MT5 rejection to a canonical failure.

        Returns:
            Canonical provider-rejection result.
        """
        retcode = int(_field(response, "retcode"))
        error = BrokerError(
            code=_map_error_code(retcode),
            message=f"MT5 {operation.value} rejected",
            provider_code=str(retcode),
            provider_message=(
                str(_optional(response, "comment"))
                if _optional(response, "comment") is not None
                else None
            ),
            capability=operation,
        )
        self._last_error = error
        return self._result(operation, error=error)

# mypy: ignore-errors

"""MT5 mutation implementations behind unreleased public policy."""

from collections.abc import Mapping
from datetime import datetime

from app.services.brokers.metatrader._legacy_types import (
    BrokerCapabilityId,
    BrokerError,
    BrokerErrorCode,
    BrokerOrderCheck,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderRequestV2,
    BrokerOrderResult,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
    StandardResponse,
    _RequestValidationError,
    _UnsupportedAdapterBase,
)
from app.services.brokers.metatrader.mapping import (
    _field,
    _map_error_code,
    _map_order_check,
    _map_order_result,
    _map_position,
    _optional,
)
from app.services.brokers.metatrader.specifications import (
    get_provider_specification_snapshot_field,
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


class _MT5MutationsMixin(_UnsupportedAdapterBase):
    """Private provider operations owned by this feature."""

    _last_error: BrokerError | None

    def _copy_prices(self, native: dict[str, object], request: object) -> None:
        """Copy stop_loss and take_profit prices to native MT5 dict.

        Args:
            native: Native MT5 request dict to mutate.
            request: Source canonical request object.
        """
        stop_loss = getattr(request, "stop_loss", None)
        if stop_loss is not None:
            native["sl"] = float(stop_loss)
        take_profit = getattr(request, "take_profit", None)
        if take_profit is not None:
            native["tp"] = float(take_profit)
        limit_price = getattr(request, "limit_price", None)
        if limit_price is not None:
            native["price"] = float(limit_price)
        stop_price = getattr(request, "stop_price", None)
        if stop_price is not None:
            native["price"] = float(stop_price)

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderCheck]:
        """Ask MT5 to validate one order without submitting it.

        Args:
            request: Value supplied to the operation.

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
        specification_getter = getattr(self, "get_provider_specification", None)
        if not callable(specification_getter):
            return self._result(
                BrokerCapabilityId.CHECK_ORDER,
                data=_map_order_check(response),
            )
        specification_response = await specification_getter(request.symbol)
        specification = specification_response.data
        if specification_response.error is not None or specification is None:
            return self._error(
                BrokerCapabilityId.CHECK_ORDER,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        observed_value = get_provider_specification_snapshot_field(
            specification, "observed_at"
        )
        if not isinstance(observed_value, str):
            return self._error(
                BrokerCapabilityId.CHECK_ORDER,
                BrokerErrorCode.BROKER_RESPONSE_INVALID,
            )
        return self._result(
            BrokerCapabilityId.CHECK_ORDER,
            data=_map_order_check(
                response,
                environment=self._config.environment,
                account_digest=str(
                    get_provider_specification_snapshot_field(
                        specification, "account_digest"
                    )
                ),
                provider_specification_checksum=str(
                    get_provider_specification_snapshot_field(specification, "checksum")
                ),
                terminal_build=str(
                    get_provider_specification_snapshot_field(
                        specification, "terminal_build"
                    )
                ),
                observed_at=datetime.fromisoformat(observed_value),
            ),
        )

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Submit exactly one MT5 order without retry.

        Args:
            request: Value supplied to the operation.

        Returns:
            Canonical acknowledged order outcome.
        """
        return await self._send_mutation(
            BrokerCapabilityId.PLACE_ORDER,
            await self._native_order_request(request),
        )

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> StandardResponse[BrokerOrderResult]:
        """Modify exactly one pending MT5 order without retry.

        Args:
            request: Value supplied to the operation.

        Returns:
            Canonical acknowledged order outcome.
        """
        orders = await self._transport.call("orders_get", ticket=int(request.order_id))
        if not orders:
            return self._error(
                BrokerCapabilityId.MODIFY_ORDER,
                BrokerErrorCode.BROKER_ORDER_NOT_FOUND,
            )
        order = orders[0]
        symbol = str(_field(order, "symbol"))
        native: dict[str, object] = {
            "action": await self._transport.constant("TRADE_ACTION_MODIFY"),
            "order": int(request.order_id),
            "symbol": symbol,
            "price": float(_field(order, "price_open")),
            "type": int(_field(order, "type")),
        }
        self._copy_prices(native, request)
        if request.quantity is not None:
            native["volume"] = float(request.quantity)
        if request.expiration is not None:
            native["expiration"] = int(request.expiration.timestamp())
        info = await self._transport.call("symbol_info", symbol)
        if info is not None:
            filling_flags = int(_field(info, "filling_mode"))
            if filling_flags & 1:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_FOK"
                )
            elif filling_flags & 2:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_IOC"
                )
            else:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_RETURN"
                )
        return await self._send_mutation(BrokerCapabilityId.MODIFY_ORDER, native)

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> StandardResponse[BrokerOrderResult]:
        """Cancel exactly one pending MT5 order without retry.

        Args:
            order_id: Value supplied to the operation.
            client_request_id: Value supplied to the operation.

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
    ) -> StandardResponse[BrokerPosition]:
        """Modify stop fields for exactly one MT5 position without retry.

        Args:
            request: Value supplied to the operation.

        Returns:
            Refreshed canonical position after provider acknowledgement.
        """
        positions = await self._transport.call(
            "positions_get", ticket=_provider_ticket(request.position_id)
        )
        if not positions:
            return self._error(
                BrokerCapabilityId.MODIFY_POSITION,
                BrokerErrorCode.BROKER_POSITION_NOT_FOUND,
            )
        position = positions[0]
        native: dict[str, object] = {
            "action": await self._transport.constant("TRADE_ACTION_SLTP"),
            "position": _provider_ticket(request.position_id),
            "symbol": str(_field(position, "symbol")),
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
    ) -> StandardResponse[BrokerOrderResult]:
        """Close or reduce exactly one MT5 position without retry.

        Args:
            request: Value supplied to the operation.

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
        symbol = str(_field(position, "symbol"))
        native: dict[str, object] = {
            "action": await self._transport.constant("TRADE_ACTION_DEAL"),
            "position": _provider_ticket(request.position_id),
            "symbol": symbol,
            "volume": float(request.quantity),
            "type": await self._transport.constant(f"ORDER_TYPE_{side}"),
        }
        tick = await self._transport.call("symbol_info_tick", symbol)
        if tick is not None:
            price = _field(tick, "bid") if side == "SELL" else _field(tick, "ask")
            native["price"] = float(price)
        info = await self._transport.call("symbol_info", symbol)
        if info is not None:
            filling_flags = int(_field(info, "filling_mode"))
            if filling_flags & 1:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_FOK"
                )
            elif filling_flags & 2:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_IOC"
                )
            else:
                native["type_filling"] = await self._transport.constant(
                    "ORDER_FILLING_RETURN"
                )
        return await self._send_mutation(BrokerCapabilityId.CLOSE_POSITION, native)

    async def _native_order_request(  # noqa: C901, PLR0912
        self, request: BrokerOrderRequest
    ) -> dict[str, object]:
        """Translate one canonical order request through documented constants.

        Args:
            request: Value supplied to the operation.

        Returns:
            Documented MT5 order-request fields.

        Raises:
            _RequestValidationError: If a v2 policy cannot map to verified MT5.
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
        elif request.order_type == "MARKET" and "price" not in native:
            tick = await self._transport.call("symbol_info_tick", request.symbol)
            if tick is not None:
                price = (
                    _field(tick, "ask")
                    if request.side == "BUY"
                    else _field(tick, "bid")
                )
                native["price"] = float(price)
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
        if isinstance(request, BrokerOrderRequestV2):
            fill_constant = {
                "FOK": "ORDER_FILLING_FOK",
                "IOC": "ORDER_FILLING_IOC",
                "RETURN": "ORDER_FILLING_RETURN",
            }.get(request.fill_policy)
            if fill_constant is None:
                raise _RequestValidationError(
                    "MT5 does not admit the requested fill policy"
                )
            time_constant = {
                "GTC": "ORDER_TIME_GTC",
                "DAY": "ORDER_TIME_DAY",
                "SPECIFIED": "ORDER_TIME_SPECIFIED",
                "SPECIFIED_DAY": "ORDER_TIME_SPECIFIED_DAY",
            }[request.time_policy]
            native["type_filling"] = await self._transport.constant(fill_constant)
            native["type_time"] = await self._transport.constant(time_constant)
        elif "type_filling" not in native:
            info = await self._transport.call("symbol_info", request.symbol)
            if info is not None:
                filling_flags = int(_field(info, "filling_mode"))
                if filling_flags & 1:
                    native["type_filling"] = await self._transport.constant(
                        "ORDER_FILLING_FOK"
                    )
                elif filling_flags & 2:
                    native["type_filling"] = await self._transport.constant(
                        "ORDER_FILLING_IOC"
                    )
                else:
                    native["type_filling"] = await self._transport.constant(
                        "ORDER_FILLING_RETURN"
                    )
        return native

    async def _send_mutation(
        self,
        operation: BrokerCapabilityId,
        native: Mapping[str, object],
    ) -> StandardResponse[BrokerOrderResult]:
        """Send one mutation once and classify its explicit response.

        Args:
            operation: Value supplied to the operation.
            native: Value supplied to the operation.

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
    ) -> StandardResponse[T]:
        """Map one explicit MT5 rejection to a canonical failure.

        Args:
            operation: Value supplied to the operation.
            response: Value supplied to the operation.

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

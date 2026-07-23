# mypy: disable-error-code="attr-defined,no-any-return,has-type"
"""cTrader mutation implementations behind unreleased public policy."""

from app.services.brokers.contracts import (
    BrokerCapabilityId,
    BrokerErrorCode,
    BrokerMarginRequest,
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
from app.services.brokers.ctrader_session.mapping import (
    _field,
    _map_error_code,
    _map_order_result,
)


class _CTraderMutationsMixin:
    """Private provider operations owned by this feature."""

    async def check_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderCheck]:
        """Validate symbol and obtain provider expected-margin evidence.

        Returns:
            Canonical non-final order check.
        """
        margin = await self.calculate_margin(
            BrokerMarginRequest(
                symbol=request.symbol,
                side=request.side,
                quantity=request.quantity,
                quantity_unit=request.quantity_unit,
                product_profile="ctrader",
                account_reference=request.account_reference,
            )
        )
        if margin.error is not None:
            return self._result(BrokerCapabilityId.CHECK_ORDER, error=margin.error)
        return self._result(
            BrokerCapabilityId.CHECK_ORDER,
            data=BrokerOrderCheck(
                accepted_for_submission=True,
                estimated_margin=margin.data,
            ),
        )

    async def place_order(
        self, request: BrokerOrderRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Submit exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        symbol_id, _digits = await self._symbol_identity(request.symbol)
        order_types = {"MARKET": 1, "LIMIT": 2, "STOP": 3, "STOP_LIMIT": 6}
        fields: dict[str, object] = {
            "symbolId": symbol_id,
            "orderType": order_types[request.order_type],
            "tradeSide": 1 if request.side == "BUY" else 2,
            "volume": await self._provider_volume(request.symbol, request.quantity),
        }
        self._copy_order_fields(fields, request)
        return await self._execution(
            BrokerCapabilityId.PLACE_ORDER,
            "ProtoOANewOrderReq",
            fallback_id=None,
            **fields,
        )

    async def modify_order(
        self, request: BrokerOrderModificationRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Modify exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        fields: dict[str, object] = {"orderId": int(request.order_id)}
        if request.quantity is not None:
            symbol = await self._symbol_for_order(request.order_id)
            fields["volume"] = await self._provider_volume(symbol, request.quantity)
        self._copy_order_fields(fields, request)
        return await self._execution(
            BrokerCapabilityId.MODIFY_ORDER,
            "ProtoOAAmendOrderReq",
            fallback_id=request.order_id,
            **fields,
        )

    async def cancel_order(
        self, order_id: str, client_request_id: str | None = None
    ) -> BrokerResult[BrokerOrderResult]:
        """Cancel exactly one cTrader order without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        del client_request_id
        return await self._execution(
            BrokerCapabilityId.CANCEL_ORDER,
            "ProtoOACancelOrderReq",
            fallback_id=order_id,
            orderId=int(order_id),
        )

    async def modify_position(
        self, request: BrokerPositionModificationRequest
    ) -> BrokerResult[BrokerPosition]:
        """Modify one cTrader position and return refreshed provider state.

        Returns:
            Canonical refreshed position.
        """
        fields: dict[str, object] = {"positionId": int(request.position_id)}
        self._copy_order_fields(fields, request)
        execution = await self._execution(
            BrokerCapabilityId.MODIFY_POSITION,
            "ProtoOAAmendPositionSLTPReq",
            fallback_id=request.position_id,
            **fields,
        )
        if execution.error is not None:
            return self._result(
                BrokerCapabilityId.MODIFY_POSITION, error=execution.error
            )
        positions = await self.get_positions(limit=100)
        if positions.data is not None:
            for position in positions.data.items:
                if position.position_id == request.position_id:
                    return self._result(
                        BrokerCapabilityId.MODIFY_POSITION, data=position
                    )
        return self._error(
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerErrorCode.BROKER_RESPONSE_INVALID,
        )

    async def close_position(
        self, request: BrokerPositionCloseRequest
    ) -> BrokerResult[BrokerOrderResult]:
        """Close or reduce exactly one cTrader position without retry.

        Returns:
            Canonical acknowledged provider outcome.
        """
        symbol = await self._symbol_for_position(request.position_id)
        return await self._execution(
            BrokerCapabilityId.CLOSE_POSITION,
            "ProtoOAClosePositionReq",
            fallback_id=request.position_id,
            positionId=int(request.position_id),
            volume=await self._provider_volume(symbol, request.quantity),
        )

    async def _symbol_for_order(self, order_id: str) -> str:
        """Resolve an active order's provider symbol without mutation.

        Returns:
            Exact provider symbol name.

        Raises:
            _RequestValidationError: If the active order is absent before any
                provider transmission.
        """
        await self._ensure_symbols()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        for order in _field(response, "order"):
            if str(_field(order, "orderId")) == order_id:
                trade = _field(order, "tradeData")
                return self._symbol_names[int(_field(trade, "symbolId"))]
        raise _RequestValidationError("cTrader active order is absent")

    async def _symbol_for_position(self, position_id: str) -> str:
        """Resolve an active position's provider symbol without mutation.

        Returns:
            Exact provider symbol name.

        Raises:
            _RequestValidationError: If the active position is absent before any
                provider transmission.
        """
        await self._ensure_symbols()
        response = await self._request("ProtoOAReconcileReq", "ProtoOAReconcileRes")
        for position in _field(response, "position"):
            if str(_field(position, "positionId")) == position_id:
                trade = _field(position, "tradeData")
                return self._symbol_names[int(_field(trade, "symbolId"))]
        raise _RequestValidationError("cTrader active position is absent")

    async def _execution(
        self,
        operation: BrokerCapabilityId,
        request_name: str,
        *,
        fallback_id: str | None = None,
        **fields: object,
    ) -> BrokerResult[BrokerOrderResult]:
        """Send one cTrader mutation once and classify its execution event.

        Returns:
            Canonical acknowledged mutation result or provider rejection.
        """
        event = await self._request(request_name, "ProtoOAExecutionEvent", **fields)
        result = _map_order_result(event, fallback_id)
        if result.outcome == "REJECTED":
            code = str(result.provider_code or "PROVIDER_ERROR")
            return self._error(operation, _map_error_code(code, operation.value))
        return self._result(operation, data=result)

    @staticmethod
    def _copy_order_fields(fields: dict[str, object], request: object) -> None:
        """Copy only explicitly supplied cTrader order fields."""
        for canonical, provider in (
            ("limit_price", "limitPrice"),
            ("stop_price", "stopPrice"),
            ("stop_loss", "stopLoss"),
            ("take_profit", "takeProfit"),
        ):
            value = getattr(request, canonical, None)
            if value is not None:
                fields[provider] = float(value)
        expiration = getattr(request, "expiration", None)
        if expiration is not None:
            fields["expirationTimestamp"] = int(expiration.timestamp() * 1000)
        for canonical, provider in (
            ("comment", "comment"),
            ("label", "label"),
            ("client_order_id", "clientOrderId"),
        ):
            value = getattr(request, canonical, None)
            if value is not None:
                fields[provider] = value

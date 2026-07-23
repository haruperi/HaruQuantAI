"""Aggregate deterministic validation for governed Trading requests."""

from collections.abc import Mapping
from decimal import Decimal

from app.services.data.evidence.account_contracts import (
    AccountStateSnapshot,
)
from app.services.trading.contracts import TradingError, TradingRequest
from app.services.trading.contracts.models import JsonValue
from app.utils import logger

_ORDER_ACTIONS = frozenset({"submit_order", "modify_order", "cancel_order"})
_POSITION_ACTIONS = frozenset({"close_position", "modify_position", "reduce_exposure"})


def _validate_mutation_targets(request: TradingRequest) -> None:
    """Require broker target identities sourced from Trading state.

    Args:
        request: Governed request under validation.

    Raises:
        TradingError: If a mutation lacks its receiver authority identity.
    """
    logger.debug("Validating Trading mutation target identities")
    if (
        request.action in {"modify_order", "cancel_order"}
        and request.target_broker_order_id is None
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Order mutation requires a Trading-state broker order target",
        )
    if request.action in _POSITION_ACTIONS and (
        request.target_broker_position_id is None
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Position mutation requires a Trading-state broker position target",
        )


def _require_instrument_evidence(request: TradingRequest) -> None:
    """Require exact instrument quantity and price precision evidence.

    Args:
        request: Governed request under validation.

    Raises:
        TradingError: If required broker-critical metadata is absent.
    """
    logger.debug("Validating Trading instrument precision evidence")
    if request.quantity is not None and any(
        value is None
        for value in (
            request.instrument_min_quantity,
            request.instrument_max_quantity,
            request.instrument_quantity_step,
        )
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Instrument quantity metadata is required",
            trace_context={"request_id": request.request_id},
        )
    if (
        any(
            value is not None
            for value in (
                request.price,
                request.stop_price,
                request.stop_loss,
                request.take_profit,
            )
        )
        and request.instrument_price_tick is None
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Instrument price metadata is required",
            trace_context={"request_id": request.request_id},
        )


def _validate_quantity(request: TradingRequest) -> None:
    """Validate quantity bounds and exact step alignment.

    Args:
        request: Governed request under validation.

    Raises:
        TradingError: If quantity violates supplied instrument evidence.
    """
    logger.debug("Validating Trading quantity bounds and step")
    if request.quantity is None:
        return
    minimum = request.instrument_min_quantity
    maximum = request.instrument_max_quantity
    step = request.instrument_quantity_step
    if minimum is None or maximum is None or step is None:
        return
    if request.quantity < minimum or request.quantity > maximum:
        raise TradingError(
            "VALIDATION_FAILED",
            "Order quantity is outside instrument bounds",
            trace_context={"request_id": request.request_id},
        )
    if (request.quantity - minimum) % step != Decimal(0):
        raise TradingError(
            "VALIDATION_FAILED",
            "Order quantity is not aligned to instrument step",
            trace_context={"request_id": request.request_id},
        )


def _validate_price_geometry(request: TradingRequest) -> None:
    """Validate exact price tick alignment and stop geometry.

    Args:
        request: Governed request under validation.

    Raises:
        TradingError: If supplied prices are misaligned or geometrically invalid.
    """
    logger.debug("Validating Trading price and stop geometry")
    prices = tuple(
        value
        for value in (
            request.price,
            request.stop_price,
            request.stop_loss,
            request.take_profit,
        )
        if value is not None
    )
    tick = request.instrument_price_tick
    if tick is not None and any(value % tick != Decimal(0) for value in prices):
        raise TradingError(
            "VALIDATION_FAILED",
            "Order price is not aligned to instrument tick",
            trace_context={"request_id": request.request_id},
        )
    if request.price is None:
        if request.stop_loss is not None or request.take_profit is not None:
            raise TradingError(
                "VALIDATION_FAILED",
                "Stop geometry requires an exact reference price",
                trace_context={"request_id": request.request_id},
            )
        return
    if request.side == "BUY" and (
        (request.stop_loss is not None and request.stop_loss >= request.price)
        or (request.take_profit is not None and request.take_profit <= request.price)
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Buy stop geometry is invalid",
            trace_context={"request_id": request.request_id},
        )
    if request.side == "SELL" and (
        (request.stop_loss is not None and request.stop_loss <= request.price)
        or (request.take_profit is not None and request.take_profit >= request.price)
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Sell stop geometry is invalid",
            trace_context={"request_id": request.request_id},
        )


def _validate_operation(
    request: TradingRequest,
    account_state: AccountStateSnapshot,
) -> None:
    """Validate action-specific identities and preconditions.

    Args:
        request: Governed request under validation.
        account_state: Current Data-owned account evidence.

    Raises:
        TradingError: If action addressing or required tickets are invalid.
    """
    logger.debug("Validating Trading operation preconditions")
    _validate_mutation_targets(request)
    if request.action in _ORDER_ACTIONS | _POSITION_ACTIONS and request.symbol is None:
        raise TradingError("VALIDATION_FAILED", "Action requires symbol")
    if request.action == "submit_order" and (
        request.quantity is None or request.side is None
    ):
        raise TradingError(
            "VALIDATION_FAILED", "Order submission requires side and size"
        )
    if request.action in {"modify_order", "cancel_order"}:
        order = next(
            (
                item
                for item in account_state.orders
                if item.order_id == request.order_id
            ),
            None,
        )
        if order is None or order.symbol != request.symbol:
            raise TradingError("VALIDATION_FAILED", "Order identity is not current")
        if request.expected_version is None:
            raise TradingError("VERSION_CONFLICT", "Order version evidence is required")
    if request.action in _POSITION_ACTIONS:
        position = next(
            (
                item
                for item in account_state.positions
                if item.position_id == request.position_id
            ),
            None,
        )
        if position is None or position.symbol != request.symbol:
            raise TradingError("VALIDATION_FAILED", "Position identity is not current")
    if (
        request.action in {"close_position", "reduce_exposure"}
        and request.quantity is None
    ):
        raise TradingError("VALIDATION_FAILED", "Position reduction requires size")


def _validate_symbol_capability(
    request: TradingRequest,
    symbol_capability: Mapping[str, JsonValue],
) -> None:
    """Validate provider order-type and instrument quantity-unit evidence.

    Args:
        request: Governed request under validation.
        symbol_capability: Explicit merged Broker feature and symbol metadata.

    Raises:
        TradingError: If capability evidence is absent, malformed, or incompatible.
    """
    logger.debug("Validating Trading symbol capability evidence")
    supported_order_types = symbol_capability.get("supported_order_types")
    quantity_unit = symbol_capability.get("quantity_unit")
    if not isinstance(supported_order_types, list) or any(
        not isinstance(item, str) for item in supported_order_types
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Symbol supported order types are required",
            trace_context={"request_id": request.request_id},
        )
    if request.order_type not in supported_order_types:
        raise TradingError(
            "VALIDATION_FAILED",
            "Order type is not supported for the selected symbol",
            trace_context={"request_id": request.request_id},
        )
    if (
        not isinstance(quantity_unit, str)
        or not quantity_unit
        or quantity_unit != quantity_unit.strip()
        or request.quantity_unit != quantity_unit
    ):
        raise TradingError(
            "VALIDATION_FAILED",
            "Quantity unit does not match validated instrument metadata",
            trace_context={"request_id": request.request_id},
        )


def validate_order_request(
    request: TradingRequest,
    account_state: AccountStateSnapshot,
    symbol_capability: Mapping[str, JsonValue],
) -> TradingRequest:
    """Validate governed order material before route selection.

    Args:
        request: Immutable canonical Trading request.
        account_state: Data-owned account-state evidence.
        symbol_capability: Explicit Broker feature and symbol metadata evidence.

    Returns:
        The same validated immutable request.

    Raises:
        TradingError: If account, instrument, margin, ticket, or operation evidence
            fails validation.
    """
    logger.info("Validating governed Trading order request %s", request.request_id)
    if request.account_id != account_state.account_id:
        raise TradingError("SCOPE_MISMATCH", "Request and account scopes differ")
    if not account_state.connected or not account_state.trading_allowed:
        raise TradingError(
            "SERVICE_UNAVAILABLE", "Account is not available for trading"
        )
    if account_state.expires_at <= request.system_time:
        raise TradingError("STALE_EVIDENCE", "Account-state evidence is stale")
    if request.action == "submit_order" and account_state.margin_available is None:
        raise TradingError("VALIDATION_FAILED", "Margin evidence is required")
    _validate_symbol_capability(request, symbol_capability)
    _require_instrument_evidence(request)
    _validate_quantity(request)
    _validate_price_geometry(request)
    _validate_operation(request, account_state)
    return request


__all__ = ["validate_order_request"]

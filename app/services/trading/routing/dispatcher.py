"""Single asynchronous authority mutation boundary for Trading intents."""

# ruff: noqa: BLE001 - the authority boundary normalizes provider failures.

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from typing import TYPE_CHECKING, Any, Literal

from app.services.brokers import (
    BrokerAdapter,
    BrokerConnectionConfig,
    BrokerErrorCode,
    BrokerOrderModificationRequest,
    BrokerOrderRequest,
    BrokerOrderResult,
    BrokerPosition,
    BrokerPositionCloseRequest,
    BrokerPositionModificationRequest,
)
from app.services.trading.contracts import ExecutionReceipt, OrderIntent, TradingError
from app.services.trading.contracts.responses import (
    error_trading_response,
    success_trading_response,
)
from app.services.trading.routing.responses import _classify_authority_response_value
from app.utils import (
    canonical_json,
    get_logger,
    parse_utc_timestamp,
)

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.trading.contracts.models import JsonValue

_CLASSIFICATION_POLICY: Mapping[str, JsonValue] = {
    "malformed_response_policy": "unknown_outcome",
    "mutation_retry_policy": "reconcile_before_retry",
}
_EXPLICIT_REJECTIONS = frozenset(
    {
        BrokerErrorCode.BROKER_AUTHENTICATION_FAILED,
        BrokerErrorCode.BROKER_AUTHORIZATION_FAILED,
        BrokerErrorCode.BROKER_SYMBOL_NOT_FOUND,
        BrokerErrorCode.BROKER_ACCOUNT_NOT_FOUND,
        BrokerErrorCode.BROKER_ORDER_NOT_FOUND,
        BrokerErrorCode.BROKER_POSITION_NOT_FOUND,
        BrokerErrorCode.BROKER_REQUEST_INVALID,
        BrokerErrorCode.BROKER_REQUEST_REJECTED,
        BrokerErrorCode.BROKER_MARKET_CLOSED,
        BrokerErrorCode.BROKER_INSUFFICIENT_MARGIN,
        BrokerErrorCode.BROKER_INSUFFICIENT_FUNDS,
    }
)
_EXPLICIT_REJECTION_CODES = frozenset(code.value for code in _EXPLICIT_REJECTIONS)


def _broker_evidence(
    result: StandardResponse[Any],
) -> tuple[str, str, str, datetime]:
    """Return required Broker scope and completion evidence.

    Args:
        result: Standard response returned by a Broker mutation.

    Returns:
        Broker identifier, operation, environment, and completion timestamp.

    Raises:
        TradingError: If required Broker evidence is absent or malformed.
    """
    extensions = result.metadata.extensions
    broker = extensions.get("broker")
    operation = extensions.get("operation")
    environment = extensions.get("environment")
    timestamp = extensions.get("timestamp")
    if (
        not isinstance(broker, str)
        or not isinstance(operation, str)
        or not isinstance(environment, str)
        or not isinstance(timestamp, str)
    ):
        raise TradingError(
            "MALFORMED_RECEIPT",
            "Broker result metadata is incomplete",
        )
    try:
        parsed_timestamp = parse_utc_timestamp(timestamp)
    except ValueError as error:
        raise TradingError(
            "MALFORMED_RECEIPT",
            "Broker result timestamp is malformed",
        ) from error
    return broker, operation, environment, parsed_timestamp


def _receipt_identity(intent: OrderIntent, authority_id: str, evidence_id: str) -> str:
    """Build a deterministic Trading-owned receipt identity.

    Args:
        intent: Dispatched executable intent.
        authority_id: Selected route authority identifier.
        evidence_id: Stable authority response or timeout evidence identifier.

    Returns:
        Stable SHA-256-prefixed receipt identity.
    """
    logger.debug("Building deterministic Trading receipt identity")
    digest = sha256(
        canonical_json(
            {
                "client_order_id": intent.client_order_id,
                "authority_id": authority_id,
                "evidence_id": evidence_id,
            }
        ).encode("utf-8")
    ).hexdigest()
    return f"trd-receipt-{digest}"


def _base_raw_response(
    intent: OrderIntent,
    authority_id: str,
    evidence_id: str,
    authority_timestamp: datetime,
    received_at: datetime,
) -> dict[str, JsonValue]:
    """Build required trace context for response classification.

    Args:
        intent: Dispatched executable intent.
        authority_id: Selected authority identifier.
        evidence_id: Stable response evidence identifier.
        authority_timestamp: Best available authority timestamp.
        received_at: Trading receipt timestamp.

    Returns:
        JSON-safe response classification material.
    """
    logger.debug("Building Trading authority response trace context")
    return {
        "receipt_id": _receipt_identity(intent, authority_id, evidence_id),
        "intent_id": intent.source_intent_id,
        "client_order_id": intent.client_order_id,
        "route": intent.route.value,
        "authority": authority_id,
        "requested_quantity": str(intent.approved_volume),
        "request_id": intent.request_id,
        "correlation_id": intent.correlation_id,
        "authority_timestamp": authority_timestamp.isoformat(),
        "received_at": received_at.isoformat(),
    }


def _order_result_fields(
    intent: OrderIntent,
    result: BrokerOrderResult,
) -> dict[str, JsonValue]:
    """Normalize one Broker order mutation result without upgrading evidence.

    Args:
        intent: Dispatched executable intent.
        result: Receiver-owned Broker order result.

    Returns:
        JSON-safe result fields for conservative classification.
    """
    logger.debug("Normalizing Broker order result %s", result.outcome)
    filled = result.filled_quantity or Decimal(0)
    if result.outcome == "UNKNOWN":
        status = "unknown_outcome"
    elif result.outcome == "REJECTED":
        status = "rejected"
    elif result.outcome == "PARTIAL":
        status = "partial"
    elif intent.action == "cancel_order":
        status = "cancelled"
    elif filled == intent.approved_volume:
        status = "filled"
    else:
        status = "accepted"
    return {
        "status": status,
        "provider_order_id": result.order_id,
        "provider_deal_ids": list(result.deal_ids),
        "filled_quantity": str(filled),
        "average_price": (
            None if result.average_price is None else str(result.average_price)
        ),
    }


def _broker_raw_response(
    intent: OrderIntent,
    result: StandardResponse[BrokerOrderResult] | StandardResponse[BrokerPosition],
    received_at: datetime,
) -> dict[str, JsonValue]:
    """Normalize one canonical Broker result for receipt classification.

    Args:
        intent: Dispatched executable intent.
        result: Canonical Broker mutation result.
        received_at: Injected Trading receipt timestamp.

    Returns:
        JSON-safe response material.
    """
    broker, operation, _, timestamp = _broker_evidence(result)
    logger.debug("Normalizing Broker result for operation %s", operation)
    raw = _base_raw_response(
        intent,
        broker,
        result.metadata.request_id,
        timestamp,
        received_at,
    )
    if result.status == "error":
        error = result.error
        explicit_rejection = (
            error is not None and error.code in _EXPLICIT_REJECTION_CODES
        )
        raw.update(
            {
                "status": "rejected" if explicit_rejection else "unknown_outcome",
                "filled_quantity": "0",
                "rate_limited": (
                    error is not None
                    and error.code == BrokerErrorCode.BROKER_RATE_LIMITED.value
                ),
            }
        )
        return raw
    if isinstance(result.data, BrokerOrderResult):
        raw.update(_order_result_fields(intent, result.data))
        authority_time = result.data.provider_timestamp or result.data.retrieved_at
        raw["authority_timestamp"] = authority_time.isoformat()
        return raw
    if isinstance(result.data, BrokerPosition):
        raw.update(
            {
                "status": "accepted",
                "provider_order_id": result.data.position_id,
                "filled_quantity": "0",
            }
        )
        authority_time = result.data.provider_timestamp or result.data.retrieved_at
        raw["authority_timestamp"] = authority_time.isoformat()
        return raw
    raw.update({"status": "success", "filled_quantity": "0"})
    return raw


def _validate_broker_selection(
    intent: OrderIntent,
    connection: BrokerConnectionConfig | None,
    broker_adapter: BrokerAdapter | None,
) -> tuple[BrokerConnectionConfig, BrokerAdapter]:
    """Validate explicit paper/live authority selection.

    Args:
        intent: Executable intent selecting paper or live.
        connection: Injected resolved Broker connection material.
        broker_adapter: Injected asynchronous Broker adapter.

    Returns:
        Validated connection and adapter pair.

    Raises:
        TradingError: If authority material is absent, disabled, or mismatched.
    """
    logger.debug("Validating injected Broker authority selection")
    if connection is None or broker_adapter is None:
        raise TradingError("SERVICE_UNAVAILABLE", "Broker authority is unavailable")
    if not connection.provider_enabled:
        raise TradingError("GATE_BLOCKED", "Broker provider is disabled")
    if intent.provider_id != connection.broker_id.value:
        raise TradingError("SCOPE_MISMATCH", "Broker provider does not match intent")
    if intent.route.value == "live" and connection.environment.value != "live":
        raise TradingError("SCOPE_MISMATCH", "Live route requires live environment")
    if intent.route.value == "paper" and connection.environment.value == "live":
        raise TradingError("SCOPE_MISMATCH", "Paper route cannot use live environment")
    if broker_adapter.contract_version != "v1":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter contract is incompatible")
    if broker_adapter.schema_id != "brokers.adapter.v1":
        raise TradingError("ADAPTER_INCOMPATIBLE", "Adapter schema is incompatible")
    return connection, broker_adapter


async def _invoke_broker(
    intent: OrderIntent,
    connection: BrokerConnectionConfig,
    broker_adapter: BrokerAdapter,
) -> StandardResponse[BrokerOrderResult] | StandardResponse[BrokerPosition]:
    """Adapt and invoke exactly one receiver-owned Broker mutation.

    Args:
        intent: Complete executable intent.
        connection: Resolved Broker connection material.
        broker_adapter: Selected asynchronous Broker adapter.

    Returns:
        Canonical Broker result from exactly one mutation call.

    Raises:
        TradingError: If the intent action has no complete Broker mutation DTO.
        ValueError: If receiver-owned DTO validation fails before mutation.
    """
    logger.info("Invoking sole Broker mutation for action %s", intent.action)
    if intent.action == "submit_order":
        request = BrokerOrderRequest(
            symbol=intent.symbol,
            side=intent.side,
            order_type=intent.order_type,
            quantity=intent.approved_volume,
            quantity_unit=intent.quantity_unit,
            environment=connection.environment,
            account_reference=connection.account_reference,
            limit_price=intent.price,
            stop_price=intent.stop_price,
            stop_loss=intent.stop_loss,
            take_profit=intent.take_profit,
            time_in_force=intent.time_in_force,
            expiration=intent.expiration,
            client_order_id=intent.client_order_id,
        )
        return await broker_adapter.place_order(request)
    if intent.action == "modify_order":
        if intent.target_broker_order_id is None:
            raise TradingError("INVALID_REQUEST", "Broker order target is absent")
        modification = BrokerOrderModificationRequest(
            order_id=intent.target_broker_order_id,
            quantity=intent.approved_volume,
            limit_price=intent.price,
            stop_price=intent.stop_price,
            stop_loss=intent.stop_loss,
            take_profit=intent.take_profit,
            time_in_force=intent.time_in_force,
            expiration=intent.expiration,
        )
        return await broker_adapter.modify_order(modification)
    if intent.action == "cancel_order":
        if intent.target_broker_order_id is None:
            raise TradingError("INVALID_REQUEST", "Broker order target is absent")
        return await broker_adapter.cancel_order(intent.target_broker_order_id)
    if intent.action == "modify_position":
        if intent.target_broker_position_id is None:
            raise TradingError("INVALID_REQUEST", "Broker position target is absent")
        position_modification = BrokerPositionModificationRequest(
            position_id=intent.target_broker_position_id,
            stop_loss=intent.stop_loss,
            take_profit=intent.take_profit,
        )
        return await broker_adapter.modify_position(position_modification)
    if intent.action in {"close_position", "reduce_exposure"}:
        if intent.target_broker_position_id is None:
            raise TradingError("INVALID_REQUEST", "Broker position target is absent")
        close_request = BrokerPositionCloseRequest(
            position_id=intent.target_broker_position_id,
            quantity=intent.approved_volume,
            quantity_unit=intent.quantity_unit,
        )
        return await broker_adapter.close_position(close_request)
    raise TradingError("INVALID_REQUEST", "Action has no Broker mutation mapping")


def _timeout_receipt(intent: OrderIntent, observed_at: datetime) -> ExecutionReceipt:
    """Classify one elapsed Broker mutation as an unknown outcome.

    Args:
        intent: Intent whose mutation boundary timed out.
        observed_at: Injected timeout observation timestamp.

    Returns:
        Conservative receipt requiring reconciliation.
    """
    logger.warning("Classifying Broker dispatch timeout as unknown outcome")
    raw = _base_raw_response(
        intent,
        intent.provider_id or "broker",
        f"timeout-{intent.client_order_id}-{intent.idempotency_hash}",
        observed_at,
        observed_at,
    )
    raw.update({"timed_out": True, "filled_quantity": "0"})
    return _classify_authority_response_value(raw, _CLASSIFICATION_POLICY)


def _uncertain_failure_receipt(
    intent: OrderIntent, observed_at: datetime
) -> ExecutionReceipt:
    """Classify an unexpected authority failure without exposing provider details.

    Args:
        intent: Intent whose mutation result could not be proven.
        observed_at: Injected failure observation timestamp.

    Returns:
        Conservative receipt requiring reconciliation.
    """
    logger.error("Classifying unexpected authority failure as unknown outcome")
    raw = _base_raw_response(
        intent,
        intent.provider_id or "simulation",
        f"uncertain-{intent.client_order_id}-{intent.idempotency_hash}",
        observed_at,
        observed_at,
    )
    raw.update({"authority_failure": True, "filled_quantity": "0"})
    return _classify_authority_response_value(raw, _CLASSIFICATION_POLICY)


def _validate_dispatch_policy(operation_timeout_seconds: Decimal) -> None:
    """Validate exact injected Broker dispatch policy.

    Args:
        operation_timeout_seconds: Candidate operation timeout.

    Raises:
        TradingError: If the timeout is not finite and positive.
    """
    logger.debug("Validating injected Trading dispatch policy")
    if (
        not isinstance(operation_timeout_seconds, Decimal)
        or not operation_timeout_seconds.is_finite()
        or operation_timeout_seconds <= 0
    ):
        raise TradingError("CONFIGURATION_INVALID", "Dispatch timeout is invalid")


async def _dispatch_order_intent_value(  # noqa: C901, PLR0912
    intent: OrderIntent,
    connection: BrokerConnectionConfig | None,
    broker_adapter: BrokerAdapter | None,
    simulation_dispatch: Callable[
        [OrderIntent], Awaitable[StandardResponse[ExecutionReceipt] | ExecutionReceipt]
    ]
    | None,
    *,
    operation_timeout_seconds: Decimal,
    clock: Callable[[], datetime],
) -> ExecutionReceipt:
    """Dispatch exactly one approved intent to its selected authority.

    Args:
        intent: Complete deterministic executable intent.
        connection: Broker connection material for paper/live, otherwise ``None``.
        broker_adapter: Broker mutation authority for paper/live, otherwise ``None``.
        simulation_dispatch: Simulation mutation callback for sim, otherwise ``None``.
        operation_timeout_seconds: Validated exact Broker operation timeout.
        clock: Injected aware UTC receipt clock.

    Returns:
        Canonical execution receipt from the selected authority.

    Raises:
        TradingError: If authority selection, DTO construction, or response evidence
            is absent, mismatched, or unsafe.
    """
    logger.info(
        "Dispatching Trading intent %s via %s", intent.client_order_id, intent.route
    )
    _validate_dispatch_policy(operation_timeout_seconds)
    if intent.route.value == "sim":
        if simulation_dispatch is None:
            raise TradingError("SERVICE_UNAVAILABLE", "Simulation authority is absent")
        if connection is not None or broker_adapter is not None:
            raise TradingError(
                "SCOPE_MISMATCH", "Sim dispatch received Broker authority"
            )
        try:
            async with asyncio.timeout(float(operation_timeout_seconds)):
                simulation_response = await simulation_dispatch(intent)
        except TimeoutError:
            return _timeout_receipt(intent, clock())
        except TradingError:
            raise
        except Exception:
            return _uncertain_failure_receipt(intent, clock())
        if isinstance(simulation_response, ExecutionReceipt):
            receipt = simulation_response
        elif simulation_response.status != "success" or not isinstance(
            simulation_response.data, ExecutionReceipt
        ):
            raise TradingError(
                "MALFORMED_RECEIPT", "Simulation returned an unsuccessful response"
            )
        else:
            receipt = simulation_response.data
        if (
            receipt.client_order_id != intent.client_order_id
            or receipt.intent_id != intent.source_intent_id
            or receipt.route != intent.route
            or receipt.request_id != intent.request_id
            or receipt.correlation_id != intent.correlation_id
        ):
            raise TradingError(
                "MALFORMED_RECEIPT", "Simulation receipt scope mismatches"
            )
        return receipt
    if simulation_dispatch is not None:
        raise TradingError(
            "SCOPE_MISMATCH", "Broker dispatch received Simulation authority"
        )
    selected_connection, selected_adapter = _validate_broker_selection(
        intent,
        connection,
        broker_adapter,
    )
    try:
        async with asyncio.timeout(float(operation_timeout_seconds)):
            result = await _invoke_broker(
                intent,
                selected_connection,
                selected_adapter,
            )
    except TimeoutError:
        return _timeout_receipt(intent, clock())
    except TradingError:
        raise
    except ValueError as error:
        raise TradingError(
            "INVALID_REQUEST",
            "Broker mutation request is invalid",
        ) from error
    except Exception:
        return _uncertain_failure_receipt(intent, clock())
    broker, _, environment, _ = _broker_evidence(result)
    if (
        broker != selected_connection.broker_id.value
        or environment != selected_connection.environment.value
    ):
        raise TradingError("MALFORMED_RECEIPT", "Broker result scope mismatches")
    return _classify_authority_response_value(
        _broker_raw_response(intent, result, clock()),
        _CLASSIFICATION_POLICY,
    )


async def dispatch_order_intent(
    intent: OrderIntent,
    connection: BrokerConnectionConfig | None,
    broker_adapter: BrokerAdapter | None,
    simulation_dispatch: Callable[
        [OrderIntent], Awaitable[StandardResponse[ExecutionReceipt] | ExecutionReceipt]
    ]
    | None,
    *,
    operation_timeout_seconds: Decimal,
    clock: Callable[[], datetime],
) -> StandardResponse[ExecutionReceipt]:
    """Dispatch one intent and preserve the raw receipt in response data.

    Args:
        intent: Complete deterministic executable intent.
        connection: Broker connection material for paper/live routes.
        broker_adapter: Broker mutation authority for paper/live routes.
        simulation_dispatch: Simulation mutation callback for sim routes.
        operation_timeout_seconds: Validated exact Broker operation timeout.
        clock: Injected aware UTC receipt clock.

    Returns:
        Successful receipt response, or an error response for unknown outcomes.
    """
    try:
        receipt = await _dispatch_order_intent_value(
            intent,
            connection,
            broker_adapter,
            simulation_dispatch,
            operation_timeout_seconds=operation_timeout_seconds,
            clock=clock,
        )
    except Exception as error:
        from app.services.trading.contracts.errors import map_trading_error

        return map_trading_error(error, {"client_order_id": intent.client_order_id})
    if receipt.status == "unknown_outcome":
        return error_trading_response(
            code="UNKNOWN_OUTCOME",
            details={"receipt": receipt.model_dump(mode="json")},
            operation="trading.dispatch_order_intent",
            message="Trading authority outcome requires reconciliation",
            risk_level="critical",
            request_id=receipt.request_id,
            correlation_id=receipt.correlation_id,
            read_only=False,
            modifies_database=True,
            places_trade=intent.route.value in {"paper", "live"},
            requires_network=intent.route.value in {"paper", "live"},
            legacy_status="unknown_outcome",
        )
    return success_trading_response(
        receipt,
        operation="trading.dispatch_order_intent",
        message="Trading authority receipt received",
        risk_level="critical",
        request_id=receipt.request_id,
        correlation_id=receipt.correlation_id,
        read_only=False,
        modifies_database=True,
        places_trade=intent.route.value in {"paper", "live"},
        requires_network=intent.route.value in {"paper", "live"},
        legacy_status=receipt.status,
    )


__all__ = ["dispatch_order_intent"]

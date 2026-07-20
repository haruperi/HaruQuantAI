"""Execution send service over the MT5 MCP boundary.

Classes and functions:
    BrokerSendGateway: Class. Provides BrokerSendGateway behavior for execution workflows.
    BrokerSendResult: Class. Provides BrokerSendResult behavior for execution workflows.
    ExecutionSendService: Class. Provides ExecutionSendService behavior for execution workflows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.agentic.contracts.execution_intent.model import ExecutionIntent
from app.services.utils.logger import logger


class BrokerSendGateway(Protocol):
    """Minimal mutating MT5 MCP gateway surface used by the send service."""

    def place_order(self, request: dict[str, Any]) -> Any:
        """Place an order through the broker gateway."""
        ...

    def modify_position(self, request: dict[str, Any]) -> Any:
        """Modify a position through the broker gateway."""
        ...

    def partial_close(self, request: dict[str, Any]) -> Any:
        """Partially close a position through the broker gateway."""
        ...

    def full_close(self, request: dict[str, Any]) -> Any:
        """Fully close a position through the broker gateway."""
        ...

    def cancel_order(self, request: dict[str, Any]) -> Any:
        """Cancel an order through the broker gateway."""
        ...


@dataclass(frozen=True)
class BrokerSendResult:
    """Raw broker send result with the submitted payload echo."""

    request_payload: dict[str, Any]
    broker_response: Any


class ExecutionSendService:
    """Submit execution intents through the MT5 MCP mutating tool boundary."""

    def __init__(self, gateway: BrokerSendGateway) -> None:
        self._gateway = gateway
        logger.debug(
            "ExecutionSendService initialized", component="execution.send_service"
        )

    def send(self, intent: ExecutionIntent) -> BrokerSendResult:
        """Perform the send execution service operation."""
        request_payload = {
            "action": intent.payload.broker_action_type,
            "symbol": intent.payload.symbol,
            "side": intent.payload.side,
            "order_type": intent.payload.order_type,
            "size": dict(intent.payload.size),
            "price_params": dict(intent.payload.price_params),
            "sl_tp_params": dict(intent.payload.sl_tp_params),
            "idempotency_key": intent.payload.idempotency_key,
        }
        logger.info(
            "Dispatching broker action",
            component="execution.send_service",
            action=intent.payload.broker_action_type,
            symbol=intent.payload.symbol,
            side=intent.payload.side,
            idempotency_key=intent.payload.idempotency_key,
        )
        broker_response = _dispatch_broker_action(self._gateway, request_payload)
        logger.debug(
            "Broker action dispatched",
            component="execution.send_service",
            action=intent.payload.broker_action_type,
            symbol=intent.payload.symbol,
        )
        return BrokerSendResult(
            request_payload=request_payload,
            broker_response=broker_response,
        )


def _dispatch_broker_action(
    gateway: BrokerSendGateway, request_payload: dict[str, Any]
) -> Any:
    action = request_payload["action"]
    if action == "submit_order":
        return gateway.place_order(request_payload)
    if action == "modify_order":
        return gateway.modify_position(request_payload)
    if action == "cancel_order":
        return gateway.cancel_order(request_payload)
    if action == "close_position":
        close_fraction = request_payload["size"].get("close_fraction")
        if close_fraction is not None and 0 < float(close_fraction) < 1:
            return gateway.partial_close(request_payload)
        return gateway.full_close(request_payload)
    logger.error(
        "Unsupported broker_action_type",
        component="execution.send_service",
        action=action,
    )
    raise ValueError("unsupported broker_action_type for send service")

"""The single broker mutation boundary for the trading package (BF-TRD-003).

This module is the *only* place in ``app/services/trading/`` permitted to call
a broker mutation entrypoint. Everything else in the package composes payloads,
evaluates gates, and persists projections without touching a broker.

It imports the active-broker *resolver* (``app.services.brokers.router``), never
a provider SDK. The resolver hands back whichever adapter is configured, so the
package's "no provider SDKs" rule stated in the package README still holds.

Keeping the boundary one file wide means `grep -rl "brokers.router"` over the
package returns exactly two hits: this module and the read-only ``info/`` layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.trading.execution.response_classifier import (
    normalize_broker_response,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.services.trading.contracts import JsonObject, NormalizedTradeResult

# `trader` treated these three provider return codes as success:
# 10009 (TRADE_RETCODE_DONE), 10008 (TRADE_RETCODE_PLACED), and 0.
# Preserved verbatim -- see plan Appendix A.3.
SUCCESS_RETCODES = frozenset({"10009", "10008", "0"})


def active_broker_name() -> str:
    """Return the name of the currently configured broker adapter.

    Returns:
        str: Active broker identifier, e.g. ``mt5`` or ``ctrader``.
    """
    from app.services.brokers.router import get_active_broker_name

    provider = get_active_broker_name()
    logger.debug("Resolved active broker provider {}.", provider)
    return provider


def build_broker_dispatch_callable(
    *,
    payload: JsonObject,
    request_id: str,
    provider: str | None = None,
) -> Callable[[], NormalizedTradeResult]:
    """Bind a dispatch payload to the active broker's ``trade()`` entrypoint.

    The returned zero-argument callable is what
    :meth:`~app.services.trading.execution.coordinator.ExecutionCoordinator.dispatch_async`
    submits to its executor. It is not invoked here.

    Args:
        payload: JSON-safe broker dispatch payload.
        request_id: Unique request identifier stamped onto the normalized
            result.
        provider: Broker identifier. Resolved from the active router when
            omitted.

    Returns:
        Callable[[], NormalizedTradeResult]: Callable performing the broker
        mutation and normalizing its raw response.
    """
    resolved_provider = provider or active_broker_name()
    logger.info(
        "Binding broker dispatch callable for request {} on provider {}.",
        request_id,
        resolved_provider,
    )

    def _dispatch() -> NormalizedTradeResult:
        """Perform the broker mutation and normalize the raw response.

        Returns:
            NormalizedTradeResult: Normalized broker outcome.
        """
        from app.services.brokers.router import get_broker_module

        logger.info("Dispatching request {} to broker.", request_id)
        broker = get_broker_module()
        raw_result = broker.trade(dict(payload))
        return normalize_broker_response(
            provider=resolved_provider,
            raw_response=raw_result,
            request_id=request_id,
        )

    return _dispatch


def is_success_retcode(retcode: str) -> bool:
    """Return whether a provider return code represents a successful mutation.

    Args:
        retcode: Provider return code as a string.

    Returns:
        bool: True when the code is in :data:`SUCCESS_RETCODES`.
    """
    return retcode in SUCCESS_RETCODES


def snapshot_broker_state() -> tuple[list[JsonObject], list[JsonObject]]:
    """Read live positions and orders for a forced reconciliation pass.

    Mirrors the reconciliation snapshot ``trader`` took after an unknown
    outcome. Read-only: it issues no mutations.

    Returns:
        tuple[list[JsonObject], list[JsonObject]]: Live positions and live
        orders, each as JSON-safe projections.
    """
    from app.services.brokers.router import get_broker_module

    logger.info("Snapshotting broker state for reconciliation.")
    broker = get_broker_module()
    raw_positions = broker.get_position_info() or []
    raw_orders = broker.get_order_info() or []

    positions: list[JsonObject] = [
        {
            "ticket": getattr(position, "ticket", 0),
            "volume": str(getattr(position, "volume", 0.0)),
            "type": getattr(position, "type", 0),
            "profit": str(getattr(position, "profit", 0.0)),
        }
        for position in raw_positions
    ]
    orders: list[JsonObject] = [
        {
            "ticket": getattr(order, "ticket", 0),
            "volume_current": str(getattr(order, "volume_current", 0.0)),
        }
        for order in raw_orders
    ]
    logger.debug(
        "Snapshotted {} position(s) and {} order(s).", len(positions), len(orders)
    )
    return positions, orders

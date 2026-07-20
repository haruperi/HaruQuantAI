"""Single static broker capability declaration source."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal

from app.services.brokers.contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerId,
)

_LOCAL = {
    BrokerCapabilityId.DISCONNECT,
    BrokerCapabilityId.GET_CONNECTION_STATUS,
    BrokerCapabilityId.GET_LAST_ERROR,
    BrokerCapabilityId.CONNECTION_EVENTS,
    BrokerCapabilityId.GET_FEATURE_FLAGS,
    BrokerCapabilityId.SUPPORTS,
    BrokerCapabilityId.UNSUBSCRIBE,
    BrokerCapabilityId.LIST_SUBSCRIPTIONS,
}
_WRITE = {
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.MODIFY_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.MODIFY_POSITION,
    BrokerCapabilityId.CLOSE_POSITION,
}

_COMMON_TARGETS = _LOCAL | {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.RECONNECT,
}
_MT5 = _COMMON_TARGETS | {
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.SELECT_SYMBOL,
    BrokerCapabilityId.GET_QUOTE,
    BrokerCapabilityId.GET_TICKS,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
    BrokerCapabilityId.GET_SPREAD,
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.GET_PERMISSIONS,
    BrokerCapabilityId.GET_ACCOUNT_INFO,
    BrokerCapabilityId.GET_BALANCES,
    BrokerCapabilityId.GET_POSITIONS,
    BrokerCapabilityId.GET_POSITION,
    BrokerCapabilityId.GET_ORDERS,
    BrokerCapabilityId.GET_ORDER,
    BrokerCapabilityId.LIST_ORDER_HISTORY,
    BrokerCapabilityId.LIST_DEAL_HISTORY,
    BrokerCapabilityId.GET_DEAL,
    BrokerCapabilityId.LIST_ACCOUNT_TRANSACTIONS,
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.MODIFY_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.MODIFY_POSITION,
    BrokerCapabilityId.CLOSE_POSITION,
    BrokerCapabilityId.CALCULATE_MARGIN,
    BrokerCapabilityId.CALCULATE_PROFIT,
}
_CTRADER = _COMMON_TARGETS | {
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.GET_QUOTE,
    BrokerCapabilityId.GET_SPREAD,
    BrokerCapabilityId.GET_TICKS,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
    BrokerCapabilityId.GET_POSITIONS,
    BrokerCapabilityId.GET_ORDERS,
    BrokerCapabilityId.LIST_ORDER_HISTORY,
    BrokerCapabilityId.LIST_DEAL_HISTORY,
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.MODIFY_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.MODIFY_POSITION,
    BrokerCapabilityId.CLOSE_POSITION,
    BrokerCapabilityId.CALCULATE_MARGIN,
    BrokerCapabilityId.CALCULATE_PROFIT,
    BrokerCapabilityId.SUBSCRIBE_QUOTES,
}
_BINANCE_SPOT = _COMMON_TARGETS | {
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_SERVER_TIME,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.GET_MARKET_STATUS,
    BrokerCapabilityId.GET_QUOTE,
    BrokerCapabilityId.GET_TICKS,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
    BrokerCapabilityId.GET_ORDER_BOOK,
    BrokerCapabilityId.GET_SPREAD,
    BrokerCapabilityId.SUBSCRIBE_QUOTES,
    BrokerCapabilityId.SUBSCRIBE_BARS,
    BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
}
_DUKASCOPY = _COMMON_TARGETS | {
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.GET_TICKS,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
}
_YAHOO = _COMMON_TARGETS | {
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
}

_IMPLEMENTED: Mapping[BrokerId, frozenset[BrokerCapabilityId]] = MappingProxyType(
    {
        BrokerId.MT5: frozenset(_MT5),
        BrokerId.CTRADER: frozenset(_CTRADER),
        BrokerId.BINANCE_SPOT: frozenset(_BINANCE_SPOT),
        BrokerId.BINANCE_USD_M_FUTURES: frozenset(),
        BrokerId.BINANCE_COIN_M_FUTURES: frozenset(),
        BrokerId.DUKASCOPY: frozenset(_DUKASCOPY),
        BrokerId.YAHOO: frozenset(_YAHOO),
    }
)

_TARGETS: Mapping[BrokerId, set[BrokerCapabilityId]] = MappingProxyType(
    {
        BrokerId.MT5: _MT5,
        BrokerId.CTRADER: _CTRADER,
        BrokerId.BINANCE_SPOT: _BINANCE_SPOT,
        BrokerId.BINANCE_USD_M_FUTURES: set(),
        BrokerId.BINANCE_COIN_M_FUTURES: set(),
        BrokerId.DUKASCOPY: _DUKASCOPY,
        BrokerId.YAHOO: _YAHOO,
    }
)


# Read-release evidence. MT5's verified demo-account reads may be released here,
# but `_capability` excludes `_WRITE` unconditionally. Downstream Trading/Risk
# controls remain defense in depth and are never used to justify catalogue release.
_RELEASED: Mapping[BrokerId, frozenset[BrokerCapabilityId]] = MappingProxyType(
    {
        BrokerId.MT5: frozenset(_IMPLEMENTED[BrokerId.MT5] - _WRITE),
    }
)


def _capability(broker: BrokerId, operation: BrokerCapabilityId) -> BrokerCapability:
    """Handle capability.

    Args:
        broker: Value supplied to the operation.
        operation: Value supplied to the operation.

    Returns:
        The operation result.
    """
    target = operation in _TARGETS[broker]
    implemented = operation in _IMPLEMENTED[broker]
    is_write = operation in _WRITE
    # CONNECT is the adapter's verification act and IS_CONNECTED performs the
    # adapter's provider-specific check. Both remain attemptable. Other reads
    # require explicit release evidence; writes are excluded unconditionally.
    connect_ready = implemented and operation in {
        BrokerCapabilityId.CONNECT,
        BrokerCapabilityId.IS_CONNECTED,
    }
    released = (
        implemented
        and operation in _RELEASED.get(broker, frozenset())
        and operation not in _WRITE
    )
    availability: Literal["AVAILABLE", "UNAVAILABLE", "DEGRADED"] = (
        "AVAILABLE" if (connect_ready or released) else "UNAVAILABLE"
    )
    return BrokerCapability(
        capability=operation,
        implementation_status="IMPLEMENTED" if implemented else "NOT_IMPLEMENTED",
        availability=availability,
        access_mode="WRITE" if is_write else "READ",
        requirement=(
            "PERMISSION"
            if is_write
            else "AUTHENTICATION"
            if broker in {BrokerId.MT5, BrokerId.CTRADER}
            else "NONE"
        ),
        verification_status="NOT_TESTED",
        execution_model="LOCAL" if operation in _LOCAL else "PROVIDER_CALL",
        reason=(
            None
            if (connect_ready or released)
            else "Release evidence is not recorded"
            if implemented
            else "Operation is not implemented"
            if target
            else "Operation is not supported for this profile"
        ),
    )


def get_broker_capability_catalogue() -> Mapping[
    BrokerId, tuple[BrokerCapability, ...]
]:
    """Return the immutable complete profile/operation declaration catalogue."""
    return MappingProxyType(
        {
            broker: tuple(
                _capability(broker, operation) for operation in BrokerCapabilityId
            )
            for broker in BrokerId
        }
    )

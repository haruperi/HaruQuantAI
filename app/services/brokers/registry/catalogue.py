"""Single static broker capability declaration source."""

from collections.abc import Mapping
from types import MappingProxyType

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

_MT5 = set(BrokerCapabilityId) - {
    BrokerCapabilityId.REFRESH_SESSION,
    BrokerCapabilityId.GET_SERVER_TIME,
    BrokerCapabilityId.GET_TRADING_SESSIONS,
    BrokerCapabilityId.SUBSCRIBE_QUOTES,
    BrokerCapabilityId.SUBSCRIBE_BARS,
    BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
    BrokerCapabilityId.LIST_ACCOUNTS,
    BrokerCapabilityId.SELECT_ACCOUNT,
    BrokerCapabilityId.LIST_ASSETS,
    BrokerCapabilityId.GET_ASSET_INFO,
    BrokerCapabilityId.REPLACE_ORDER,
    BrokerCapabilityId.GET_COMMISSION_ESTIMATE,
}
_CTRADER = set(BrokerCapabilityId) - {
    BrokerCapabilityId.SELECT_SYMBOL,
    BrokerCapabilityId.LIST_ACCOUNTS,
    BrokerCapabilityId.SELECT_ACCOUNT,
    BrokerCapabilityId.REPLACE_ORDER,
    BrokerCapabilityId.GET_COMMISSION_ESTIMATE,
}
_BINANCE_SPOT = _LOCAL | {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.RECONNECT,
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
_DUKASCOPY = _LOCAL | {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.RECONNECT,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.GET_TICKS,
}
_YAHOO = _LOCAL | {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.GET_PLATFORM_INFO,
    BrokerCapabilityId.RECONNECT,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
}

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


# Credential-gated release evidence. MT5 has a verified real demo-account
# connection (see README "Current implementation evidence"), so its
# implemented capabilities are released for the skeleton build. Live-order
# safety remains enforced downstream by Trading's runtime gates
# (ALLOW_LIVE_MUTATIONS) and Risk's kill switch; this table only stops
# adapters whose provider connection has never been verified.
_RELEASED: Mapping[BrokerId, frozenset[BrokerCapabilityId]] = MappingProxyType(
    {
        BrokerId.MT5: frozenset(_MT5),
    }
)


def _capability(broker: BrokerId, operation: BrokerCapabilityId) -> BrokerCapability:
    implemented = operation in _TARGETS[broker]
    is_write = operation in _WRITE
    # CONNECT is the adapter's own verification act, and IS_CONNECTED is a
    # purely local read of tracked session state (no provider call): both
    # must always be attemptable so a caller can establish and observe a
    # session. Every other capability stays UNAVAILABLE until credential-gated
    # release evidence is recorded, matching this domain's fail-closed policy.
    connect_ready = implemented and operation in {
        BrokerCapabilityId.CONNECT,
        BrokerCapabilityId.IS_CONNECTED,
    }
    released = (
        implemented
        and operation in _RELEASED.get(broker, frozenset())
        and operation not in _WRITE
    )
    availability = "AVAILABLE" if (connect_ready or released) else "UNAVAILABLE"
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
            else "Operation is not implemented for this profile"
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

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
    BrokerCapabilityId.REPLACE_ORDER,
}
# Operations that mutate provider watch-list or session subscription state
# without placing an order. They are neither pure reads nor order writes, so
# they are declared `READ_WRITE` and a read-scoped consumer cannot invoke them
# by mistaking them for observations.
_SESSION_MUTATING = {
    BrokerCapabilityId.SELECT_SYMBOL,
    BrokerCapabilityId.SELECT_ACCOUNT,
    BrokerCapabilityId.SUBSCRIBE_QUOTES,
    BrokerCapabilityId.SUBSCRIBE_BARS,
    BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
    BrokerCapabilityId.UNSUBSCRIBE,
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
        BrokerId.BINANCE_SPOT: frozenset(
            {
                BrokerCapabilityId.GET_SYMBOLS,
                BrokerCapabilityId.GET_SYMBOL_INFO,
                BrokerCapabilityId.GET_HISTORICAL_BARS,
            }
        ),
        BrokerId.DUKASCOPY: frozenset(_IMPLEMENTED[BrokerId.DUKASCOPY] - _WRITE),
        BrokerId.YAHOO: frozenset({BrokerCapabilityId.GET_HISTORICAL_BARS}),
    }
)

# Recorded evidence for every released read, satisfying FR-BRK-010. A released
# capability must name the deterministic provider-response suites that prove it;
# an entry may never be added without the corresponding passing tests.
_READ_EVIDENCE: Mapping[BrokerId, tuple[str, ...]] = MappingProxyType(
    {
        BrokerId.MT5: (
            "tests/brokers/unit/test_mt5_transport.py",
            "tests/brokers/unit/test_mt5_mapping.py",
            "tests/brokers/unit/test_mt5_adapter.py",
            "tests/brokers/integration/test_provider_contracts.py",
        ),
        BrokerId.BINANCE_SPOT: (
            "tests/brokers/unit/test_binance_transport.py",
            "tests/brokers/unit/test_binance_mapping.py",
            "tests/brokers/unit/test_binance_adapter.py",
        ),
        BrokerId.DUKASCOPY: (
            "tests/brokers/unit/test_dukascopy_transport.py",
            "tests/brokers/unit/test_dukascopy_mapping.py",
            "tests/brokers/unit/test_dukascopy_adapter.py",
        ),
        BrokerId.YAHOO: (
            "tests/brokers/unit/test_yahoo_transport.py",
            "tests/brokers/unit/test_yahoo_mapping.py",
            "tests/brokers/unit/test_yahoo_adapter.py",
        ),
    }
)

# The adapter's own verification act. `connect` establishes and verifies the
# session and `is_connected` reads local/provider session state, so both remain
# attemptable without prior release evidence; every other provider call does not.
_SELF_VERIFYING = {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
}


def _access_mode(
    operation: BrokerCapabilityId,
) -> Literal["READ", "WRITE", "READ_WRITE"]:
    """Classify one operation's effect on provider and session state.

    Args:
        operation: Capability being declared.

    Returns:
        `WRITE` for order mutations, `READ_WRITE` for session-mutating
        operations, and `READ` for pure observations.
    """
    if operation in _WRITE:
        return "WRITE"
    if operation in _SESSION_MUTATING:
        return "READ_WRITE"
    return "READ"


def _capability(broker: BrokerId, operation: BrokerCapabilityId) -> BrokerCapability:
    """Declare one profile/operation entry from the single static source.

    Args:
        broker: Exact registered provider profile.
        operation: Canonical capability being declared.

    Returns:
        The complete immutable capability declaration for the pair.
    """
    target = operation in _TARGETS[broker]
    implemented = operation in _IMPLEMENTED[broker]
    # CONNECT is the adapter's verification act and IS_CONNECTED performs the
    # adapter's provider-specific check. Both remain attemptable. Other reads
    # require explicit release evidence; writes are excluded unconditionally.
    connect_ready = implemented and operation in _SELF_VERIFYING
    released = (
        implemented
        and operation in _RELEASED.get(broker, frozenset())
        and operation not in _WRITE
    )
    available = connect_ready or released
    availability: Literal["AVAILABLE", "UNAVAILABLE", "DEGRADED"] = (
        "AVAILABLE" if available else "UNAVAILABLE"
    )
    evidence = _READ_EVIDENCE.get(broker, ()) if released else ()
    return BrokerCapability(
        capability=operation,
        implementation_status="IMPLEMENTED" if implemented else "NOT_IMPLEMENTED",
        availability=availability,
        access_mode=_access_mode(operation),
        requirement=(
            "PERMISSION"
            if operation in _WRITE
            else "AUTHENTICATION"
            if broker in {BrokerId.MT5, BrokerId.CTRADER}
            else "NONE"
        ),
        verification_status="TESTED_SANDBOX" if released else "NOT_TESTED",
        verification_evidence=evidence,
        execution_model="LOCAL" if operation in _LOCAL else "PROVIDER_CALL",
        reason=(
            None
            if available
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

"""Single static broker capability matrix declaration source."""

from __future__ import annotations

import time
from collections.abc import Mapping
from types import MappingProxyType
from typing import Literal, TypedDict

from app.services.brokers.canonical_contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerId,
    StandardResponse,
)
from app.utils import (
    build_response_metadata,
    generate_id,
    success_response,
)

RiskLevel = Literal["none", "low", "medium", "high", "critical"]
OrderType = Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP"]
TimeInForce = Literal["GTC", "IOC", "FOK", "GTD", "DAY"]
Support = Literal["UNDECLARED", "SUPPORTED", "UNSUPPORTED"]
PositionMode = Literal[
    "UNDECLARED",
    "NOT_APPLICABLE",
    "ACCOUNT_DEPENDENT",
    "NETTING",
    "HEDGING",
    "NETTING_AND_HEDGING",
]
SandboxAvailability = Literal["UNDECLARED", "AVAILABLE", "UNAVAILABLE"]


class _CapabilityTraits(TypedDict):
    """Typed immutable inputs for one capability declaration."""

    supported_order_types: tuple[OrderType, ...]
    supported_time_in_force: tuple[TimeInForce, ...]
    bracket_order_support: Support
    oco_order_support: Support
    position_mode: PositionMode
    partial_fill_support: Support
    modification_support: Support
    cancellation_support: Support
    sandbox_availability: SandboxAvailability


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
    BrokerCapabilityId.ATTACH_PROTECTION,
    BrokerCapabilityId.REDUCE_POSITION,
}
_MT5_DEMO_RELEASED_WRITES = {
    BrokerCapabilityId.CHECK_ORDER,
    BrokerCapabilityId.PLACE_ORDER,
    BrokerCapabilityId.CANCEL_ORDER,
    BrokerCapabilityId.CLOSE_POSITION,
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
    BrokerCapabilityId.GET_PROVIDER_SPECIFICATION,
}
_SIMULATION = {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.DISCONNECT,
    BrokerCapabilityId.RECONNECT,
    BrokerCapabilityId.IS_CONNECTED,
    BrokerCapabilityId.GET_CONNECTION_STATUS,
    BrokerCapabilityId.PING,
    BrokerCapabilityId.GET_LAST_ERROR,
    BrokerCapabilityId.CONNECTION_EVENTS,
    BrokerCapabilityId.GET_FEATURE_FLAGS,
    BrokerCapabilityId.SUPPORTS,
    BrokerCapabilityId.GET_SYMBOLS,
    BrokerCapabilityId.GET_SYMBOL_INFO,
    BrokerCapabilityId.GET_PROVIDER_SPECIFICATION,
    BrokerCapabilityId.GET_TRADING_SESSIONS,
    BrokerCapabilityId.GET_QUOTE,
    BrokerCapabilityId.GET_SPREAD,
    BrokerCapabilityId.GET_TICKS,
    BrokerCapabilityId.GET_HISTORICAL_BARS,
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
    BrokerCapabilityId.REDUCE_POSITION,
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
    BrokerCapabilityId.GET_TRADING_SESSIONS,
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
        BrokerId.SIM: frozenset(_SIMULATION),
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
        BrokerId.SIM: _SIMULATION,
    }
)


# Provider-operation release evidence. MT5's verified demo-account reads and
# single-target writes plus cTrader's verified demo session read may be released
# here. Adapter instances independently downgrade released writes outside the
# demo environment; downstream Trading/Risk controls remain defense in depth
# and never justify release.
_RELEASED: Mapping[BrokerId, frozenset[BrokerCapabilityId]] = MappingProxyType(
    {
        BrokerId.MT5: frozenset(
            (_IMPLEMENTED[BrokerId.MT5] - _WRITE) | _MT5_DEMO_RELEASED_WRITES
        ),
        BrokerId.CTRADER: frozenset({BrokerCapabilityId.GET_TRADING_SESSIONS}),
        BrokerId.BINANCE_SPOT: frozenset(
            {
                BrokerCapabilityId.GET_SYMBOLS,
                BrokerCapabilityId.GET_SYMBOL_INFO,
                BrokerCapabilityId.GET_HISTORICAL_BARS,
            }
        ),
        BrokerId.DUKASCOPY: frozenset(_IMPLEMENTED[BrokerId.DUKASCOPY] - _WRITE),
        BrokerId.YAHOO: frozenset({BrokerCapabilityId.GET_HISTORICAL_BARS}),
        BrokerId.SIM: frozenset(_SIMULATION),
    }
)

# Recorded evidence for every released read, satisfying FR-BRK-010.
_READ_EVIDENCE: Mapping[BrokerId, tuple[str, ...]] = MappingProxyType(
    {
        BrokerId.MT5: (
            "tests/brokers/unit/test_mt5_transport.py",
            "tests/brokers/unit/test_mt5_mapping.py",
            "tests/brokers/unit/test_mt5_adapter.py",
            "tests/brokers/integration/test_provider_contracts.py",
            "tests/brokers/unit/test_provider_specifications.py",
            "tests/brokers/integration/test_provider_specification_contract.py",
        ),
        BrokerId.CTRADER: (
            "tests/brokers/unit/test_ctrader_network.py",
            "tests/brokers/unit/test_ctrader_transport.py",
            "tests/brokers/unit/test_ctrader_sessions.py",
            "tests/brokers/unit/test_ctrader_adapter.py",
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
        BrokerId.SIM: (
            "tests/brokers/unit/simulation/test_simulation_lifecycle.py",
            "tests/brokers/unit/simulation/test_simulation_reads.py",
            "tests/brokers/unit/simulation/test_simulation_deals.py",
            "tests/brokers/unit/simulation/test_simulation_transactions.py",
            "tests/brokers/unit/simulation/test_simulation_read_time.py",
            "tests/brokers/integration/test_simulation_conformance.py",
            "tests/brokers/integration/test_simulation_read_conformance.py",
            "tests/brokers/integration/test_simulation_deal_conformance.py",
            "tests/brokers/integration/test_simulation_delivery_gaps.py",
            "tests/brokers/unit/simulation/test_simulation_order_mutations.py",
            "tests/brokers/unit/simulation/test_simulation_position_mutations.py",
            "tests/brokers/unit/simulation/test_simulation_retcode_mapping.py",
            "tests/brokers/integration/test_simulation_mutation_conformance.py",
        ),
    }
)

_MT5_DEMO_WRITE_EVIDENCE = (
    "tests/brokers/unit/test_mt5_transport.py",
    "tests/brokers/unit/test_mt5_mapping.py",
    "tests/brokers/unit/test_mt5_adapter.py",
    "tests/brokers/integration/test_mt5_demo_mutations.py",
)
_MT5_DEMO_WRITE_APPROVAL = "FR-BRK-010:MT5_DEMO_ONLY"
_SIMULATION_WRITE_APPROVAL = "FR-BRK-182:SIMULATION_ONLY"

# The adapter's own verification act. `connect` establishes and verifies the
# session and `is_connected` reads local/provider session state, so both remain
# attemptable without prior release evidence; every other provider call does not.
_SELF_VERIFYING = {
    BrokerCapabilityId.CONNECT,
    BrokerCapabilityId.IS_CONNECTED,
}

_ORDER_TYPES: Mapping[BrokerId, tuple[OrderType, ...]] = MappingProxyType(
    {
        BrokerId.MT5: ("MARKET", "LIMIT", "STOP", "STOP_LIMIT"),
        BrokerId.CTRADER: ("MARKET", "LIMIT", "STOP", "STOP_LIMIT"),
    }
)
_TIME_IN_FORCE: Mapping[BrokerId, tuple[TimeInForce, ...]] = MappingProxyType(
    {BrokerId.MT5: ("IOC", "FOK")}
)


def _declared_traits(
    broker: BrokerId, operation: BrokerCapabilityId
) -> _CapabilityTraits:
    """Return explicit fail-closed adapter and route traits.

    Args:
        broker: Exact registered provider profile.
        operation: Canonical capability being declared.

    Returns:
        Trait values supported by implementation evidence. Empty order and TIF
        tuples mean unsupported; advanced order semantics remain unsupported
        unless a focused implementation exists.
    """
    is_order_write = operation in _WRITE
    supports_modify = (
        operation is BrokerCapabilityId.MODIFY_ORDER
        and operation in _IMPLEMENTED[broker]
    )
    supports_cancel = (
        operation is BrokerCapabilityId.CANCEL_ORDER
        and operation in _IMPLEMENTED[broker]
    )
    supports_partial_fill = operation is BrokerCapabilityId.PLACE_ORDER and broker in {
        BrokerId.MT5,
        BrokerId.CTRADER,
    }
    position_mode: PositionMode = (
        "ACCOUNT_DEPENDENT"
        if broker in {BrokerId.MT5, BrokerId.CTRADER}
        else "NETTING"
        if broker is BrokerId.BINANCE_SPOT
        else "NOT_APPLICABLE"
    )
    return {
        "supported_order_types": _ORDER_TYPES.get(broker, ()) if is_order_write else (),
        "supported_time_in_force": _TIME_IN_FORCE.get(broker, ())
        if is_order_write
        else (),
        "bracket_order_support": "UNSUPPORTED",
        "oco_order_support": "UNSUPPORTED",
        "position_mode": position_mode,
        "partial_fill_support": "SUPPORTED" if supports_partial_fill else "UNSUPPORTED",
        "modification_support": "SUPPORTED" if supports_modify else "UNSUPPORTED",
        "cancellation_support": "SUPPORTED" if supports_cancel else "UNSUPPORTED",
        "sandbox_availability": (
            "AVAILABLE"
            if operation in _RELEASED.get(broker, frozenset())
            else "UNAVAILABLE"
        ),
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
    # adapter's provider-specific check. Both remain attemptable. Other
    # provider calls require explicit release evidence.
    connect_ready = implemented and operation in _SELF_VERIFYING
    released = implemented and operation in _RELEASED.get(broker, frozenset())
    available = connect_ready or released
    availability: Literal["AVAILABLE", "UNAVAILABLE", "DEGRADED"] = (
        "AVAILABLE" if available else "UNAVAILABLE"
    )
    is_demo_write = broker is BrokerId.MT5 and operation in _WRITE and released
    is_simulation_write = broker is BrokerId.SIM and operation in _WRITE and released
    evidence = (
        _MT5_DEMO_WRITE_EVIDENCE
        if is_demo_write
        else _READ_EVIDENCE.get(broker, ())
        if released
        else ()
    )
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
        release_approval_reference=(
            _MT5_DEMO_WRITE_APPROVAL
            if is_demo_write
            else _SIMULATION_WRITE_APPROVAL
            if is_simulation_write
            else None
        ),
        execution_model=(
            "LOCAL"
            if broker is BrokerId.SIM or operation in _LOCAL
            else "PROVIDER_CALL"
        ),
        reason=(
            None
            if available
            else "Release evidence is not recorded"
            if implemented
            else "Operation is not implemented"
            if target
            else "Operation is not supported for this profile"
        ),
        **_declared_traits(broker, operation),
    )


def get_broker_capability_catalogue() -> StandardResponse[
    Mapping[BrokerId, tuple[BrokerCapability, ...]]
]:
    """Return the immutable complete profile/operation declaration catalogue.

    Returns:
        A successful standard response containing the immutable catalogue
        directly in ``data``.
    """
    start_time = time.perf_counter_ns()
    catalogue: Mapping[BrokerId, tuple[BrokerCapability, ...]] = MappingProxyType(
        {
            broker: tuple(
                _capability(broker, operation) for operation in BrokerCapabilityId
            )
            for broker in BrokerId
        }
    )
    metadata = build_response_metadata(
        name="brokers.capabilities.get_broker_capability_catalogue",
        domain="brokers",
        risk_level="none",
        request_id=generate_id("req"),
        start_time=start_time,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
    )
    return success_response(
        catalogue,
        message="Broker capability catalogue retrieved",
        metadata=metadata,
    )

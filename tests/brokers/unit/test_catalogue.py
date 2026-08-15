"""Static capability catalogue tests."""

from collections.abc import Mapping
from types import MappingProxyType

import pytest
from app.services.brokers import get_broker_capability_catalogue
from app.services.brokers.canonical_contracts import (
    BrokerCapability,
    BrokerCapabilityId,
    BrokerId,
)
from app.utils.identity import validate_id
from app.utils.responses.models import RiskLevel

# Verbatim transcription of the normative provider/profile capability matrix in
# `app/services/brokers/README.md` Section 4.8. Column order is MT5, cTrader,
# Binance Spot, Binance USD-M / Coin-M Futures, Dukascopy, Yahoo.
_MATRIX_COLUMNS = (
    BrokerId.MT5,
    BrokerId.CTRADER,
    BrokerId.BINANCE_SPOT,
    BrokerId.BINANCE_USD_M_FUTURES,
    BrokerId.BINANCE_COIN_M_FUTURES,
    BrokerId.DUKASCOPY,
    BrokerId.YAHOO,
)

_NORMATIVE_MATRIX: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        (
            "connect",
            "disconnect",
            "reconnect",
            "is_connected",
            "get_connection_status",
            "ping",
            "get_last_error",
            "connection_events",
            "get_feature_flags",
            "supports",
            "get_platform_info",
            "unsubscribe",
            "list_subscriptions",
            "get_historical_bars",
        ),
        ("A", "A", "A", "U", "U", "A", "A"),
    ),
    (
        ("get_symbols", "get_symbol_info", "get_ticks"),
        ("A", "A", "A", "U", "U", "A", "U"),
    ),
    (("get_quote", "get_spread"), ("A", "A", "A", "U", "U", "U", "U")),
    (
        (
            "get_positions",
            "get_orders",
            "list_order_history",
            "list_deal_history",
            "calculate_margin",
            "calculate_profit",
        ),
        ("A", "A", "U", "U", "U", "U", "U"),
    ),
    (("get_provider_specification",), ("A", "U", "U", "U", "U", "U", "U")),
    (
        (
            "select_symbol",
            "get_permissions",
            "get_account_info",
            "get_balances",
            "get_position",
            "get_order",
            "get_deal",
            "list_account_transactions",
        ),
        ("A", "U", "U", "U", "U", "U", "U"),
    ),
    (("subscribe_quotes",), ("U", "A", "A", "U", "U", "U", "U")),
    (
        (
            "get_server_time",
            "get_market_status",
            "get_order_book",
            "subscribe_bars",
            "subscribe_order_book",
        ),
        ("U", "U", "A", "U", "U", "U", "U"),
    ),
    (
        (
            "check_order",
            "place_order",
            "modify_order",
            "cancel_order",
            "modify_position",
            "close_position",
        ),
        ("W", "W", "U", "U", "U", "U", "U"),
    ),
    (
        (
            "refresh_session",
            "list_accounts",
            "select_account",
            "list_assets",
            "get_asset_info",
            "replace_order",
            "get_commission_estimate",
        ),
        ("U", "U", "U", "U", "U", "U", "U"),
    ),
    (
        # application Phase 0 safe-order-command additions (feature).
        # attach_protection and reduce_position are fail-closed UNAVAILABLE for
        # every profile until a provider records release evidence.
        ("attach_protection", "reduce_position"),
        ("U", "U", "U", "U", "U", "U", "U"),
    ),
    (("get_trading_sessions",), ("U", "A", "U", "U", "U", "U", "U")),
)


def _catalogue() -> Mapping[BrokerId, tuple[BrokerCapability, ...]]:
    """Return the successfully validated raw capability catalogue."""
    response = get_broker_capability_catalogue()
    assert response.status == "success"
    assert response.data is not None
    return response.data


def _expected_cells() -> dict[tuple[BrokerId, BrokerCapabilityId], str]:
    """Flatten the normative matrix into one cell per profile/operation.

    Returns:
        Mapping of each profile/operation pair to its normative `A`/`W`/`U` cell.
    """
    cells: dict[tuple[BrokerId, BrokerCapabilityId], str] = {}
    for operations, row in _NORMATIVE_MATRIX:
        for name in operations:
            operation = BrokerCapabilityId(name)
            for broker, value in zip(_MATRIX_COLUMNS, row, strict=True):
                cells[(broker, operation)] = value
    simulation = {
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
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.REDUCE_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
    }
    for operation in BrokerCapabilityId:
        cells[(BrokerId.SIM, operation)] = (
            "W"
            if operation
            in {
                BrokerCapabilityId.CHECK_ORDER,
                BrokerCapabilityId.PLACE_ORDER,
                BrokerCapabilityId.MODIFY_ORDER,
                BrokerCapabilityId.CANCEL_ORDER,
                BrokerCapabilityId.MODIFY_POSITION,
                BrokerCapabilityId.REDUCE_POSITION,
                BrokerCapabilityId.CLOSE_POSITION,
            }
            else "A"
            if operation in simulation
            else "U"
        )
    return cells


def _actual_cell(entry: object) -> str:
    """Reduce one declared capability to its matrix cell value.

    Args:
        entry: Declared `BrokerCapability` from the catalogue.

    Returns:
        `W` for an order-write target, `A` for another implementation target,
        and `U` when the operation is not a target for the profile.
    """
    if entry.implementation_status != "IMPLEMENTED":  # type: ignore[attr-defined]
        return "U"
    return "W" if entry.access_mode == "WRITE" else "A"  # type: ignore[attr-defined]


def test_catalogue_response_preserves_immutable_raw_data_and_metadata() -> None:
    """The standard response retains the mapping proxy and serializes it safely."""
    response = get_broker_capability_catalogue()

    assert response.status == "success"
    assert response.message == "Broker capability catalogue retrieved"
    assert response.error is None
    assert isinstance(response.data, MappingProxyType)
    with pytest.raises(TypeError):
        response.data[BrokerId.MT5] = ()
    assert response.metadata.name == (
        "brokers.capabilities.get_broker_capability_catalogue"
    )
    assert response.metadata.domain == "brokers"
    assert response.metadata.risk_level is RiskLevel.NONE
    assert validate_id(response.metadata.request_id, expected_prefix="req")
    assert response.metadata.execution_ms >= 0
    assert response.metadata.execution_ms == round(response.metadata.execution_ms, 3)
    assert response.metadata.read_only is True
    assert response.metadata.writes_file is False
    assert response.metadata.modifies_database is False
    assert response.metadata.places_trade is False
    assert response.metadata.requires_network is False
    assert dict(response.metadata.extensions) == {}
    serialized = response.model_dump(mode="json")["data"]
    assert isinstance(serialized, dict)
    assert set(serialized) == {broker.value for broker in BrokerId}


def test_catalogue_is_the_single_complete_declaration_source() -> None:
    """Every profile declares every canonical operation exactly once."""
    catalogue = _catalogue()
    assert set(catalogue) == set(BrokerId)
    for entries in catalogue.values():
        assert {entry.capability for entry in entries} == set(BrokerCapabilityId)
        writes = {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
        }
        for entry in entries:
            if entry.capability in writes and entry.availability == "AVAILABLE":
                assert entry.verification_status == "TESTED_SANDBOX"
                assert entry.verification_evidence
                assert entry.release_approval_reference


def test_only_mt5_sandbox_verified_writes_are_released() -> None:
    """FR-BRK-010 releases only evidence-backed MT5 demo-write operations."""
    catalogue = _catalogue()
    released = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.CLOSE_POSITION,
    }
    mt5_writes = tuple(
        entry for entry in catalogue[BrokerId.MT5] if entry.access_mode == "WRITE"
    )
    assert mt5_writes
    assert all(
        entry.availability
        == ("AVAILABLE" if entry.capability in released else "UNAVAILABLE")
        for entry in mt5_writes
    )
    for entry in mt5_writes:
        if entry.capability in released:
            assert entry.verification_status == "TESTED_SANDBOX"
            assert entry.release_approval_reference == "FR-BRK-010:MT5_DEMO_ONLY"
    ctrader_writes = tuple(
        entry for entry in catalogue[BrokerId.CTRADER] if entry.access_mode == "WRITE"
    )
    assert ctrader_writes
    assert all(entry.availability == "UNAVAILABLE" for entry in ctrader_writes)


def test_catalogue_matches_the_normative_matrix() -> None:
    """The README capability matrix and the static catalogue never diverge."""
    expected = _expected_cells()
    assert len(expected) == len(BrokerId) * len(BrokerCapabilityId)
    catalogue = _catalogue()
    divergences = [
        (broker.value, entry.capability.value, expected[(broker, entry.capability)])
        for broker, entries in catalogue.items()
        for entry in entries
        if _actual_cell(entry) != expected[(broker, entry.capability)]
    ]
    assert not divergences, (
        f"catalogue diverges from the normative matrix: {divergences}"
    )


def test_available_provider_calls_carry_verification_evidence() -> None:
    """FR-BRK-010: a released provider read records its verification evidence."""
    catalogue = _catalogue()
    self_verifying = {BrokerCapabilityId.CONNECT, BrokerCapabilityId.IS_CONNECTED}
    unproven = [
        (broker.value, entry.capability.value)
        for broker, entries in catalogue.items()
        for entry in entries
        if entry.availability == "AVAILABLE"
        and entry.execution_model == "PROVIDER_CALL"
        and entry.capability not in self_verifying
        and (
            entry.verification_status == "NOT_TESTED" or not entry.verification_evidence
        )
    ]
    assert not unproven, f"available provider calls without evidence: {unproven}"


def test_yahoo_historical_bars_are_released_with_provider_evidence() -> None:
    """Yahoo's tested historical-bar read is available through the registry."""
    entry = next(
        item
        for item in _catalogue()[BrokerId.YAHOO]
        if item.capability == BrokerCapabilityId.GET_HISTORICAL_BARS
    )
    assert entry.availability == "AVAILABLE"
    assert entry.verification_status == "TESTED_SANDBOX"
    assert entry.verification_evidence == (
        "tests/brokers/unit/test_yahoo_transport.py",
        "tests/brokers/unit/test_yahoo_mapping.py",
        "tests/brokers/unit/test_yahoo_adapter.py",
    )


def test_binance_data_reads_are_released_with_provider_evidence() -> None:
    """Only Data's three tested Binance Spot reads are released."""
    entries = {item.capability: item for item in _catalogue()[BrokerId.BINANCE_SPOT]}
    released = {
        BrokerCapabilityId.GET_SYMBOLS,
        BrokerCapabilityId.GET_SYMBOL_INFO,
        BrokerCapabilityId.GET_HISTORICAL_BARS,
    }
    for operation in released:
        entry = entries[operation]
        assert entry.availability == "AVAILABLE"
        assert entry.verification_evidence == (
            "tests/brokers/unit/test_binance_transport.py",
            "tests/brokers/unit/test_binance_mapping.py",
            "tests/brokers/unit/test_binance_adapter.py",
        )
    assert entries[BrokerCapabilityId.GET_QUOTE].availability == "UNAVAILABLE"


def test_ctrader_sessions_are_released_with_demo_evidence() -> None:
    """Release only the provider-validated cTrader session operation."""
    entries = {item.capability: item for item in _catalogue()[BrokerId.CTRADER]}
    session_entry = entries[BrokerCapabilityId.GET_TRADING_SESSIONS]
    assert session_entry.availability == "AVAILABLE"
    assert session_entry.verification_status == "TESTED_SANDBOX"
    assert session_entry.verification_evidence == (
        "tests/brokers/unit/test_ctrader_network.py",
        "tests/brokers/unit/test_ctrader_transport.py",
        "tests/brokers/unit/test_ctrader_sessions.py",
        "tests/brokers/unit/test_ctrader_adapter.py",
    )
    assert entries[BrokerCapabilityId.GET_SYMBOLS].availability == "UNAVAILABLE"


def test_session_mutating_operations_are_not_declared_pure_reads() -> None:
    """Watch-list and subscription mutations are declared `READ_WRITE`."""
    catalogue = _catalogue()
    session_mutating = {
        BrokerCapabilityId.SELECT_SYMBOL,
        BrokerCapabilityId.SELECT_ACCOUNT,
        BrokerCapabilityId.SUBSCRIBE_QUOTES,
        BrokerCapabilityId.SUBSCRIBE_BARS,
        BrokerCapabilityId.SUBSCRIBE_ORDER_BOOK,
        BrokerCapabilityId.UNSUBSCRIBE,
    }
    for entries in catalogue.values():
        for entry in entries:
            if entry.capability in session_mutating:
                assert entry.access_mode == "READ_WRITE"


@pytest.mark.parametrize(
    "operation",
    [
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.MODIFY_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.MODIFY_POSITION,
        BrokerCapabilityId.REDUCE_POSITION,
        BrokerCapabilityId.CLOSE_POSITION,
    ],
)
def test_every_order_mutation_is_declared_write_everywhere(
    operation: BrokerCapabilityId,
) -> None:
    """The write gate permits only evidence-backed MT5 sandbox operations."""
    catalogue = _catalogue()
    mt5_released = {
        BrokerCapabilityId.CHECK_ORDER,
        BrokerCapabilityId.PLACE_ORDER,
        BrokerCapabilityId.CANCEL_ORDER,
        BrokerCapabilityId.CLOSE_POSITION,
    }
    for broker, entries in catalogue.items():
        entry = next(item for item in entries if item.capability == operation)
        assert entry.access_mode == "WRITE"
        simulation_released = {
            BrokerCapabilityId.CHECK_ORDER,
            BrokerCapabilityId.PLACE_ORDER,
            BrokerCapabilityId.MODIFY_ORDER,
            BrokerCapabilityId.CANCEL_ORDER,
            BrokerCapabilityId.MODIFY_POSITION,
            BrokerCapabilityId.REDUCE_POSITION,
            BrokerCapabilityId.CLOSE_POSITION,
        }
        if broker is BrokerId.MT5 and operation in mt5_released:
            assert entry.availability == "AVAILABLE"
            assert entry.verification_status == "TESTED_SANDBOX"
            assert entry.release_approval_reference == "FR-BRK-010:MT5_DEMO_ONLY"
        elif broker is BrokerId.SIM and operation in simulation_released:
            assert entry.availability == "AVAILABLE"
            assert entry.verification_status == "TESTED_SANDBOX"
            assert entry.release_approval_reference == "FR-BRK-182:SIMULATION_ONLY"
        else:
            assert entry.availability == "UNAVAILABLE"


def test_adapter_and_route_traits_are_explicit_and_fail_closed() -> None:
    """Every matrix entry declares the requested routing semantics."""
    catalogue = _catalogue()
    for entries in catalogue.values():
        for entry in entries:
            assert entry.bracket_order_support != "UNDECLARED"
            assert entry.oco_order_support != "UNDECLARED"
            assert entry.position_mode != "UNDECLARED"
            assert entry.partial_fill_support != "UNDECLARED"
            assert entry.modification_support != "UNDECLARED"
            assert entry.cancellation_support != "UNDECLARED"
            assert entry.sandbox_availability != "UNDECLARED"

    mt5 = {entry.capability: entry for entry in catalogue[BrokerId.MT5]}
    place_order = mt5[BrokerCapabilityId.PLACE_ORDER]
    assert place_order.supported_order_types == (
        "MARKET",
        "LIMIT",
        "STOP",
        "STOP_LIMIT",
    )
    assert place_order.supported_time_in_force == ("IOC", "FOK")
    assert place_order.position_mode == "ACCOUNT_DEPENDENT"
    assert place_order.partial_fill_support == "SUPPORTED"
    assert place_order.sandbox_availability == "AVAILABLE"

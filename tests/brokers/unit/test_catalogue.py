"""Static capability catalogue tests."""

import pytest
from app.services.brokers import BrokerCapabilityId, BrokerId
from app.services.brokers.registry import get_broker_capability_catalogue

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
            "get_trading_sessions",
            "list_accounts",
            "select_account",
            "list_assets",
            "get_asset_info",
            "replace_order",
            "get_commission_estimate",
        ),
        ("U", "U", "U", "U", "U", "U", "U"),
    ),
)


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


def test_catalogue_is_the_single_complete_declaration_source() -> None:
    """Every profile declares every canonical operation exactly once."""
    catalogue = get_broker_capability_catalogue()
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
            if entry.capability in writes:
                assert entry.availability == "UNAVAILABLE"


def test_implemented_writes_are_still_unconditionally_unavailable() -> None:
    """DEC-BRK-003 release policy cannot be bypassed by implementation state."""
    catalogue = get_broker_capability_catalogue()
    for broker in (BrokerId.MT5, BrokerId.CTRADER):
        writes = tuple(
            entry for entry in catalogue[broker] if entry.access_mode == "WRITE"
        )
        assert writes
        assert all(entry.implementation_status == "IMPLEMENTED" for entry in writes)
        assert all(entry.availability == "UNAVAILABLE" for entry in writes)


def test_catalogue_matches_the_normative_matrix() -> None:
    """The README capability matrix and the static catalogue never diverge."""
    expected = _expected_cells()
    assert len(expected) == len(BrokerId) * len(BrokerCapabilityId)
    catalogue = get_broker_capability_catalogue()
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
    catalogue = get_broker_capability_catalogue()
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
        for item in get_broker_capability_catalogue()[BrokerId.YAHOO]
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
    entries = {
        item.capability: item
        for item in get_broker_capability_catalogue()[BrokerId.BINANCE_SPOT]
    }
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


def test_session_mutating_operations_are_not_declared_pure_reads() -> None:
    """Watch-list and subscription mutations are declared `READ_WRITE`."""
    catalogue = get_broker_capability_catalogue()
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
        BrokerCapabilityId.CLOSE_POSITION,
    ],
)
def test_every_order_mutation_is_declared_write_everywhere(
    operation: BrokerCapabilityId,
) -> None:
    """The order-write release gate covers all six mutations on every profile."""
    catalogue = get_broker_capability_catalogue()
    for entries in catalogue.values():
        entry = next(item for item in entries if item.capability == operation)
        assert entry.access_mode == "WRITE"
        assert entry.availability == "UNAVAILABLE"

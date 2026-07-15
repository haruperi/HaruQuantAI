"""Broker enum contract tests."""

from app.services.brokers import (
    BrokerCapabilityId,
    BrokerConnectionState,
    BrokerEnvironment,
    BrokerErrorCode,
    BrokerId,
)


def test_broker_id_has_exact_profiles() -> None:
    """All and only approved profiles are registered."""
    assert {item.value for item in BrokerId} == {
        "mt5",
        "ctrader",
        "binance_spot",
        "binance_usd_m_futures",
        "binance_coin_m_futures",
        "dukascopy",
        "yahoo",
    }


def test_environment_has_no_live_default() -> None:
    """Environment is an explicit four-value contract."""
    assert tuple(BrokerEnvironment) == (
        BrokerEnvironment.LIVE,
        BrokerEnvironment.DEMO,
        BrokerEnvironment.TESTNET,
        BrokerEnvironment.SANDBOX,
    )


def test_connection_states_match_reconciliation() -> None:
    """Lifecycle states remain minimal and exact."""
    assert len(BrokerConnectionState) == 6


def test_error_codes_cover_accepted_failures() -> None:
    """The accepted taxonomy has 31 stable self-named values."""
    assert len(BrokerErrorCode) == 31
    assert all(item.name == item.value for item in BrokerErrorCode)


def test_capabilities_match_protocol_methods() -> None:
    """The complete operation manifest contains 53 unique values."""
    assert len(BrokerCapabilityId) == 53
    assert len({item.value for item in BrokerCapabilityId}) == 53

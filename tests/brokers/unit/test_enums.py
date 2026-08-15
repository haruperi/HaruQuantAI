"""Broker enum contract tests."""

from app.services.brokers.canonical_contracts import (
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
        "sim",
    }


def test_environment_has_no_live_default() -> None:
    """Environment is an explicit five-value contract."""
    assert tuple(BrokerEnvironment) == (
        BrokerEnvironment.LIVE,
        BrokerEnvironment.DEMO,
        BrokerEnvironment.TESTNET,
        BrokerEnvironment.SANDBOX,
        BrokerEnvironment.SIMULATION,
    )


def test_connection_states_match_reconciliation() -> None:
    """Lifecycle states remain minimal and exact."""
    assert len(BrokerConnectionState) == 6


def test_error_codes_cover_accepted_failures() -> None:
    """The accepted taxonomy has 31 stable self-named values."""
    assert len(BrokerErrorCode) == 31
    assert all(item.name == item.value for item in BrokerErrorCode)


def test_capabilities_match_protocol_methods() -> None:
    """The complete operation manifest contains 56 unique values.

    The application Phase 0 safe-order-command port (``feature``)
    added ``attach_protection`` and ``reduce_position`` to the 53 prior
    values; parity-programme Phase 4a added ``get_provider_specification``.
    """
    assert len(BrokerCapabilityId) == 56
    assert len({item.value for item in BrokerCapabilityId}) == 56

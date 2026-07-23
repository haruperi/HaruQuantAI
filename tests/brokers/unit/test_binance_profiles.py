"""Binance immutable profile declaration tests."""

from app.services.brokers import BrokerEnvironment, BrokerId
from app.services.brokers.binance_session.profiles import _BINANCE_PROFILES


def test_every_registered_binance_profile_is_declared() -> None:
    """Spot and both registered Futures profiles are declared exactly once."""
    assert set(_BINANCE_PROFILES) == {
        BrokerId.BINANCE_SPOT,
        BrokerId.BINANCE_USD_M_FUTURES,
        BrokerId.BINANCE_COIN_M_FUTURES,
    }


def test_binance_profiles_never_allow_demo_or_sandbox() -> None:
    """Every Binance profile only declares LIVE and TESTNET environments."""
    for profile in _BINANCE_PROFILES.values():
        assert profile.environments == {
            BrokerEnvironment.LIVE,
            BrokerEnvironment.TESTNET,
        }


def test_binance_profiles_share_the_same_credential_shape() -> None:
    """Every profile requires exactly api_key/api_secret credentials."""
    for profile in _BINANCE_PROFILES.values():
        assert profile.credential_keys == ("api_key", "api_secret")


def test_binance_profile_endpoint_modes_are_distinct() -> None:
    """Each product profile declares its own distinct endpoint mode."""
    modes = {profile.endpoint_mode for profile in _BINANCE_PROFILES.values()}
    assert modes == {"spot", "usd_m_futures", "coin_m_futures"}

"""Immutable Binance product-profile declarations."""

from dataclasses import dataclass

from app.services.brokers.contracts import BrokerEnvironment, BrokerId


@dataclass(frozen=True, slots=True)
class _BinanceProfile:
    """Represent the binance profile broker contract or runtime behavior."""

    broker_id: BrokerId
    environments: frozenset[BrokerEnvironment]
    endpoint_mode: str
    credential_keys: tuple[str, ...]


_BINANCE_PROFILES = {
    BrokerId.BINANCE_SPOT: _BinanceProfile(
        broker_id=BrokerId.BINANCE_SPOT,
        environments=frozenset({BrokerEnvironment.LIVE, BrokerEnvironment.TESTNET}),
        endpoint_mode="spot",
        credential_keys=("api_key", "api_secret"),
    ),
    BrokerId.BINANCE_USD_M_FUTURES: _BinanceProfile(
        broker_id=BrokerId.BINANCE_USD_M_FUTURES,
        environments=frozenset({BrokerEnvironment.LIVE, BrokerEnvironment.TESTNET}),
        endpoint_mode="usd_m_futures",
        credential_keys=("api_key", "api_secret"),
    ),
    BrokerId.BINANCE_COIN_M_FUTURES: _BinanceProfile(
        broker_id=BrokerId.BINANCE_COIN_M_FUTURES,
        environments=frozenset({BrokerEnvironment.LIVE, BrokerEnvironment.TESTNET}),
        endpoint_mode="coin_m_futures",
        credential_keys=("api_key", "api_secret"),
    ),
}

"""Feature specification manifest for Binance Connection."""

from __future__ import annotations

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-BINANCE",
    domain="broker",
    provides=frozenset({PROVIDER_BINANCE_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Direct provider connection and operational adapter for Binance Crypto Exchange.",
    state=StateDeclaration(
        namespace="broker.binance",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Binance connection configuration and state",
    ),
    config_keys=frozenset(
        {
            "database_path",
            "api_key",
            "api_secret",
            "testnet",
            "timeout",
        }
    ),
)

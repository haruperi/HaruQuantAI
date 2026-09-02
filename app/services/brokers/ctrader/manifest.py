"""Feature specification manifest for cTrader Connection."""

from __future__ import annotations

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CTRADER",
    domain="broker",
    provides=frozenset({PROVIDER_CTRADER_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Direct provider connection and operational adapter for Spotware cTrader OpenAPI.",
    state=StateDeclaration(
        namespace="broker.ctrader",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="cTrader connection configuration and state",
    ),
    config_keys=frozenset(
        {
            "database_path",
            "client_id",
            "client_secret",
            "access_token",
            "account_id",
            "live",
            "timeout",
        }
    ),
)

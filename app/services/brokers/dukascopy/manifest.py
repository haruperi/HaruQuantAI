"""Feature specification manifest for Dukascopy Connection."""

from __future__ import annotations

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-DUKASCOPY",
    domain="broker",
    provides=frozenset({PROVIDER_DUKASCOPY_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Direct provider connection and operational adapter for Dukascopy Bank / JForex.",
    state=StateDeclaration(
        namespace="broker.dukascopy",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Dukascopy connection configuration and state",
    ),
    config_keys=frozenset(
        {
            "database_path",
            "username",
            "password",
            "account_id",
            "live",
            "timeout",
        }
    ),
)

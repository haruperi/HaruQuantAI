"""Feature specification manifest for Yahoo Finance Provider."""

from __future__ import annotations

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-YAHOO",
    domain="broker",
    provides=frozenset({PROVIDER_YAHOO_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Market data and fundamental provider adapter for Yahoo Finance.",
    state=StateDeclaration(
        namespace="broker.yahoo",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Yahoo Finance preferences and state",
    ),
    config_keys=frozenset(
        {
            "database_path",
            "timeout",
        }
    ),
)

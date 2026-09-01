"""Feature specification for Data retention management."""

from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_RETENTION_COLLECTOR_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy as StateRetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-MANAGE_RETENTION",
    domain="data",
    provides=frozenset({MANAGE_RETENTION_CAPABILITY}),
    requires=frozenset({DATA_SERIES_RETENTION_COLLECTOR_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Define Data retention policy and collect unreachable series safely.",
    config_keys=frozenset({"database_path", "collection_limit"}),
    state=StateDeclaration(
        namespace="data.retention_policy",
        schema_version=1,
        retention_policy=StateRetentionPolicy.RETAIN,
        description="Versioned Data retention policy definitions.",
    ),
)

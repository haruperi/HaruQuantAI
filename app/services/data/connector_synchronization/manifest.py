"""Feature specification for Connector Synchronization."""

from app.contracts.data.capabilities import SYNC_CONNECTORS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-SYNC_CONNECTORS",
    domain="data",
    provides=frozenset({SYNC_CONNECTORS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Plan, fetch, checkpoint, normalize, revise, and secure provider"
        " synchronization."
    ),
    state=None,
    config_keys=frozenset(
        {
            "default_overlap_window_seconds",
            "default_deduplication_policy",
            "default_revision_policy",
            "max_records_per_page",
            "max_rate_limit_per_window",
            "rate_limit_window_seconds",
            "strict_secret_isolation",
        }
    ),
)

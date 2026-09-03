"""Feature specification for Run Data Binding."""

from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-BIND_RUN_DATA",
    domain="data",
    provides=frozenset({BIND_RUN_DATA_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Pin committed input data and validate precision prerequisites.",
    state=None,
    config_keys=frozenset(
        {
            "strict_precision_check",
            "allow_synthetic_sources",
            "require_committed_status",
            "supported_precisions",
        }
    ),
)

"""Feature specification for External Series Alignment."""

from app.contracts.data.capabilities import ALIGN_SERIES_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-ALIGN_SERIES",
    domain="data",
    provides=frozenset({ALIGN_SERIES_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Align external numeric series without future visibility.",
    state=None,
    config_keys=frozenset(
        {
            "max_series_points_per_request",
            "default_timezone",
            "default_max_age_seconds",
            "default_missing_policy",
        }
    ),
)

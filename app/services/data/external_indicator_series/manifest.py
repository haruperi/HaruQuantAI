"""Feature specification for External Indicator Series."""

from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-IMPORT_INDICATORS",
    domain="data",
    provides=frozenset({IMPORT_INDICATORS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Import and align immutable external-indicator values.",
    state=None,
    config_keys=frozenset(
        {
            "default_timezone",
            "max_points_per_series",
            "require_deterministic_reimport",
            "allow_future_timestamps",
            "default_missing_policy",
        }
    ),
)

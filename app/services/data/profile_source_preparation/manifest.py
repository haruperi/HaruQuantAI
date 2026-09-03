"""Feature specification for Volume Profile Source Preparation."""

from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-PREPARE_PROFILES",
    domain="data",
    provides=frozenset({PREPARE_PROFILES_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Prepare validated session/bin inputs for volume profile and tpo.",
    state=None,
    config_keys=frozenset(
        {
            "default_price_step",
            "default_bin_count",
            "min_price_step",
            "max_bin_count",
            "require_session_alignment",
        }
    ),
)

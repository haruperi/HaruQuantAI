"""Feature specification for Synthetic and Scenario Series."""

from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-GENERATE_SCENARIOS",
    domain="data",
    provides=frozenset({GENERATE_SCENARIOS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Create seeded synthetic bars, ticks, and bounded scenario series "
        "with complete provenance."
    ),
    state=None,
    config_keys=frozenset(
        {
            "max_records",
            "default_model",
            "default_rounding",
            "supported_transform_types",
        }
    ),
)

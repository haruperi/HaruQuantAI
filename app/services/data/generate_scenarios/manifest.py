"""Feature specification for synthetic and scenario Data generation."""

from app.contracts.data.capabilities import GENERATE_SCENARIOS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-GENERATE_SCENARIOS",
    domain="data",
    provides=frozenset({GENERATE_SCENARIOS_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Generate explicitly synthetic/scenario Data versions deterministically.",
    config_keys=frozenset({"max_points"}),
)

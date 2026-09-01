"""Feature specification for volume-profile source preparation."""

from app.contracts.data.capabilities import PREPARE_PROFILES_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-PREPARE_PROFILES",
    domain="data",
    provides=frozenset({PREPARE_PROFILES_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Validate stored Data precision for downstream profile calculations.",
    config_keys=frozenset(),
)

"""Feature specification for external indicator-series import."""

from app.contracts.data.capabilities import IMPORT_INDICATORS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-IMPORT_INDICATORS",
    domain="data",
    provides=frozenset({IMPORT_INDICATORS_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Import externally calculated indicator series as immutable Data evidence."
    ),
    config_keys=frozenset(),
)

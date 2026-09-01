"""Feature specification for point-in-time series alignment."""

from app.contracts.data.capabilities import ALIGN_SERIES_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-ALIGN_SERIES",
    domain="data",
    provides=frozenset({ALIGN_SERIES_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Align immutable external series without permitting look-ahead.",
    config_keys=frozenset(),
)

"""Feature specification for deterministic tick normalization."""

from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-NORMALIZE_TICKS",
    domain="data",
    provides=frozenset({NORMALIZE_TICKS_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Normalize raw tick batches into immutable ordered Data evidence.",
    config_keys=frozenset(),
)

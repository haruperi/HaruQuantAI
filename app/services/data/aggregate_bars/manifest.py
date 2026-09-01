"""Feature specification for deterministic bar aggregation."""

from app.contracts.catalogue.capabilities import DEFINE_SESSIONS_CAPABILITY
from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-AGGREGATE_BARS",
    domain="data",
    provides=frozenset({AGGREGATE_BARS_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset({DEFINE_SESSIONS_CAPABILITY}),
    conflicts=frozenset(),
    description="Aggregate committed bars under explicit UTC or Catalogue session boundaries.",
    config_keys=frozenset({"max_output_bars"}),
)

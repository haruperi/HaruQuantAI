"""Feature specification for Tick Normalization."""

from app.contracts.data.capabilities import NORMALIZE_TICKS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-NORMALIZE_TICKS",
    domain="data",
    provides=frozenset({NORMALIZE_TICKS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Preserve and normalize complete tick semantics.",
    state=None,
    config_keys=frozenset({"max_batch_size"}),
)

"""Feature specification for the market reference gateway."""

from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_REFERENCE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OBSERVE_MARKET_REFERENCE",
    domain="interfaces",
    provides=frozenset({OBSERVE_MARKET_REFERENCE_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset({BROWSE_REFERENCE_CAPABILITY}),
    conflicts=frozenset(),
    description=(
        "Expose market reference, quotes, bars, and directory operations "
        "over the boundary."
    ),
    state=None,
    config_keys=frozenset(),
)

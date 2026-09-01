"""Feature specification for Plugin Result Panels."""

from app.contracts.plugins.capabilities import (
    REGISTER_CONTRIBUTIONS_CAPABILITY,
    RENDER_RESULT_PANELS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-PLUG-RENDER_RESULT_PANELS",
    domain="plugins",
    provides=frozenset({RENDER_RESULT_PANELS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset({REGISTER_CONTRIBUTIONS_CAPABILITY}),
    conflicts=frozenset(),
    description=(
        "Isolate result-panel frontend bundles behind a narrow read-only bridge."
    ),
    config_keys=frozenset(
        {
            "allowed_bridge_operations",
            "enforce_secure_content_source",
            "max_panels_per_query",
        }
    ),
)

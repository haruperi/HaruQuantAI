"""Feature specification for Plugin Analysis Boundary."""

from app.contracts.plugins.capabilities import (
    ISOLATE_ANALYSIS_CAPABILITY,
    SANDBOX_PERMISSIONS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-PLUG-ISOLATE_ANALYSIS",
    domain="plugins",
    provides=frozenset({ISOLATE_ANALYSIS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset({SANDBOX_PERMISSIONS_CAPABILITY}),
    conflicts=frozenset(),
    description="Constrain plugin analysis inputs and staged outputs.",
    config_keys=frozenset(
        {
            "max_input_handles",
            "enforce_staged_output_schema",
            "max_parameter_bytes",
        }
    ),
)

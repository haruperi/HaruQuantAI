"""Feature specification for plugin development compatibility."""

from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MAINTAIN_COMPATIBILITY_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-PLUG-MAINTAIN_COMPATIBILITY",
    domain="plugins",
    provides=frozenset({MAINTAIN_COMPATIBILITY_CAPABILITY}),
    requires=frozenset(
        {DECLARE_MANIFESTS_CAPABILITY, REGISTER_CONTRIBUTIONS_CAPABILITY}
    ),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Validate plugin conformance and publish compatibility policy.",
    config_keys=frozenset(),
)

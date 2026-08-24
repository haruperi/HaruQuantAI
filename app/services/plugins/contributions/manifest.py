"""Feature specification for Plugin Contributions."""

from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    REGISTER_CONTRIBUTIONS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-PLUG-REGISTER_CONTRIBUTIONS",
    domain="plugins",
    provides=frozenset({REGISTER_CONTRIBUTIONS_CAPABILITY}),
    requires=frozenset({DECLARE_MANIFESTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Register typed plugin contribution capabilities.",
    config_keys=frozenset({"strict_contract_tests", "max_contributions_per_plugin"}),
)

"""Feature specification for Agentic role contributions."""

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, ROLES_CAPABILITY
from app.contracts.plugins.capabilities import REGISTER_CONTRIBUTIONS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-AGT-REGISTER_ROLES", domain="agentic",
    provides=frozenset({ROLES_CAPABILITY}),
    requires=frozenset({MANDATE_CAPABILITY, REGISTER_CONTRIBUTIONS_CAPABILITY}),
    optional=frozenset(), conflicts=frozenset(),
    description="Register immutable role artifacts and resolve only current independently eligible roles.",
    state=None, config_keys=frozenset(),
)

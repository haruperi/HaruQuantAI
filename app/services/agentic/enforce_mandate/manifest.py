"""Feature specification for Mandate Enforcement."""

from app.contracts.agentic.capabilities import ENFORCE_MANDATE_CAPABILITY
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    MANAGE_ACCOUNTS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-AGT-ENFORCE_MANDATE",
    domain="agentic",
    provides=frozenset({ENFORCE_MANDATE_CAPABILITY}),
    requires=frozenset({MANAGE_ACCOUNTS_CAPABILITY, ADMINISTER_SETTINGS_CAPABILITY}),
    optional=frozenset(),
    description=(
        "Validate immutable mandate identity/integrity, effective interval, "
        "objectives, enabled roles/features, environment/account/asset scope "
        "and finite budgets."
    ),
    state=None,
    config_keys=frozenset(),
)

__all__ = ["SPEC"]

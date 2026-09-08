"""Feature specification for Agentic mandate enforcement."""

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY, MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-AGT-ENFORCE_MANDATE",
    domain="agentic",
    provides=frozenset({MANDATE_CAPABILITY}),
    requires=frozenset({MANAGE_ACCOUNTS_CAPABILITY, ADMINISTER_SETTINGS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Validate immutable Agentic mandate integrity, time, scope and finite budgets without granting receiver authority.",
    state=None,
    config_keys=frozenset(),
)

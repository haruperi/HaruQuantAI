"""Feature specification for the system settings gateway."""

from app.contracts.interfaces.capabilities import OPERATE_SETTINGS_CAPABILITY
from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OPERATE_SETTINGS",
    domain="interfaces",
    provides=frozenset({OPERATE_SETTINGS_CAPABILITY}),
    requires=frozenset({ADMINISTER_SETTINGS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose system settings administration operations over the boundary.",
    state=None,
    config_keys=frozenset(),
)

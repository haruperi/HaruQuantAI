"""Feature specification for the account identity gateway."""

from app.contracts.interfaces.capabilities import OPERATE_IDENTITY_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OPERATE_IDENTITY",
    domain="interfaces",
    provides=frozenset({OPERATE_IDENTITY_CAPABILITY}),
    requires=frozenset({MANAGE_ACCOUNTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose account identity and session operations over the boundary.",
    state=None,
    config_keys=frozenset({"default_principal"}),
)

"""Feature specification for the account watchlist gateway."""

from app.contracts.interfaces.capabilities import OPERATE_WATCHLISTS_CAPABILITY
from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OPERATE_WATCHLISTS",
    domain="interfaces",
    provides=frozenset({OPERATE_WATCHLISTS_CAPABILITY}),
    requires=frozenset({MANAGE_WATCHLISTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose account watchlist operations over the boundary.",
    state=None,
    config_keys=frozenset({"default_account_id"}),
)

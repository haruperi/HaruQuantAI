"""Feature specification for the governed trading gateway."""

from app.contracts.interfaces.capabilities import OPERATE_TRADING_CAPABILITY
from app.contracts.trading.capabilities import (
    ACCOUNT_OPERATIONS_CAPABILITY,
    DISPATCH_ORDERS_CAPABILITY,
    MANAGE_TRADING_SESSIONS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OPERATE_TRADING",
    domain="interfaces",
    provides=frozenset({OPERATE_TRADING_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(
        {
            ACCOUNT_OPERATIONS_CAPABILITY,
            DISPATCH_ORDERS_CAPABILITY,
            MANAGE_TRADING_SESSIONS_CAPABILITY,
        }
    ),
    conflicts=frozenset(),
    description="Expose governed trading operations and events over the boundary.",
    state=None,
    config_keys=frozenset({"default_account_id", "max_order_quantity"}),
)

"""Feature specification for account watchlist management."""

from app.contracts.workspace.capabilities import MANAGE_WATCHLISTS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-MANAGE_WATCHLISTS",
    domain="workspace",
    provides=frozenset({MANAGE_WATCHLISTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own account watchlists with exactly-one-default invariants.",
    state=StateDeclaration(
        namespace="workspace.manage_watchlists",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Standalone users, api_watchlists, and watchlist_items tables "
            "holding account-owned watchlist state."
        ),
    ),
    config_keys=frozenset({"database_path", "auto_migrate", "default_account_id"}),
)

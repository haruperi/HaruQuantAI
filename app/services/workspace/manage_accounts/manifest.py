"""Feature specification for the account registry."""

from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-MANAGE_ACCOUNTS",
    domain="workspace",
    provides=frozenset({MANAGE_ACCOUNTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Own the workstation account registry and opaque server-side "
        "sessions: scrypt-hashed registration, login, session "
        "validation, and revocation."
    ),
    state=StateDeclaration(
        namespace="workspace.manage_accounts",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained account records and digest-only session records "
            "in the shared workspace database."
        ),
    ),
    config_keys=frozenset({"database_path"}),
)

"""Feature specification for the system settings administration feature."""

from app.contracts.workspace.capabilities import ADMINISTER_SETTINGS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-ADMINISTER_SETTINGS",
    domain="workspace",
    provides=frozenset({ADMINISTER_SETTINGS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Own the administrator settings surface: the authoritative "
        "setting-definition manifest, versioned system settings under "
        "legacy wire keys, write-only credential slots, and the MT5 "
        "snapshot bridge runtime projection."
    ),
    state=StateDeclaration(
        namespace="workspace.administer_settings",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained settings rows and audit history in the shared workspace database."
        ),
    ),
    config_keys=frozenset({"database_path"}),
)

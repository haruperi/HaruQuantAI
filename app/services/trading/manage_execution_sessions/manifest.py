"""Feature specification for the trading execution sessions manager."""

from app.contracts.trading.capabilities import MANAGE_EXECUTION_SESSIONS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-TRD-MANAGE_EXECUTION_SESSIONS",
    domain="trading",
    provides=frozenset({MANAGE_EXECUTION_SESSIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Own trading execution sessions, default session selection, "
        "lifecycle state transitions, account profile projections, and "
        "instrument constraints."
    ),
    state=StateDeclaration(
        namespace="trading.manage_execution_sessions",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained execution session profiles and instrument definitions "
            "in the database."
        ),
    ),
    config_keys=frozenset({"database_path"}),
)

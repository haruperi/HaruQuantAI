"""Feature specification for Data immutable series storage."""

from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-MANAGE_SERIES",
    domain="data",
    provides=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own immutable Data series payload storage and run-binding pins.",
    config_keys=frozenset({"database_path"}),
    state=StateDeclaration(
        namespace="data.series_store",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Immutable Data payloads and exact run-binding references.",
    ),
)

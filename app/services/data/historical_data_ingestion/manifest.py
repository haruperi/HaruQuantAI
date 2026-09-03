"""Feature specification for Historical Data Ingestion."""

from app.contracts.data.capabilities import INGEST_HISTORY_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-INGEST_HISTORY",
    domain="data",
    provides=frozenset({INGEST_HISTORY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Register sources, import files, stage, publish, describe, "
        "and account for historical data."
    ),
    state=StateDeclaration(
        namespace="data.historical_ingestion",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained historical data connections, import plans, receipts, "
            "and published data series versions."
        ),
    ),
    config_keys=frozenset({"database_path", "auto_migrate"}),
)

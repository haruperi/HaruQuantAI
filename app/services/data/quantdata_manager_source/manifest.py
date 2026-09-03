"""Feature specification for QuantDataManager Source."""

from app.contracts.data.capabilities import IMPORT_QUANTDATA_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-IMPORT_QUANTDATA",
    domain="data",
    provides=frozenset({IMPORT_QUANTDATA_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Discover and decode governed StrategyQuant QuantDataManager M1/tick "
        "files and synchronize reference metadata."
    ),
    state=StateDeclaration(
        namespace="data.quantdata_manager_source",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained QuantDataManager import specs, discovered series manifests, "
            "and decoded lineage records."
        ),
    ),
    config_keys=frozenset({"allowed_root", "database_path", "auto_migrate"}),
)

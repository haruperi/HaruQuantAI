"""Feature specification for the market-data reference browser."""

from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-BROWSE_REFERENCE",
    domain="data",
    provides=frozenset({BROWSE_REFERENCE_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Own market-data series reference catalogue, broker profiles, "
        "instrument specifications, historical bars retrieval, and "
        "market directory projections."
    ),
    state=StateDeclaration(
        namespace="data.browse_reference",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained market reference tables, broker profiles, "
            "instrument specifications, and bar history in SQLite."
        ),
    ),
    config_keys=frozenset({"database_path"}),
)

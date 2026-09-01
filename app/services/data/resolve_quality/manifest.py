"""Feature specification for explicit Data quality resolution."""

from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-RESOLVE_QUALITY",
    domain="data",
    provides=frozenset({RESOLVE_QUALITY_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Detect Data quality findings and record explicit immutable decisions.",
    config_keys=frozenset({"database_path"}),
    state=StateDeclaration(
        namespace="data.quality",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Detected quality findings and explicit resolution decisions.",
    ),
)

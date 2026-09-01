"""Feature specification for immutable run-data binding."""

from app.contracts.data.capabilities import BIND_RUN_DATA_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-BIND_RUN_DATA",
    domain="data",
    provides=frozenset({BIND_RUN_DATA_CAPABILITY}),
    requires=frozenset({DATA_SERIES_STORE_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Bind immutable committed Data versions to reproducible run manifests.",
    config_keys=frozenset({"database_path"}),
    state=StateDeclaration(
        namespace="data.run_bindings",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Immutable run-to-series bindings and precision evidence.",
    ),
)

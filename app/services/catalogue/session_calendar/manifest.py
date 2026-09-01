"""Feature specification for Sessions and Calendars."""

from app.contracts.catalogue.capabilities import DEFINE_SESSIONS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-CAT-DEFINE_SESSIONS",
    domain="catalogue",
    provides=frozenset({DEFINE_SESSIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Manage and preview effective trading intervals.",
    state=StateDeclaration(
        namespace="catalogue.sessions",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Retained trading session and market calendar definitions.",
    ),
    config_keys=frozenset({"database_path"}),
)

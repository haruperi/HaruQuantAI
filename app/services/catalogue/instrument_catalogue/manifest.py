"""Feature specification for Instrument Catalogue."""

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-CAT-CATALOG_INSTRUMENTS",
    domain="catalogue",
    provides=frozenset({CATALOG_INSTRUMENTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Manage, version, retain, and protect canonical instruments.",
    state=StateDeclaration(
        namespace="catalogue.instruments",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Retained canonical instrument definitions and version history.",
    ),
    config_keys=frozenset({"database_path"}),
)

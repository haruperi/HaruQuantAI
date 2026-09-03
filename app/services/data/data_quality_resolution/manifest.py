"""Feature specification for Data Quality and Resolution."""

from app.contracts.data.capabilities import RESOLVE_QUALITY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-RESOLVE_QUALITY",
    domain="data",
    provides=frozenset({RESOLVE_QUALITY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Detect, resolve, normalize, and serialize conflicting quality operations."
    ),
    state=None,
    config_keys=frozenset({"database_path", "auto_migrate", "max_findings"}),
)

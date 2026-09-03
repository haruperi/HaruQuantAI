"""Feature specification for Data Inspection, Export, and Retention."""

from app.contracts.data.capabilities import MANAGE_RETENTION_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-MANAGE_RETENTION",
    domain="data",
    provides=frozenset({MANAGE_RETENTION_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Preview, export, and garbage-collect data versions safely.",
    state=None,
    config_keys=frozenset(
        {
            "default_preview_limit",
            "max_preview_limit",
            "default_quarantine_days",
            "supported_export_formats",
        }
    ),
)

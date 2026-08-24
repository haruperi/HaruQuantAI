"""Feature specification for Plugin Manifests."""

from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-PLUG-DECLARE_MANIFESTS",
    domain="plugins",
    provides=frozenset({DECLARE_MANIFESTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Validate plugin identity, package integrity, compatibility, "
        "capabilities, and resource declarations."
    ),
    config_keys=frozenset(
        {"max_package_size_bytes", "max_file_count", "strict_signatures"}
    ),
)

"""Feature declaration for plugin permissions sandboxing."""

from app.contracts.plugins.capabilities import SANDBOX_PERMISSIONS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-PLUG-SANDBOX_PERMISSIONS",
    domain="plugins",
    provides=frozenset({SANDBOX_PERMISSIONS_CAPABILITY}),
    description="Grant and execute pure-Python plugins in a bounded process sandbox.",
    config_keys=frozenset(
        {
            "package_roots",
            "secret_env_names",
            "ceilings",
            "max_protocol_bytes",
            "enforcement_mode",
        }
    ),
)

"""Feature specification for Secure Local Access."""

from app.contracts.workspace.capabilities import (
    MANAGE_ACCOUNTS_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "default_session_ttl_seconds",
        "enforce_loopback",
        "allowed_remote_subnets",
        "require_authenticated_remote_policy",
    }
)

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-SECURE_LOCAL_ACCESS",
    domain="workspace",
    provides=frozenset({SECURE_LOCAL_ACCESS_CAPABILITY}),
    requires=frozenset({MANAGE_ACCOUNTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Resolve secrets and protect host access.",
    state=None,
    config_keys=CONFIG_KEYS,
)

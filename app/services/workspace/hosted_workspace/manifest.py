"""Feature specification for Hosted Workspace Boundary."""

from app.contracts.workspace.capabilities import (
    HOST_WORKSPACES_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-HOST_WORKSPACES",
    domain="workspace",
    provides=frozenset({HOST_WORKSPACES_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Isolate hosted workspaces and authorize principals.",
    state=None,
    config_keys=frozenset(),
)

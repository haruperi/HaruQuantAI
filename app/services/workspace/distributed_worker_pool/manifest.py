"""Feature specification for Distributed Worker Pool."""

from app.contracts.workspace.capabilities import (
    DISTRIBUTE_WORKERS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-DISTRIBUTE_WORKERS",
    domain="workspace",
    provides=frozenset({DISTRIBUTE_WORKERS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Register, authenticate, schedule, and transfer artifacts to remote workers."
    ),
    state=None,
    config_keys=frozenset(),
)

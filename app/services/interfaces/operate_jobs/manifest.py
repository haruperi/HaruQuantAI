"""Feature specification for job/resource/worker interface translation."""

from app.contracts.interfaces.capabilities import OPERATE_JOBS_CAPABILITY
from app.contracts.orchestration.capabilities import (
    LOCAL_WORKERS_CAPABILITY,
    MANAGE_JOBS_CAPABILITY,
    RESERVE_RESOURCES_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-IFACE-OPERATE_JOBS",
    domain="interfaces",
    provides=frozenset({OPERATE_JOBS_CAPABILITY}),
    requires=frozenset(
        {
            MANAGE_JOBS_CAPABILITY,
            RESERVE_RESOURCES_CAPABILITY,
            LOCAL_WORKERS_CAPABILITY,
        }
    ),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Translate current job, resource, and local-worker owner projections.",
    state=None,
    config_keys=frozenset(),
)

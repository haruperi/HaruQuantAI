"""Feature specification for spawn-safe local work."""

from app.contracts.orchestration.capabilities import LOCAL_WORKERS_CAPABILITY, MANAGE_JOBS_CAPABILITY, RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-ORCH-EXECUTE_LOCAL_WORK", domain="orchestration",
    provides=frozenset({LOCAL_WORKERS_CAPABILITY}),
    requires=frozenset({ARTIFACTS_CAPABILITY, MANAGE_JOBS_CAPABILITY, RESERVE_RESOURCES_CAPABILITY}),
    optional=frozenset(), conflicts=frozenset(),
    description="Execute bounded spawn-safe local work using immutable shared input handles and fenced attempts.",
    state=None, config_keys=frozenset({"max_input_bytes", "cancellation_grace_seconds"}),
)

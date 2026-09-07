"""Feature specification for durable job management."""

from app.contracts.orchestration.capabilities import MANAGE_JOBS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-ORCH-MANAGE_JOBS",
    domain="orchestration",
    provides=frozenset({MANAGE_JOBS_CAPABILITY}),
    description="Persist jobs and publish isolated progress observations.",
    state=StateDeclaration(
        namespace="orchestration.manage_jobs",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Jobs, versions, progress, and idempotency identities.",
    ),
    config_keys=frozenset({"database_path", "callback_queue_capacity"}),
)

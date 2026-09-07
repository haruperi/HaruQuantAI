"""Feature specification for governed notification delivery."""

from app.contracts.notification.capabilities import NOTIFICATION_DELIVERY_CAPABILITY
from app.contracts.orchestration.capabilities import (
    DELIVER_NOTIFICATIONS_CAPABILITY,
    MANAGE_JOBS_CAPABILITY,
)
from app.contracts.workspace.capabilities import MANAGE_ACCOUNTS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-ORCH-DELIVER_NOTIFICATIONS",
    domain="orchestration",
    provides=frozenset({DELIVER_NOTIFICATIONS_CAPABILITY}),
    requires=frozenset({MANAGE_JOBS_CAPABILITY, MANAGE_ACCOUNTS_CAPABILITY}),
    optional=frozenset({NOTIFICATION_DELIVERY_CAPABILITY}),
    description="Coordinate policy-gated notification delivery and receipts.",
    state=StateDeclaration(
        namespace="orchestration.deliver_notifications",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Idempotency identities, attempts, and delivery receipts.",
    ),
    config_keys=frozenset({"database_path"}),
)

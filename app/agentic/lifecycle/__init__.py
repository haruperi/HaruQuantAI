"""Public `FEAT-AGT-18` Artefact Promotion and Lifecycle API."""

from app.agentic.lifecycle.migrations import (
    build_lifecycle_migration_request,
    get_lifecycle_migration_statements,
)
from app.agentic.lifecycle.models import (
    LifecycleRecord,
    PromotionAssessment,
    PromotionEvidencePacket,
    build_lifecycle_record,
    build_promotion_assessment,
    build_promotion_evidence_packet,
    is_terminal_state,
    permitted_next_states,
    validate_transition,
)
from app.agentic.lifecycle.repository import build_in_memory_lifecycle_store
from app.agentic.lifecycle.service import (
    assess_promotion,
    can_transition,
    get_artifact_history,
    get_artifact_state,
    is_settled,
    transition_artifact,
)

__all__: tuple[str, ...] = (
    "LifecycleRecord",
    "PromotionAssessment",
    "PromotionEvidencePacket",
    "assess_promotion",
    "build_in_memory_lifecycle_store",
    "build_lifecycle_migration_request",
    "build_lifecycle_record",
    "build_promotion_assessment",
    "build_promotion_evidence_packet",
    "can_transition",
    "get_artifact_history",
    "get_artifact_state",
    "get_lifecycle_migration_statements",
    "is_settled",
    "is_terminal_state",
    "permitted_next_states",
    "transition_artifact",
    "validate_transition",
)

"""Promotion ladder and preconditions subsystem package.

Exports the gate checks, transition managers, and simulation route validation helpers.
"""

from app.services.trading.promotion.ladder import (
    PROMOTION_SEQUENCE,
    ROUTE_CAPABILITY_MATRIX,
    compute_canonical_promotion_hash,
    evaluate_promotion_stage_gate,
    validate_promotion_transition,
    validate_route_stage_capability,
)
from app.services.trading.promotion.preconditions import (
    validate_preactivation_conditions,
    validate_sim_metadata_lookup,
)

__all__ = [
    "PROMOTION_SEQUENCE",
    "ROUTE_CAPABILITY_MATRIX",
    "compute_canonical_promotion_hash",
    "evaluate_promotion_stage_gate",
    "validate_preactivation_conditions",
    "validate_promotion_transition",
    "validate_route_stage_capability",
    "validate_sim_metadata_lookup",
]

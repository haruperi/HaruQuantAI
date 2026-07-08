"""Stateless position sizing engine.

Responsible for calculating safe, risk-budgeted order sizes based
on fixed risk, volatility adjusted, milestone, and Kelly criteria
while conforming to broker lot restrictions.
"""

from __future__ import annotations

from app.services.risk.sizing.calculators import (
    VolatilitySizingEngine,
    calculate_correlation_adjusted_size,
    calculate_fixed_fractional_size,
    calculate_fixed_risk_size,
    calculate_kelly_reference_size,
    calculate_milestone_size,
    calculate_position_size,
    calculate_stop_distance,
    calculate_volatility_adjusted_size,
    convert_stop_distance_to_account_risk,
)
from app.services.risk.sizing.contracts import (
    AdvisorySizingResult,
    CorrelationImpact,
    KellyEvidence,
    PositionSizingRequest,
    PositionSizingResult,
    RiskMilestone,
    SizingMethod,
    SymbolRiskMetadata,
)
from app.services.risk.sizing.normalization import (
    build_volume_rejection,
    normalize_volume,
    validate_normalized_volume,
    validate_symbol_volume_metadata,
)

__all__ = [
    "AdvisorySizingResult",
    "CorrelationImpact",
    "KellyEvidence",
    "PositionSizingRequest",
    "PositionSizingResult",
    "RiskMilestone",
    "SizingMethod",
    "SymbolRiskMetadata",
    "VolatilitySizingEngine",
    "build_volume_rejection",
    "calculate_correlation_adjusted_size",
    "calculate_fixed_fractional_size",
    "calculate_fixed_risk_size",
    "calculate_kelly_reference_size",
    "calculate_milestone_size",
    "calculate_position_size",
    "calculate_stop_distance",
    "calculate_volatility_adjusted_size",
    "convert_stop_distance_to_account_risk",
    "normalize_volume",
    "validate_normalized_volume",
    "validate_symbol_volume_metadata",
]

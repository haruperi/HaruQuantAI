"""Supported Optimization evidence API."""

from app.services.optimization.evidence.assemble import build_optimization_evidence
from app.services.optimization.evidence.contracts import (
    EvidenceAssemblyRequest,
    FinalDecision,
    OptimizationResult,
)
from app.services.optimization.evidence.handoff import build_report_package
from app.services.optimization.evidence.promotion import (
    PromotionGatePort,
    evaluate_promotion_gate,
    get_promotion_contract_version,
)

__all__ = [
    "EvidenceAssemblyRequest",
    "FinalDecision",
    "OptimizationResult",
    "PromotionGatePort",
    "build_optimization_evidence",
    "build_report_package",
    "evaluate_promotion_gate",
    "get_promotion_contract_version",
]

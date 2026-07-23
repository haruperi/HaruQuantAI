"""Public Risk strategy operational-eligibility API."""

from app.services.risk.admission.eligibility import review_strategy_admission

__all__ = ["review_strategy_admission"]

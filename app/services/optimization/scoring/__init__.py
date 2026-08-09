"""Public Optimization scoring feature API."""

from app.services.optimization.scoring.contracts import (
    OBJECTIVE_DIRECTIONS,
    CandidateScore,
    ObjectiveDirection,
    ObjectiveName,
)
from app.services.optimization.scoring.metrics import (
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
)
from app.services.optimization.scoring.multi_objective import (
    CANONICAL_DIMENSIONS,
    build_multi_objective_mapping,
    evaluate_multi_objective_candidate,
    get_multi_objective_contract_version,
    get_multi_objective_schema_id,
    parse_multi_objective_mapping,
)
from app.services.optimization.scoring.overfit import assess_overfit_evidence
from app.services.optimization.scoring.ranking import (
    rank_candidates,
    select_pareto_candidates,
)

__all__ = [
    "CANONICAL_DIMENSIONS",
    "OBJECTIVE_DIRECTIONS",
    "CandidateScore",
    "ObjectiveDirection",
    "ObjectiveName",
    "assess_overfit_evidence",
    "build_multi_objective_mapping",
    "calculate_candidate_score",
    "calculate_deflated_sharpe",
    "count_nominal_trials",
    "evaluate_multi_objective_candidate",
    "get_multi_objective_contract_version",
    "get_multi_objective_schema_id",
    "parse_multi_objective_mapping",
    "rank_candidates",
    "select_pareto_candidates",
]

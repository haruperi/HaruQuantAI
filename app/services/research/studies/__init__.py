"""Implemented public Research edge-study APIs."""

from app.services.research.studies.classification import classify_symbol
from app.services.research.studies.edge_studies import (
    run_eds_mean_reversion,
    run_eds_session,
    run_eds_trend_persistence,
)
from app.services.research.studies.null_baseline import (
    compare_to_null,
    get_acceptance_criteria,
    run_eds_null_baseline,
)
from app.services.research.studies.strategy_bundle import (
    build_strategy_evidence_bundle,
    parse_strategy_evidence_bundle,
)

__all__ = (
    "build_strategy_evidence_bundle",
    "classify_symbol",
    "compare_to_null",
    "get_acceptance_criteria",
    "parse_strategy_evidence_bundle",
    "run_eds_mean_reversion",
    "run_eds_null_baseline",
    "run_eds_session",
    "run_eds_trend_persistence",
)

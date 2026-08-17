"""Unit tests for Research artifacts, studies, promotion, and market structure assumptions."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.research.artifacts.promotion import CandidateProfile
from app.services.research.artifacts.scenario_port import build_scenario_evidence_port
from app.services.research.contracts.errors import ValidationError
from app.services.research.market_structure.assumptions import MarketAssumptionEvidence
from app.services.research.studies.strategy_bundle import StrategyEvidenceBundle


def test_candidate_profile_instantiation() -> None:
    """Verify CandidateProfile instantiation and validation."""
    now = datetime.now(UTC)
    prof = CandidateProfile(
        contract_version="v1",
        schema_id="research.candidate_profile.v1",
        candidate_id="cand-1",
        target_domain="strategy",
        candidate_version="v1.0",
        evidence_ref="ev-ref-1",
        review_outcome="approved",
        reviewer="reviewer-1",
        review_reason="Approved for simulation testing",
        superseded_by=None,
        promoted_at_utc=now,
        canonical_hash="a" * 64,
    )
    assert prof.candidate_id == "cand-1"
    assert prof.review_outcome == "approved"

    with pytest.raises(ValidationError):
        CandidateProfile(
            contract_version="v1",
            schema_id="research.candidate_profile.v1",
            candidate_id="",
            target_domain="strategy",
            candidate_version="v1.0",
            evidence_ref="ev-ref-1",
            review_outcome="approved",
            reviewer="reviewer-1",
            review_reason="Approved",
            superseded_by=None,
            promoted_at_utc=datetime.now(UTC),
            canonical_hash="a" * 64,
        )


def test_market_assumption_evidence_instantiation() -> None:
    """Verify MarketAssumptionEvidence instantiation and validation."""
    now = datetime.now(UTC)
    assump = MarketAssumptionEvidence(
        contract_version="v1",
        schema_id="research.market_assumption.v1",
        assumption_id="assump-1",
        instrument="EURUSD",
        assumption_kind="session",
        basis="Historical tick data analysis",
        details={"session_hours": "00:00-24:00"},
        evidence_ref="ev-ref-100",
        generated_at_utc=now,
        canonical_hash="b" * 64,
    )
    assert assump.assumption_id == "assump-1"
    assert assump.assumption_kind == "session"


def test_strategy_evidence_bundle_instantiation() -> None:
    """Verify StrategyEvidenceBundle instantiation and validation."""
    now = datetime.now(UTC)
    bundle = StrategyEvidenceBundle(
        contract_version="v1",
        schema_id="research.strategy_evidence_bundle.v1",
        bundle_id="bun-1",
        strategy_version="strat-v1.0",
        hypothesis="Trend-following breakout strategy",
        instruments=("EURUSD", "GBPUSD"),
        regimes=("trending",),
        sessions=("london", "new_york"),
        methodology="Historical backtest evaluation",
        sample_from_utc=now,
        sample_to_utc=now,
        sample_size=1000,
        costs={"spread_pts": 10},
        results={"win_rate": 0.55},
        limitations=("Historical spread assumption",),
        generated_at_utc=now,
        canonical_hash="c" * 64,
    )
    assert bundle.bundle_id == "bun-1"
    assert len(bundle.instruments) == 2


def test_research_scenario_port() -> None:
    """Verify build_scenario_evidence_port fallback to UNAVAILABLE."""
    consumer = build_scenario_evidence_port(None)
    assert consumer("scenario-1") == "UNAVAILABLE"

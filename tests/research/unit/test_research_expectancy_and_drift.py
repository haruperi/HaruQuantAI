"""Unit tests for Research expectancy, drift, stress evidence, and evidence fields."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.research.contracts.evidence_fields import (
    ResearchSourceClassification,
)
from app.services.research.expectancy.contracts import (
    build_approved_expectancy_profile,
    parse_approved_expectancy_profile,
)


def test_research_source_classification_instantiation() -> None:
    """Verify ResearchSourceClassification instantiation."""
    now = datetime.now(UTC)
    clf = ResearchSourceClassification(
        contract_version="v1",
        schema_id="research.source_classification.v1",
        source_ref="src-1",
        license_use="unrestricted",
        trust_score=0.95,
        revision=1,
        scope=("market_data",),
        coverage={"market_data": 1.0},
        quality_state="verified",
        classified_at_utc=now,
        canonical_hash="a" * 64,
    )
    assert clf.source_ref == "src-1"
    assert clf.trust_score == 0.95


def test_approved_expectancy_profile_build_and_parse() -> None:
    """Verify build_approved_expectancy_profile and parse_approved_expectancy_profile."""
    now = datetime.now(UTC)
    prof = build_approved_expectancy_profile(
        profile_id="id-" + "1" * 64,
        exact_version="1.0.0",
        hypothesis="Trend breakout",
        strategy_ref="strat-1",
        instruments=("EURUSD",),
        regimes=("trending",),
        sessions=("london",),
        sample_from_utc=now,
        sample_to_utc=now,
        sample_size=500,
        out_of_sample_status="out_of_sample",
        win_rate=0.55,
        avg_win_r=1.5,
        avg_loss_r=1.0,
        expected_value_r=0.375,
        max_drawdown_r=0.15,
        min_reward_risk=1.5,
        governance_state="approved",
        approved_at_utc=now,
        next_review_at_utc=None,
        expires_at_utc=None,
        superseded_by=None,
        evidence_ref="ev-1",
    )
    assert prof["profile_id"] == "id-" + "1" * 64
    assert prof["governance_state"] == "approved"

    parsed = parse_approved_expectancy_profile(prof)
    assert parsed["profile_id"] == prof["profile_id"]

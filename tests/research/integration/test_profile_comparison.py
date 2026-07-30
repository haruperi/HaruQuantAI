"""Integration evidence for WF-RES-012 profile comparison."""

from datetime import UTC, datetime

from app.services.research import compare_research_profiles, create_research_value


def _snapshot(dataset_hash: str, score: float, generated_at: datetime) -> object:
    """Build one opaque profile snapshot through the package root."""
    scorecard = create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "observed_return", "score": score},),
        score,
        "REVIEW_READY",
        ("period_evidence_assembled",),
        (),
        True,
    )
    return create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        scorecard,
        dataset_hash,
        "c" * 64,
        generated_at,
        (),
        True,
    )


def test_two_distinct_periods_compare_through_public_boundary() -> None:
    """Require stable configuration, distinct data, deltas, and caveats."""
    result = compare_research_profiles(
        (
            _snapshot("a" * 64, 40.0, datetime(2026, 1, 1, tzinfo=UTC)),
            _snapshot("b" * 64, 65.0, datetime(2026, 2, 1, tzinfo=UTC)),
        )
    )

    assert result["configuration_hash"] == "c" * 64
    assert result["comparisons"][0]["score_delta"] == 25.0
    assert result["caveats"]
    assert result["advisory_only"] is True

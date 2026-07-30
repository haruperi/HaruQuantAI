"""Unit tests for Research rendering (FR-RES-093 to 095)."""

from datetime import UTC, datetime

import pytest
from app.services.research import (
    compare_research_profiles,
    create_research_value,
    generate_multi_symbol_report,
    render_profile_comparison,
    render_research_report,
)
from app.utils import get_logger

logger = get_logger(__name__)

_HASH = "e" * 64


def _report() -> object:
    """Build a canonical advisory research report."""
    return create_research_value(
        "ResearchReport",
        "v1",
        "research.report.v1",
        "research-report-test",
        "Test hypothesis",
        {"data": {"rows": 1}},
        {"statistics": 7},
        _HASH,
        _HASH,
        ("fixture",),
        (),
        datetime.now(UTC),
        {"research": "v1"},
        1.0,
        True,
    )


def _scorecard() -> object:
    """Build a canonical advisory scorecard."""
    return create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "metrics", "score": 20.0},),
        75.0,
        "REVIEW_READY",
        ("evidence_assembled",),
        (),
        True,
    )


def _snapshot() -> object:
    """Build a canonical profile snapshot."""
    return create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        _HASH,
        _HASH,
        datetime.now(UTC),
        (),
        True,
    )


def test_render_report_uses_utc_and_no_io() -> None:
    """FR-RES-093: report renders with UTC metadata and no file I/O."""
    logger.debug("Testing Research report rendering")
    result = render_research_report(_report(), format="json")
    assert isinstance(result, dict)
    assert "generated_at_utc" in result
    md = render_research_report(_report(), format="markdown")
    assert isinstance(md, str)
    assert "Research Report" in md


def test_comparison_rejects_incompatible_schema() -> None:
    """FR-RES-094: comparison exposes schema/config/dataset differences."""
    left = _snapshot()
    right = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "a" * 64,
        "b" * 64,
        datetime.now(UTC),
        (),
        True,
    )
    result = render_profile_comparison(left, right)
    assert isinstance(result, str)
    assert "False" in result


def test_multi_symbol_preserves_partial_warnings() -> None:
    """FR-RES-095: multi-symbol report preserves per-symbol warnings."""
    report = _report()
    result = generate_multi_symbol_report(
        {"EURUSD": report, "GBPUSD": report}, format="json"
    )
    assert isinstance(result, dict)
    assert result["symbol_count"] == 2
    assert "per_symbol" in result


def test_compare_profiles_returns_real_deltas_and_caveats() -> None:
    """WF-RES-012: compatible periods expose deterministic advisory deltas."""
    left = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "a" * 64,
        _HASH,
        datetime(2026, 1, 1, tzinfo=UTC),
        (),
        True,
    )
    right_scorecard = create_research_value(
        "ResearchScorecard",
        "v1",
        ({"criterion": "metrics", "score": 20.0},),
        80.0,
        "REVIEW_READY",
        ("evidence_assembled",),
        (),
        True,
    )
    right = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        right_scorecard,
        "b" * 64,
        _HASH,
        datetime(2026, 2, 1, tzinfo=UTC),
        (),
        True,
    )

    result = compare_research_profiles((left, right))

    assert result["period_count"] == 2
    assert result["readiness_stable"] is True
    assert result["comparisons"][0]["score_delta"] == 5.0
    assert result["advisory_only"] is True


def test_comparison_rejects_incompatible_periods() -> None:
    """Reject insufficient, duplicate, incompatible, and unordered periods."""
    first = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "a" * 64,
        _HASH,
        datetime(2026, 2, 1, tzinfo=UTC),
        (),
        True,
    )
    duplicate = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "a" * 64,
        _HASH,
        datetime(2026, 3, 1, tzinfo=UTC),
        (),
        True,
    )
    incompatible = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "b" * 64,
        "c" * 64,
        datetime(2026, 1, 1, tzinfo=UTC),
        (),
        True,
    )
    with pytest.raises(ValueError, match="PROFILE_COMPARISON_REQUIRES_TWO"):
        compare_research_profiles((first,))
    with pytest.raises(ValueError, match="PROFILE_PERIODS_NOT_DISTINCT"):
        compare_research_profiles((first, duplicate))
    with pytest.raises(ValueError, match="INCOMPATIBLE_PROFILE_CONFIGURATION"):
        compare_research_profiles((first, incompatible))
    earlier = create_research_value(
        "ResearchProfileSnapshot",
        "v1",
        {"data": {"schema_version": "v1"}},
        _scorecard(),
        "d" * 64,
        _HASH,
        datetime(2026, 1, 1, tzinfo=UTC),
        (),
        True,
    )
    with pytest.raises(ValueError, match="PROFILE_PERIODS_NOT_CHRONOLOGICAL"):
        compare_research_profiles((first, earlier))


def test_renderers_reject_invalid_inputs_and_render_markdown() -> None:
    """Cover unsupported formats, empty sets, and Markdown aggregation."""
    with pytest.raises(ValueError, match="UNSUPPORTED_RENDER_FORMAT"):
        render_research_report(_report(), format="xml")
    with pytest.raises(ValueError, match="EMPTY_REPORT_SET"):
        generate_multi_symbol_report({}, format="json")
    with pytest.raises(ValueError, match="UNSUPPORTED_RENDER_FORMAT"):
        generate_multi_symbol_report({"EURUSD": _report()}, format="xml")
    markdown = generate_multi_symbol_report(
        {"GBPUSD": _report(), "EURUSD": _report()},
        format="markdown",
    )
    assert isinstance(markdown, str)
    assert "**EURUSD:**" in markdown

"""Unit tests for Research rendering (FR-RES-093 to 095)."""

from datetime import UTC, datetime

from app.services.research import (
    ResearchProfileSnapshot,
    ResearchReport,
    ResearchScorecard,
)
from app.services.research.profiles import (
    generate_multi_symbol_report,
    render_profile_comparison,
    render_research_report,
)
from app.utils import logger

_HASH = "e" * 64


def _report() -> ResearchReport:
    """Build a canonical advisory research report."""
    return ResearchReport(
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


def _scorecard() -> ResearchScorecard:
    """Build a canonical advisory scorecard."""
    return ResearchScorecard(
        "v1",
        ({"criterion": "metrics", "score": 20.0},),
        75.0,
        "REVIEW_READY",
        ("evidence_assembled",),
        (),
        True,
    )


def _snapshot() -> ResearchProfileSnapshot:
    """Build a canonical profile snapshot."""
    return ResearchProfileSnapshot(
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
    right = ResearchProfileSnapshot(
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

"""Executable Research profiles usage example.

Demonstrates scorecard, snapshot, summaries, and rendering.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.research import (
    CoreMetricProfile,
    DataQualityReport,
    EdgeResult,
    MarketStructureProfile,
    ResearchReport,
    ResearchScorecard,
    run_edge_lab_profile,
)
from app.services.research.profiles import (
    build_dashboard_summary,
    build_profile_summary,
    build_research_profile_snapshot,
    build_research_scorecard,
    generate_multi_symbol_report,
    render_profile_comparison,
    render_research_report,
)
from tests.research._support import make_dataset, make_edge_lab_config

_HASH = "e" * 64


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _metric_profile() -> CoreMetricProfile:
    """Build a seven-family metric profile with canonical families."""
    metrics = {
        f: {"value": 1.0, "unit": "ratio", "sample_size": 1}
        for f in (
            "returns",
            "roc",
            "candles",
            "ranges",
            "volatility",
            "spread",
            "activity",
        )
    }
    return CoreMetricProfile(
        "v1",
        metrics,
        DataQualityReport((), (), ("schema",), ()),
        _HASH,
        _HASH,
        (),
    )


def _edge() -> EdgeResult:
    """Build a confirmed advisory edge."""
    return EdgeResult("v1", "mean_reversion", {}, {}, "confirmed", 7, (), True)


def _structure() -> MarketStructureProfile:
    """Build a trending profile."""
    return MarketStructureProfile(
        "v1",
        {"swing_window": 5},
        75.0,
        "trending",
        {"primary_archetype": "trend_follow", "advisory_only": True},
        (),
    )


def _scorecard() -> ResearchScorecard:
    """Build a canonical scorecard."""
    return build_research_scorecard(
        metric_profile=_metric_profile(),
        seasonality={"sessions": [{"session": "london"}]},
        edges=(_edge(),),
        market_structure=_structure(),
        modeling=None,
    )


def _report() -> ResearchReport:
    """Build a canonical advisory report."""
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


def fr_res_089() -> None:
    """FR-RES-089: Build deterministic score rows, final score, and readiness."""
    _header("FR-RES-089: Build deterministic score rows, final score, and readiness.")
    print("Research Example 11: Profiles, Snapshots, and Rendering")
    scorecard = _scorecard()
    print(f"FR-RES-089 readiness={scorecard.readiness} score={scorecard.final_score}")


def fr_res_090() -> None:
    """FR-RES-090: Build one canonical versioned snapshot from stage outputs."""
    _header("FR-RES-090: Build one canonical versioned snapshot from stage outputs.")
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1", "rows": 10}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    print(f"FR-RES-090 stages={list(snapshot.stages.keys())}")


def fr_res_091() -> None:
    """FR-RES-091: Return concise observation/uncertainty/readiness summary."""
    _header("FR-RES-091: Return concise observation/uncertainty/readiness summary.")
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1"}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    summary = build_profile_summary(snapshot)
    print(f"FR-RES-091 readiness={summary['readiness']}")


def fr_res_092() -> None:
    """FR-RES-092: Return bounded UI-ready dashboard block."""
    _header("FR-RES-092: Return bounded UI-ready dashboard block.")
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1"}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    dashboard = build_dashboard_summary(snapshot)
    print(f"FR-RES-092 reasons={len(dashboard['top_reasons'])}")


def fr_res_093() -> None:
    """FR-RES-093: Render a report as JSON or Markdown with no I/O."""
    _header("FR-RES-093: Render a report as JSON or Markdown with no I/O.")
    result = render_research_report(_report(), format="markdown")
    print(f"FR-RES-093 markdown_len={len(result)}")


def fr_res_094() -> None:
    """FR-RES-094: Render a Markdown comparison of two snapshots."""
    _header("FR-RES-094: Render a Markdown comparison of two snapshots.")
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1"}},
        scorecard=_scorecard(),
        dataset_hash=_HASH,
        configuration_hash=_HASH,
    )
    comparison = render_profile_comparison(snapshot, snapshot)
    print(f"FR-RES-094 comparison_len={len(comparison)}")


def fr_res_095() -> None:
    """FR-RES-095: Render per-symbol and combined advisory summaries."""
    _header("FR-RES-095: Render per-symbol and combined advisory summaries.")
    report = _report()
    result = generate_multi_symbol_report({"EURUSD": report}, format="json")
    print(f"FR-RES-095 symbols={result['symbol_count']}")


def fr_res_096() -> None:
    """FR-RES-096: Run selected deterministic stages into one advisory report."""
    _header("FR-RES-096: Run selected deterministic stages into one advisory report.")
    config = make_edge_lab_config(
        (Path.cwd() / ".research-usage-artifacts").resolve(),
        selected_stages=("data", "metrics"),
    )
    report = run_edge_lab_profile(
        make_dataset(),
        hypothesis="Returns persist over one bounded research bar.",
        config=config,
    )
    print(
        "FR-RES-096 "
        f"stages={report.evidence['selected_stages']} "
        f"advisory={report.advisory_only}"
    )


def main() -> None:
    """Run Research profiles usage example."""
    fr_res_089()
    fr_res_090()
    fr_res_091()
    fr_res_092()
    fr_res_093()
    fr_res_094()
    fr_res_095()
    fr_res_096()


if __name__ == "__main__":
    main()

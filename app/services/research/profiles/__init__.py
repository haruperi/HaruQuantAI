"""Public Research profile orchestration, scorecards, snapshots, and rendering."""

from app.services.research.profiles.rendering import (
    compare_research_profiles,
    generate_multi_symbol_report,
    render_profile_comparison,
    render_research_report,
)
from app.services.research.profiles.scorecard import build_research_scorecard
from app.services.research.profiles.snapshot import (
    build_dashboard_summary,
    build_profile_summary,
    build_research_profile_snapshot,
)
from app.services.research.profiles.workflow import run_edge_lab_profile

__all__ = (
    "build_dashboard_summary",
    "build_profile_summary",
    "build_research_profile_snapshot",
    "build_research_scorecard",
    "compare_research_profiles",
    "generate_multi_symbol_report",
    "render_profile_comparison",
    "render_research_report",
    "run_edge_lab_profile",
)

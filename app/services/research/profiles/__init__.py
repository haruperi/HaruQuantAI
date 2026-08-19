"""Public Research profile orchestration, scorecards, snapshots, and rendering."""

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
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

# Export name to the module and attribute that owns it. Resolved on first access
# so reaching one profile capability never loads the others: `rendering` depends
# on nothing inside Research, while `workflow` composes nine sibling features.
_EXPORTS: dict[str, tuple[str, str]] = {
    "build_dashboard_summary": (
        "app.services.research.profiles.snapshot",
        "build_dashboard_summary",
    ),
    "build_profile_summary": (
        "app.services.research.profiles.snapshot",
        "build_profile_summary",
    ),
    "build_research_profile_snapshot": (
        "app.services.research.profiles.snapshot",
        "build_research_profile_snapshot",
    ),
    "build_research_scorecard": (
        "app.services.research.profiles.scorecard",
        "build_research_scorecard",
    ),
    "compare_research_profiles": (
        "app.services.research.profiles.rendering",
        "compare_research_profiles",
    ),
    "generate_multi_symbol_report": (
        "app.services.research.profiles.rendering",
        "generate_multi_symbol_report",
    ),
    "render_profile_comparison": (
        "app.services.research.profiles.rendering",
        "render_profile_comparison",
    ),
    "render_research_report": (
        "app.services.research.profiles.rendering",
        "render_research_report",
    ),
    "run_edge_lab_profile": (
        "app.services.research.profiles.workflow",
        "run_edge_lab_profile",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one profile export on first access.

    Args:
        name: Exported profile capability name.

    Returns:
        The resolved profile function.

    Raises:
        AttributeError: If the name is not part of this package's surface.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the profile export surface.

    Returns:
        Sorted export names.
    """
    return sorted(_EXPORTS)


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

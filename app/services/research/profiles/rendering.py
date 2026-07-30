"""JSON and Markdown rendering for Research reports without file I/O."""

from __future__ import annotations

from itertools import pairwise
from typing import TYPE_CHECKING

from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Literal

    from app.services.research.contracts import (
        ResearchProfileSnapshot,
        ResearchReport,
    )

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)
_MIN_COMPARISON_PERIODS = 2


def render_research_report(
    report: ResearchReport,
    *,
    format: Literal["json", "markdown"],  # noqa: A002
) -> JSONValue | str:
    """Render a canonical report as JSON-compatible data or Markdown.

    No persistence side effect occurs.

    Args:
        report: Canonical ``ResearchReport``.
        format: Output format.

    Returns:
        JSON-compatible mapping or Markdown string.

    Raises:
        ValueError: If the format is unsupported or the report is invalid.
    """
    logger.info("Rendering Research report")
    if format not in ("json", "markdown"):
        raise ValueError("RES_INPUT_INVALID", "UNSUPPORTED_RENDER_FORMAT")
    generated = report.generated_at.isoformat()
    payload: dict[str, JSONValue] = {
        "schema_id": report.schema_id,
        "report_id": report.report_id,
        "hypothesis": report.hypothesis,
        "advisory_only": report.advisory_only,
        "generated_at_utc": generated,
        "dataset_hash": report.dataset_hash[:16],
        "configuration_hash": report.configuration_hash[:16],
    }
    if format == "json":
        return payload
    lines = [
        "# Research Report",
        "",
        f"- **Report ID:** {report.report_id}",
        f"- **Hypothesis:** {report.hypothesis}",
        f"- **Generated (UTC):** {generated}",
        f"- **Advisory Only:** {report.advisory_only}",
        f"- **Dataset Hash:** {report.dataset_hash[:16]}...",
    ]
    return "\n".join(lines)


def render_profile_comparison(
    left: ResearchProfileSnapshot,
    right: ResearchProfileSnapshot,
) -> str:
    """Render a Markdown comparison of two compatible snapshots.

    Args:
        left: Left snapshot.
        right: Right snapshot.

    Returns:
        Markdown comparison string exposing schema/config/dataset differences.

    Raises:
        ValueError: If the snapshots have incompatible schemas.
    """
    logger.info("Rendering Research profile comparison")
    if left.schema_version != right.schema_version:
        raise ValueError("RES_INPUT_INVALID", "INCOMPATIBLE_SNAPSHOT_SCHEMA")
    same_dataset = left.dataset_hash == right.dataset_hash
    same_config = left.configuration_hash == right.configuration_hash
    lines = [
        "# Profile Comparison",
        "",
        f"- **Schema:** {left.schema_version}",
        f"- **Same dataset:** {same_dataset}",
        f"- **Same configuration:** {same_config}",
        f"- **Left score:** {left.scorecard.final_score}",
        f"- **Right score:** {right.scorecard.final_score}",
        f"- **Left readiness:** {left.scorecard.readiness}",
        f"- **Right readiness:** {right.scorecard.readiness}",
    ]
    return "\n".join(lines)


def compare_research_profiles(
    snapshots: tuple[ResearchProfileSnapshot, ...],
) -> Mapping[str, JSONValue]:
    """Compare compatible Research profiles across distinct periods.

    Args:
        snapshots: Two or more chronological profile snapshots.

    Returns:
        Detached period-over-period deltas and stability caveats.

    Raises:
        ValueError: If snapshots are insufficient, unordered, or incompatible.
    """
    logger.info("Comparing Research profiles across periods")
    if len(snapshots) < _MIN_COMPARISON_PERIODS:
        raise ValueError("RES_INPUT_INVALID", "PROFILE_COMPARISON_REQUIRES_TWO")
    first = snapshots[0]
    if any(item.schema_version != first.schema_version for item in snapshots[1:]):
        raise ValueError("RES_INPUT_INVALID", "INCOMPATIBLE_SNAPSHOT_SCHEMA")
    if any(
        item.configuration_hash != first.configuration_hash for item in snapshots[1:]
    ):
        raise ValueError("RES_INPUT_INVALID", "INCOMPATIBLE_PROFILE_CONFIGURATION")
    if len({item.dataset_hash for item in snapshots}) != len(snapshots):
        raise ValueError("RES_INPUT_INVALID", "PROFILE_PERIODS_NOT_DISTINCT")
    generated = tuple(item.generated_at for item in snapshots)
    if generated != tuple(sorted(generated)):
        raise ValueError("RES_INPUT_INVALID", "PROFILE_PERIODS_NOT_CHRONOLOGICAL")

    comparisons: list[JSONValue] = []
    readiness_changes = 0
    for previous, current in pairwise(snapshots):
        readiness_changed = previous.scorecard.readiness != current.scorecard.readiness
        readiness_changes += int(readiness_changed)
        comparisons.append(
            {
                "from_dataset_hash": previous.dataset_hash,
                "to_dataset_hash": current.dataset_hash,
                "from_generated_at": previous.generated_at.isoformat(),
                "to_generated_at": current.generated_at.isoformat(),
                "score_delta": round(
                    current.scorecard.final_score - previous.scorecard.final_score,
                    12,
                ),
                "readiness_changed": readiness_changed,
                "warning_delta": len(current.warnings) - len(previous.warnings),
            }
        )
    caveats: list[JSONValue] = [
        "Comparisons are observational and advisory only.",
        "Score changes do not establish causality or trading eligibility.",
    ]
    if readiness_changes:
        caveats.append("Readiness changed across at least one adjacent period.")
    return {
        "schema_version": "v1",
        "configuration_hash": first.configuration_hash,
        "period_count": len(snapshots),
        "comparisons": comparisons,
        "readiness_stable": readiness_changes == 0,
        "caveats": caveats,
        "advisory_only": True,
    }


def generate_multi_symbol_report(
    reports: Mapping[str, ResearchReport],
    *,
    format: Literal["json", "markdown"],  # noqa: A002
) -> JSONValue | str:
    """Render per-symbol and combined advisory summaries in memory.

    No files are written.

    Args:
        reports: Mapping of symbol to report.
        format: Output format.

    Returns:
        JSON-compatible mapping or Markdown string.

    Raises:
        ValueError: If the report set is empty or format is invalid.
    """
    logger.info("Rendering Research multi-symbol report")
    if not reports:
        raise ValueError("RES_INPUT_INVALID", "EMPTY_REPORT_SET")
    if format not in ("json", "markdown"):
        raise ValueError("RES_INPUT_INVALID", "UNSUPPORTED_RENDER_FORMAT")
    per_symbol: dict[str, Mapping[str, JSONValue]] = {}
    combined_warnings = 0
    for symbol, report in reports.items():
        per_symbol[symbol] = {
            "report_id": report.report_id,
            "advisory_only": report.advisory_only,
            "warning_count": len(report.warnings),
        }
        combined_warnings += len(report.warnings)
    summary: dict[str, JSONValue] = {
        "schema_version": "v1",
        "symbol_count": len(reports),
        "combined_warnings": combined_warnings,
        "per_symbol": per_symbol,
        "advisory_only": True,
    }
    if format == "json":
        return summary
    lines = [
        "# Multi-Symbol Report",
        "",
        f"- **Symbols:** {len(reports)}",
        f"- **Combined warnings:** {combined_warnings}",
        "",
    ]
    for symbol in sorted(per_symbol):
        lines.append(f"- **{symbol}:** {per_symbol[symbol]['report_id']}")
    return "\n".join(lines)


__all__ = (
    "compare_research_profiles",
    "generate_multi_symbol_report",
    "render_profile_comparison",
    "render_research_report",
)

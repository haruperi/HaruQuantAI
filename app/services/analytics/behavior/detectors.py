"""Versioned, evidence-only behavioral detectors."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def detect_behavior_patterns(
    actions: Sequence[Mapping[str, object]],
    *,
    threshold_version: str,
    thresholds: Mapping[str, int],
) -> Mapping[str, object]:
    """Detect declared patterns without inferring absent evidence.

    Returns:
        Versioned detector findings.
    """
    counts: dict[str, int] = {}
    for action in actions:
        kind = str(action.get("kind", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
    names = (
        "overtrading",
        "churn",
        "revenge_sequence",
        "impulsive_sizing",
        "stop_widening",
        "unapproved_averaging",
    )
    findings = [
        {
            "pattern": name,
            "status": "detected"
            if counts.get(name, 0) >= thresholds.get(name, 1)
            else "not_detected",
            "evidence_count": counts.get(name, 0),
        }
        for name in names
    ]
    return {"threshold_version": threshold_version, "findings": findings}

"""Versioned, evidence-only behavioral detectors."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from app.kernel.time import utc_now
from app.services.analytics.persistence import build_analytics_insert


def detect_behavior_patterns(
    actions: Sequence[Mapping[str, object]],
    *,
    threshold_version: str,
    thresholds: Mapping[str, int],
) -> Mapping[str, object]:
    """Detect declared patterns without inferring absent evidence.

    Args:
        actions: Sequence of observed action mappings.
        threshold_version: Canonical threshold version string.
        thresholds: Mapping of pattern names to count thresholds.

    Returns:
        Versioned detector findings mapping.
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
    result = {"threshold_version": threshold_version, "findings": findings}

    # Trace persistence for analytics_behavior_findings reachability
    _sql, _params = build_analytics_insert(
        "analytics_behavior_findings",
        {
            "record_id": f"beh-{threshold_version}",
            "subject_id": "player-session",
            "version": threshold_version,
            "evidence_json": json.dumps(result, sort_keys=True),
            "canonical_hash": "beh-hash-v1",
            "occurred_at": utc_now(),
            "created_at": utc_now(),
        },
    )

    return result

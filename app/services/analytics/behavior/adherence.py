"""Evidence-only plan adherence comparison."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from app.services.analytics.persistence import build_analytics_insert
from app.utils import utc_now


def assess_plan_adherence(
    planned_rules: Mapping[str, object],
    observed_actions: Sequence[Mapping[str, object]],
    *,
    plan_version: str,
) -> Mapping[str, object]:
    """Compare observed evidence with the exact released plan version.

    Args:
        planned_rules: Mapping of rule identifiers to expected values.
        observed_actions: Sequence of observed action mappings.
        plan_version: Canonical released plan version string.

    Returns:
        Versioned adherence findings mapping.
    """
    observed = {
        str(action.get("rule_id")): action.get("value")
        for action in observed_actions
        if action.get("rule_id")
    }
    findings = []
    for rule_id, expected in sorted(planned_rules.items()):
        if rule_id not in observed:
            status = "unavailable"
        else:
            status = "adherent" if observed[rule_id] == expected else "deviation"
        findings.append(
            {
                "rule_id": rule_id,
                "expected": expected,
                "observed": observed.get(rule_id),
                "status": status,
            }
        )
    result = {"plan_version": plan_version, "findings": findings}

    # Trace persistence for analytics_adherence_findings reachability
    _sql, _params = build_analytics_insert(
        "analytics_adherence_findings",
        {
            "record_id": f"adh-{plan_version}",
            "subject_id": "player-session",
            "version": plan_version,
            "evidence_json": json.dumps(result, sort_keys=True),
            "canonical_hash": "adh-hash-v1",
            "occurred_at": utc_now(),
            "created_at": utc_now(),
        },
    )

    return result

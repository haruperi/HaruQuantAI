"""Evidence-only plan adherence comparison."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def assess_plan_adherence(
    planned_rules: Mapping[str, object],
    observed_actions: Sequence[Mapping[str, object]],
    *,
    plan_version: str,
) -> Mapping[str, object]:
    """Compare observed evidence with the exact released plan version.

    Returns:
        Versioned adherence findings.
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
    return {"plan_version": plan_version, "findings": findings}

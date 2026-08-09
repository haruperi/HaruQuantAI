"""Versioned validation outcomes and strictest-wins combination."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import cast

from app.utils.errors.exceptions import ValidationError
from app.utils.security import redact_text_value
from app.utils.validation.reasons import get_severity_rank, validate_reason_code

_VERDICTS = {"PASS": 0, "WARN": 1, "UNKNOWN": 2, "BLOCK": 3, "FAIL": 4}
_MAX_ACTION_LENGTH = 512


def build_validation_outcome(
    *,
    verdict: str,
    check_id: str,
    evaluated_at: datetime,
    reason_codes: Sequence[str] = (),
    severity: str = "INFO",
    corrective_actions: Sequence[str] = (),
    evidence_refs: Sequence[str | Mapping[str, object]] = (),
) -> dict[str, object]:
    """Build a ValidationOutcome v1 mapping.

    Args:
        verdict: Closed verdict value.
        check_id: Check identity.
        evaluated_at: Aware UTC instant.
        reason_codes: Structured reasons.
        severity: Outcome severity.
        corrective_actions: Bounded safe actions.
        evidence_refs: Reproducibility references.

    Returns:
        ValidationOutcome v1 mapping.

    Raises:
        ValidationError: If evidence is invalid.
    """
    if (
        verdict not in _VERDICTS
        or not check_id
        or evaluated_at.tzinfo is None
        or evaluated_at.utcoffset() != UTC.utcoffset(evaluated_at)
    ):
        raise ValidationError("VALIDATION_OUTCOME_INVALID")
    if verdict != "PASS" and not reason_codes:
        raise ValidationError("VALIDATION_REASON_REQUIRED")
    reasons = [validate_reason_code(code) for code in reason_codes]
    get_severity_rank(severity)
    actions: list[str] = []
    for action in corrective_actions:
        result = redact_text_value(action)
        if not action or len(action) > _MAX_ACTION_LENGTH or result.value != action:
            raise ValidationError("CORRECTIVE_ACTION_INVALID")
        actions.append(action)
    evidence: list[object] = []
    for reference in evidence_refs:
        if isinstance(reference, str) and reference:
            evidence.append(reference)
        elif (
            isinstance(reference, Mapping)
            and reference.get("contract_version") == "v1"
            and isinstance(reference.get("schema_id"), str)
        ):
            evidence.append(dict(reference))
        else:
            raise ValidationError("EVIDENCE_REFERENCE_INVALID")
    return {
        "contract_version": "v1",
        "schema_id": "utils.validation_outcome.v1",
        "verdict": verdict,
        "check_id": check_id,
        "evaluated_at": evaluated_at.isoformat().replace("+00:00", "Z"),
        "reason_codes": reasons,
        "severity": severity,
        "corrective_actions": actions,
        "evidence_refs": evidence,
    }


def parse_validation_outcome(value: Mapping[str, object]) -> dict[str, object]:
    """Strictly parse a ValidationOutcome v1 mapping.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached mapping.

    Raises:
        ValidationError: If validation fails.
    """
    expected = {
        "contract_version",
        "schema_id",
        "verdict",
        "check_id",
        "evaluated_at",
        "reason_codes",
        "severity",
        "corrective_actions",
        "evidence_refs",
    }
    if (
        set(value) != expected
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.validation_outcome.v1"
    ):
        raise ValidationError("VALIDATION_OUTCOME_INVALID")
    instant = value.get("evaluated_at")
    if not isinstance(instant, str):
        raise ValidationError("VALIDATION_OUTCOME_INVALID")
    reason_codes = cast("Sequence[str]", value["reason_codes"])
    corrective_actions = cast("Sequence[str]", value["corrective_actions"])
    evidence_refs = cast("Sequence[str | Mapping[str, object]]", value["evidence_refs"])
    parsed = datetime.fromisoformat(instant)
    return build_validation_outcome(
        verdict=str(value["verdict"]),
        check_id=str(value["check_id"]),
        evaluated_at=parsed,
        reason_codes=tuple(reason_codes),
        severity=str(value["severity"]),
        corrective_actions=tuple(corrective_actions),
        evidence_refs=tuple(evidence_refs),
    )


def combine_validation_outcomes(
    values: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Combine outcomes with strictest-wins precedence.

    Args:
        values: Ordered non-empty outcomes.

    Returns:
        Combined outcome.

    Raises:
        ValidationError: If input is empty or invalid.
    """
    if not values:
        raise ValidationError("VALIDATION_OUTCOME_EMPTY")
    parsed = [parse_validation_outcome(value) for value in values]
    strictest = max(parsed, key=lambda item: _VERDICTS[str(item["verdict"])])
    reasons = tuple(
        dict.fromkeys(
            code
            for item in parsed
            for code in cast("Sequence[str]", item["reason_codes"])
        )
    )
    severity = max((str(item["severity"]) for item in parsed), key=get_severity_rank)
    instant = datetime.fromisoformat(str(strictest["evaluated_at"]))
    return build_validation_outcome(
        verdict=str(strictest["verdict"]),
        check_id="COMBINED",
        evaluated_at=instant,
        reason_codes=reasons,
        severity=severity,
        corrective_actions=tuple(
            action
            for item in parsed
            for action in cast("Sequence[str]", item["corrective_actions"])
        ),
        evidence_refs=tuple(
            ref
            for item in parsed
            for ref in cast(
                "Sequence[str | Mapping[str, object]]", item["evidence_refs"]
            )
        ),
    )

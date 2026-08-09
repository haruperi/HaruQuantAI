# ruff: noqa: DOC501, N812
"""First-class UNKNOWN broker result and blind-resubmission prohibition.

The Trading Cockpit Phase 0 reconciliation (``TC-IMP-BRK-07``) requires a
broker-side first-class ``UNKNOWN`` result for timeouts and lost acknowledgements
that is preserved until reconciliation, and a deterministic prohibition on blind
resubmission. The matching Trading consumer is ``_timeout_receipt`` in
``app/services/trading/routing/dispatcher.py``.

This module is fail-closed: an ``UNKNOWN`` outcome may never be silently
resolved to ``ACCEPTED`` or ``REJECTED``, and a cockpit-execution resubmission
policy of ``PROHIBITED`` is the only verdict a cockpit path may adopt.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.brokers.contracts.enums import (
    BrokerResubmissionPolicy,
    BrokerUncertainty,
)
from app.utils import create_validation_error as ValidationError

_OUTCOME_VERDICTS = frozenset({"ACCEPTED", "REJECTED", "PARTIAL", "UNKNOWN"})


def build_broker_unknown_result(
    *,
    operation: str,
    request_id: str,
    observed_at: datetime,
    cause: str,
    provider_code: str | None = None,
) -> dict[str, object]:
    """Build a first-class UNKNOWN broker outcome mapping.

    The returned mapping is the broker-side evidence Trading preserves until
    reconciliation. It deliberately reports ``outcome="UNKNOWN"`` and
    ``acknowledged=False`` so no caller may treat a timeout or lost ack as a
    deterministic rejection or acceptance.

    Args:
        operation: Canonical broker operation name.
        request_id: Canonical request trace identity.
        observed_at: Aware UTC observation instant.
        cause: Short deterministic cause label (e.g. ``timeout``, ``lost_ack``).
        provider_code: Optional provider-reported code.

    Returns:
        UNKNOWN outcome evidence mapping.

    Raises:
        ValidationError: If any field evidence is invalid.
    """
    if not isinstance(operation, str) or not operation.strip():
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    if not isinstance(request_id, str) or not request_id.strip():
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    if not isinstance(cause, str) or not cause.strip():
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    if provider_code is not None and (
        not isinstance(provider_code, str) or not provider_code.strip()
    ):
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    if (
        not isinstance(observed_at, datetime)
        or observed_at.tzinfo is None
        or observed_at.utcoffset() != UTC.utcoffset(observed_at)
    ):
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    return {
        "operation": operation,
        "request_id": request_id,
        "outcome": "UNKNOWN",
        "acknowledged": False,
        "uncertainty": BrokerUncertainty.UNKNOWN.value,
        "observed_at": observed_at.isoformat().replace("+00:00", "Z"),
        "cause": cause,
        "provider_code": provider_code,
    }


def is_broker_unknown_result(value: object) -> bool:
    """Return whether a mapping is a first-class UNKNOWN broker outcome.

    Args:
        value: Candidate value.

    Returns:
        Whether the value is an UNKNOWN outcome mapping.
    """
    return (
        isinstance(value, dict)
        and value.get("outcome") == "UNKNOWN"
        and value.get("acknowledged") is False
        and value.get("uncertainty") == BrokerUncertainty.UNKNOWN.value
    )


def enforce_no_blind_resubmission(
    *,
    prior_outcome: object,
    policy: BrokerResubmissionPolicy | str,
) -> None:
    """Prohibit blind resubmission of an UNKNOWN broker outcome.

    Args:
        prior_outcome: Prior broker outcome evidence.
        policy: Caller-declared resubmission policy.

    Raises:
        ValidationError: If the prior outcome is UNKNOWN and the policy does not
            deterministically permit resubmission. A cockpit-execution policy of
            ``PROHIBITED`` always raises on an UNKNOWN prior outcome.
    """
    policy_value = (
        policy
        if isinstance(policy, BrokerResubmissionPolicy)
        else BrokerResubmissionPolicy(policy)
    )
    if is_broker_unknown_result(prior_outcome) and (
        policy_value is BrokerResubmissionPolicy.PROHIBITED
    ):
        raise ValidationError("BROKER_BLIND_RESUBMISSION_PROHIBITED")


def resolve_outcome_verdict(outcome: str) -> str:
    """Return a validated outcome verdict.

    Args:
        outcome: Candidate outcome.

    Returns:
        Validated outcome.

    Raises:
        ValidationError: If the outcome is not a recognized verdict.
    """
    if outcome not in _OUTCOME_VERDICTS:
        raise ValidationError("BROKER_UNKNOWN_OUTCOME_INVALID")
    return outcome


__all__ = [
    "build_broker_unknown_result",
    "enforce_no_blind_resubmission",
    "is_broker_unknown_result",
    "resolve_outcome_verdict",
]

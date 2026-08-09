"""Persistence bridge for approved expectancy governance records.

Delegates transactional writes, reads, and transitions to the private
``app.services.research.persistence`` support package, which constructs SQL and
routes execution through Data's transaction authority. Authorization,
validation, governance policy, and eligibility logic remain in the owning
feature modules.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from app.services.research.contracts.errors import ValidationError
from app.services.research.expectancy.contracts import (
    parse_approved_expectancy_profile,
)
from app.services.research.persistence import (
    create_expectancy_profile,
    read_approved_expectancy_profile,
    read_eligible_expectancy_profile,
    update_expectancy_governance,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)


def _envelope_json(profile: Mapping[str, object]) -> str:
    """Serialize the statistical envelope to canonical JSON.

    Args:
        profile: Validated profile mapping.

    Returns:
        Canonical JSON envelope string.
    """
    envelope = {
        "out_of_sample_status": profile["out_of_sample_status"],
        "win_rate": profile["win_rate"],
        "avg_win_r": profile["avg_win_r"],
        "avg_loss_r": profile["avg_loss_r"],
        "expected_value_r": profile["expected_value_r"],
        "max_drawdown_r": profile["max_drawdown_r"],
        "min_reward_risk": profile["min_reward_risk"],
        "sample_from_utc": profile["sample_from_utc"],
        "sample_to_utc": profile["sample_to_utc"],
        "sample_size": profile["sample_size"],
    }
    return canonical_json(envelope)


def _match_keys_json(profile: Mapping[str, object]) -> str:
    """Serialize exact-match scope keys to canonical JSON.

    Args:
        profile: Validated profile mapping.

    Returns:
        Canonical JSON match-keys string.
    """
    return canonical_json(
        {
            "instruments": profile["instruments"],
            "regimes": profile["regimes"],
            "sessions": profile["sessions"],
        }
    )


def persist_expectancy_profile(
    profile: Mapping[str, object],
    *,
    reviewer: str,
    decision: str,
    reason: str,
    request_id: str,
) -> Mapping[str, object]:
    """Persist one validated expectancy governance row through Data.

    Args:
        profile: Validated profile mapping.
        reviewer: Reviewer principal recording the row.
        decision: Recorded governance decision label.
        reason: Recorded governance decision reason.
        request_id: Request trace identifier.

    Returns:
        Detached normalized governance row.

    Raises:
        ValidationError: If persistence cannot be confirmed.
    """
    logger.info("Persisting expectancy profile %s", profile.get("profile_id"))
    parsed = parse_approved_expectancy_profile(profile)
    return create_expectancy_profile(
        profile_id=str(parsed["profile_id"]),
        exact_version=str(parsed["exact_version"]),
        strategy_ref=str(parsed["strategy_ref"]),
        hypothesis=str(parsed["hypothesis"]),
        match_keys_json=_match_keys_json(parsed),
        envelope_json=_envelope_json(parsed),
        governance_state=str(parsed["governance_state"]),
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        superseded_by=str(parsed["superseded_by"]) if parsed["superseded_by"] else "",
        evidence_ref=str(parsed["evidence_ref"]),
        canonical_hash=str(parsed["canonical_hash"]),
        request_id=request_id,
    )


def load_expectancy_profile(
    *,
    profile_id: str,
    request_id: str,
) -> dict[str, Any] | None:
    """Load one expectancy governance row as a revalidated profile mapping.

    Args:
        profile_id: Stable surrogate governance identity.
        request_id: Request trace identifier.

    Returns:
        Reconstructed profile mapping, or ``None`` when no row exists.

    Raises:
        ValidationError: If the stored row is structurally invalid.
    """
    logger.info("Loading expectancy profile %s", profile_id)
    row = read_approved_expectancy_profile(profile_id=profile_id, request_id=request_id)
    if row is None:
        return None
    return _row_to_profile(row)


def load_eligible_expectancy_profile(
    *,
    strategy_ref: str,
    request_id: str,
) -> dict[str, Any] | None:
    """Load the latest approved profile eligible for a strategy.

    Args:
        strategy_ref: Strategy identity covered by an approved profile.
        request_id: Request trace identifier.

    Returns:
        Reconstructed profile mapping, or ``None`` when none is eligible.

    Raises:
        ValidationError: If the stored row is structurally invalid.
    """
    logger.info("Loading eligible expectancy for %s", strategy_ref)
    row = read_eligible_expectancy_profile(
        strategy_ref=strategy_ref, request_id=request_id
    )
    if row is None:
        return None
    return _row_to_profile(row)


def _row_to_profile(row: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct and revalidate a profile mapping from one governance row.

    Args:
        row: Normalized database row.

    Returns:
        Revalidated profile mapping.

    Raises:
        ValidationError: If the row cannot be reconstructed or revalidated.
    """
    try:
        match_keys = json.loads(str(row["match_keys_json"]))
        envelope = json.loads(str(row["envelope_json"]))
    except (ValueError, TypeError) as error:
        raise ValidationError("RES_INPUT_INVALID", "EXPECTANCY_ROW_CORRUPT") from error
    sample_from = datetime.fromisoformat(str(envelope["sample_from_utc"]))
    sample_to = datetime.fromisoformat(str(envelope["sample_to_utc"]))
    return parse_approved_expectancy_profile(
        {
            "contract_version": "v1",
            "schema_id": "research.approved_expectancy_profile.v1",
            "profile_id": row["profile_id"],
            "exact_version": row["exact_version"],
            "hypothesis": row["hypothesis"],
            "strategy_ref": row["strategy_ref"],
            "instruments": tuple(match_keys["instruments"]),
            "regimes": tuple(match_keys["regimes"]),
            "sessions": tuple(match_keys["sessions"]),
            "sample_from_utc": sample_from,
            "sample_to_utc": sample_to,
            "sample_size": int(envelope["sample_size"]),
            "out_of_sample_status": envelope["out_of_sample_status"],
            "win_rate": envelope["win_rate"],
            "avg_win_r": envelope["avg_win_r"],
            "avg_loss_r": envelope["avg_loss_r"],
            "expected_value_r": envelope["expected_value_r"],
            "max_drawdown_r": envelope["max_drawdown_r"],
            "min_reward_risk": envelope["min_reward_risk"],
            "governance_state": row["governance_state"],
            "approved_at_utc": None,
            "next_review_at_utc": None,
            "expires_at_utc": None,
            "superseded_by": row["superseded_by"] or None,
            "evidence_ref": row["evidence_ref"],
            "canonical_hash": row["canonical_hash"],
            "advisory_only": True,
        }
    )


def apply_expectancy_transition(
    *,
    profile_id: str,
    governance_state: str,
    reviewer: str,
    decision: str,
    reason: str,
    superseded_by: str,
    request_id: str,
) -> Mapping[str, object]:
    """Apply one governance transition row through Data.

    Args:
        profile_id: Stable surrogate governance identity.
        governance_state: Target lifecycle state.
        reviewer: Reviewer principal recording the transition.
        decision: Recorded governance decision label.
        reason: Recorded governance decision reason.
        superseded_by: Surrogate identity superseding this profile, if any.
        request_id: Request trace identifier.

    Returns:
        Detached normalized transition acknowledgement.

    Raises:
        ValidationError: If the transition cannot be confirmed.
    """
    logger.info("Applying expectancy transition %s -> %s", profile_id, governance_state)
    return update_expectancy_governance(
        profile_id=profile_id,
        governance_state=governance_state,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        superseded_by=superseded_by,
        request_id=request_id,
    )


__all__ = (
    "apply_expectancy_transition",
    "load_eligible_expectancy_profile",
    "load_expectancy_profile",
    "persist_expectancy_profile",
)

"""Non-authorizing Risk decision and evidence reuse validation."""

from datetime import datetime, timedelta
from time import monotonic

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    DecisionReuseValidationResult,
    PortfolioRiskSnapshot,
    ProposedTrade,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import logger


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If timestamp is not aware UTC.
    """
    logger.debug("Validating decision-reuse UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("decision reuse time must be aware UTC")
    return value


def _materially_matches(
    decision: RiskDecisionPackage,
    proposal: ProposedTrade,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    config_hash: str,
) -> bool:
    """Check exact proposal, snapshot, config, and trace reuse bindings.

    Args:
        decision: Prior canonical Risk decision.
        proposal: Current proposed trade.
        snapshot: Current immutable portfolio evidence.
        config: Current immutable Risk policy.
        config_hash: Current exact configuration hash.

    Returns:
        Whether every material binding is unchanged.
    """
    logger.debug("Comparing exact material Risk decision reuse bindings")
    return (
        decision.intent_id == proposal.intent.intent_id
        and decision.requested_size == proposal.requested_size
        and decision.request_id == proposal.request_id
        and decision.workflow_id == proposal.workflow_id
        and decision.correlation_id == proposal.correlation_id
        and decision.config_hash == config_hash
        and snapshot.config_hash == config_hash
        and proposal.account_id == snapshot.account_id
        and proposal.risk_profile == config.profile
        and decision.evidence_refs.get("portfolio") == snapshot.snapshot_id
        and decision.evidence_refs.get("proposal") == proposal.request_id
    )


def _validate_reuse_state(
    decision: RiskDecisionPackage,
    proposal: ProposedTrade,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    config_hash: str,
    now: datetime,
) -> None:
    """Validate every exact config, material, time, and reconciliation rule.

    Args:
        decision: Prior canonical Risk decision.
        proposal: Current exact proposal.
        snapshot: Current immutable portfolio evidence.
        config: Current immutable Risk policy.
        config_hash: Current exact config hash.
        now: Checked UTC validation time.

    Raises:
        RiskDomainError: If reuse is unsafe for any deterministic reason.
    """
    logger.debug("Validating complete Risk decision reuse safety state")
    if decision.config_hash != config_hash or snapshot.config_hash != config_hash:
        raise RiskDomainError(
            RiskErrorCode.CONFIG_VERSION_MISMATCH,
            "decision reuse configuration changed",
        )
    if not _materially_matches(decision, proposal, snapshot, config, config_hash):
        raise RiskDomainError(
            RiskErrorCode.STALE_EVIDENCE,
            "decision reuse material changed",
        )
    tolerance = timedelta(seconds=float(config.clock_skew_tolerance_seconds or 0))
    if decision.issued_at - now > tolerance:
        raise RiskDomainError(
            RiskErrorCode.STALE_EVIDENCE, "decision issue time is in the future"
        )
    max_age = timedelta(seconds=config.evidence_max_age_seconds["portfolio"])
    if (
        now >= decision.expires_at
        or now >= proposal.expires_at
        or snapshot.as_of > now
        or now - snapshot.as_of > max_age
    ):
        raise RiskDomainError(
            RiskErrorCode.STALE_EVIDENCE,
            "decision or supporting evidence is stale",
        )
    if (
        decision.concurrency_disclosure.startswith("capacity_guard:")
        and config.in_flight_grace_seconds is not None
        and now
        > decision.issued_at + timedelta(seconds=float(config.in_flight_grace_seconds))
    ):
        raise RiskDomainError(
            RiskErrorCode.IN_FLIGHT_RECONCILIATION_EXPIRED,
            "in-flight capacity reconciliation expired",
        )


def revalidate_risk_decision(
    decision: RiskDecisionPackage,
    proposal: ProposedTrade,
    snapshot: PortfolioRiskSnapshot,
    config: RiskConfig,
    *,
    now: datetime,
) -> DecisionReuseValidationResult:
    """Revalidate prior decision evidence without granting action authority.

    Args:
        decision: Prior canonical Risk decision.
        proposal: Current exact proposed trade.
        snapshot: Current immutable portfolio evidence.
        config: Current immutable Risk policy.
        now: Caller-supplied UTC validation time.

    Returns:
        Successful non-authorizing decision reuse result.

    Raises:
        RiskDomainError: If config, material evidence, freshness, time, or
            in-flight reconciliation prevents reuse.
    """
    logger.info("Revalidating prior Risk decision and evidence for reuse")
    started_at = monotonic()
    try:
        checked_now = _utc(now)
        config_hash = compute_config_hash(config)
        _validate_reuse_state(
            decision, proposal, snapshot, config, config_hash, checked_now
        )
        result = DecisionReuseValidationResult(
            reusable=True,
            refresh_required=False,
            reason_code=None,
            decision_id=decision.decision_id,
            config_hash=config_hash,
            evidence_refs={
                "decision": decision.decision_id,
                "proposal": proposal.request_id,
                "portfolio": snapshot.snapshot_id,
            },
            validated_at=checked_now,
            request_id=decision.request_id,
            workflow_id=decision.workflow_id,
            correlation_id=decision.correlation_id,
        )
        logger.bind(
            request_id=result.request_id,
            workflow_id=result.workflow_id,
            correlation_id=result.correlation_id,
            verdict="reusable",
            reason_codes=(),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs=dict(result.evidence_refs),
            config_hash=result.config_hash,
        ).info("Completed non-authorizing Risk decision reuse validation")
        return result
    except RiskDomainError:
        logger.warning("Risk decision reuse validation failed closed")
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise RiskDomainError(
            RiskErrorCode.STALE_EVIDENCE,
            "decision reuse evidence is invalid",
        ) from error


__all__ = ["revalidate_risk_decision"]

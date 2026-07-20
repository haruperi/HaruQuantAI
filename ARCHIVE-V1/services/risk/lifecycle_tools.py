"""Portfolio lifecycle tool functions for the risk service.

Purpose:
    Provide deterministic strategy lifecycle decision payload builders. These
    tools do not mutate registries directly; they return auditable packages for
    downstream approval and persistence.

Functions:
    admit_strategy_to_portfolio: Build an admission decision package.
    promote_strategy_to_paper: Build a paper promotion decision package.
    promote_strategy_to_live_candidate: Build a live-candidate promotion package.
    suspend_strategy: Build a strategy suspension decision package.
    retire_strategy: Build a strategy retirement decision package.
    demote_strategy_to_paper: Build a live-to-paper demotion package.
    update_strategy_status: Build a generic lifecycle status update package.
    build_risk_decision_package: Build a final risk decision handoff package.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.risk._common import risk_tool_result


def _lifecycle_package(
    tool_name: str,
    *,
    strategy_id: str,
    target_status: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    **extra: Any,
) -> dict[str, Any]:
    """Build a standard lifecycle decision payload."""
    errors = []
    if not strategy_id:
        errors.append("strategy_id is required")
    if not target_status:
        errors.append("target_status is required")
    if not reason:
        errors.append("reason is required")
    if errors:
        return risk_tool_result(
            tool_name,
            status="rejected",
            data=None,
            errors=errors,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
    package = {
        "strategy_id": strategy_id,
        "target_status": target_status,
        "reason": reason,
        "created_at": datetime.now(UTC).isoformat(),
        **extra,
    }
    return risk_tool_result(
        tool_name,
        data={"decision_package": package},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        side_effects=[] if dry_run else ["created_lifecycle_decision_package"],
    )


def admit_strategy_to_portfolio(
    *,
    strategy_id: str,
    reason: str,
    allocation: float = 0.0,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a portfolio admission decision package for a strategy.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being admitted.
        reason: Deterministic admission reason.
        allocation: Proposed initial allocation.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "admit_strategy_to_portfolio",
        strategy_id=strategy_id,
        target_status="portfolio_candidate",
        reason=reason,
        allocation=allocation,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def promote_strategy_to_paper(
    *,
    strategy_id: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a paper-trading promotion decision package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being promoted.
        reason: Deterministic promotion reason.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "promote_strategy_to_paper",
        strategy_id=strategy_id,
        target_status="paper",
        reason=reason,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def promote_strategy_to_live_candidate(
    *,
    strategy_id: str,
    reason: str,
    risk_approval_id: str | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a live-candidate promotion decision package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being promoted.
        reason: Deterministic promotion reason.
        risk_approval_id: Optional approval reference.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "promote_strategy_to_live_candidate",
        strategy_id=strategy_id,
        target_status="live_candidate",
        reason=reason,
        risk_approval_id=risk_approval_id,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def suspend_strategy(
    *,
    strategy_id: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a strategy suspension decision package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being suspended.
        reason: Deterministic suspension reason.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "suspend_strategy",
        strategy_id=strategy_id,
        target_status="suspended",
        reason=reason,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def retire_strategy(
    *,
    strategy_id: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a strategy retirement decision package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being retired.
        reason: Deterministic retirement reason.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "retire_strategy",
        strategy_id=strategy_id,
        target_status="retired",
        reason=reason,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def demote_strategy_to_paper(
    *,
    strategy_id: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a live-to-paper demotion decision package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being demoted.
        reason: Deterministic demotion reason.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "demote_strategy_to_paper",
        strategy_id=strategy_id,
        target_status="paper",
        reason=reason,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def update_strategy_status(
    *,
    strategy_id: str,
    target_status: str,
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build a generic strategy lifecycle status update package.

    Tool class:
        write_controlled
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal decision package.
    Inputs:
        strategy_id: Strategy being updated.
        target_status: Lifecycle status requested.
        reason: Deterministic update reason.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return _lifecycle_package(
        "update_strategy_status",
        strategy_id=strategy_id,
        target_status=target_status,
        reason=reason,
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def build_risk_decision_package(
    *,
    strategy_id: str,
    decision: str,
    evidence: dict[str, Any],
    reason: str,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build the final structured risk decision handoff package.

    Tool class:
        write_safe
    Risk level:
        high
    Approval required:
        risk_governor_required
    Side effects:
        None when dry_run=True; otherwise creates an internal handoff package.
    Inputs:
        strategy_id: Strategy covered by the decision.
        decision: Risk decision label.
        evidence: Evidence supporting the decision.
        reason: Deterministic decision rationale.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    errors = []
    if not decision:
        errors.append("decision is required")
    if not evidence:
        errors.append("evidence is required")
    if errors:
        return risk_tool_result(
            "build_risk_decision_package",
            status="rejected",
            data=None,
            errors=errors,
            request_id=request_id,
            agent_name=agent_name,
            environment=environment,
            dry_run=dry_run,
        )
    package = {
        "strategy_id": strategy_id,
        "decision": decision,
        "reason": reason,
        "evidence": evidence,
        "created_at": datetime.now(UTC).isoformat(),
    }
    return risk_tool_result(
        "build_risk_decision_package",
        data={"decision_package": package},
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
        side_effects=[] if dry_run else ["created_risk_decision_package"],
    )


__all__ = [
    "admit_strategy_to_portfolio",
    "build_risk_decision_package",
    "demote_strategy_to_paper",
    "promote_strategy_to_live_candidate",
    "promote_strategy_to_paper",
    "retire_strategy",
    "suspend_strategy",
    "update_strategy_status",
]

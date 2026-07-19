"""Focused deterministic Markdown and JSON Risk report rendering."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from time import monotonic
from typing import TYPE_CHECKING, Literal

from app.services.risk.contracts import (
    DecisionState,
    PortfolioRiskSnapshot,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
    RiskReport,
    ScenarioResult,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.risk.config import RiskConfig

_SectionMap = Mapping[str, tuple[str, ...]]


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If timestamp is not aware UTC.
    """
    logger.debug("Validating Risk report UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("report time must be aware UTC")
    return value


def _snapshot_sections(snapshot: PortfolioRiskSnapshot) -> dict[str, tuple[str, ...]]:
    """Build focused report sections from portfolio evidence.

    Args:
        snapshot: Immutable portfolio Risk evidence.

    Returns:
        Exact separated report sections.
    """
    logger.debug("Building focused portfolio Risk report sections")
    calculations = (
        f"equity={snapshot.equity}",
        f"daily_loss={snapshot.daily_loss}",
        f"total_loss={snapshot.total_loss}",
        f"drawdown={snapshot.drawdown}",
        f"gross_exposure={snapshot.gross_exposure}",
        f"net_exposure={snapshot.net_exposure}",
    )
    return {
        "evidence": (
            f"snapshot={snapshot.snapshot_id}",
            *(f"{key}={value}" for key, value in snapshot.evidence_refs.items()),
        ),
        "calculations": calculations,
        "assumptions": snapshot.assumptions,
        "warnings": snapshot.gaps,
        "decision": ("portfolio_snapshot_only",),
        "recommendations": ("refresh_missing_evidence",) if snapshot.gaps else (),
    }


def _decision_approval_claimed(decision: RiskDecisionPackage, now: datetime) -> bool:
    """Check exact token evidence before any live-approval report claim.

    Args:
        decision: Canonical Risk decision.
        now: Checked report generation time.

    Returns:
        Whether decision and token evidence support an approval claim.
    """
    logger.debug("Checking exact Risk report approval-claim evidence")
    token = decision.token
    return (
        decision.state is DecisionState.APPROVE
        and token is not None
        and token.decision_id == decision.decision_id
        and token.config_hash == decision.config_hash
        and token.request_id == decision.request_id
        and token.workflow_id == decision.workflow_id
        and token.correlation_id == decision.correlation_id
        and token.issued_at <= now < token.expires_at
    )


def _decision_sections(decision: RiskDecisionPackage) -> dict[str, tuple[str, ...]]:
    """Build focused report sections from one canonical decision.

    Args:
        decision: Canonical Risk decision package.

    Returns:
        Exact separated report sections with primary failure first.
    """
    logger.debug("Building focused canonical Risk decision report sections")
    decision_items = (
        (f"primary_failure={decision.primary_failure_limit}",)
        if decision.primary_failure_limit is not None
        else ()
    )
    decision_items = (*decision_items, f"state={decision.state.value}")
    calculations = tuple(
        f"{item.precedence}:{item.limit_id}={item.status.value}"
        for item in decision.ordered_checks
    )
    return {
        "evidence": tuple(
            f"{key}={value}" for key, value in decision.evidence_refs.items()
        ),
        "calculations": calculations,
        "assumptions": (),
        "warnings": decision.composite_breach_flags,
        "decision": decision_items,
        "recommendations": decision.recommendations,
    }


def _scenario_sections(
    scenarios: Sequence[ScenarioResult],
) -> dict[str, tuple[str, ...]]:
    """Build focused report sections from advisory scenario comparisons.

    Args:
        scenarios: Non-empty ordered advisory results.

    Returns:
        Exact separated aggregate scenario sections.

    Raises:
        ValueError: If no scenario result is supplied.
    """
    logger.debug("Building focused advisory Risk scenario report sections")
    if not scenarios:
        raise ValueError("scenario report requires at least one result")
    return {
        "evidence": tuple(
            f"{scenario.scenario_id}:{reference}"
            for scenario in scenarios
            for reference in scenario.evidence_refs
        ),
        "calculations": tuple(
            f"{scenario.scenario_id}:{metric}={difference}"
            for scenario in scenarios
            for metric, difference in scenario.differences.items()
        ),
        "assumptions": tuple(
            assumption for scenario in scenarios for assumption in scenario.assumptions
        ),
        "warnings": tuple(
            warning for scenario in scenarios for warning in scenario.warnings
        ),
        "decision": ("advisory_only=true", "approved=false"),
        "recommendations": (),
    }


def _markdown(sections: _SectionMap) -> str:
    """Render exact separated report sections as Markdown.

    Args:
        sections: Ordered report section values.

    Returns:
        Deterministic Markdown content.
    """
    logger.debug("Rendering deterministic Markdown Risk report")
    rendered: list[str] = ["# Risk Report"]
    for name, values in sections.items():
        rendered.extend(("", f"## {name.title()}", ""))
        rendered.extend(f"- {value}" for value in values)
        if not values:
            rendered.append("- None")
    return "\n".join(rendered) + "\n"


def _json_content(sections: _SectionMap) -> Mapping[str, object]:
    """Render exact separated sections as JSON-safe mapping content.

    Args:
        sections: Ordered report section values.

    Returns:
        Canonically round-tripped JSON-safe mapping.

    Raises:
        TypeError: If canonical JSON unexpectedly is not a mapping.
    """
    logger.debug("Rendering deterministic exact JSON Risk report")
    serialized = json.dumps(
        {name: list(values) for name, values in sections.items()},
        sort_keys=True,
        separators=(",", ":"),
    )
    loaded = json.loads(serialized)
    if not isinstance(loaded, Mapping):
        raise TypeError("JSON report content must be a mapping")
    return loaded


def _report_id(
    source: PortfolioRiskSnapshot | RiskDecisionPackage | Sequence[ScenarioResult],
    format: Literal["markdown", "json"],  # noqa: A002 - public contract name
) -> str:
    """Derive a stable readable report identity from source identity.

    Args:
        source: Supported report source.
        format: Selected exact output format.

    Returns:
        Stable report identity.
    """
    logger.debug("Deriving stable focused Risk report identity")
    if isinstance(source, PortfolioRiskSnapshot):
        identity = source.snapshot_id
    elif isinstance(source, RiskDecisionPackage):
        identity = source.decision_id
    else:
        identity = "-".join(item.scenario_id for item in source)
    return f"risk-report:{identity}:{format}"


def _validate_format(format: str, config: RiskConfig) -> None:  # noqa: A002
    """Validate exact report format against active policy.

    Args:
        format: Requested report format.
        config: Active immutable report policy.

    Raises:
        ValueError: If requested format conflicts with policy.
    """
    logger.debug("Validating requested Risk report format against policy")
    if format != config.risk_report_format:
        raise ValueError("report format conflicts with active policy")


def _validate_timeout(started: float, config: RiskConfig) -> None:
    """Validate elapsed report work against configured timeout.

    Args:
        started: Monotonic operation start.
        config: Active immutable report policy.

    Raises:
        TimeoutError: If elapsed generation exceeds policy.
    """
    logger.debug("Validating Risk report generation timeout")
    if monotonic() - started > float(config.report_timeout_seconds):
        raise TimeoutError("Risk report generation exceeded timeout")


def generate_risk_report(
    source: PortfolioRiskSnapshot | RiskDecisionPackage | Sequence[ScenarioResult],
    format: Literal["markdown", "json"],  # noqa: A002 - public contract name
    config: RiskConfig,
    *,
    now: datetime,
) -> RiskReport:
    """Generate one bounded focused deterministic Risk report.

    Args:
        source: Supported snapshot, decision, or scenario results.
        format: Exact selected Markdown or JSON format.
        config: Active immutable report policy.
        now: Caller-supplied UTC generation time.

    Returns:
        Focused Risk report with separated evidence and recommendations.

    Raises:
        RiskDomainError: If source, format, rendering, or timeout policy fails.
    """
    logger.info("Generating one focused deterministic Risk report")
    started = monotonic()
    try:
        checked_now = _utc(now)
        _validate_format(format, config)
        if isinstance(source, PortfolioRiskSnapshot):
            sections = _snapshot_sections(source)
            approval_claimed = False
        elif isinstance(source, RiskDecisionPackage):
            sections = _decision_sections(source)
            approval_claimed = _decision_approval_claimed(source, checked_now)
        else:
            sections = _scenario_sections(source)
            approval_claimed = False
        content: str | Mapping[str, object]
        content = (
            _markdown(sections) if format == "markdown" else _json_content(sections)
        )
        _validate_timeout(started, config)
        return RiskReport(
            report_id=_report_id(source, format),
            format=format,
            content=content,
            evidence=sections["evidence"],
            assumptions=sections["assumptions"],
            warnings=sections["warnings"],
            decision=sections["decision"],
            recommendations=sections["recommendations"],
            approval_claimed=approval_claimed,
            generated_at=checked_now,
        )
    except (KeyError, TypeError, ValueError, TimeoutError) as error:
        raise RiskDomainError(
            RiskErrorCode.REPORT_GENERATION_FAILED,
            "focused Risk report generation failed",
        ) from error


__all__ = ["generate_risk_report"]

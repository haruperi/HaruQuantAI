"""Risk report builder module.

Assembles JSON-safe, redacted, evidence-only risk reports from stored evidence
without recomputing metrics or performing active market checks.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import Field

from app.services.risk.models import (
    DrawdownState,
    PortfolioRiskSnapshot,
    PortfolioState,
    RiskContract,
    RiskDecisionPackage,
)
from app.utils.logger import logger
from app.utils.normalization import utc_now
from app.utils.security import redact_mapping, redact_text
from app.utils.standard import canonical_json, stable_identifier


class PortfolioRiskReport(RiskContract):
    """Consolidated portfolio-level risk metrics.

    Args:
        total_exposure: Gross portfolio exposure in account currency.
        var: Value-at-Risk snapshot metric value.
        es: Expected Shortfall snapshot metric value.
        stress_loss: Max projected stress scenario loss.
        margin_usage: Margin utilization percentage.
        drawdown: Current portfolio drawdown percentage.
    """

    total_exposure: float = Field(
        ..., description="Gross exposure in account currency."
    )
    var: float | None = Field(
        default=None, description="Value-at-Risk snapshot metric value."
    )
    es: float | None = Field(
        default=None, description="Expected Shortfall snapshot metric value."
    )
    stress_loss: float | None = Field(
        default=None, description="Max projected stress scenario loss."
    )
    margin_usage: float | None = Field(
        default=None, description="Margin utilization percentage."
    )
    drawdown: float | None = Field(
        default=None, description="Current portfolio drawdown percentage."
    )


class RiskDecisionSummary(RiskContract):
    """Summary of a single pre-trade risk decision.

    Args:
        decision_id: Unique decision ID.
        request_id: Associated request ID.
        status: Synthesized decision status.
        rule_key: Policy rule key matching the decision.
        reason: Explanation text.
        timestamp: Time of decision.
        symbol: Traded symbol.
        volume: Approved trade volume in lots.
    """

    decision_id: str = Field(..., description="Unique decision ID.")
    request_id: str = Field(..., description="Associated request ID.")
    status: str = Field(..., description="Synthesized decision status.")
    rule_key: str = Field(..., description="Primary rule key applied.")
    reason: str = Field(..., description="Explanation of decision.")
    timestamp: datetime = Field(..., description="Time of decision.")
    symbol: str | None = Field(default=None, description="Traded symbol.")
    volume: float | None = Field(
        default=None, description="Approved trade volume in lots."
    )


class RiskReport(RiskContract):
    """Structured report containing aggregated risk decision data and metrics.

    Args:
        report_id: Unique report ID.
        generated_at: Report generation timestamp.
        policy_profile: Active policy profile name.
        config_hash: Active configuration hash.
        mode: Execution trading mode.
        portfolio_exposure: Total portfolio gross exposure.
        currency_exposure: Currency exposures mapping.
        correlation_clusters: Cluster exposures mapping.
        var: Value-at-Risk snapshot metric value.
        es: Expected Shortfall snapshot metric value.
        stress_loss: Max projected stress loss.
        drawdown_state: Throttling drawdown state summary.
        margin_usage: Margin utilization percentage.
        breaches: List of rule/constraint limit breaches.
        warnings: List of advisory warnings.
        decisions: pre-trade decisions list.
        metadata: trace and version metadata.
    """

    report_id: str = Field(..., description="Unique report ID.")
    generated_at: datetime = Field(..., description="Report generation timestamp.")
    policy_profile: str | None = Field(
        default=None, description="Active policy profile name."
    )
    config_hash: str | None = Field(
        default=None, description="Active configuration hash."
    )
    mode: str | None = Field(default=None, description="Execution trading mode.")
    portfolio_exposure: float | None = Field(
        default=None, description="Total portfolio gross exposure."
    )
    currency_exposure: dict[str, float] | None = Field(
        default=None, description="Currency exposures mapping."
    )
    correlation_clusters: dict[str, float] | None = Field(
        default=None, description="Cluster exposures mapping."
    )
    var: float | None = Field(
        default=None, description="Value-at-Risk snapshot metric value."
    )
    es: float | None = Field(
        default=None, description="Expected Shortfall snapshot metric value."
    )
    stress_loss: float | None = Field(
        default=None, description="Max projected stress loss."
    )
    drawdown_state: dict[str, Any] | None = Field(
        default=None, description="Throttling drawdown state summary."
    )
    margin_usage: float | None = Field(
        default=None, description="Margin utilization percentage."
    )
    breaches: list[str] = Field(
        default_factory=list, description="List of rule/constraint limit breaches."
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of advisory warnings."
    )
    decisions: list[RiskDecisionSummary] = Field(
        default_factory=list, description="pre-trade decisions list."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="trace and version metadata."
    )

    def to_json(self) -> str:
        """Serialize and redact sensitive fields, returning a JSON string."""
        logger.debug(f"Serializing RiskReport {self.report_id} to JSON.")
        dump = self.model_dump()

        if "decisions" in dump:
            for dec in dump["decisions"]:
                if dec.get("reason"):
                    dec["reason"] = redact_text(dec["reason"])

        if dump.get("metadata"):
            dump["metadata"] = redact_mapping(dump["metadata"])

        if dump.get("drawdown_state"):
            dump["drawdown_state"] = redact_mapping(dump["drawdown_state"])

        return canonical_json(_coerce_report_value(dump))


def _coerce_report_value(v: Any) -> Any:  # noqa: ANN401
    """Coerce Decimal to float and datetime to ISO format recursively."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _coerce_report_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_coerce_report_value(val) for val in v]
    return v


def _to_float(v: Any) -> float | None:  # noqa: ANN401
    """Safely convert value to float, returning None on failure."""
    if v is None:
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _to_float_dict(d: Any) -> dict[str, float] | None:  # noqa: ANN401
    """Safely convert dictionary values to float, returning None on failure."""
    if not isinstance(d, dict):
        return None
    res = {}
    for k, v in d.items():
        fl = _to_float(v)
        if fl is not None:
            res[k] = fl
    return res


def build_risk_decision_summary(
    decision: RiskDecisionPackage,
) -> RiskDecisionSummary:
    """Build a summary from a RiskDecisionPackage.

    Args:
        decision: The decision package.

    Returns:
        RiskDecisionSummary: Summarized pre-trade decision.
    """
    logger.debug(f"Building summary for decision: {decision.decision_id}")
    details = decision.details or {}
    proposed_action = details.get("proposed_action") or {}
    if isinstance(proposed_action, dict):
        symbol = proposed_action.get("symbol")
        volume = proposed_action.get("volume")
    else:
        symbol = getattr(proposed_action, "symbol", None)
        volume = getattr(proposed_action, "volume", None)

    reason_redacted = redact_text(decision.reason) if decision.reason else ""

    return RiskDecisionSummary(
        decision_id=decision.decision_id,
        request_id=decision.request_id,
        status=decision.status,
        rule_key=decision.rule_key,
        reason=reason_redacted,
        timestamp=decision.snapshot_as_of,
        symbol=symbol,
        volume=_to_float(volume),
    )


class RiskReportEvidence(RiskContract):
    """Durable evidence object for compiling reports.

    Args:
        decisions: Immutable sequence of decisions.
        drawdown_state: Drawdown details or None.
        events: Immutable sequence of audit events.
    """

    decisions: Sequence[RiskDecisionPackage] = Field(default_factory=list)
    drawdown_state: DrawdownState | None = None
    events: Sequence[Any] = Field(default_factory=list)


class ReportRedactionPolicy:
    """Redaction configuration for report compilation."""

    def __init__(self, redact: bool = True) -> None:
        """Initialize redaction policy."""
        self.redact = redact
        logger.debug(f"ReportRedactionPolicy created: redact={redact}")


class RiskReportOptions(RiskContract):
    """Configuration options for report generation.

    Args:
        request_id: Request identification string.
        redact_sensitive: True if fields must be redacted.
    """

    request_id: str | None = None
    redact_sensitive: bool = True


class RiskReportBuilder:
    """Builder class for assembling a RiskReport from stored evidence."""

    def __init__(self, evidence: RiskReportEvidence) -> None:
        """Initialize with report evidence.

        Args:
            evidence: The gathered report evidence.
        """
        self.evidence = evidence
        logger.debug("RiskReportBuilder initialized with evidence.")

    def _parse_events(
        self,
    ) -> tuple[
        list[RiskDecisionSummary], set[str], set[str], RiskDecisionPackage | None
    ]:
        """Parse decisions and gather breaches/warnings from audit events."""
        logger.debug("Parsing decisions and events.")
        decisions_list: list[RiskDecisionSummary] = []
        breaches: set[str] = set()
        warnings: set[str] = set()
        latest_decision: RiskDecisionPackage | None = None

        # Parse decisions explicitly from evidence decisions
        for dec in self.evidence.decisions:
            summary = build_risk_decision_summary(dec)
            decisions_list.append(summary)

            dec_details = dec.details or {}
            dec_warnings = (
                dec_details.get("warning_flags") or dec_details.get("warnings") or []
            )
            for flag in dec_warnings:
                warnings.add(flag)

            for flag in dec.composite_breach_flags:
                if flag not in dec_warnings:
                    breaches.add(flag)

            if (
                latest_decision is None
                or dec.snapshot_as_of > latest_decision.snapshot_as_of
            ):
                latest_decision = dec

        # Parse additional events if decisions list is empty
        for event in self.evidence.events:
            decision_data = event.details.get("decision")
            if decision_data and not self.evidence.decisions:
                try:
                    dec = RiskDecisionPackage.model_validate(decision_data)
                    summary = build_risk_decision_summary(dec)
                    decisions_list.append(summary)

                    dec_details = dec.details or {}
                    dec_warnings = (
                        dec_details.get("warning_flags")
                        or dec_details.get("warnings")
                        or []
                    )
                    for flag in dec_warnings:
                        warnings.add(flag)

                    for flag in dec.composite_breach_flags:
                        if flag not in dec_warnings:
                            breaches.add(flag)

                    if (
                        latest_decision is None
                        or dec.snapshot_as_of > latest_decision.snapshot_as_of
                    ):
                        latest_decision = dec
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing decision from audit event: {e}")

        return decisions_list, breaches, warnings, latest_decision

    def build(self, options: RiskReportOptions) -> RiskReport:
        """Build and populate the RiskReport.

        Args:
            options: Configuration options for report generation.

        Returns:
            RiskReport: Populated report.
        """
        logger.info(f"Building report under request ID: {options.request_id}")
        decisions_list, breaches, warnings, latest_decision = self._parse_events()

        policy_profile = None
        config_hash = None
        mode = None
        portfolio_exposure = None
        currency_exposure = None
        correlation_clusters = None
        var_val = None
        es_val = None
        stress_loss_val = None
        margin_usage_val = None

        if latest_decision:
            config_hash = latest_decision.config_hash
            details = latest_decision.details or {}
            policy_profile = details.get("policy_profile")
            mode = details.get("mode")
            portfolio_exposure = details.get("portfolio_exposure")
            currency_exposure = details.get("currency_exposure")
            correlation_clusters = details.get("correlation_clusters")
            var_val = details.get("var")
            es_val = details.get("es")
            stress_loss_val = details.get("stress_loss")
            margin_usage_val = details.get("margin_usage")

            snap = latest_decision.risk_snapshot
            if snap:
                if portfolio_exposure is None:
                    portfolio_exposure = snap.exposure
                if var_val is None:
                    var_val = snap.var_es
                if stress_loss_val is None:
                    stress_loss_val = snap.stress_loss

        drawdown = self.evidence.drawdown_state
        drawdown_dict = None
        if drawdown:
            drawdown_dict = {
                "current_drawdown": float(drawdown.current_drawdown),
                "soft_limit": float(drawdown.soft_limit),
                "hard_limit": float(drawdown.hard_limit),
                "multiplier": float(drawdown.multiplier),
            }
        elif latest_decision and latest_decision.details:
            drawdown_dict = latest_decision.details.get("drawdown_state")

        meta: dict[str, Any] = {
            "risk.request_id": options.request_id or "",
            "risk.schema_version": "1.0.0",
        }
        meta = redact_mapping(meta)

        report_id = stable_identifier(
            {
                "generated_at": utc_now().isoformat(),
                "decisions_count": len(decisions_list),
            },
            prefix="report",
        )

        return RiskReport(
            report_id=report_id,
            generated_at=utc_now(),
            policy_profile=policy_profile,
            config_hash=config_hash,
            mode=mode,
            portfolio_exposure=_to_float(portfolio_exposure),
            currency_exposure=_to_float_dict(currency_exposure),
            correlation_clusters=_to_float_dict(correlation_clusters),
            var=_to_float(var_val),
            es=_to_float(es_val),
            stress_loss=_to_float(stress_loss_val),
            drawdown_state=drawdown_dict,
            margin_usage=_to_float(margin_usage_val),
            breaches=sorted(breaches),
            warnings=sorted(warnings),
            decisions=decisions_list,
            metadata=meta,
        )


def generate_risk_report(
    evidence: Any = None,
    options: Any = None,
    *,
    state_store: Any = None,
    audit_sink: Any = None,
    decision_store: Any = None,
    request_id: str | None = None,
    write_to_path: str | None = None,
) -> RiskReport:
    """Generate a risk report from stored evidence or store facades.

    Args:
        evidence: The gathered report evidence (RiskReportEvidence) or state_store.
        options: Configuration options (RiskReportOptions) or None.
        state_store: Deprecated store interface.
        audit_sink: Deprecated audit trail interface.
        decision_store: Deprecated decision storage.
        request_id: Tracing correlation ID.
        write_to_path: Target path to write JSON report output.

    Returns:
        RiskReport: Generated report.
    """
    logger.info("Generating risk report.")

    # Dual-signature check
    if evidence is not None and not isinstance(evidence, RiskReportEvidence):
        state_store = evidence
        evidence = None

    if evidence is None:
        decisions = []
        if decision_store is not None:
            decisions = decision_store.list_decisions()

        drawdown_state = None
        if state_store is not None:
            if hasattr(state_store, "get_drawdown_state"):
                drawdown_state = state_store.get_drawdown_state()

        events = []
        if audit_sink is not None:
            if hasattr(audit_sink, "list_audit_events"):
                events = audit_sink.list_audit_events()
            elif hasattr(audit_sink, "_audit_events"):
                events = audit_sink._audit_events

        evidence = RiskReportEvidence(
            decisions=decisions,
            drawdown_state=drawdown_state,
            events=events,
        )

    if options is None:
        options = RiskReportOptions(request_id=request_id)

    builder = RiskReportBuilder(evidence)
    report = builder.build(options)

    if options.redact_sensitive:
        report = redact_risk_report(report)

    if write_to_path is not None:
        from app.services.risk.reports.exporter import (
            AuthorizedReportPath,
            write_risk_report,
        )

        path_obj = Path(write_to_path)
        if path_obj.is_absolute():
            if str(path_obj).startswith(str(Path.cwd())):
                rel = str(path_obj.relative_to(Path.cwd()))
                root_dir = str(Path.cwd())
            else:
                root_dir = str(path_obj.anchor)
                rel = str(path_obj.relative_to(path_obj.anchor))
        else:
            root_dir = str(Path.cwd())
            rel = write_to_path

        dest = AuthorizedReportPath(
            root=root_dir,
            relative_path=rel,
            overwrite=True,
            request_id=options.request_id,
        )
        write_risk_report(report, dest)

    return report


def redact_risk_report(
    report: RiskReport,
    policy: ReportRedactionPolicy | None = None,
) -> RiskReport:
    """Remove sensitive fields from the report.

    Args:
        report: The report to redact.
        policy: The optional redaction policy config.

    Returns:
        RiskReport: Redacted report copy.
    """
    logger.info(f"Redacting risk report: {report.report_id}")
    active_policy = policy or ReportRedactionPolicy()
    if not active_policy.redact:
        return report

    copied = report.model_copy(deep=True)

    for dec in copied.decisions:
        if dec.reason:
            dec.reason = redact_text(dec.reason)

    if copied.metadata:
        copied.metadata = redact_mapping(copied.metadata)

    if copied.drawdown_state:
        copied.drawdown_state = redact_mapping(copied.drawdown_state)

    return copied


def build_portfolio_risk_snapshot(
    portfolio_state: dict[str, Any] | PortfolioState,
    market_context: dict[str, Any],
    config_profile: str = "default",
) -> PortfolioRiskSnapshot:
    """Compile a complete portfolio risk snapshot.

    Args:
        portfolio_state: Account balance, equity, and position lists.
        market_context: Active market quotes and returns databases.
        config_profile: Configuration profile name.

    Returns:
        PortfolioRiskSnapshot: The compiled portfolio risk snapshot.
    """
    logger.info("Compiling portfolio risk snapshot.")
    from app.services.risk.config import load_risk_config
    from app.services.risk.stress import build_default_scenario_registry
    from app.services.risk.tail_risk import calculate_var_es_snapshots

    if isinstance(portfolio_state, dict):
        p_state = PortfolioState.model_validate(portfolio_state)
    else:
        p_state = portfolio_state

    config = load_risk_config(config_profile)

    try:
        var_snap, _es_snap = calculate_var_es_snapshots(
            portfolio_state=p_state,
            proposed_trade=None,
            market_context=market_context,
            config=config,
            min_samples=2,
        )
        var_val = var_snap.result
    except Exception as e:  # noqa: BLE001
        logger.warning(f"VaR/ES snapshot calculation failed: {e}")
        var_val = Decimal("0.0")

    try:
        registry = build_default_scenario_registry()
        stress_results = registry.evaluate_portfolio(
            portfolio_state=p_state,
            proposed_trade=None,
            market_context=market_context,
            config=config,
        )
        max_stress = max(
            (sr.impact_pct for sr in stress_results), default=Decimal("0.0")
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Stress scenarios evaluation failed: {e}")
        max_stress = Decimal("0.0")

    drawdown_pct = Decimal("0.0")
    if p_state.balance > 0:
        drawdown_pct = max(
            (p_state.balance - p_state.equity) / p_state.balance, Decimal("0.0")
        )

    total_exposure = sum(
        (abs(pos.quantity * pos.current_price) for pos in p_state.positions),
        Decimal("0.0"),
    )

    return PortfolioRiskSnapshot(
        positions=p_state.positions,
        pending_orders=[],
        in_flight_orders=[],
        exposure=total_exposure,
        var_es=var_val,
        stress_loss=max_stress,
        drawdown=drawdown_pct,
    )

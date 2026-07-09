# ruff: noqa: BLE001, SLF001, E501, TRY301
"""Official AI-callable Risk tools.

Provides the standardized, safe, and governed surface for all Risk tools.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Any, Literal, TypeVar

from pydantic import Field

from app.services.risk.config import load_risk_config
from app.services.risk.governor import RiskGovernor
from app.services.risk.models import (
    PortfolioState,
    PositionSizingRequest,
    ProposedAllocation,
    ProposedTrade,
    RiskApprovalToken,
    RiskAssessmentRequest,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    StrategyAdmissionRequest,
)
from app.services.risk.regime import RegimeAssessment, assess_risk_regime
from app.services.risk.sizing import calculate_position_size
from app.services.risk.storage import InMemoryRiskStateStore
from app.services.risk.stress import build_default_scenario_registry
from app.services.risk.tail_risk import calculate_var_es_snapshots
from app.utils.errors import ValidationError, exception_to_error_payload

# Type variable for generics
T = TypeVar("T", bound=RiskContract)


# --- Response Envelopes ---
class ToolError(RiskContract):
    """Standardized tool error structure."""

    code: str = Field(..., description="Error classification code.")
    details: str = Field(..., description="Failure explanation details.")


class ToolResponse[T: RiskContract](RiskContract):
    """Standardized tool response envelope."""

    status: Literal["success", "error"] = Field(..., description="Execution status.")
    message: str = Field(..., description="Summary execution message.")
    data: T | None = Field(default=None, description="The success payload.")
    error: ToolError | None = Field(default=None, description="The error payload.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Tool execution metadata."
    )


# --- Request Contracts ---
class PortfolioRiskSnapshotToolRequest(RiskContract):
    """Request contract for compiling portfolio risk snapshots."""

    portfolio_state: PortfolioState
    market_context: dict[str, Any]
    config_profile: str = "default"
    request_id: str | None = None


class TradeRiskReviewToolRequest(RiskContract):
    """Request contract for pre-trade risk checks."""

    proposed_trade: ProposedTrade
    portfolio_state: PortfolioState
    market_context: dict[str, Any]
    config_profile: str = "default"
    request_id: str | None = None


class PositionSizeToolRequest(RiskContract):
    """Request contract for position sizing calculations."""

    portfolio_state: PortfolioState
    proposed_trade: ProposedTrade
    market_context: dict[str, Any]
    config_profile: str = "default"
    request_id: str | None = None


class RiskRegimeToolRequest(RiskContract):
    """Request contract for market regime assessments."""

    symbol: str = "EURUSD"
    market_context: dict[str, Any]
    config_profile: str = "default"
    request_id: str | None = None


class StrategyAdmissionToolRequest(RiskContract):
    """Request contract for strategy lifecycle promotion reviews."""

    strategy_admission_request: StrategyAdmissionRequest
    portfolio_state: PortfolioState
    config_profile: str = "default"
    request_id: str | None = None


class AllocationReviewToolRequest(RiskContract):
    """Request contract for capital allocation adjustments."""

    proposed_allocation: ProposedAllocation
    portfolio_state: PortfolioState
    config_profile: str = "default"
    request_id: str | None = None


class PortfolioGovernorToolRequest(RiskContract):
    """Request contract for periodic portfolio governance sweeps."""

    portfolio_state: PortfolioState
    config_profile: str = "default"
    request_id: str | None = None


class TokenValidationToolRequest(RiskContract):
    """Request contract for cryptographic token validations."""

    token: RiskApprovalToken
    expected_scope: dict[str, Any] | None = None
    request_id: str | None = None


class KillSwitchStatusToolRequest(RiskContract):
    """Request contract for checking active kill switches."""

    scope: str = "global"
    target_id: str | None = None
    request_id: str | None = None


class ScenarioAnalysisToolRequest(RiskContract):
    """Request contract for portfolio shock scenario stress tests."""

    portfolio_state: PortfolioState
    scenario_name: str | None = None
    market_context: dict[str, Any] | None = None
    config_profile: str = "default"
    request_id: str | None = None


class RiskReportToolRequest(RiskContract):
    """Request contract for generating risk reports."""

    report_type: str = "standard"
    request_id: str | None = None
    authorized_path: str | None = None


# --- Payload Contracts ---
class RiskSnapshotPayload(RiskContract):
    """Response payload for portfolio risk snapshot metrics."""

    positions: list[Any] = Field(default_factory=list)
    pending_orders: list[Any] = Field(default_factory=list)
    in_flight_orders: list[Any] = Field(default_factory=list)
    exposure: Decimal
    var_es: Decimal
    stress_loss: Decimal
    drawdown: Decimal


class RiskDecisionPayload(RiskContract):
    """Response payload for governor decision outcomes."""

    status: RiskDecisionStatus
    reason: str
    decision_id: str | None = None
    breaches: list[str] = Field(default_factory=list)


class PositionSizingPayload(RiskContract):
    """Response payload for calculated position sizes."""

    calculated_volume: Decimal
    method: str
    stop_loss_pips: Decimal | None = None


RegimePayload = RegimeAssessment


class TokenValidationPayload(RiskContract):
    """Response payload for token validations."""

    valid: bool
    message: str


class KillSwitchPayload(RiskContract):
    """Response payload for kill switch status queries."""

    active: bool
    scope: str
    reason: str | None = None


class StressPayload(RiskContract):
    """Response payload for stress test results."""

    results: dict[str, Any] = Field(default_factory=dict)


class RiskReportPayload(RiskContract):
    """Response payload for generated risk reports."""

    report_id: str
    report_path: str | None = None
    authorized: bool = False


# --- Shared Backend Components ---
_shared_store = InMemoryRiskStateStore()
_shared_governor = RiskGovernor(
    state_store=_shared_store,
    audit_sink=_shared_store,
    policy_store=_shared_store,
    decision_store=_shared_store,
)


def _validate_live_sensitive_tool_context(
    market_context: dict[str, Any],
    config_profile: str,
    operator_role: str | None = None,
) -> None:
    """Validate live-sensitive requests."""
    mode = market_context.get("mode", "paper")
    env = market_context.get("environment", "local")
    is_live = mode in {"micro_live", "full_live"} or env in {"production", "live"}
    if is_live:
        if mode not in {"micro_live", "full_live"}:
            msg = f"Invalid live execution mode: '{mode}'."
            raise ValidationError(msg)
        if not config_profile or not isinstance(config_profile, str):
            msg = "A valid policy profile name is required in live execution mode."
            raise ValidationError(msg)
        if not operator_role or str(operator_role).lower() not in {
            "operator",
            "risk_manager",
            "admin",
            "compliance_officer",
        }:
            msg = "Missing or unauthorized operator role for live execution mode."
            raise ValidationError(msg)
        if not market_context.get("freshness"):
            msg = "Freshness evidence is required for live execution mode."
            raise ValidationError(msg)


# --- Official Tool Wrapper Implementations ---


def build_portfolio_risk_snapshot_tool(
    request: PortfolioRiskSnapshotToolRequest,
) -> ToolResponse[RiskSnapshotPayload]:
    """Compiles portfolio risk snapshot and exposure metrics."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        config = load_risk_config(request.config_profile)
        p_state = request.portfolio_state
        market_context = request.market_context

        # 1. Calculate VaR/ES
        try:
            var_snap, _es_snap = calculate_var_es_snapshots(
                portfolio_state=p_state,
                proposed_trade=None,
                market_context=market_context,
                config=config,
                min_samples=2,
            )
            var_val = var_snap.result
        except Exception:
            var_val = Decimal("0.0")

        # 2. Stress loss
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
        except Exception:
            max_stress = Decimal("0.0")

        # 3. Drawdown
        drawdown_pct = Decimal("0.0")
        if p_state.balance > 0:
            drawdown_pct = max(
                (p_state.balance - p_state.equity) / p_state.balance, Decimal("0.0")
            )

        # 4. Total exposure
        total_exposure = sum(
            (abs(pos.quantity * pos.current_price) for pos in p_state.positions),
            Decimal("0.0"),
        )

        payload = RiskSnapshotPayload(
            positions=p_state.positions,
            exposure=total_exposure,
            var_es=var_val,
            stress_loss=max_stress,
            drawdown=drawdown_pct,
        )

        meta = {
            "haruquant.tool.name": "build_portfolio_risk_snapshot_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message="Successfully compiled portfolio risk snapshot.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "build_portfolio_risk_snapshot_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to compile portfolio risk snapshot.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def review_trade_risk_tool(
    request: TradeRiskReviewToolRequest,
) -> ToolResponse[RiskDecisionPayload]:
    """Performs pre-trade check against active limits and policies."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        market_context = request.market_context
        _validate_live_sensitive_tool_context(
            market_context,
            request.config_profile,
            market_context.get("operator_role"),
        )

        assessment_req = RiskAssessmentRequest(
            proposed_action=request.proposed_trade,
            portfolio_state=request.portfolio_state,
            risk_config=RiskConfig(profile_name=request.config_profile),
            market_context=market_context,
            request_id=req_id,
        )
        decision = _shared_governor.review_trade(assessment_req)

        payload = RiskDecisionPayload(
            status=decision.status,
            reason=decision.reason,
            decision_id=decision.decision_id,
            breaches=decision.composite_breach_flags,
        )

        meta = {
            "haruquant.tool.name": "review_trade_risk_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Trade risk review completed with status: {decision.status}.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "review_trade_risk_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to execute trade risk review.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def calculate_position_size_tool(
    request: PositionSizeToolRequest,
) -> ToolResponse[PositionSizingPayload]:
    """Calculates policy-bounded volume for proposed position."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        config = load_risk_config(request.config_profile)
        p_state = request.portfolio_state
        trade = request.proposed_trade
        market_context = request.market_context

        sizing_req_data = market_context.get("sizing_request") or {}
        sizing_request = PositionSizingRequest(
            symbol=trade.symbol,
            method=sizing_req_data.get("method", "fixed_lot"),
            fixed_volume=Decimal(str(sizing_req_data.get("fixed_volume")))
            if sizing_req_data.get("fixed_volume") is not None
            else trade.volume,
            risk_percent=Decimal(str(sizing_req_data.get("risk_percent")))
            if sizing_req_data.get("risk_percent") is not None
            else None,
            stop_loss_pips=Decimal(str(sizing_req_data.get("stop_loss_pips")))
            if sizing_req_data.get("stop_loss_pips") is not None
            else None,
            atr_value=Decimal(str(sizing_req_data.get("atr_value")))
            if sizing_req_data.get("atr_value") is not None
            else None,
        )

        res = calculate_position_size(
            request=sizing_request,
            portfolio_state=p_state,
            market_context=market_context,
            config=config,
        )

        payload = PositionSizingPayload(
            calculated_volume=res.calculated_volume,
            method=res.sizing_method,
            stop_loss_pips=res.stop_distance_pips,
        )

        meta = {
            "haruquant.tool.name": "calculate_position_size_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Position size calculation complete: {res.calculated_volume} lots.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "calculate_position_size_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to calculate position size.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def assess_risk_regime_tool(
    request: RiskRegimeToolRequest,
) -> ToolResponse[RegimePayload]:
    """Assesses active market conditions and regime risk status."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        config = load_risk_config(request.config_profile)
        market_context = request.market_context

        # Assemble temporary snapshot
        from app.services.risk.models import MarketRiskSnapshot
        from app.utils.normalization import parse_datetime, utc_now

        symbol = request.symbol
        spreads_list = market_context.get("spreads", {}).get(symbol, [])
        current_spread = (
            Decimal(str(spreads_list[-1])) if spreads_list else Decimal("0.0001")
        )
        volatility = Decimal(str(market_context.get("volatility", "0.001")))
        session = market_context.get("session", "active")

        rollover_time = market_context.get("rollover_time")
        if isinstance(rollover_time, str):
            rollover_time = parse_datetime(rollover_time)

        freshness = market_context.get("freshness")
        if isinstance(freshness, str):
            freshness = parse_datetime(freshness)
        if not freshness:
            freshness = utc_now()

        snap = MarketRiskSnapshot(
            spread=current_spread,
            volatility=volatility,
            session=session,
            rollover_time=rollover_time,
            news_impact=market_context.get("news_impact"),
            freshness=freshness,
        )

        calendar_evidence = market_context.get("calendar_evidence", [])
        res = assess_risk_regime(
            market_snapshot=snap,
            calendar_evidence=calendar_evidence,
            risk_config=config,
            market_context=market_context,
        )

        payload = res

        meta = {
            "haruquant.tool.name": "assess_risk_regime_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Market regime assessment complete: {res.regime}.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "assess_risk_regime_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "low",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to assess risk regime.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def review_strategy_admission_tool(
    request: StrategyAdmissionToolRequest,
) -> ToolResponse[RiskDecisionPayload]:
    """Reviews strategy promotion lifecycle stage."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        market_context: dict[str, Any] = {}
        assessment_req = RiskAssessmentRequest(
            proposed_action=request.strategy_admission_request,
            portfolio_state=request.portfolio_state,
            risk_config=RiskConfig(profile_name=request.config_profile),
            market_context=market_context,
            request_id=req_id,
        )
        decision = _shared_governor.review_strategy_admission(assessment_req)

        payload = RiskDecisionPayload(
            status=decision.status,
            reason=decision.reason,
            decision_id=decision.decision_id,
            breaches=decision.composite_breach_flags,
        )

        meta = {
            "haruquant.tool.name": "review_strategy_admission_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Strategy admission review completed with status: {decision.status}.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "review_strategy_admission_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to review strategy admission.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def review_allocation_proposal_tool(
    request: AllocationReviewToolRequest,
) -> ToolResponse[RiskDecisionPayload]:
    """Reviews dynamic capital allocation adjustments."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        market_context = request.portfolio_state.as_of.isoformat()
        fake_context = {"mode": "paper", "freshness": market_context}
        _validate_live_sensitive_tool_context(
            fake_context,
            request.config_profile,
            "risk_manager",
        )

        assessment_req = RiskAssessmentRequest(
            proposed_action=request.proposed_allocation,
            portfolio_state=request.portfolio_state,
            risk_config=RiskConfig(profile_name=request.config_profile),
            market_context=fake_context,
            request_id=req_id,
        )
        decision = _shared_governor.review_allocation(assessment_req)

        payload = RiskDecisionPayload(
            status=decision.status,
            reason=decision.reason,
            decision_id=decision.decision_id,
            breaches=decision.composite_breach_flags,
        )

        meta = {
            "haruquant.tool.name": "review_allocation_proposal_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Allocation proposal review completed with status: {decision.status}.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "review_allocation_proposal_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to review allocation proposal.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def run_portfolio_risk_governor_tool(
    request: PortfolioGovernorToolRequest,
) -> ToolResponse[RiskDecisionPayload]:
    """Executes portfolio risk governor validation loop."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        fake_context = {
            "mode": "paper",
            "freshness": request.portfolio_state.as_of.isoformat(),
        }
        _validate_live_sensitive_tool_context(
            fake_context,
            request.config_profile,
            "risk_manager",
        )

        assessment_req = RiskAssessmentRequest(
            proposed_action=ProposedTrade(
                strategy_id="portfolio-check",
                symbol="EURUSD",
                side="buy",
                volume=Decimal("0.0"),
            ),
            portfolio_state=request.portfolio_state,
            risk_config=RiskConfig(profile_name=request.config_profile),
            market_context=fake_context,
            request_id=req_id,
        )
        decision = _shared_governor.run_portfolio_risk_governor(assessment_req)

        payload = RiskDecisionPayload(
            status=decision.status,
            reason=decision.reason,
            decision_id=decision.decision_id,
            breaches=decision.composite_breach_flags,
        )

        meta = {
            "haruquant.tool.name": "run_portfolio_risk_governor_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "critical",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Portfolio risk governor run completed with status: {decision.status}.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "run_portfolio_risk_governor_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "critical",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to run portfolio risk governor.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def validate_risk_approval_token_tool(
    request: TokenValidationToolRequest,
) -> ToolResponse[TokenValidationPayload]:
    """Verifies the authenticity and state of an approval token."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        from app.services.risk.audit import (
            validate_risk_approval_token as _validate_token,
        )

        config = load_risk_config("default")
        valid = _validate_token(
            token=request.token,
            expected_scope=request.expected_scope or {},
            active_config_hash=config.contract_hash(),
            active_policy_hash="",
            state_store=_shared_store,
        )

        payload = TokenValidationPayload(
            valid=valid,
            message="Token is valid"
            if valid
            else "Token is invalid or expired/revoked",
        )

        meta = {
            "haruquant.tool.name": "validate_risk_approval_token_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message="Token validation check completed.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "validate_risk_approval_token_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to validate approval token.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def check_risk_kill_switch_tool(
    request: KillSwitchStatusToolRequest,
) -> ToolResponse[KillSwitchPayload]:
    """Queries active global/portfolio/strategy kill switch status."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        from app.services.risk.governance.kill_switch import get_kill_switch_manager

        manager = get_kill_switch_manager()
        active = False
        reason = None

        scope = request.scope.lower().strip()
        target = request.target_id or "*"

        with manager._lock:
            active = manager.is_blocked(scope, target)
            if active:
                if scope == "global":
                    rec = manager.states.get("global")
                    reason = (
                        rec.get("reason")
                        if isinstance(rec, dict)
                        else "Global kill switch active"
                    )
                elif scope == "portfolio":
                    rec = manager.states.get("portfolio")
                    reason = (
                        rec.get("reason")
                        if isinstance(rec, dict)
                        else "Portfolio kill switch active"
                    )
                elif scope == "strategy":
                    rec = manager.states.get("strategies", {}).get(target)
                    reason = (
                        rec.get("reason")
                        if isinstance(rec, dict)
                        else f"Strategy {target} kill switch active"
                    )
                elif scope == "symbol":
                    rec = manager.states.get("symbols", {}).get(target)
                    reason = (
                        rec.get("reason")
                        if isinstance(rec, dict)
                        else f"Symbol {target} kill switch active"
                    )
                elif scope == "currency":
                    rec = manager.states.get("currencies", {}).get(target)
                    reason = (
                        rec.get("reason")
                        if isinstance(rec, dict)
                        else f"Currency {target} kill switch active"
                    )
                else:
                    reason = "Kill switch active"
            else:
                reason = "No active kill switch"

        payload = KillSwitchPayload(
            active=active,
            scope=request.scope,
            reason=reason,
        )

        meta = {
            "haruquant.tool.name": "check_risk_kill_switch_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message="Kill switch status check completed.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "check_risk_kill_switch_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to check kill switch status.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def run_risk_scenario_analysis_tool(
    request: ScenarioAnalysisToolRequest,
) -> ToolResponse[StressPayload]:
    """Runs stress scenario analysis against portfolio models."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        config = load_risk_config(request.config_profile)
        p_state = request.portfolio_state
        registry = build_default_scenario_registry()

        # Determine market context
        market_context = request.market_context or {}

        results = {}
        if request.scenario_name:
            # Evaluate single scenario
            scenario = registry.scenarios.get(request.scenario_name)
            if not scenario:
                msg = f"Scenario '{request.scenario_name}' not found in registry."
                raise ValidationError(msg)
            res = scenario.evaluate(p_state, None, market_context, config)
            results[request.scenario_name] = res.model_dump()
        else:
            # Evaluate all scenarios
            list_res = registry.evaluate_portfolio(
                p_state, None, market_context, config
            )
            for r in list_res:
                results[r.scenario_name] = r.model_dump()

        payload = StressPayload(results=results)

        meta = {
            "haruquant.tool.name": "run_risk_scenario_analysis_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message=f"Scenario analysis complete. Executed {len(results)} scenarios.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "run_risk_scenario_analysis_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "high",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": False,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to run stress scenario analysis.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )


def generate_risk_report_tool(
    request: RiskReportToolRequest,
) -> ToolResponse[RiskReportPayload]:
    """Generates standard and redacted risk reports."""
    t_start = time.perf_counter()
    req_id = request.request_id
    try:
        from app.services.risk.reports.builder import (
            RiskReportOptions,
            generate_risk_report,
        )
        from app.services.risk.reports.exporter import write_risk_report

        # Gather evidence from shared store
        evidence = _shared_store.get_all_events()
        options = RiskReportOptions(request_id=req_id)

        report = generate_risk_report(evidence, options)

        path_written = None
        authorized = False
        if request.authorized_path:
            authorized = True
            from pathlib import Path

            from app.services.risk.reports.exporter import AuthorizedReportPath

            dest = AuthorizedReportPath(
                root=str(Path(request.authorized_path).parent),
                relative_path=str(Path(request.authorized_path).name),
                overwrite=True,
                request_id=req_id,
            )
            receipt = write_risk_report(report, dest)
            path_written = receipt.destination_path

        payload = RiskReportPayload(
            report_id=report.report_id,
            report_path=path_written,
            authorized=authorized,
        )

        meta = {
            "haruquant.tool.name": "generate_risk_report_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": True,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }

        return ToolResponse(
            status="success",
            message="Risk report generated successfully.",
            data=payload,
            metadata=meta,
        )
    except Exception as e:
        meta = {
            "haruquant.tool.name": "generate_risk_report_tool",
            "haruquant.tool.version": "1.0.0",
            "haruquant.tool.category": "risk",
            "haruquant.tool.risk_level": "medium",
            "haruquant.request.id": req_id,
            "haruquant.execution.ms": (time.perf_counter() - t_start) * 1000.0,
            "haruquant.reads": True,
            "haruquant.writes": True,
            "haruquant.updates": False,
            "haruquant.deletes": False,
            "haruquant.trades": False,
            "haruquant.requires_network": False,
        }
        err_info = exception_to_error_payload(e, default_code="TOOL_EXECUTION_FAILED")
        return ToolResponse(
            status="error",
            message="Failed to generate risk report.",
            error=ToolError(code=err_info["code"], details=err_info["details"]),
            metadata=meta,
        )

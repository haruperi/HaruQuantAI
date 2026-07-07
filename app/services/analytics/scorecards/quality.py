# ruff: noqa: C901, PLR0912, PLR0915
"""Strategy quality scorecard evaluations for Analytics.

Evaluates an analytics report to produce a non-binding scorecard with warnings,
strengths, and recommended action.
All calculations are stateless pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError

if TYPE_CHECKING:
    from app.services.analytics.reports import AnalyticsReport


@dataclass(frozen=True, slots=True)
class NonBindingRecommendation:
    """Non-binding recommendation container.

    Args:
        action: Non-binding action recommendation.
        rationale: Rationale behind the recommendation.
    """

    action: str
    rationale: str = ""


@dataclass(frozen=True, slots=True)
class StrategyQualityAssessment:
    """Non-binding strategy-quality scorecard result assessment.

    Args:
        score: Normalized 0-to-100 quality score.
        strengths: Positive evidence strings.
        warnings: Warning evidence strings.
        recommendation: Non-binding recommended action details.
        is_binding_decision: Always ``False`` for Analytics outputs.
        disclaimer: Legal disclaimer text.
    """

    score: float
    strengths: tuple[str, ...]
    warnings: tuple[str, ...]
    recommendation: NonBindingRecommendation
    is_binding_decision: bool = False
    disclaimer: str = (
        "This report represents non-binding analytics evidence and decision "
        "context only. It does not certify live-readiness or execute orders."
    )


@dataclass(frozen=True, slots=True)
class StrategyQualityConfig:
    """Configuration options for strategy quality scorecard rules.

    Args:
        profit_factor_min: Minimum profit factor allowed before penalty.
        profit_factor_robust: Profit factor threshold for high robustness.
        win_rate_min: Minimum win rate allowed before penalty.
        win_rate_robust: Win rate threshold for high robustness.
        trades_min: Minimum total trades required.
        trades_robust: Total trades threshold for high statistical power.
        drawdown_max: Maximum drawdown percent allowed before penalty.
        drawdown_robust: Maximum drawdown threshold for high robustness.
        sharpe_min: Minimum Sharpe ratio allowed before penalty.
        sharpe_robust: Sharpe ratio threshold for high robustness.
    """

    profit_factor_min: float = 1.2
    profit_factor_robust: float = 1.5
    win_rate_min: float = 0.45
    win_rate_robust: float = 0.55
    trades_min: int = 50
    trades_robust: int = 100
    drawdown_max: float = 25.0
    drawdown_robust: float = 10.0
    sharpe_min: float = 1.0
    sharpe_robust: float = 1.5


@dataclass(frozen=True, slots=True)
class ScorecardRule:
    """Non-binding analytics scorecard rule.

    Args:
        metric_name: Metric Definition Catalog key the rule evaluates.
        threshold: Numeric threshold for the rule.
        direction: Passing direction: ``gte`` or ``lte``.
        warning_code: Stable warning or quality-flag code.
        severity: Warning severity.
        recommendation: Non-binding recommendation text.
    """

    metric_name: str
    threshold: float
    direction: str
    warning_code: str
    severity: str = "warning"
    recommendation: str = "Review before promotion."


@dataclass(frozen=True, slots=True)
class ScorecardResult:
    """Non-binding strategy-quality scorecard result wrapper.

    Args:
        score: Normalized 0-to-100 quality score.
        strengths: Positive evidence strings.
        warnings: Warning evidence strings.
        recommended_action: Non-binding recommended action.
        is_binding_decision: Always ``False`` for Analytics.
        quality_flags: Structured quality flags.
    """

    score: float
    strengths: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_action: str = "Review before promotion."
    is_binding_decision: bool = False
    quality_flags: list[dict[str, Any]] = field(default_factory=list)


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None and (
        not isinstance(request_id, str) or not request_id.strip()
    ):
        raise ValidationError("request_id must be a non-empty string.")


def sqn(
    report: AnalyticsReport | dict[str, Any] | None,
    _config: StrategyQualityConfig | None = None,
) -> StrategyQualityAssessment:
    """Calculate and assess System Quality Number (SQN)."""
    # Extract report sections safely
    sections: dict[str, Any] = {}
    if report is not None:
        if isinstance(report, dict):
            sections = report.get("sections") or report
        elif hasattr(report, "sections"):
            sections = report.sections

    ratio_sec = sections.get("ratio_metrics") or sections.get("ratios") or {}
    sqn_val = float(ratio_sec.get("sqn", 0.0))

    strengths = []
    warnings = []
    score = 100.0

    if sqn_val >= 3.0:  # noqa: PLR2004
        strengths.append(f"Superb System Quality Number (SQN: {sqn_val:.2f})")
    elif sqn_val >= 2.0:  # noqa: PLR2004
        strengths.append(f"Good System Quality Number (SQN: {sqn_val:.2f})")
    elif sqn_val > 0:
        warnings.append(
            f"Average or low System Quality Number (SQN: {sqn_val:.2f})"
        )
        score -= 20.0
    else:
        warnings.append("System Quality Number (SQN) is zero or negative.")
        score -= 40.0

    score = max(min(score, 100.0), 0.0)
    rec_action = (
        "Review SQN performance and trade distribution before live sandbox "
        "promotion."
    )
    return StrategyQualityAssessment(
        score=score,
        strengths=tuple(strengths),
        warnings=tuple(warnings),
        recommendation=NonBindingRecommendation(action=rec_action),
    )


def sample_size_warning(
    report: AnalyticsReport | dict[str, Any] | None,
    config: StrategyQualityConfig | None = None,
) -> StrategyQualityAssessment:
    """Assess metric reliability based on trade sample size."""
    cfg = config or StrategyQualityConfig()
    sections: dict[str, Any] = {}
    if report is not None:
        if isinstance(report, dict):
            sections = report.get("sections") or report
        elif hasattr(report, "sections"):
            sections = report.sections

    trade_sec = sections.get("trade_metrics") or sections.get("trade") or {}
    total_tr = int(trade_sec.get("total_trades", 0))

    strengths = []
    warnings = []
    score = 100.0

    if total_tr >= cfg.trades_robust:
        strengths.append(f"Sufficient sample size ({total_tr} trades)")
    elif total_tr < cfg.trades_min:
        score -= 30.0
        warnings.append(
            f"Critically small sample size ({total_tr} trades < "
            f"{cfg.trades_min} min required)"
        )
    else:
        score -= 15.0
        warnings.append(
            f"Moderate sample size ({total_tr} trades), statistical variance "
            "may be high"
        )

    score = max(min(score, 100.0), 0.0)
    rec_action = (
        "Gather more walk-forward or simulation periods to stabilize "
        "statistical metrics."
    )
    return StrategyQualityAssessment(
        score=score,
        strengths=tuple(strengths),
        warnings=tuple(warnings),
        recommendation=NonBindingRecommendation(action=rec_action),
    )


def evaluate_strategy_quality(
    report: AnalyticsReport | dict[str, Any] | None,
    config: StrategyQualityConfig | None = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Evaluate a strategy report to provide a non-binding quality score."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="evaluate_strategy_quality",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        if report is None:
            return response_from_exception(
                exception=ValidationError("report must not be None."),
                metadata=meta,
            )
        if not isinstance(report, dict) and not hasattr(report, "sections"):
            return response_from_exception(
                exception=ValidationError(
                    "report must be a dictionary or have a sections attribute."
                ),
                metadata=meta,
            )

        cfg = config or StrategyQualityConfig()
        sections: dict[str, Any] = {}
        if isinstance(report, dict):
            sections = report.get("sections") or report
        else:
            sections = report.sections

        trade_sec = sections.get("trade_metrics") or sections.get("trade") or {}
        ratio_sec = sections.get("ratio_metrics") or sections.get("ratios") or {}
        dd_sec = sections.get("drawdown_metrics") or sections.get("drawdown") or {}

        # Default values
        p_factor = float(ratio_sec.get("profit_factor", 1.0))
        w_rate = float(trade_sec.get("win_rate", 0.5))
        total_tr = int(trade_sec.get("total_trades", 0))
        max_dd = float(dd_sec.get("max_drawdown_percent", 0.0))
        sharpe = float(ratio_sec.get("sharpe_ratio", 0.0))

        score = 100.0
        strengths = []
        warnings = []

        if p_factor >= cfg.profit_factor_robust:
            strengths.append(f"Robust profit factor (> {cfg.profit_factor_robust})")
        elif p_factor < cfg.profit_factor_min:
            score -= 20.0
            warnings.append(f"Low profit factor (< {cfg.profit_factor_min})")

        if w_rate >= cfg.win_rate_robust:
            strengths.append(f"High win rate (> {int(cfg.win_rate_robust * 100)}%)")
        elif w_rate < cfg.win_rate_min:
            score -= 15.0
            warnings.append(f"Low win rate (< {int(cfg.win_rate_min * 100)}%)")

        if total_tr >= cfg.trades_robust:
            strengths.append(f"Sufficient sample size (> {cfg.trades_robust} trades)")
        elif total_tr < cfg.trades_min:
            score -= 15.0
            warnings.append(
                f"Small sample size (< {cfg.trades_min} trades) makes "
                "statistics less reliable"
            )

        if 0 < max_dd <= cfg.drawdown_robust:
            strengths.append(f"Low maximum drawdown (<= {cfg.drawdown_robust}%)")
        elif max_dd > cfg.drawdown_max:
            score -= 25.0
            warnings.append(f"High drawdown (> {cfg.drawdown_max}%) risk exposure")

        if sharpe >= cfg.sharpe_robust:
            strengths.append(
                f"Excellent risk-adjusted returns (Sharpe >= {cfg.sharpe_robust})"
            )
        elif sharpe < cfg.sharpe_min:
            score -= 15.0
            warnings.append(
                f"Sharpe ratio (< {cfg.sharpe_min}) shows sub-optimal "
                "risk-adjusted return"
            )

        # Keep score within [0, 100]
        score = max(min(score, 100.0), 0.0)

        # Recommended action based on score
        if score >= 80:  # noqa: PLR2004
            rec_action = (
                "Promote to paper trading sandbox for out-of-sample validation."
            )
        elif score >= 50:  # noqa: PLR2004
            rec_action = (
                "Perform parameter sensitivity checks and adjust sizing "
                "down before promotion."
            )
        else:
            rec_action = (
                "Reject. Reject promotion. Review strategy entries/exits/rules."
            )

        data = {
            "score": score,
            "strengths": strengths,
            "warnings": warnings,
            "recommended_action": rec_action,
            "is_binding_decision": False,
            "disclaimer": (
                "This report represents non-binding analytics evidence and "
                "decision context only. It does not certify live-readiness "
                "or execute orders."
            ),
        }

        return success_response(
            message="Strategy quality scorecard evaluation completed.",
            data=data,
            metadata=meta,
        )
    except Exception as e:  # noqa: BLE001
        return response_from_exception(exception=e, metadata=meta)

"""decision_scorecard.py - Convert analytics reports into strategy quality decisions and warnings.

This module analyzes a comprehensive backtest report and assigns a quality score,
identifies strengths and warnings, and provides a final PASS/REJECT decision.

Classes:
    None.

Functions:
    evaluate_strategy_quality: Evaluate strategy quality based on the unified report payload (AI Tool).
    _evaluate_strategy_quality_impl: Core logic for strategy quality evaluation.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.analytics.common import analytics_tool_result
from app.services.utils.logger import logger

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "analytics"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
CREATES = False
READS = True
UPDATES = False
DELETES = False
TRADES = False


def _section_value(section: Mapping[str, Any], key: str, default: Any = 0) -> Any:
    """Read a scorecard metric from an analytics section."""
    return section.get(key, default)


def _evaluate_strategy_quality_core(report: dict[str, Any]) -> dict[str, Any]:
    """Core logic for evaluating strategy quality based on the unified report payload.

    Args:
        report: A dictionary containing backtest analytics (summary, metrics, ratios, etc.).

    Returns:
        A dictionary with decision, score, strengths, warnings, and recommended action.
    """
    # Extract categories safely
    summary = report.get("summary", {}).get("all", {})
    metrics = report.get("metrics", {}).get("all", {})
    ratios = report.get("ratios", {}).get("all", {})
    drawdowns = report.get("drawdowns", {}).get("all", {})
    validation = report.get("validation", {}).get("all", {})

    score = 0.0
    strengths = []
    warnings = []
    fail_reasons = []

    # 1. Profitability & Growth (Max 30 points)
    net_profit = summary.get("return_usd", 0)
    cagr = summary.get("cagr", 0)
    profit_factor = _section_value(ratios, "profit_factor", 0)

    if net_profit > 0:
        score += 5
        if cagr > 15:
            score += 10
            strengths.append(f"Strong growth (CAGR: {cagr:.1f}%)")
        elif cagr > 5:
            score += 5

        if profit_factor > 2.0:
            score += 15
            strengths.append(f"Excellent profit factor ({profit_factor:.2f})")
        elif profit_factor > 1.5:
            score += 10
            strengths.append(f"Good profit factor ({profit_factor:.2f})")
        elif profit_factor > 1.2:
            score += 5
    else:
        fail_reasons.append("Strategy is not profitable in the testing period.")

    # 2. Risk & Robustness (Max 30 points)
    max_dd_pct = _section_value(drawdowns, "max_drawdown_pct", 100)
    sharpe = _section_value(ratios, "sharpe_ratio", 0)
    dsr_p = validation.get("dsr_p_value", 1.0)

    if max_dd_pct < 10:
        score += 15
        strengths.append("Very low drawdown exposure")
    elif max_dd_pct < 20:
        score += 10
    elif max_dd_pct > 35:
        warnings.append(f"High maximum drawdown ({max_dd_pct:.1f}%)")
        score -= 5

    if sharpe > 2.0:
        score += 15
        strengths.append("Superior risk-adjusted returns (Sharpe > 2)")
    elif sharpe > 1.0:
        score += 10
        strengths.append("Solid risk-adjusted returns (Sharpe > 1)")

    if dsr_p < 0.05:
        score += 5
        strengths.append("Statistically significant edge (DSR P-Value < 0.05)")
    elif dsr_p > 0.5:
        warnings.append("High probability of backtest overfitting (High DSR P-Value)")

    # 3. Execution & Efficiency (Max 20 points)
    win_rate = _section_value(metrics, "win_rate", 0)
    expectancy_r = _section_value(ratios, "expectancy_r", 0)
    num_trades = _section_value(metrics, "total_trades", 0)

    if num_trades < 30:
        warnings.append(
            f"Small sample size ({num_trades} trades). Results may not be stable."
        )
        score -= 10
    elif num_trades > 100:
        score += 5

    if expectancy_r > 0.2:
        score += 10
        strengths.append(f"High expectancy per trade ({expectancy_r:.2f} R)")
    elif expectancy_r > 0.1:
        score += 5

    if win_rate > 60:
        score += 5
        strengths.append(f"High win rate ({win_rate:.1f}%)")
    elif win_rate < 35:
        warnings.append(
            f"Low win rate ({win_rate:.1f}%). Requires high psychological discipline."
        )

    # 4. Final Decision
    final_score = max(0.0, min(100.0, score))

    decision = "REJECT"
    recommended_action = "reject"

    if final_score >= 75 and not fail_reasons:
        decision = "PASS"
        recommended_action = "promote_to_oos"
    elif final_score >= 50 and not fail_reasons:
        decision = "WATCHLIST"
        recommended_action = "run_more_tests"

    if fail_reasons:
        decision = "REJECT"
        recommended_action = "reject"

    return {
        "decision": decision,
        "score": round(final_score, 1),
        "strengths": strengths,
        "warnings": warnings,
        "fail_reasons": fail_reasons,
        "recommended_action": recommended_action,
    }


def _evaluate_strategy_quality_impl(report: dict[str, Any]) -> dict[str, Any]:
    """Evaluate strategy quality based on the unified report payload (AI Tool).

    Args:
        report: A dictionary containing the full backtest report.

    Returns:
        Standardized tool result with strategy evaluation data.
    """
    try:
        # Input Validation
        if not isinstance(report, dict):
            return {
                "status": "error",
                "message": "Invalid report format. Expected a dictionary.",
            }

        # Core Execution
        evaluation = _evaluate_strategy_quality_core(report)

        # Structured Return
        logger.info("Executed evaluate_strategy_quality tool successfully.")
        return analytics_tool_result("evaluate_strategy_quality", data=evaluation)

    except Exception as e:
        logger.error(f"Error in evaluate_strategy_quality: {e!s}")
        return {"status": "error", "message": str(e)}


__evaluate_strategy_quality_impl_impl = _evaluate_strategy_quality_core


def evaluate_strategy_quality(report: dict[str, Any]) -> dict[str, Any]:
    """AI Tool wrapper for _evaluate_strategy_quality_impl."""
    try:
        import pandas as pd
        from app.services.utils.logger import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_report = report
        if "report" in ["trades", "open_trades"] and isinstance(
            arg_report, (list, dict)
        ):
            arg_report = pd.DataFrame(arg_report)
        elif "report" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_report, list):
            arg_report = pd.Series(arg_report)
        kwargs["report"] = arg_report

        res = _evaluate_strategy_quality_impl(**kwargs)
        logger.info("Executed evaluate_strategy_quality tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "evaluate_strategy_quality",
            data={"evaluate_strategy_quality": data_payload},
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}

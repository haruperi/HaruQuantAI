"""Portfolio cost governance service.

Purpose:
    Portfolio cost governance service.

Classes:
    CostService: Public class defined by this module.

Functions:
    None.

Notes:
    External-facing exports are collected in app/services/portfolio/__init__.py;
    private underscore helpers remain implementation details.
"""

from typing import Any

from app.agentic.agents._shared.persistence import utc_stamp, write_json_artifact
from app.agentic.agents.portfolio.shared.contracts import CostReport


class CostService:
    """Public class for cost_service.CostService."""

    protected_decision_types = {
        "risk_governor",
        "order_router",
        "execution",
        "risk_approval",
    }

    def report(
        self, *, period: str, usage: list[dict[str, Any]], budget: float
    ) -> CostReport:
        """Public function for cost_service.report."""
        total = sum(float(item.get("cost", 0.0)) for item in usage)
        (
            by_agent,
            by_provider,
            by_model,
            by_task,
            by_workflow,
            by_strategy,
            routing,
            anomalies,
        ) = {}, {}, {}, {}, {}, {}, {}, []
        prompt_tokens = completion_tokens = 0
        failed_call_cost = backtest_compute_cost = 0.0
        for item in usage:
            by_agent[item.get("agent", "unknown")] = by_agent.get(
                item.get("agent", "unknown"), 0.0
            ) + float(item.get("cost", 0.0))
            by_provider[item.get("model_provider", "unknown")] = by_provider.get(
                item.get("model_provider", "unknown"), 0.0
            ) + float(item.get("cost", 0.0))
            by_model[item.get("model_name", "unknown")] = by_model.get(
                item.get("model_name", "unknown"), 0.0
            ) + float(item.get("cost", 0.0))
            by_task[item.get("task_id", item.get("task_type", "unknown"))] = (
                by_task.get(item.get("task_id", item.get("task_type", "unknown")), 0.0)
                + float(item.get("cost", 0.0))
            )
            by_workflow[item.get("workflow_id", "unknown")] = by_workflow.get(
                item.get("workflow_id", "unknown"), 0.0
            ) + float(item.get("cost", 0.0))
            by_strategy[item.get("strategy_id", "unknown")] = by_strategy.get(
                item.get("strategy_id", "unknown"), 0.0
            ) + float(item.get("cost", 0.0))
            routing[item.get("task_type", "unknown")] = item.get(
                "model_name", "unknown"
            )
            prompt_tokens += int(item.get("prompt_tokens", 0))
            completion_tokens += int(item.get("completion_tokens", 0))
            if item.get("failed"):
                failed_call_cost += float(item.get("cost", 0.0))
            if item.get("task_type") == "backtest_compute":
                backtest_compute_cost += float(item.get("cost", 0.0))
            if item.get("task_type") in self.protected_decision_types and item.get(
                "model_name"
            ) not in {None, "deterministic", "none"}:
                anomalies.append(
                    f"protected_decision_routed_to_llm:{item.get('task_type')}"
                )
        if total > budget:
            anomalies.append("budget_exceeded")
        report = CostReport(
            period=period,
            total_cost=total,
            budget=budget,
            by_agent=by_agent,
            by_model_provider=by_provider,
            by_model_name=by_model,
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
            cost_by_task=by_task,
            cost_by_workflow=by_workflow,
            cost_by_strategy=by_strategy,
            failed_call_cost=failed_call_cost,
            backtest_compute_cost=backtest_compute_cost,
            model_routing=routing,
            high_cost_workflow_approval_required=total > budget,
            risk_controls_protected=not any(
                item.startswith("protected_decision_routed_to_llm")
                for item in anomalies
            ),
            anomalies=anomalies,
            recommendations=[
                "use_cache_for_repeated_summaries",
                "batch_low_risk_reports",
            ],
        )
        report.audit_ref = write_json_artifact(
            "app/agentic/audit/reports/portfolio",
            f"cost-{period}-{utc_stamp()}.json",
            report.model_dump() if hasattr(report, "model_dump") else report.dict(),
        )
        return report

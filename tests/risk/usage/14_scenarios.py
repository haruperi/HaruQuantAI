"""Executable Risk scenarios usage example.

Demonstrates running risk scenario analysis against baseline snapshot.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk.config import RiskConfig
from app.services.risk.contracts import PortfolioRiskSnapshot, ScenarioDefinition
from app.services.risk.scenarios import run_risk_scenario_analysis

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _snapshot() -> PortfolioRiskSnapshot:
    """Build immutable snapshot input."""
    return PortfolioRiskSnapshot(
        snapshot_id="snapshot-1",
        account_id="account-1",
        base_currency="USD",
        equity=Decimal(10000),
        daily_loss=Decimal(0),
        total_loss=Decimal(0),
        gross_exposure=Decimal(0),
        net_exposure=Decimal(0),
        drawdown=Decimal(0),
        margin_utilization=Decimal(0),
        effective_leverage=Decimal(0),
        historical_var=None,
        historical_cvar=None,
        volatility=None,
        portfolio_correlation=Decimal(0),
        exposure_by_dimension={},
        contributions={},
        limit_statuses={},
        assumptions=(),
        coverage={"account": "complete"},
        gaps=(),
        regime=None,
        as_of=NOW,
        config_hash="a" * 64,
        evidence_refs={"account": "account-evidence-1"},
        request_id="request-1",
        workflow_id="workflow-1",
    )


def example_scenarios() -> None:
    """Demonstrate risk scenario stress testing."""
    print("=" * 80)
    print("Risk Example 10: Scenario Stress Testing")
    print("=" * 80)

    config = RiskConfig(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60},
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )

    scenarios = (
        ScenarioDefinition(
            scenario_id="equity-stress",
            shocks={"equity": Decimal("-0.10")},
            randomized=True,
            seed=42,
            assumptions=("declared ten-percent equity shock",),
        ),
    )

    results = run_risk_scenario_analysis(_snapshot(), scenarios, config, now=NOW)
    print(
        f"Scenario result count: {len(results)}, seed: {results[0].seed}, "
        f"approved: {results[0].approved}"
    )


def main() -> None:
    """Run Risk scenarios usage example."""
    example_scenarios()


if __name__ == "__main__":
    main()

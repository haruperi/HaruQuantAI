"""Executable Risk scenarios usage example.

Demonstrates running risk scenario analysis against baseline snapshot.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import (
    create_portfolio_risk_snapshot,
    create_risk_config,
    create_scenario_definition,
    run_risk_scenario_analysis,
)

from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _snapshot() -> create_portfolio_risk_snapshot:
    """Build immutable snapshot input."""
    return create_portfolio_risk_snapshot(
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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def fr_risk_045() -> None:
    """FR-RISK-045: Deterministically apply bounded scenarios to immutable
    snapshot evidence, return baseline/projected risk differences, preserve
    explicit seed, and mark every result advisory."""
    _header(
        "FR-RISK-045: Deterministically apply bounded scenarios to immutable snapshot evidence, return baseline/projected risk differences, preserve explicit seed, and mark every result advisory."
    )
    print("Risk Example 10: Scenario Stress Testing")

    config = create_risk_config(
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
        create_scenario_definition(
            scenario_id="equity-stress",
            shocks={"equity": Decimal("-0.10")},
            randomized=True,
            seed=42,
            assumptions=("declared ten-percent equity shock",),
        ),
    )

    results = unwrap_risk_response(
        run_risk_scenario_analysis(_snapshot(), scenarios, config, now=NOW),
        operation="run_risk_scenario_analysis",
    )
    print("Complete bounded advisory scenario results:")
    for result in results:
        print(result.model_dump(warnings=False, mode="json"))


def main() -> None:
    """Run the FR-RISK-045 scenario demonstration."""
    fr_risk_045()


if __name__ == "__main__":
    main()

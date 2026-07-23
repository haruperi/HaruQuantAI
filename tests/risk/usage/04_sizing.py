"""Executable Risk sizing usage example.

Demonstrates calculating position sizing based on fixed monetary risk.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk.config import RiskConfig
from app.services.risk.contracts import PortfolioRiskSnapshot, PositionSizingRequest
from app.services.risk.sizing import calculate_position_size

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


def _config() -> RiskConfig:
    """Build risk policy config."""
    return RiskConfig(
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


def example_sizing() -> None:
    """Demonstrate calculating position size."""
    print("=" * 80)
    print("Risk Example 8: Position Sizing Calculation")
    print("=" * 80)

    snapshot = _snapshot()
    request = PositionSizingRequest(
        method="fixed_risk",
        requested_size=None,
        fixed_lot=None,
        risk_amount=Decimal(1000),
        risk_fraction=None,
        stop_distance=Decimal(100),
        unit_value=Decimal(10),
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"snapshot": snapshot.snapshot_id},
        request_id="request-1",
    )
    result = calculate_position_size(request, snapshot, _config())
    print(
        f"Calculated normalized size: {result.normalized_size}, "
        f"approved: {result.approved}"
    )


def main() -> None:
    """Run Risk sizing usage example."""
    example_sizing()


if __name__ == "__main__":
    main()

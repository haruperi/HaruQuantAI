"""Executable Risk reporting usage example.

Demonstrates generating deterministic Markdown risk reports.
"""

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.risk import PortfolioRiskSnapshot, RiskConfig, generate_risk_report

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )


def fr_risk_046() -> None:
    """FR-RISK-046: Render evidence, calculations, assumptions, warnings,
    decision, and recommendations separately; show primary failure first; never
    claim live approval without valid decision/token evidence. Active config and
    explicit time are required so format/timeout policy and generated time are
    deterministic."""
    _header(
        "FR-RISK-046: Render evidence, calculations, assumptions, warnings, decision, and recommendations separately; show primary failure first; never claim live approval without valid decision/token evidence. Active config and explicit time are required so format/timeout policy and generated time are deterministic."
    )
    print("Risk Example 11: Risk Reporting")

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

    report = generate_risk_report(_snapshot(), "markdown", config, now=NOW)
    print(
        f"Generated report format: {report.format}, "
        f"approval_claimed: {report.approval_claimed}"
    )


def main() -> None:
    """Run the FR-RISK-046 reporting demonstration."""
    fr_risk_046()


if __name__ == "__main__":
    main()

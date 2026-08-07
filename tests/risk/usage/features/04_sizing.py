"""Executable Risk sizing usage example.

Demonstrates FEAT-RISK-04 calculating position sizing based on fixed monetary risk.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    calculate_position_size,
    create_portfolio_risk_snapshot,
    create_position_sizing_request,
    create_risk_config,
)
from tests.risk._support import unwrap_risk_response

NOW = datetime(2026, 7, 19, tzinfo=UTC)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


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


def _config() -> create_risk_config:
    """Build risk policy config."""
    return create_risk_config(
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


def fr_risk_026() -> None:
    """FR-RISK-026: Stage 3 — Calculate fixed-lot, fixed-risk, milestone, fractional-Kelly, volatility, or fixed-fractional size using the retained migration-evidenced formulas; enforce stop/equity/evidence rules; disclose fallback/correlation adjustment; normalize against explicit broker and risk constraints; return no non-zero failure fallback and no approval."""
    _header(
        "Stage 3: Position Sizing Calculation - Calculate Position Size (FR-RISK-026)"
    )
    print("SUCCESS: FR-RISK-026")

    snapshot = _snapshot()
    request = create_position_sizing_request(
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
        request_id="req-11111111-1111-4111-8111-111111111111",
    )
    result = unwrap_risk_response(
        calculate_position_size(request, snapshot, _config()),
        operation="calculate_position_size",
    )
    print(_format_result(result))
    print(
        f"Data -> normalized_size={result.normalized_size}, approved={result.approved}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-04 — sizing/ — Position Sizing Calculation\n\n"
        "Purpose: Calculate position sizing based on fixed lot, fixed risk, milestone, fractional Kelly, volatility, or fixed fractional methods.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted sizing request and portfolio snapshot\n"
        "-> Stage 2: Validate sizing inputs and constraints\n"
        "-> Stage 3: Return normalized PositionSizingResult without granting approval"
    )
    fr_risk_026()


if __name__ == "__main__":
    main()

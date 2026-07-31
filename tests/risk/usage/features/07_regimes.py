"""Executable Risk regimes usage example.

Demonstrates FEAT-RISK-07 risk regime assessment under enabled regime policy.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_market_context_evidence
from app.services.risk import (
    assess_risk_regime,
    create_portfolio_risk_snapshot,
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


def _market() -> build_market_context_evidence:
    """Build market context evidence."""
    return build_market_context_evidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state="clear",
        spread=Decimal(1),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=NOW,
        expires_at=NOW + timedelta(seconds=60),
        provenance={"source": "data"},
        missing_fields=(),
        request_id="req-cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    )


def fr_risk_031() -> None:
    """FR-RISK-031: Stage 3 — Classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes; record deterministic transitions/evidence; return only equal-or-stricter modifiers; fail closed on required missing/unknown live evidence."""
    _header("Stage 3: Regime Classification - Assess Risk Regime (FR-RISK-031)")

    config = create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="block",
        evidence_max_age_seconds={"portfolio": 60, "market": 30},
        regime_assessment_enabled=True,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )

    assessment = unwrap_risk_response(
        assess_risk_regime(_snapshot(), _market(), config, now=NOW),
        operation="assess_risk_regime",
    )
    print(_format_result(assessment))
    print(
        f"Data -> assessed_at='{assessment.assessed_at}', missing_fields={len(assessment.missing_fields)}"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-07 — regimes/ — Risk Regime Assessment\n\n"
        "Purpose: Classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes with equal-or-stricter modifiers.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted portfolio snapshot and market context evidence\n"
        "-> Stage 2: Validate regime policy and freshness\n"
        "-> Stage 3: Return deterministic RegimeAssessment output"
    )
    fr_risk_031()


if __name__ == "__main__":
    main()

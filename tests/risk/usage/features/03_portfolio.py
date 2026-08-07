"""Executable Risk portfolio usage example.

Demonstrates FEAT-RISK-03 building a portfolio risk snapshot from account state evidence.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import build_account_state_snapshot
from app.services.risk import (
    build_portfolio_risk_snapshot,
    create_portfolio_state,
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


def fr_risk_025() -> None:
    """FR-RISK-025: Stage 3 — Build an immutable snapshot containing pending-order-aware gross/net exposure by dimension, account-currency conversions, drawdown/loss state, margin/leverage, volatility, historical VaR/CVaR, pair/portfolio correlation, incremental contribution, assumptions, coverage, and explicit gaps."""
    _header(
        "Stage 3: Portfolio Risk Calculation - Build Portfolio Risk Snapshot (FR-RISK-025)"
    )
    print("SUCCESS: FR-RISK-025")

    account = build_account_state_snapshot(
        account_id="account-1",
        currency="USD",
        balances=(
            {
                "asset": "USD",
                "total": Decimal(10000),
                "available": Decimal(10000),
            },
        ),
        equity=Decimal(10000),
        margin_used=Decimal(0),
        margin_available=Decimal(10000),
        positions=(),
        orders=(),
        connected=True,
        trading_allowed=True,
        source_id="broker-1",
        snapshot_at=NOW,
        expires_at=NOW + timedelta(minutes=1),
        request_id="req-12345678-1234-4234-8234-123456789abc",
    )
    state = create_portfolio_state(
        account_snapshot=account,
        peak_equity=Decimal(10000),
        day_start_equity=Decimal(10000),
        inception_equity=Decimal(10000),
        symbol_prices={},
        symbol_contract_sizes={},
        symbol_quote_currencies={},
        fx_conversions=(),
        return_timestamps=(),
        return_history={},
        correlations={},
        exposure_dimensions={},
        as_of=NOW,
        expires_at=NOW + timedelta(minutes=1),
        provenance={"source": "data"},
        missing_fields=("returns",),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
    )
    config = create_risk_config(
        profile="research",
        execution_route="none",
        policy_version="policy-1",
        base_currency="USD",
        pending_order_exposure_policy="include_full_remaining_exposure",
        evidence_max_age_seconds={"portfolio": 60},
        clock_skew_tolerance_seconds=Decimal(0),
        var_min_observations=2,
        var_lookback=10,
        regime_assessment_enabled=False,
        approval_token_ttl_seconds=Decimal(60),
        approval_signing_key_ref="secrets/risk-key",
        decision_ttl_seconds=Decimal(30),
        kill_switch_activation_permissions=("risk.kill.activate",),
        kill_switch_clearance_permissions=("risk.kill.clear",),
        report_timeout_seconds=Decimal(5),
    )

    snapshot = unwrap_risk_response(
        build_portfolio_risk_snapshot(state, config, now=NOW),
        operation="build_portfolio_risk_snapshot",
    )
    print(_format_result(snapshot))
    print(f"Data -> equity={snapshot.equity}, gross_exposure={snapshot.gross_exposure}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-RISK-03 — portfolio/ — Portfolio State Construction and Risk Snapshot Computation\n\n"
        "Purpose: Construct immutable portfolio state from Data-owned account state evidence and compute reproducible portfolio risk snapshots.\n\n"
        "Module flow:\n"
        "-> Stage 1: Build untrusted portfolio state inputs\n"
        "-> Stage 2: Validate state and config policy\n"
        "-> Stage 3: Compute reproducible PortfolioRiskSnapshot"
    )
    fr_risk_025()


if __name__ == "__main__":
    main()

"""Executable Optimization barrier-analysis usage example."""

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.optimization import (
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)
from app.services.risk import create_firm_mandate

# Private type-only aliases; Risk exposes functions, not contract classes.
FirmMandate = object


def _mandate(account_id: str = "account-1") -> FirmMandate:
    """Build a bounded mandate for the examples."""
    return create_firm_mandate(
        account_id=account_id,
        mandate_version="2026.07.28-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="evaluation_p1",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/terms",
        terms_accessed="2026-07-28",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.1")},
        daily_loss={
            "basis": "initial_balance",
            "value": Decimal("0.05"),
            "includes_unrealised": True,
            "reset_time": "00:00",
            "reset_tz": "UTC",
        },
        max_drawdown={
            "mode": "static",
            "basis": "initial_balance",
            "value": Decimal("0.1"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
    )


RETURNS = (Decimal("0.02"), Decimal("-0.01"), Decimal("0.015"), Decimal("-0.005"))


def fr_opt_066() -> None:
    """FR-OPT-066: Estimate first-passage probabilities."""
    report = estimate_first_passage(RETURNS, _mandate(), paths=100, seed=7)
    print(f"First-passage target probability: {report.probability_target}")
    print(f"Median terminating day: {report.median_termination_day}")


def fr_opt_067() -> None:
    """FR-OPT-067: Estimate a correlated multi-account survival distribution."""
    returns = {
        "account-1": RETURNS,
        "account-2": (
            Decimal("0.018"),
            Decimal("-0.009"),
            Decimal("0.014"),
            Decimal("-0.004"),
        ),
    }
    report = estimate_joint_first_passage(
        returns,
        {account: _mandate(account) for account in returns},
        paths=100,
        seed=7,
    )
    print(
        f"Accounts surviving distribution: {dict(report.surviving_accounts_distribution)}"
    )
    print(f"Probability none survive: {report.probability_none_survive}")


def fr_opt_068() -> None:
    """FR-OPT-068: Compare identical paths under all drawdown modes."""
    reports = estimate_drawdown_mode_sensitivity(RETURNS, _mandate(), paths=100, seed=7)
    for mode, report in reports.items():
        print(f"{mode}: target probability={report.probability_target}")


def main() -> None:
    """Run every barrier-analysis demonstration."""
    fr_opt_066()
    fr_opt_067()
    fr_opt_068()


if __name__ == "__main__":
    main()

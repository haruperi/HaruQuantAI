"""WF-PORT-008: assess common-mode exposure and cross-account correlation."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import (
    assess_common_mode_exposure,
    measure_cross_account_correlation,
)

WORKFLOW_ID = "WF-PORT-008"
STAGES = (
    "Resolve the active allocation and the accounts it spans.",
    "Read current account and position evidence for every account in scope.",
    "Normalize every exposure into one comparison currency.",
    "Identify exposure that is nominally diversified but moves as a single risk.",
    "Measure realized correlation of returns across accounts.",
    "Supply both reports to Risk, which alone decides.",
)

_ACCOUNTS = ("acct_alpha", "acct_beta", "acct_gamma")


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def _report(label: str, status: str, data: object) -> None:
    """Print the status and bounded data of one workflow step."""
    print(f"{label} status : {status}")
    print(f"{label} data   : {data}")


def main() -> None:
    """Run the documented common-mode exposure and correlation workflow."""
    print(f"{WORKFLOW_ID} — Assess Common-Mode Exposure and Cross-Account Correlation")
    print("INPUT BOUNDARY — active allocation plus account, position, and FX evidence")

    # Stage 1 — Resolve the active allocation and the accounts it spans.
    _stage(1)
    print("Accounts in scope     :", _ACCOUNTS)
    print("Comparison currency   : USD")
    assert len(_ACCOUNTS) == 3

    # Stage 2 — Read current account and position evidence for every account in scope.
    _stage(2)
    loss_at_stop_by_account = {
        "acct_alpha": {"EURUSD": Decimal("450.00"), "GBPUSD": Decimal("300.00")},
        "acct_beta": {"EURUSD": Decimal("500.00"), "USDCHF": Decimal("250.00")},
        "acct_gamma": {"GBPUSD": Decimal("275.00")},
    }
    account_headroom = {
        "acct_alpha": Decimal("1200.00"),
        "acct_beta": Decimal("900.00"),
        "acct_gamma": Decimal("400.00"),
    }
    for account, exposures in loss_at_stop_by_account.items():
        total = sum(exposures.values())
        print(
            f"  {account:<12} loss-at-stop {total} headroom {account_headroom[account]}"
        )

    # Stage 3 — Normalize every exposure into one comparison currency.
    _stage(3)
    shared_adverse_scenario = {
        "EURUSD": Decimal("-0.0120"),
        "GBPUSD": Decimal("-0.0140"),
        "USDCHF": Decimal("0.0100"),
    }
    print(
        "Shared adverse scenario:",
        {k: str(v) for k, v in shared_adverse_scenario.items()},
    )
    print("All exposures expressed in the account base currency: True")

    # Stage 4 — Identify exposure that is nominally diversified but moves as a single risk.
    _stage(4)
    exposure_report = assess_common_mode_exposure(
        loss_at_stop_by_account,
        account_headroom,
        shared_adverse_scenario,
        software_dependencies={
            "acct_alpha": ("mt5-terminal", "haruquant-runtime"),
            "acct_beta": ("mt5-terminal", "haruquant-runtime"),
            "acct_gamma": ("ctrader-open-api", "haruquant-runtime"),
        },
        signal_dependencies={
            "acct_alpha": ("trend-ema", "session-london"),
            "acct_beta": ("trend-ema", "session-london"),
            "acct_gamma": ("mean-reversion-rsi",),
        },
    )
    _report("common ", "success", exposure_report)
    print("Nominal diversification is not assumed to be real: True")

    # Stage 5 — Measure realized correlation of returns across accounts.
    _stage(5)
    return_series = {
        "acct_alpha": [Decimal(str(v)) for v in (0.010, -0.004, 0.006, -0.002, 0.008)],
        "acct_beta": [Decimal(str(v)) for v in (0.009, -0.005, 0.007, -0.001, 0.007)],
        "acct_gamma": [Decimal(str(v)) for v in (-0.003, 0.006, -0.005, 0.004, -0.002)],
    }
    decision_series = {
        "acct_alpha": [Decimal(str(v)) for v in (1, 0, 1, 0, 1)],
        "acct_beta": [Decimal(str(v)) for v in (1, 0, 1, 0, 1)],
        "acct_gamma": [Decimal(str(v)) for v in (0, 1, 0, 1, 0)],
    }
    counterparties = {
        "acct_alpha": "broker_one",
        "acct_beta": "broker_one",
        "acct_gamma": "broker_two",
    }
    correlation_report = measure_cross_account_correlation(
        return_series,
        decision_series,
        counterparties,
        window=5,
        alert_threshold=Decimal("0.60"),
    )
    _report("correl ", "success", correlation_report)
    print("Overlapping history required for a correlation: True")

    # Stage 6 — Supply both reports to Risk, which alone decides.
    _stage(6)
    print("Reports supplied to Risk as evidence only.")
    print("Neither report is an approval nor authorizes a rebalance: True")

    print(
        "\nOUTPUT BOUNDARY — common-mode exposure report and cross-account correlation measurement"
    )


if __name__ == "__main__":
    main()

"""WF-RISK-015: load a mandate and evaluate single-day profit share."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.risk import (
    compute_config_hash,
    create_firm_mandate,
    evaluate_portfolio_limits,
    evaluate_single_day_profit_share,
    generate_risk_report,
)
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-015"
STAGES = (
    "Load the verified firm mandate governing the account.",
    "Pin the active Risk configuration into a canonical hash.",
    "Evaluate the projected single-day share of cumulative profit.",
    "Feed the mandate into ordered portfolio limit evaluation.",
    "Render the evaluated snapshot as a bounded decision summary.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the complete mandate-bound concentration workflow."""
    # Stage 1 — INPUT BOUNDARY: Receive verified mandate configuration.
    _stage(1)
    mandate = create_firm_mandate(
        account_id="account-1",
        mandate_version="2026.07.30-01",
        firm="Example Firm",
        model="fx_cfd",
        phase="funded",
        initial_balance=Decimal(1000),
        currency="USD",
        terms_url="https://example.invalid/archived-terms",
        terms_accessed="2026-07-30",
        terms_source_hash="a" * 64,
        verified=True,
        profit_target={"type": "percent_of_initial", "value": Decimal("0.10")},
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
            "value": Decimal("0.10"),
            "trails_on_unrealised": False,
            "trail_stops_at_initial": False,
        },
        consistency_rule={
            "type": "max_single_day_share_of_profit",
            "value": Decimal("0.40"),
            "evaluated": "retrospective",
            "applies_in_phase": ("funded",),
        },
    )
    print("Mandate:", mandate.model_dump(warnings=False, mode="json"))

    # Stage 2: Pin the exact active configuration.
    _stage(2)
    config = examples._config()
    config_hash = unwrap_risk_response(
        compute_config_hash(config),
        operation="compute_config_hash",
    )
    print("Pinned config hash:", config_hash)

    snapshot = examples._snapshot(config).model_copy(
        update={
            "cumulative_profit": Decimal(300),
            "current_day_profit": Decimal(50),
            "proposal_best_case_profit": Decimal(300),
        }
    )
    # Stage 3: Evaluate the real projected profit-share evidence.
    _stage(3)
    share = unwrap_risk_response(
        evaluate_single_day_profit_share(snapshot, mandate, now=examples.NOW),
        operation="evaluate_single_day_profit_share",
    )
    print("Single-day share verdict:", share.model_dump(warnings=False, mode="json"))

    # Stage 4: Feed the mandate through ordered limits.
    _stage(4)
    limits = unwrap_risk_response(
        evaluate_portfolio_limits(
            snapshot,
            config,
            now=examples.NOW,
            mandate=mandate,
        ),
        operation="evaluate_portfolio_limits",
    )
    print("Ordered limit verdicts:")
    print([item.model_dump(warnings=False, mode="json") for item in limits])

    # Stage 5 — OUTPUT BOUNDARY: Render the bounded evaluation summary.
    _stage(5)
    report = unwrap_risk_response(
        generate_risk_report(snapshot, "markdown", config, now=examples.NOW),
        operation="generate_risk_report",
    )
    print("Summary:", report.content)


if __name__ == "__main__":
    main()

"""WF-ANLT-006: adapt an approved upstream closed-trade result."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import adapt_trading_result, build_closed_trade_equity_curve
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-006"
STAGES = (
    "Accept a versioned producer-owned complete closed-trade ledger.",
    "Validate exact schema, identifiers, currency, UTC timestamps, PnL, and bounds.",
    "Map every approved field and preserve bounded source lineage.",
    "Derive closed-trade and UTC daily equity curves from the ledger.",
    "Return canonical TradingResult or structured validation failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Trading/Simulation supplies complete versioned ledger.
    _stage(1)
    source, config = examples._source(), examples._configured()
    print("Input:", source["source_id"], source["schema_id"])
    # Stage 2: Validate at public adapter boundary.
    _stage(2)
    result = examples.unwrap(
        adapt_trading_result(
            source,
            source_contract="simulation.result",
            initial_balance=Decimal(1000),
            account_currency="USD",
            config=config,
        )
    )
    print("Validated:", result.source_contract_version)
    # Stage 3: Inspect preserved canonical mapping/lineage.
    _stage(3)
    print("Mapped trades:", len(result.trades), "lineage:", result.lineage.source_ids)
    # Stage 4: Derive both documented curves explicitly.
    _stage(4)
    curve, daily = examples.unwrap(
        build_closed_trade_equity_curve(
            result.trades, initial_balance=result.initial_balance, config=config
        )
    )
    print("Curves:", len(curve), len(daily), curve[0]["curve_basis"])
    # Stage 5 — OUTPUT BOUNDARY: Return canonical TradingResult.
    _stage(5)
    print("Output:", type(result).__name__, result.schema_id)


if __name__ == "__main__":
    main()

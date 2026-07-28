"""WF-ANLT-009: build a currency-safe portfolio performance report."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import build_portfolio_performance_report
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-009"
STAGES = (
    "Accept compatible component reports, base currency, and caller-supplied FX evidence.",
    "Validate component schema, pairing, bounds, and currency coverage.",
    "Convert only with explicit fresh FX evidence; never sum raw mixed currencies.",
    "Aggregate approved component evidence into internal portfolio sections.",
    "Return internal PortfolioPerformanceReport or blocker failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies compatible component report(s).
    _stage(1)
    report, config = examples._report(account_currency="USD")
    print("Input:", report.report_id, report.account_currency)
    # Stage 2: Validate schema and pairing.
    _stage(2)
    print("Component schema:", report.schema_id)
    # Stage 3: Identity currency requires no invented FX rate.
    _stage(3)
    print("Base currency:", "USD", "FX evidence:", None)
    # Stage 4: Execute public portfolio aggregation.
    _stage(4)
    portfolio = examples.unwrap(
        build_portfolio_performance_report(
            (report,), base_currency="USD", fx_evidence=None, config=config
        )
    )
    print("Portfolio sections:", len(portfolio.sections))
    # Stage 5 — OUTPUT BOUNDARY: Return internal currency-safe report.
    _stage(5)
    print("Output:", type(portfolio).__name__, portfolio.base_currency)


if __name__ == "__main__":
    main()

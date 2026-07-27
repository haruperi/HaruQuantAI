"""WF-ANLT-008: compute reproducibility hashes and serialize a report."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import (
    adapt_trading_result,
    compute_reproducibility_hashes,
    serialize_report,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-008"
STAGES = (
    "Accept validated canonical result and PerformanceReport.",
    "Canonicalize input, config, ledger, equity, benchmark, and report payloads.",
    "Compute SHA-256-or-stronger reproducibility hashes.",
    "Serialize canonical JSON or approved minimal human-readable output.",
    "Return hashes and serialized value without writing files.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies validated result/report.
    _stage(1)
    report, config = examples._report()
    result = adapt_trading_result(
        examples._source(),
        source_contract="simulation.result",
        initial_balance=Decimal(1000),
        account_currency="USD",
        config=config,
    )
    print("Input:", result.source_id, report.report_id)
    # Stage 2: Canonical JSON policy is applied internally.
    _stage(2)
    print("Canonical schema:", report.schema_id)
    # Stage 3: Compute complete reproducibility hashes.
    _stage(3)
    hashes = compute_reproducibility_hashes(result, report)
    print("Report hash:", hashes.report_hash)
    # Stage 4: Serialize without filesystem writes.
    _stage(4)
    serialized = serialize_report(report, format_name="json", config=config)
    print("Serialized bytes:", len(serialized))
    # Stage 5 — OUTPUT BOUNDARY: Return hashes and in-memory serialization.
    _stage(5)
    print("Output:", type(hashes).__name__, type(serialized).__name__)


if __name__ == "__main__":
    main()

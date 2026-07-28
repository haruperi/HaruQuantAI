"""WF-RES-011: run the complete selected Edge Lab profile."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import run_edge_lab_profile
from tests.research._support import make_edge_lab_config
from tests.research.usage.workflows._support import live_market_dataset

WORKFLOW_ID = "WF-RES-011"
STAGES = (
    "Receive explicit hypothesis, EdgeLabConfig, and genuine MT5 MarketDataset v1.",
    "Validate selected stages and execute them in canonical dependency order.",
    "Assemble bounded provenance, quality, statistics, warnings, and stage evidence.",
    "Return advisory ResearchReport v1 to the external orchestrator.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented complete Edge Lab workflow."""
    print(f"{WORKFLOW_ID} — Run Complete Edge Lab Profile")
    print("INPUT BOUNDARY — hypothesis, EdgeLabConfig, genuine MT5 MarketDataset v1")
    with tempfile.TemporaryDirectory(prefix="wf-res-011-") as directory:
        # Stage 1 — Receive explicit hypothesis, EdgeLabConfig, and genuine MT5 MarketDataset v1.
        _stage(1)
        dataset = live_market_dataset()
        config = make_edge_lab_config(
            Path(directory),
            selected_stages=("data", "metrics"),
        )

        # Stage 2 — Validate selected stages and execute them in canonical dependency order.
        _stage(2)
        response = run_edge_lab_profile(
            dataset,
            hypothesis="Bounded MT5 returns contain measurable structure.",
            config=config,
        )
        assert response.status == "success"
        report = response.data

        # Stage 3 — Assemble bounded provenance, quality, statistics, warnings, and stage evidence.
        _stage(3)
        assert report is not None
        assert report.evidence["selected_stages"] == ["data", "metrics"]
        print(
            "Provenance entries:",
            len(report.source_references) + len(report.dependency_versions),
        )

        # Stage 4 — Return advisory ResearchReport v1 to the external orchestrator.
        _stage(4)
        print(
            "OUTPUT BOUNDARY — typed ResearchReport v1:",
            report.report_id,
            report.advisory_only,
        )


if __name__ == "__main__":
    main()

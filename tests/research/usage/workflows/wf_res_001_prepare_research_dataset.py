"""WF-RES-001: prepare genuine MT5 evidence for Research."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import CleaningConfig, EnrichmentConfig
from app.services.research.data import (
    clean_dataset,
    enrich_dataset,
    prepare_research_dataset,
    validate_dataset,
)
from tests.research.usage.workflows._support import (
    limits,
    live_market_dataset,
)

WORKFLOW_ID = "WF-RES-001"
STAGES = (
    "Validate the Data-owned MarketDataset and produce quality evidence.",
    "Clean a copy using only explicit approved actions.",
    "Enrich the cleaned copy with Research-owned fields.",
    "Prepare and return the versioned dataset, hashes, and report.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented dataset-preparation workflow."""
    print(f"{WORKFLOW_ID} — Prepare Research Dataset")
    print("INPUT BOUNDARY — genuine MT5 MarketDataset v1 from Data")
    dataset = live_market_dataset()
    cleaning = CleaningConfig("UTC", "error", "none", "keep_warn", "error")
    enrichment = EnrichmentConfig("EURUSD", True, True, False, True)

    # Stage 1 — Validate the Data-owned MarketDataset and produce quality evidence.
    _stage(1)
    validation = validate_dataset(dataset, limits=limits())

    # Stage 2 — Clean a copy using only explicit approved actions.
    _stage(2)
    cleaned, clean_report = clean_dataset(
        dataset,
        config=cleaning,
        report=validation,
        limits=limits(),
    )

    # Stage 3 — Enrich the cleaned copy with Research-owned fields.
    _stage(3)
    enriched, enrichment_report = enrich_dataset(
        cleaned,
        config=enrichment,
        report=clean_report,
    )

    # Stage 4 — Prepare and return the versioned dataset, hashes, and report.
    _stage(4)
    prepared = prepare_research_dataset(
        dataset,
        cleaning=cleaning,
        enrichment=enrichment,
        limits=limits(),
    )
    assert len(prepared.data) == len(enriched)
    print("Quality actions:", len(enrichment_report.cleaning_actions))
    print("OUTPUT BOUNDARY — typed PreparedDataset:", prepared.dataset_hash)


if __name__ == "__main__":
    main()

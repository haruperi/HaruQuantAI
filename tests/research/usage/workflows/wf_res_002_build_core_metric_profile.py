"""WF-RES-002: build the canonical seven-family metric profile."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import build_core_metric_profile
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-002"
STAGES = (
    "Receive the prepared genuine MT5 dataset.",
    "Resolve the immutable default metric registry.",
    "Compute the seven metric families with explicit units and warnings.",
    "Return the immutable CoreMetricProfile with provenance.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented core-metric workflow."""
    print(f"{WORKFLOW_ID} — Build Core Metric Profile")
    print("INPUT BOUNDARY — PreparedDataset derived from genuine MT5 evidence")

    # Stage 1 — Receive the prepared genuine MT5 dataset.
    _stage(1)
    prepared = prepared_dataset()

    # Stage 2 — Resolve the immutable default metric registry.
    _stage(2)
    from app.services.research import build_default_registry

    registry = build_default_registry()

    # Stage 3 — Compute the seven metric families with explicit units and warnings.
    _stage(3)
    profile = build_core_metric_profile(prepared, registry=registry, limits=limits())

    # Stage 4 — Return the immutable CoreMetricProfile with provenance.
    _stage(4)
    print("Metric families:", tuple(profile.metrics))
    print("OUTPUT BOUNDARY — typed CoreMetricProfile:", profile.dataset_hash)


if __name__ == "__main__":
    main()

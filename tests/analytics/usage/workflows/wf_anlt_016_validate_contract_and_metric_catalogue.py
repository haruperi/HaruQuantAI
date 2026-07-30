"""WF-ANLT-016: demonstrate real Analytics catalogue validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import (
    get_metric_definition_catalog,
    validate_contract_version,
    validate_metric_catalog,
)
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-016"
STAGES = (
    "Validate a registered source contract.",
    "Validate the actual metric catalogue.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"{'=' * 88}\nStage {number}/{len(STAGES)}\n{'=' * 88}")


def main() -> None:
    """Execute contract and catalogue validation with observable evidence."""
    # Stage 1: INPUT BOUNDARY -- registered source version.
    _stage(1)
    print(
        "Contract result:",
        examples.unwrap(validate_contract_version("simulation.result", "v1")),
    )
    # Stage 2: OUTPUT BOUNDARY -- validated registered catalogue.
    _stage(2)
    print("Metric keys:", tuple(get_metric_definition_catalog())[:8])
    print(
        "Catalogue validation:",
        examples.unwrap(validate_metric_catalog(get_metric_definition_catalog())),
    )


if __name__ == "__main__":
    main()

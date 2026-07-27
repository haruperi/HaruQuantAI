"""Execute every active Indicators workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_indi_001_core_batch_indicator_calculation.py",
    "wf_indi_002_decision_time_consumption.py",
    "wf_indi_003_warmup_coordination.py",
    "wf_indi_004_availability_aware_multi_timeframe_calculation.py",
    "wf_indi_005_static_registry_discovery_validation.py",
)


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    package = "tests.indicators.usage.workflows"
    for filename in WORKFLOWS:
        module = importlib.import_module(f"{package}.{filename[:-3]}")
        module.main()
    print(f"\nIndicators workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()

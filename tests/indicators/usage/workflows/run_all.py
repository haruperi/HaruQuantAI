"""Execute every active Indicators workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_indi_pri_core_batch_indicator_calculation.py",
    "wf_indi_sec_decision_time_consumption.py",
    "wf_indi_003_warmup_coordination.py",
    "wf_indi_ter_availability_aware_multi_timeframe_calculation.py",
    "wf_indi_005_static_registry_discovery_validation.py",
    "wf_indi_006_candlestick_pattern_detection.py",
    "wf_indi_007_volume_profile_distribution.py",
    "wf_indi_008_capability_matrix_introspection.py",
)


def _feature_header(title: str) -> None:
    """Print the feature banner and module flow."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    _feature_header(
        "Indicators Workflow Orchestrator\n\n"
        "Purpose: Execute workflow usage scripts in a fixed registry order.\n\n"
        "Module flow:\n"
        "-> load workflow module\n"
        "-> run workflow main() in order\n"
        "-> report aggregate completion"
    )
    print(f"Data -> planned_workflows={len(WORKFLOWS)}")
    print(f"Data -> workflow_ids={WORKFLOWS}")

    package = "tests.indicators.usage.workflows"
    for filename in WORKFLOWS:
        module = importlib.import_module(f"{package}.{filename[:-3]}")
        print(_format_result(module))
        module.main()

    print(f"\nIndicators workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()

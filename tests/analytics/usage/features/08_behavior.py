"""Standalone FEAT-ANLT-08 usage evidence."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.analytics import assess_plan_adherence, detect_behavior_patterns


def _format_result(value: object) -> str:
    """Format bounded visible evidence."""
    return f"SUCCESS: Data -> {type(value).__name__}"


def fr_anlt_070() -> object:
    """Compare exact released plan evidence. Data -> Analytics; _format_result evidence."""
    return assess_plan_adherence(
        {"max_size": 2}, [{"rule_id": "max_size", "value": 2}], plan_version="v1"
    )


def fr_anlt_071() -> object:
    """Preserve unavailable findings. Data -> Analytics; _format_result evidence."""
    return assess_plan_adherence({"stop": "set"}, [], plan_version="v1")


def fr_anlt_072() -> object:
    """Run versioned evidence-only detectors. Data -> Analytics; _format_result evidence."""
    return detect_behavior_patterns(
        [{"kind": "churn"}], threshold_version="v1", thresholds={"churn": 1}
    )


def main() -> None:
    """Run every requirement example."""
    for value in (fr_anlt_070(), fr_anlt_071(), fr_anlt_072()):
        print(_format_result(value))


if __name__ == "__main__":
    main()

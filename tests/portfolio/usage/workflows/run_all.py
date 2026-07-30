"""Execute every active Portfolio workflow usage program."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_port_001_validate_construction_evidence.py",
    "wf_port_pri_construct_allocation_candidate.py",
    "wf_port_003_coordinate_simulation_risk_review.py",
    "wf_port_sec_activate_allocation_version.py",
    "wf_port_ter_detect_drift_plan_rebalance.py",
    "wf_port_006_submit_measure_rebalance.py",
    "wf_port_007_rollback_allocation.py",
    "wf_port_008_assess_common_mode_exposure.py",
)


def main() -> None:
    """Execute every workflow against its own genuine bounded evidence."""
    for filename in WORKFLOWS:
        runpy.run_path(
            str(Path(__file__).with_name(filename)),
            run_name="__main__",
        )
    print(f"\nPortfolio workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()

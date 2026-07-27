"""Execute every active Risk workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_risk_001_build_portfolio_risk_snapshot.py",
    "wf_risk_002_calculate_position_size.py",
    "wf_risk_003_assess_risk_regime.py",
    "wf_risk_004_review_proposed_trade_risk.py",
    "wf_risk_005_run_current_portfolio_governor.py",
    "wf_risk_006_review_strategy_operational_eligibility.py",
    "wf_risk_007_review_activate_allocation_risk.py",
    "wf_risk_008_validate_approval_token.py",
    "wf_risk_009_apply_check_kill_switch_state.py",
    "wf_risk_010_run_scenario_what_if_analysis.py",
    "wf_risk_011_generate_risk_decision_summary.py",
    "wf_risk_012_persist_risk_audit_token_state.py",
    "wf_risk_014_revalidate_decision_evidence_before_reuse.py",
)


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    package = "tests.risk.usage.workflows"
    for filename in WORKFLOWS:
        importlib.import_module(f"{package}.{filename[:-3]}").main()
    print(f"\nRisk workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()

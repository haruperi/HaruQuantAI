"""Execute every active Trading workflow usage program."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

WORKFLOWS = (
    "wf_trd_001_validate_package_route_action.py",
    "wf_trd_002_execute_simulation_route_action.py",
    "wf_trd_003_start_enable_live_session.py",
    "wf_trd_004_gate_dispatch_live_action.py",
    "wf_trd_005_resolve_unknown_route_outcome.py",
    "wf_trd_006_read_route_facts_aggregate_readiness.py",
    "wf_trd_007_enforce_kill_switch_emergency_controls.py",
    "wf_trd_008_persist_evidence_recover_state.py",
    "wf_trd_009_perform_safe_live_shutdown.py",
    "wf_trd_010_emit_monitoring_cost_incident_evidence.py",
    "wf_trd_011_build_execution_reconciliation_evidence.py",
    "wf_trd_012_accept_governed_upstream_request.py",
    "wf_trd_013_execute_authorized_portfolio_rebalance.py",
    "wf_trd_014_run_live_paper_evaluation_cycle.py",
)


def main() -> None:
    """Import and execute all workflow programs in registry order."""
    package = "tests.trading.usage.workflows"
    for filename in WORKFLOWS:
        importlib.import_module(f"{package}.{filename[:-3]}").main()
    print(f"\nTrading workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()

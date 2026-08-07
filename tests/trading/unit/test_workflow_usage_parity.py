"""Verify Trading workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/trading/usage/workflows"
README = ROOT / "app/services/trading/README.md"
EXPECTED = {
    "WF-TRD-SEC": "wf_trd_sec_validate_package_route_action.py",
    "WF-TRD-002": "wf_trd_002_execute_simulation_route_action.py",
    "WF-TRD-003": "wf_trd_003_start_enable_live_session.py",
    "WF-TRD-PRI": "wf_trd_pri_gate_dispatch_live_action.py",
    "WF-TRD-005": "wf_trd_005_resolve_unknown_route_outcome.py",
    "WF-TRD-006": "wf_trd_006_read_route_facts_aggregate_readiness.py",
    "WF-TRD-TER": "wf_trd_ter_enforce_kill_switch_emergency_controls.py",
    "WF-TRD-008": "wf_trd_008_persist_evidence_recover_state.py",
    "WF-TRD-009": "wf_trd_009_perform_safe_live_shutdown.py",
    "WF-TRD-010": "wf_trd_010_emit_monitoring_cost_incident_evidence.py",
    "WF-TRD-011": "wf_trd_011_build_execution_reconciliation_evidence.py",
    "WF-TRD-012": "wf_trd_012_accept_governed_upstream_request.py",
    "WF-TRD-013": "wf_trd_013_execute_authorized_portfolio_rebalance.py",
    "WF-TRD-014": "wf_trd_014_run_live_paper_evaluation_cycle.py",
    "WF-TRD-015": "wf_trd_015_pause_resume_strategy_route.py",
    "WF-TRD-016": "wf_trd_016_modify_working_order_or_open_position.py",
    "WF-TRD-017": "wf_trd_017_broker_agnostic_main_operations.py",
}


def _assignment(path: Path, name: str) -> Any:
    """Return one literal module assignment."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is missing from {path.name}")


def test_trading_workflow_registry_has_one_complete_program_per_workflow() -> None:
    """Require exact README, runner, separator, stage, and boundary parity."""
    readme = README.read_text(encoding="utf-8")
    actual = {path.name for path in WORKFLOW_DIR.glob("wf_*.py")}
    assert actual == set(EXPECTED.values())
    assert tuple(EXPECTED.values()) == _assignment(
        WORKFLOW_DIR / "run_all.py", "WORKFLOWS"
    )
    for workflow_id, filename in EXPECTED.items():
        path = WORKFLOW_DIR / filename
        source = path.read_text(encoding="utf-8")
        stages = _assignment(path, "STAGES")
        assert _assignment(path, "WORKFLOW_ID") == workflow_id
        assert source.count("# Stage ") == len(stages)
        assert "'=' * 88" in source
        assert "INPUT BOUNDARY" in source
        assert "OUTPUT BOUNDARY" in source
        assert "def main() -> None:" in source
        assert 'if __name__ == "__main__":' in source
        assert f"`{workflow_id}`" in readme
        assert f"`tests/trading/usage/workflows/{filename}`" in readme
    for workflow_id in ("WF-TRD-003", "WF-TRD-PRI", "WF-TRD-013"):
        source = (WORKFLOW_DIR / EXPECTED[workflow_id]).read_text(encoding="utf-8")
        assert "No broker mutation was transmitted" in source
    assert (
        len(
            _assignment(
                WORKFLOW_DIR / EXPECTED["WF-TRD-PRI"],
                "STAGES",
            )
        )
        == 22
    )
    broker_agnostic = WORKFLOW_DIR / EXPECTED["WF-TRD-017"]
    assert len(_assignment(broker_agnostic, "STAGES")) == 17
    source = broker_agnostic.read_text(encoding="utf-8")
    expected_examples = (
        "example_01_connect",
        "example_02_platform",
        "example_03_account",
        "example_04_symbol",
        "example_05_positions",
        "example_06_orders",
        "example_07_history_orders",
        "example_08_history_deals",
        "example_09_open_position",
        "example_10_calculate_profit_margin",
        "example_11_modify_position",
        "example_12_partial_close_position",
        "example_13_close_position",
        "example_14_place_pending_order",
        "example_15_modify_pending_order",
        "example_16_cancel_pending_order",
        "example_17_shutdown",
    )
    for example in expected_examples:
        assert source.count(f"async def {example}(") == 1
    for renderer in (
        "_render_platform",
        "_render_account",
        "_render_symbol",
        "_render_quote",
        "_render_positions",
        "_render_orders",
        "_render_deals",
        "_render_execution",
    ):
        assert f"def {renderer}(" in source
    assert 'EXECUTION_TARGET: Target = "sim"' in source
    assert "app.services.brokers.mt5" not in source
    assert "app.services.brokers.ctrader" not in source

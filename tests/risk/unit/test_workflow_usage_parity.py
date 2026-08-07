"""Verify Risk workflow registry and standalone usage-program parity."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / "tests/risk/usage/workflows"
README = ROOT / "app/services/risk/README.md"
EXPECTED = {
    "WF-RISK-001": "wf_risk_001_build_portfolio_risk_snapshot.py",
    "WF-RISK-TER": "wf_risk_ter_calculate_position_size.py",
    "WF-RISK-003": "wf_risk_003_assess_risk_regime.py",
    "WF-RISK-PRI": "wf_risk_pri_review_proposed_trade_risk.py",
    "WF-RISK-005": "wf_risk_005_run_current_portfolio_governor.py",
    "WF-RISK-006": "wf_risk_006_review_strategy_operational_eligibility.py",
    "WF-RISK-007": "wf_risk_007_review_activate_allocation_risk.py",
    "WF-RISK-008": "wf_risk_008_validate_approval_token.py",
    "WF-RISK-SEC": "wf_risk_sec_apply_check_kill_switch_state.py",
    "WF-RISK-010": "wf_risk_010_run_scenario_what_if_analysis.py",
    "WF-RISK-011": "wf_risk_011_generate_risk_decision_summary.py",
    "WF-RISK-012": "wf_risk_012_persist_risk_audit_token_state.py",
    "WF-RISK-014": "wf_risk_014_revalidate_decision_evidence_before_reuse.py",
    "WF-RISK-015": "wf_risk_015_firm_mandate_single_day_profit_share.py",
    "WF-RISK-016": "wf_risk_016_compute_pin_risk_config_hash.py",
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


def test_risk_workflow_registry_has_one_complete_program_per_workflow() -> None:
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
        assert f"`tests/risk/usage/workflows/{filename}`" in readme
    assert "WF-RISK-013" not in {
        _assignment(WORKFLOW_DIR / filename, "WORKFLOW_ID")
        for filename in EXPECTED.values()
    }


def test_primary_workflow_is_the_complete_safe_teaching_trace() -> None:
    """Keep the primary workflow complete without executing Trading or a broker."""
    path = WORKFLOW_DIR / EXPECTED["WF-RISK-PRI"]
    source = path.read_text(encoding="utf-8")
    stages = _assignment(path, "STAGES")

    assert len(stages) == 24
    assert source.count("# Stage ") == 24
    assert "virtual_positions" in source
    assert "virtual_pending_orders" in source
    assert "virtual_closed_trade" in source
    assert source.count("review_trade_risk(") == 2
    assert "Canonical verdict:" in source
    assert "Blocked scenario:" in source
    assert "ILLUSTRATIVE BOUNDARY" in source
    assert "Trading must revalidate and atomically consume; not executed here" in source
    for forbidden in ("submit_order(", "dispatch_order_intent(", "open_socket("):
        assert forbidden not in source

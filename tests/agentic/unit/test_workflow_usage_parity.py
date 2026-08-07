"""Mechanical parity checks for Agentic workflow usage evidence."""

from pathlib import Path


def test_every_active_workflow_has_one_stage_labelled_program() -> None:
    """Workflow usage filenames reconcile with the active registry."""
    root = Path("tests/agentic/usage/workflows")
    assert {path.name for path in root.glob("wf_agt_*.py")} == {
        "wf_agt_pri_firm_research_council.py",
        "wf_agt_002_interpret_deterministic_evidence.py",
        "wf_agt_003_hypothesis_to_experiment.py",
        "wf_agt_004_bounded_optimization.py",
        "wf_agt_005_author_code_artifact.py",
        "wf_agt_sec_promote_artifact.py",
        "wf_agt_ter_portfolio_risk_council.py",
        "wf_agt_008_submit_trade_proposal.py",
        "wf_agt_009_model_upgrade.py",
        "wf_agt_010_incident_recovery.py",
        "wf_agt_011_governed_memory.py",
        "wf_agt_012_tool_permission_approval.py",
    }
    assert (root / "run_all.py").is_file()

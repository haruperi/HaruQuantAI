"""Workflow integration test for focused Risk decision reporting."""

from app.services.risk.reporting import generate_risk_report

from tests.risk.usage import test_usage_decisions as decision_examples
from tests.risk.usage import test_usage_policy as policy_examples


def test_report_separates_evidence_and_decision() -> None:
    """Keep source evidence separate and place primary block before verdict."""
    config = decision_examples._config()
    governor, _, _ = decision_examples._services(config)
    active = decision_examples._inactive_state().model_copy(
        update={"state": "active", "reason": "operator safety stop"}
    )
    decision = governor.review_trade_risk(
        decision_examples._proposal(config),
        decision_examples._snapshot(config),
        policy_examples._market(),
        decision_examples._regime(),
        (active,),
        decision_examples._auth(config),
        attestation=decision_examples._attestation(config),
        now=decision_examples.NOW,
    )
    report = generate_risk_report(
        decision, "markdown", config, now=decision_examples.NOW
    )
    assert report.evidence != report.decision
    assert report.decision[0] == "primary_failure=kill_switch"
    assert report.decision[1] == "state=block"
    assert report.approval_claimed is False

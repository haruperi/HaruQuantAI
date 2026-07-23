"""Unit tests for focused deterministic Risk report rendering."""

from decimal import Decimal

from app.services.risk.contracts import DecisionState, ScenarioDefinition
from app.services.risk.reporting import generate_risk_report
from app.services.risk.scenarios import run_risk_scenario_analysis

from tests.risk import _support as decision_examples
from tests.risk import _support as policy_examples


def test_report_has_no_false_approval_claim() -> None:
    """Never claim live approval for a pending decision without token evidence."""
    config = decision_examples._config()
    governor, _, _ = decision_examples._services(config)
    decision = governor.review_trade_risk(
        decision_examples._proposal(config),
        decision_examples._snapshot(config),
        policy_examples._market(),
        decision_examples._regime(),
        (decision_examples._inactive_state(),),
        decision_examples._auth(config),
        now=decision_examples.NOW,
    )
    assert decision.state is DecisionState.NEEDS_APPROVAL
    report = generate_risk_report(
        decision, "markdown", config, now=decision_examples.NOW
    )
    assert report.approval_claimed is False
    assert report.decision[0] == "primary_failure=approval_required"
    assert "## Evidence" in str(report.content)
    assert "## Recommendations" in str(report.content)


def test_report_claims_only_current_bound_token_and_exact_json() -> None:
    """Claim approval only for current exact token and render configured JSON."""
    config = decision_examples._config()
    governor, _, _ = decision_examples._services(config)
    decision = governor.review_trade_risk(
        decision_examples._proposal(config),
        decision_examples._snapshot(config),
        policy_examples._market(),
        decision_examples._regime(),
        (decision_examples._inactive_state(),),
        decision_examples._auth(config),
        attestation=decision_examples._attestation(config),
        now=decision_examples.NOW,
    )
    json_config = config.model_copy(update={"risk_report_format": "json"})
    report = generate_risk_report(
        decision, "json", json_config, now=decision_examples.NOW
    )
    assert report.approval_claimed is True
    assert isinstance(report.content, dict)
    assert set(report.content) == {
        "assumptions",
        "calculations",
        "decision",
        "evidence",
        "recommendations",
        "warnings",
    }


def test_report_renders_advisory_scenarios_without_approval() -> None:
    """Render scenario calculations while preserving advisory-only decision."""
    config = decision_examples._config()
    scenario_results = run_risk_scenario_analysis(
        decision_examples._snapshot(config),
        (
            ScenarioDefinition(
                scenario_id="stress-1",
                shocks={"equity": Decimal("-0.10")},
                randomized=False,
                seed=None,
                assumptions=("declared equity stress",),
            ),
        ),
        config,
        now=decision_examples.NOW,
    )
    report = generate_risk_report(
        scenario_results, "markdown", config, now=decision_examples.NOW
    )
    assert report.approval_claimed is False
    assert report.decision == ("advisory_only=true", "approved=false")
    assert report.report_id == "risk-report:stress-1:markdown"

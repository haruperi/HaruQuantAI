"""Workflow integration test for current-state portfolio Risk governor."""

from app.services.risk.contracts import DecisionState

from tests.risk.usage import test_usage_decisions as examples
from tests.risk.usage import test_usage_policy as policy_examples


def test_portfolio_governor_has_no_execution_side_effect() -> None:
    """Return audited compliance without calling or mutating execution state."""
    config = examples._config()
    governor, _, audit = examples._services(config)
    snapshot = examples._snapshot(config)
    before = snapshot.model_dump(mode="python")
    execution_state = {"orders_cancelled": False, "positions_closed": False}
    decision = governor.run_portfolio_risk_governor(
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (examples._inactive_state(),),
        examples._auth(config),
        now=examples.NOW,
    )
    assert decision.state is DecisionState.APPROVE
    assert snapshot.model_dump(mode="python") == before
    assert execution_state == {"orders_cancelled": False, "positions_closed": False}
    assert audit.records[-1].decision_id == decision.decision_id

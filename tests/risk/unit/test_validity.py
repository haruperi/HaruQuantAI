"""Unit tests for non-authorizing Risk decision reuse validation."""

from datetime import timedelta
from decimal import Decimal

from app.services.risk.contracts import RiskErrorCode
from app.services.risk.contracts.responses import unwrap_risk_response
from app.services.risk.validity import revalidate_risk_decision

from tests.risk import _support as examples
from tests.risk import _support as policy_examples


def test_material_change_invalidates() -> None:
    """Reject reuse when requested size changes after canonical review."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    decision = unwrap_risk_response(
        governor.review_trade_risk(
            proposal,
            snapshot,
            policy_examples._market(),
            examples._regime(),
            (examples._inactive_state(),),
            examples._auth(config),
            attestation=examples._attestation(config),
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    changed = proposal.model_copy(update={"requested_size": Decimal(2)})
    response = revalidate_risk_decision(
        decision, changed, snapshot, config, now=examples.NOW
    )
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == RiskErrorCode.STALE_EVIDENCE.value


def test_config_change_and_expiry_invalidate() -> None:
    """Distinguish exact config mismatch from expired decision evidence."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    decision = unwrap_risk_response(
        governor.review_trade_risk(
            proposal,
            snapshot,
            policy_examples._market(),
            examples._regime(),
            (examples._inactive_state(),),
            examples._auth(config),
            attestation=examples._attestation(config),
            now=examples.NOW,
        ),
        operation="risk_governor.review_trade_risk",
    )
    changed_config = config.model_copy(update={"max_drawdown": Decimal("0.09")})
    mismatch = revalidate_risk_decision(
        decision, proposal, snapshot, changed_config, now=examples.NOW
    )
    assert mismatch.status == "error"
    assert mismatch.error is not None
    assert mismatch.error.code == RiskErrorCode.CONFIG_VERSION_MISMATCH.value
    expired = revalidate_risk_decision(
        decision,
        proposal,
        snapshot,
        config,
        now=examples.NOW + timedelta(seconds=31),
    )
    assert expired.status == "error"
    assert expired.error is not None
    assert expired.error.code == RiskErrorCode.STALE_EVIDENCE.value

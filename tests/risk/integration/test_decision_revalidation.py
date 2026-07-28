"""Workflow integration test for material Risk decision revalidation."""

from decimal import Decimal

import pytest
from app.services.risk import (
    RiskDomainError,
    RiskErrorCode,
    revalidate_risk_decision,
)

from tests.risk import _support as examples
from tests.risk import _support as policy_examples


def test_material_change_requires_new_decision() -> None:
    """Require a fresh canonical review after material proposal size change."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    decision = examples.unwrap_risk_response(
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
    with pytest.raises(RiskDomainError) as captured:
        examples.unwrap_risk_response(
            revalidate_risk_decision(
                decision, changed, snapshot, config, now=examples.NOW
            ),
            operation="revalidate_risk_decision",
        )
    assert captured.value.risk_code is RiskErrorCode.STALE_EVIDENCE

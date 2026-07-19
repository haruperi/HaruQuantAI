"""Unit tests for non-authorizing Risk decision reuse validation."""

from datetime import timedelta
from decimal import Decimal

import pytest
from app.services.risk.contracts import RiskDomainError, RiskErrorCode
from app.services.risk.decisions import revalidate_risk_decision

from tests.risk.usage import test_usage_decisions as examples
from tests.risk.usage import test_usage_policy as policy_examples


def test_material_change_invalidates() -> None:
    """Reject reuse when requested size changes after canonical review."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    decision = governor.review_trade_risk(
        proposal,
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (examples._inactive_state(),),
        examples._auth(config),
        attestation=examples._attestation(config),
        now=examples.NOW,
    )
    changed = proposal.model_copy(update={"requested_size": Decimal(2)})
    with pytest.raises(RiskDomainError) as captured:
        revalidate_risk_decision(decision, changed, snapshot, config, now=examples.NOW)
    assert captured.value.risk_code is RiskErrorCode.STALE_EVIDENCE


def test_config_change_and_expiry_invalidate() -> None:
    """Distinguish exact config mismatch from expired decision evidence."""
    config = examples._config()
    governor, _, _ = examples._services(config)
    proposal = examples._proposal(config)
    snapshot = examples._snapshot(config)
    decision = governor.review_trade_risk(
        proposal,
        snapshot,
        policy_examples._market(),
        examples._regime(),
        (examples._inactive_state(),),
        examples._auth(config),
        attestation=examples._attestation(config),
        now=examples.NOW,
    )
    changed_config = config.model_copy(update={"max_drawdown": Decimal("0.09")})
    with pytest.raises(RiskDomainError) as mismatch:
        revalidate_risk_decision(
            decision, proposal, snapshot, changed_config, now=examples.NOW
        )
    assert mismatch.value.risk_code is RiskErrorCode.CONFIG_VERSION_MISMATCH
    with pytest.raises(RiskDomainError) as expired:
        revalidate_risk_decision(
            decision,
            proposal,
            snapshot,
            config,
            now=examples.NOW + timedelta(seconds=31),
        )
    assert expired.value.risk_code is RiskErrorCode.STALE_EVIDENCE

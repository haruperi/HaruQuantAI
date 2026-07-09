"""Unit tests for Risk Audit & Decision Token package."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from app.services.risk.audit.events import (
    AuditContext,
    AuditRedactionPolicy,
    build_canonical_audit_payload,
    create_risk_audit_event,
    redact_audit_payload,
)
from app.services.risk.audit.hash_chain import (
    AuditChainVerification,
    append_audit_hash,
    build_genesis_hash,
    require_valid_audit_chain,
    verify_risk_audit_chain,
)
from app.services.risk.audit.tokens import (
    DefaultTokenSigner,
    RequiredActionScope,
    TokenValidationContext,
    create_risk_decision_token,
    revoke_risk_approval_token,
    validate_risk_approval_token,
    validate_token_expiry,
    validate_token_scope,
)
from app.services.risk.models import (
    ProposedTrade,
    RiskAuditEvent,
    RiskDecisionPackage,
    RiskDecisionToken,
)
from app.services.risk.models.enums import RiskDecisionStatus, RiskMode
from app.utils.errors import ValidationError


@pytest.fixture
def sample_decision() -> RiskDecisionPackage:
    """Fixture for a baseline RiskDecisionPackage."""
    return RiskDecisionPackage(
        decision_id="dec_test_123",
        request_id="req_test_123",
        workflow_id="wf_test_123",
        status=RiskDecisionStatus.APPROVE,
        rule_key="limits_passed",
        snapshot_as_of=datetime.now(UTC),
        config_hash="config_abc_123",
        reason="Success",
        composite_breach_flags=[],
        calculated_volume=Decimal("1.0"),
        policy_hash="policy_xyz_123",
        policy_version="1.0.0",
        policy_scope={},
        details={
            "proposed_action": {
                "strategy_id": "strat_1",
                "symbol": "EURUSD",
                "side": "buy",
                "volume": 1.0,
                "environment": "live",
                "api_key": "some_secret_key",
            },
            "account_id": "acc_1",
        },
    )


@pytest.fixture
def sample_trade() -> ProposedTrade:
    """Fixture for a ProposedTrade."""
    return ProposedTrade(
        strategy_id="strat_1",
        symbol="EURUSD",
        side="buy",
        volume=Decimal("1.0"),
    )


# ==========================================
# 1. Tests for hash_chain.py
# ==========================================


def test_build_genesis_hash() -> None:
    """Test building genesis hash computes consistent SHA256."""
    payload = {"symbol": "EURUSD", "volume": Decimal("1.5")}
    h1 = build_genesis_hash(payload)
    h2 = build_genesis_hash(payload)
    assert h1 == h2
    assert len(h1) == 64


def test_append_audit_hash() -> None:
    """Test append_audit_hash chains deterministic hashes."""
    prev_hash = "0" * 64
    payload = {"symbol": "GBPUSD", "volume": Decimal("2.0")}
    h1 = append_audit_hash(prev_hash, payload)
    h2 = append_audit_hash(prev_hash, payload)
    assert h1 == h2
    assert len(h1) == 64
    assert h1 != prev_hash


def test_verify_risk_audit_chain_empty() -> None:
    """Test verify_risk_audit_chain handles empty event sequence."""
    res = verify_risk_audit_chain([])
    assert res.valid is True
    assert res.tampered is False


def test_verify_risk_audit_chain_valid_single() -> None:
    """Test verify_risk_audit_chain for a single valid genesis event."""
    event = RiskAuditEvent(
        event_id="evt_01",
        decision_id="dec_01",
        policy_name="policy",
        action_taken="approve",
        payload_hash="payload_hash",
        severity="info",
        previous_hash="0" * 64,
        hash="",
        timestamp=datetime.now(UTC),
        details={"symbol": "EURUSD"},
    )
    event.hash = append_audit_hash("0" * 64, event.model_dump())

    res = verify_risk_audit_chain([event])
    assert res.valid is True
    assert res.tampered is False


def test_verify_risk_audit_chain_genesis_mismatch() -> None:
    """Test verify_risk_audit_chain fails when genesis block previous_hash is not zero."""
    event = RiskAuditEvent(
        event_id="evt_01",
        decision_id="dec_01",
        policy_name="policy",
        action_taken="approve",
        payload_hash="payload_hash",
        severity="info",
        previous_hash="invalid_prev_hash",
        hash="",
        timestamp=datetime.now(UTC),
        details={"symbol": "EURUSD"},
    )
    event.hash = append_audit_hash("invalid_prev_hash", event.model_dump())

    res = verify_risk_audit_chain([event])
    assert res.valid is False
    assert res.tampered is True
    assert "Genesis previous hash mismatch" in res.details["message"]


def test_verify_risk_audit_chain_linkage_broken() -> None:
    """Test verify_risk_audit_chain fails when sequence continuity is broken."""
    evt1 = RiskAuditEvent(
        event_id="evt_01",
        decision_id="dec_01",
        policy_name="policy",
        action_taken="approve",
        payload_hash="payload_hash",
        severity="info",
        previous_hash="0" * 64,
        hash="",
        timestamp=datetime.now(UTC),
        details={"symbol": "EURUSD"},
    )
    evt1.hash = append_audit_hash("0" * 64, evt1.model_dump())

    evt2 = RiskAuditEvent(
        event_id="evt_02",
        decision_id="dec_02",
        policy_name="policy",
        action_taken="approve",
        payload_hash="payload_hash",
        severity="info",
        previous_hash="broken_link",
        hash="",
        timestamp=datetime.now(UTC),
        details={"symbol": "EURUSD"},
    )
    evt2.hash = append_audit_hash("broken_link", evt2.model_dump())

    res = verify_risk_audit_chain([evt1, evt2])
    assert res.valid is False
    assert res.tampered is True
    assert "Sequence linkage broken" in res.details["message"]


def test_verify_risk_audit_chain_hash_mismatch() -> None:
    """Test verify_risk_audit_chain fails when stored hash does not match computed."""
    event = RiskAuditEvent(
        event_id="evt_01",
        decision_id="dec_01",
        policy_name="policy",
        action_taken="approve",
        payload_hash="payload_hash",
        severity="info",
        previous_hash="0" * 64,
        hash="modified_hash_for_tampering",
        timestamp=datetime.now(UTC),
        details={"symbol": "EURUSD"},
    )

    res = verify_risk_audit_chain([event])
    assert res.valid is False
    assert res.tampered is True
    assert "Event hash mismatch" in res.details["message"]


def test_require_valid_audit_chain() -> None:
    """Test require_valid_audit_chain fail-closed logic."""
    ok_verification = AuditChainVerification(valid=True, tampered=False)
    bad_verification = AuditChainVerification(valid=False, tampered=True)

    # 1. Non-live mode should pass even if chain is tampered
    res = require_valid_audit_chain(bad_verification, RiskMode.PAPER)
    assert res["valid"] is True

    # 2. Live mode must pass when chain is valid
    res = require_valid_audit_chain(ok_verification, RiskMode.MICRO_LIVE)
    assert res["valid"] is True

    # 3. Live mode must fail closed when chain is tampered/invalid
    res = require_valid_audit_chain(bad_verification, RiskMode.MICRO_LIVE)
    assert res["valid"] is False
    assert res["code"] == "AUDIT_CHAIN_CORRUPT"


# ==========================================
# 2. Tests for tokens.py
# ==========================================


def test_create_risk_decision_token(sample_decision: RiskDecisionPackage) -> None:
    """Test create_risk_decision_token assigns and signs fields correctly."""
    signer = DefaultTokenSigner()
    now = datetime.now(UTC)

    # 1. Success creation
    token = create_risk_decision_token(sample_decision, signer, now)
    assert token.token_id.startswith("tok")
    assert token.config_hash == sample_decision.config_hash
    assert token.policy_hash == sample_decision.policy_hash
    assert token.scope["strategy_id"] == "strat_1"
    assert token.signature is not None

    # 2. Scope extraction with generic details dict
    sample_decision.details = {
        "strategy_id": "strat_2",
        "account_id": "acc_2",
        "symbol": "GBPUSD",
        "environment": "production",
    }
    token2 = create_risk_decision_token(sample_decision, signer, now)
    assert token2.scope["strategy_id"] == "strat_2"
    assert token2.scope["account_id"] == "acc_2"

    # 3. Validation failure raises ValueError
    bad_decision = sample_decision.model_copy()
    bad_decision.decision_id = ""
    with pytest.raises(ValueError, match="decision_id and status are required"):
        create_risk_decision_token(bad_decision, signer, now)


def test_validate_token_expiry() -> None:
    """Test validate_token_expiry handles active vs expired tokens."""
    now = datetime.now(UTC)
    active_token = RiskDecisionToken(
        token_id="tok_1",
        expiry=now + timedelta(minutes=5),
        policy_hash="policy",
        config_hash="config",
        signature="sig",
    )
    expired_token = RiskDecisionToken(
        token_id="tok_2",
        expiry=now - timedelta(minutes=1),
        policy_hash="policy",
        config_hash="config",
        signature="sig",
    )

    assert validate_token_expiry(active_token, now)["valid"] is True
    res = validate_token_expiry(expired_token, now)
    assert res["valid"] is False
    assert res["code"] == "TOKEN_EXPIRED"


def test_validate_token_scope() -> None:
    """Test validate_token_scope matches scopes with alt keys."""
    token = RiskDecisionToken(
        token_id="tok_1",
        expiry=datetime.now(UTC),
        policy_hash="policy",
        config_hash="config",
        signature="sig",
        scope={
            "strategy": "strat_1",
            "account": "acc_1",
            "symbol": "EURUSD",
            "environment": "live",
        },
    )

    req_scope = RequiredActionScope(
        action="execute_trade",
        strategy_id="strat_1",
        account_id="acc_1",
        symbol="EURUSD",
        environment="live",
    )
    assert validate_token_scope(token, req_scope)["valid"] is True

    # Check mismatch
    bad_scope = RequiredActionScope(action="execute_trade", strategy_id="strat_2")
    res = validate_token_scope(token, bad_scope)
    assert res["valid"] is False
    assert res["code"] == "SCOPE_MISMATCH"


def test_validate_risk_approval_token(
    sample_decision: RiskDecisionPackage,
) -> None:
    """Test validate_risk_approval_token completes all checks."""
    signer = DefaultTokenSigner()
    now = datetime.now(UTC)

    # 1. Sign a valid token
    token = create_risk_decision_token(sample_decision, signer, now)

    scope = RequiredActionScope(
        action="execute_trade",
        strategy_id="strat_1",
        account_id="acc_1",
        symbol="EURUSD",
        environment="live",
    )
    context = TokenValidationContext(
        active_config_hash=sample_decision.config_hash,
        active_policy_hash=sample_decision.policy_hash,
        required_scope=scope,
        now_utc=now,
    )

    # Valid validation
    res = validate_risk_approval_token(token, context, signer)
    assert res.valid is True
    assert res.code == "OK"

    # 2. Check invalid instance type
    bad_res = validate_risk_approval_token("not-a-token", context, signer)  # type: ignore
    assert bad_res.valid is False
    assert bad_res.code == "INVALID_TOKEN_SCHEMA"

    # 3. Signature verification failure
    tampered_token = token.model_copy()
    tampered_token.signature = "tampered_signature"
    res = validate_risk_approval_token(tampered_token, context, signer)
    assert res.valid is False
    assert res.code == "SIGNATURE_INVALID"

    # 4. Token expired
    context_future = context.model_copy()
    context_future.now_utc = now + timedelta(minutes=10)
    res = validate_risk_approval_token(token, context_future, signer)
    assert res.valid is False
    assert res.code == "TOKEN_EXPIRED"

    # 5. Token revoked
    signer.revoke_token(token.token_id)
    res = validate_risk_approval_token(token, context, signer)
    assert res.valid is False
    assert res.code == "TOKEN_REVOKED"


def test_validate_risk_approval_token_hash_mismatch(
    sample_decision: RiskDecisionPackage,
) -> None:
    """Test validate_risk_approval_token fails when policy/config hashes mismatch."""
    signer = DefaultTokenSigner()
    now = datetime.now(UTC)
    token = create_risk_decision_token(sample_decision, signer, now)

    scope = RequiredActionScope(
        action="execute_trade",
        strategy_id="strat_1",
        account_id="acc_1",
        symbol="EURUSD",
        environment="live",
    )

    # Config hash mismatch
    context_bad_cfg = TokenValidationContext(
        active_config_hash="mismatch_config_hash",
        active_policy_hash=sample_decision.policy_hash,
        required_scope=scope,
        now_utc=now,
    )
    res = validate_risk_approval_token(token, context_bad_cfg, signer)
    assert res.valid is False
    assert res.code == "CONFIG_HASH_MISMATCH"

    # Policy hash mismatch
    context_bad_policy = TokenValidationContext(
        active_config_hash=sample_decision.config_hash,
        active_policy_hash="mismatch_policy_hash",
        required_scope=scope,
        now_utc=now,
    )
    res = validate_risk_approval_token(token, context_bad_policy, signer)
    assert res.valid is False
    assert res.code == "POLICY_HASH_MISMATCH"


def test_revoke_risk_approval_token() -> None:
    """Test standalone helper revoke_risk_approval_token."""
    mock_store = MagicMock()
    revoke_risk_approval_token("tok_rev_123", mock_store)
    mock_store.revoke_token.assert_called_once_with("tok_rev_123")


# ==========================================
# 3. Tests for events.py
# ==========================================


def test_redact_audit_payload() -> None:
    """Test redact_audit_payload filters sensitive keys recursively."""
    policy = AuditRedactionPolicy()
    payload = {
        "api_key": "secret_key_value",
        "symbol": "EURUSD",
        "inner_dict": {
            "password": "my_passphrase",
            "volume": Decimal("1.0"),
        },
    }
    redacted = redact_audit_payload(payload, policy)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["symbol"] == "EURUSD"
    assert redacted["inner_dict"]["password"] == "[REDACTED]"
    assert redacted["inner_dict"]["volume"] == Decimal("1.0")


def test_build_canonical_audit_payload(
    sample_decision: RiskDecisionPackage, sample_trade: ProposedTrade
) -> None:
    """Test build_canonical_audit_payload coerces decimals and redacts keys."""
    context = AuditContext(proposed_action=sample_trade)
    details = build_canonical_audit_payload(sample_decision, context)

    # Decimals coerced to floats
    assert details["proposed_action"]["volume"] == 1.0
    # Redacted values applied to decision payload
    assert details["decision"]["details"]["proposed_action"]["api_key"] == "[REDACTED]"
    assert details["decision"]["details"]["proposed_action"]["environment"] == "live"


def test_create_risk_audit_event_pure(
    sample_decision: RiskDecisionPackage, sample_trade: ProposedTrade
) -> None:
    """Test pure create_risk_audit_event creation."""
    context = AuditContext(proposed_action=sample_trade, previous_hash="0" * 64)
    event = create_risk_audit_event(sample_decision, context)

    assert event.event_id.startswith("event")
    assert event.decision_id == sample_decision.decision_id
    assert event.action_taken == sample_decision.status
    assert event.previous_hash == "0" * 64
    assert event.hash != ""


def test_create_risk_audit_event_v1_legacy(
    sample_decision: RiskDecisionPackage, sample_trade: ProposedTrade
) -> None:
    """Test legacy V1 write interface works correctly."""
    mock_sink = MagicMock()
    mock_sink.get_last_event.return_value = None

    event = create_risk_audit_event(sample_decision, sample_trade, mock_sink)

    assert event.previous_hash == "0" * 64
    mock_sink.get_last_event.assert_called_once()
    mock_sink.write_event.assert_called_once_with(event)


def test_create_risk_audit_event_v1_legacy_error(
    sample_decision: RiskDecisionPackage, sample_trade: ProposedTrade
) -> None:
    """Test V1 write error wraps in database ValidationError."""
    mock_sink_read_fail = MagicMock()
    mock_sink_read_fail.get_last_event.side_effect = RuntimeError("Read DB failed")

    with pytest.raises(ValidationError, match="Audit persistence query failed"):
        create_risk_audit_event(sample_decision, sample_trade, mock_sink_read_fail)

    mock_sink_write_fail = MagicMock()
    mock_sink_write_fail.get_last_event.return_value = None
    mock_sink_write_fail.write_event.side_effect = RuntimeError("Write DB failed")

    with pytest.raises(ValidationError, match="Audit persistence write failed"):
        create_risk_audit_event(sample_decision, sample_trade, mock_sink_write_fail)

"""Unit tests for operator approval and risk decision binding verification."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.services.trading.contracts import TradingAction
from app.services.trading.gates.approval import (
    HARD_DUAL_APPROVAL_ACTION_IDS,
    ApprovalScope,
    OperatorApprovalToken,
    RiskDecisionEvidence,
    compute_canonical_request_hash,
    requires_dual_approval,
    validate_dual_operator_approval,
    validate_operator_approval,
    validate_risk_decision,
)
from app.services.trading.gates.policy_matrix import PolicyMatrixEntry
from app.services.trading.security.error_mapping import TradingMappedError

NOW = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
FUTURE = "2026-07-09T13:00:00Z"
PAST = "2026-07-09T11:00:00Z"
REQUEST_HASH = compute_canonical_request_hash(
    symbol="EURUSD",
    account_id="acct-1",
    side="buy",
    volume="0.10",
    price=None,
    sl=None,
    tp=None,
    route="live",
    strategy_id="strat-1",
)


def _token(**overrides: object) -> OperatorApprovalToken:
    defaults: dict[str, object] = {
        "approval_id": "appr-1",
        "operator_id": "op-1",
        "governed_action_id": "submit_order",
        "scope": ApprovalScope(),
        "canonical_request_hash": REQUEST_HASH,
        "issued_at": "2026-07-09T10:00:00Z",
        "expires_at": FUTURE,
    }
    defaults.update(overrides)
    return OperatorApprovalToken(**defaults)  # type: ignore[arg-type]


def test_compute_canonical_request_hash_is_deterministic() -> None:
    """The same order parameters always produce the same hash."""
    again = compute_canonical_request_hash(
        symbol="EURUSD",
        account_id="acct-1",
        side="buy",
        volume="0.10",
        price=None,
        sl=None,
        tp=None,
        route="live",
        strategy_id="strat-1",
    )
    assert again == REQUEST_HASH
    assert len(REQUEST_HASH) == 64


def test_operator_approval_token_rejects_blank_fields() -> None:
    """OperatorApprovalToken fails closed on a blank identifier field."""
    with pytest.raises(ValueError, match="must be non-empty"):
        _token(approval_id=" ")


def test_validate_operator_approval_rejects_revoked() -> None:
    """A revoked token is rejected."""
    token = _token(revoked=True)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_REVOKED"


def test_validate_operator_approval_rejects_consumed() -> None:
    """A consumed single-use token is rejected."""
    token = _token(consumed=True)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_CONSUMED"


def test_validate_operator_approval_rejects_expired() -> None:
    """An expired token is rejected."""
    token = _token(expires_at=PAST)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_EXPIRED"


def test_validate_operator_approval_rejects_hash_mismatch() -> None:
    """A token bound to different order parameters is rejected."""
    token = _token(canonical_request_hash="0" * 64)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_INVALID"


def test_validate_operator_approval_accepts_unscoped_token() -> None:
    """An unscoped token (all scope fields None) matches any request scope."""
    token = _token()
    validate_operator_approval(
        token=token,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(
            account_id="acct-1", strategy_id="strat-1", symbol="EURUSD"
        ),
    )


def test_validate_operator_approval_rejects_account_scope_mismatch() -> None:
    """A token scoped to a different account is rejected."""
    token = _token(scope=ApprovalScope(account_id="acct-2"))
    with pytest.raises(TradingMappedError) as exc_info:
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(account_id="acct-1"),
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_INVALID"


def test_validate_operator_approval_rejects_strategy_scope_mismatch() -> None:
    """A token scoped to a matching account but different strategy is rejected."""
    token = _token(scope=ApprovalScope(account_id="acct-1", strategy_id="strat-2"))
    with pytest.raises(TradingMappedError):
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(account_id="acct-1", strategy_id="strat-1"),
        )


def test_validate_operator_approval_rejects_symbol_scope_mismatch() -> None:
    """A token scoped only to a different symbol is rejected."""
    token = _token(scope=ApprovalScope(symbol="GBPUSD"))
    with pytest.raises(TradingMappedError):
        validate_operator_approval(
            token=token,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(symbol="EURUSD"),
        )


def test_validate_operator_approval_accepts_fully_matching_scope() -> None:
    """A token fully scoped and matching the request passes."""
    token = _token(
        scope=ApprovalScope(account_id="acct-1", strategy_id="strat-1", symbol="EURUSD")
    )
    validate_operator_approval(
        token=token,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(
            account_id="acct-1", strategy_id="strat-1", symbol="EURUSD"
        ),
    )


def test_requires_dual_approval_for_hard_coded_actions() -> None:
    """Hard-coded governance actions always require dual approval."""
    for action_id in HARD_DUAL_APPROVAL_ACTION_IDS:
        assert requires_dual_approval(governed_action_id=action_id) is True


def test_requires_dual_approval_from_matrix_entry() -> None:
    """A policy matrix entry can require dual approval for other actions."""
    entry_required = PolicyMatrixEntry(
        action=TradingAction.SUBMIT_ORDER, requires_dual_approval=True
    )
    entry_not_required = PolicyMatrixEntry(
        action=TradingAction.SUBMIT_ORDER, requires_dual_approval=False
    )
    assert (
        requires_dual_approval(
            governed_action_id="submit_order", matrix_entry=entry_required
        )
        is True
    )
    assert (
        requires_dual_approval(
            governed_action_id="submit_order", matrix_entry=entry_not_required
        )
        is False
    )


def test_requires_dual_approval_defaults_false_without_matrix_entry() -> None:
    """Dual approval defaults to False when no matrix entry is supplied."""
    assert requires_dual_approval(governed_action_id="submit_order") is False


def test_validate_dual_operator_approval_requires_two_tokens() -> None:
    """Dual approval fails closed with fewer than two tokens."""
    with pytest.raises(TradingMappedError) as exc_info:
        validate_dual_operator_approval(
            tokens=(_token(),),
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_REQUIRED"


def test_validate_dual_operator_approval_requires_distinct_operators() -> None:
    """Dual approval fails closed when both tokens share one operator."""
    tokens = (_token(approval_id="a1"), _token(approval_id="a2"))
    with pytest.raises(TradingMappedError) as exc_info:
        validate_dual_operator_approval(
            tokens=tokens,
            now=NOW,
            expected_request_hash=REQUEST_HASH,
            expected_scope=ApprovalScope(),
        )
    assert exc_info.value.code == "APPROVAL_REQUIRED"


def test_validate_dual_operator_approval_passes_with_distinct_operators() -> None:
    """Dual approval passes with two distinct, valid operator tokens."""
    tokens = (
        _token(approval_id="a1", operator_id="op-1"),
        _token(approval_id="a2", operator_id="op-2"),
    )
    validate_dual_operator_approval(
        tokens=tokens,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(),
    )


def _risk_evidence(**overrides: object) -> RiskDecisionEvidence:
    defaults: dict[str, object] = {
        "risk_decision_id": "risk-1",
        "canonical_request_hash": REQUEST_HASH,
        "issued_at": "2026-07-09T10:00:00Z",
        "expires_at": FUTURE,
    }
    defaults.update(overrides)
    return RiskDecisionEvidence(**defaults)  # type: ignore[arg-type]


def test_risk_decision_evidence_rejects_blank_fields() -> None:
    """RiskDecisionEvidence fails closed on a blank identifier field."""
    with pytest.raises(ValueError, match="must be non-empty"):
        _risk_evidence(risk_decision_id=" ")


def test_validate_risk_decision_rejects_revoked() -> None:
    """A revoked risk decision is rejected."""
    evidence = _risk_evidence(revoked=True)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_risk_decision(
            evidence=evidence, now=NOW, expected_request_hash=REQUEST_HASH
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_REVOKED"


def test_validate_risk_decision_rejects_expired() -> None:
    """An expired risk decision is rejected."""
    evidence = _risk_evidence(expires_at=PAST)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_risk_decision(
            evidence=evidence, now=NOW, expected_request_hash=REQUEST_HASH
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_EXPIRED"


def test_validate_risk_decision_rejects_hash_mismatch() -> None:
    """A risk decision bound to different order parameters is rejected."""
    evidence = _risk_evidence(canonical_request_hash="0" * 64)
    with pytest.raises(TradingMappedError) as exc_info:
        validate_risk_decision(
            evidence=evidence, now=NOW, expected_request_hash=REQUEST_HASH
        )
    assert exc_info.value.code == "APPROVAL_TOKEN_INVALID"


def test_validate_risk_decision_passes_when_valid() -> None:
    """A fresh, matching, non-revoked risk decision passes."""
    evidence = _risk_evidence()
    validate_risk_decision(
        evidence=evidence, now=NOW, expected_request_hash=REQUEST_HASH
    )


def test_parse_utc_handles_naive_and_aware_timestamps() -> None:
    """Both naive and timezone-aware expiry timestamps are handled."""
    naive_token = _token(expires_at="2026-07-09T13:00:00")
    validate_operator_approval(
        token=naive_token,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(),
    )
    aware_token = _token(expires_at="2026-07-09T13:00:00+00:00")
    validate_operator_approval(
        token=aware_token,
        now=NOW,
        expected_request_hash=REQUEST_HASH,
        expected_scope=ApprovalScope(),
    )

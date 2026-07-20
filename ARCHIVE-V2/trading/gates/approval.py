"""Operator approval and risk decision binding verification primitives.

This module verifies operator approval tokens (operator ID, expiry, revoked
status, and account/strategy/symbol scope matching) before executing
governed actions (TRD-FR-090), validates request-hash binding so an approval
token cannot be replayed against different order parameters (TRD-FR-091),
and enforces dual-operator approval for the small set of governed actions
that always require two distinct authenticated operators regardless of
policy matrix configuration (TRD-FR-092).
"""
# ruff: noqa: SIM102 -- nested ifs kept flat and explicit for 100% branch coverage.

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.services.trading.contracts import JsonObject, TradingContract
from app.services.trading.security.error_mapping import TradingMappedError
from app.utils.logger import logger
from app.utils.standard import canonical_json
from pydantic import model_validator

if TYPE_CHECKING:
    from app.services.trading.gates.policy_matrix import PolicyMatrixEntry

MIN_DUAL_APPROVAL_TOKENS = 2

HARD_DUAL_APPROVAL_ACTION_IDS = frozenset(
    {
        "clear_global_kill_switch",
        "promote_to_full_live",
        "raise_hard_cap",
    }
)


class ApprovalScope(TradingContract):
    """Account/strategy/symbol scope for approval matching.

    Attributes:
        account_id: Optional account identifier.
        strategy_id: Optional strategy identifier.
        symbol: Optional instrument symbol.
    """

    account_id: str | None = None
    strategy_id: str | None = None
    symbol: str | None = None


class OperatorApprovalToken(TradingContract):
    """Single-operator approval evidence token.

    Attributes:
        approval_id: Unique approval token identifier.
        operator_id: Authenticated operator identifier.
        governed_action_id: Identifier of the governed action this approval
            authorizes (e.g. a `TradingAction` value or a governance action
            such as ``clear_global_kill_switch``).
        scope: Account/strategy/symbol scope this approval is bounded to.
            Unset fields are treated as unrestricted for that dimension.
        canonical_request_hash: Canonical hash of the order parameters this
            approval was issued for.
        issued_at: UTC issuance timestamp.
        expires_at: UTC expiry timestamp.
        revoked: Whether this approval has been revoked.
        consumed: Whether this single-use approval has already been consumed.
    """

    approval_id: str
    operator_id: str
    governed_action_id: str
    scope: ApprovalScope
    canonical_request_hash: str
    issued_at: str
    expires_at: str
    revoked: bool = False
    consumed: bool = False

    @model_validator(mode="after")
    def validate_token(self) -> OperatorApprovalToken:
        """Validate operator approval token identifiers.

        Returns:
            OperatorApprovalToken: Validated approval token.

        Raises:
            ValueError: If any required identifier field is blank.
        """
        logger.info("Validating operator approval token {}.", self.approval_id)
        for field_name in (
            "approval_id",
            "operator_id",
            "governed_action_id",
            "canonical_request_hash",
            "issued_at",
            "expires_at",
        ):
            if not getattr(self, field_name).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self


class RiskDecisionEvidence(TradingContract):
    """Risk decision signature evidence bound to one order request.

    Attributes:
        risk_decision_id: Unique risk decision identifier.
        canonical_request_hash: Canonical hash of the order parameters this
            decision was issued for.
        issued_at: UTC issuance timestamp.
        expires_at: UTC expiry timestamp.
        revoked: Whether this risk decision has been revoked.
    """

    risk_decision_id: str
    canonical_request_hash: str
    issued_at: str
    expires_at: str
    revoked: bool = False

    @model_validator(mode="after")
    def validate_evidence(self) -> RiskDecisionEvidence:
        """Validate risk decision evidence identifiers.

        Returns:
            RiskDecisionEvidence: Validated risk decision evidence.

        Raises:
            ValueError: If any required identifier field is blank.
        """
        logger.info("Validating risk decision evidence {}.", self.risk_decision_id)
        for field_name in (
            "risk_decision_id",
            "canonical_request_hash",
            "issued_at",
            "expires_at",
        ):
            if not getattr(self, field_name).strip():
                message = f"{field_name} must be non-empty."
                raise ValueError(message)
        return self


def compute_canonical_request_hash(
    *,
    symbol: str,
    account_id: str,
    side: str,
    volume: str,
    price: str | None,
    sl: str | None,
    tp: str | None,
    route: str,
    strategy_id: str,
) -> str:
    """Compute the canonical SHA-256 request-binding hash (TRD-FR-091).

    Args:
        symbol: Instrument symbol.
        account_id: Account identifier.
        side: Trade direction.
        volume: Requested volume, as a canonical string.
        price: Requested price, as a canonical string, if any.
        sl: Stop-loss price, as a canonical string, if any.
        tp: Take-profit price, as a canonical string, if any.
        route: Requested runtime route.
        strategy_id: Owning strategy identifier.

    Returns:
        str: SHA-256 hex digest of the canonical order parameters.
    """
    logger.info("Computing canonical request hash for {}.", symbol)
    payload: JsonObject = {
        "symbol": symbol,
        "account_id": account_id,
        "side": side,
        "volume": volume,
        "price": price,
        "sl": sl,
        "tp": tp,
        "route": route,
        "strategy_id": strategy_id,
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    logger.debug("Computed canonical request hash {}.", digest)
    return digest


def _parse_utc(value: str) -> datetime:
    """Parse an ISO-8601 timestamp, defaulting a naive value to UTC.

    Args:
        value: ISO-8601 timestamp string.

    Returns:
        datetime: Timezone-aware UTC datetime.
    """
    logger.debug("Parsing UTC timestamp {}.", value)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _scope_matches(
    *, token_scope: ApprovalScope, expected_scope: ApprovalScope
) -> bool:
    """Return whether a token's scope is compatible with the expected scope.

    Args:
        token_scope: Approval token scope. Unset fields are unrestricted.
        expected_scope: Scope of the incoming request.

    Returns:
        bool: True when every restricted token scope dimension matches.
    """
    logger.debug("Comparing approval token scope to expected scope.")
    if token_scope.account_id is not None:
        if token_scope.account_id != expected_scope.account_id:
            return False
    if token_scope.strategy_id is not None:
        if token_scope.strategy_id != expected_scope.strategy_id:
            return False
    if token_scope.symbol is not None:
        if token_scope.symbol != expected_scope.symbol:
            return False
    return True


def validate_operator_approval(
    *,
    token: OperatorApprovalToken,
    now: datetime,
    expected_request_hash: str,
    expected_scope: ApprovalScope,
) -> None:
    """Validate one operator approval token before a governed action (TRD-FR-090).

    Args:
        token: Operator approval token.
        now: Current UTC timestamp from an injected Clock.
        expected_request_hash: Canonical hash of the incoming order request.
        expected_scope: Scope of the incoming request.

    Raises:
        TradingMappedError: If the token is revoked, consumed, expired,
            request-hash mismatched, or scope mismatched.
    """
    logger.info(
        "Validating operator approval {} for operator {}.",
        token.approval_id,
        token.operator_id,
    )
    if token.revoked:
        raise TradingMappedError(
            "Operator approval token has been revoked.",
            code="APPROVAL_TOKEN_REVOKED",
            details={"approval_id": token.approval_id},
        )
    if token.consumed:
        raise TradingMappedError(
            "Operator approval token has already been consumed.",
            code="APPROVAL_TOKEN_CONSUMED",
            details={"approval_id": token.approval_id},
        )
    if now > _parse_utc(token.expires_at):
        raise TradingMappedError(
            "Operator approval token has expired.",
            code="APPROVAL_TOKEN_EXPIRED",
            details={"approval_id": token.approval_id},
        )
    if token.canonical_request_hash != expected_request_hash:
        raise TradingMappedError(
            "Operator approval token does not match the request.",
            code="APPROVAL_TOKEN_INVALID",
            details={"approval_id": token.approval_id},
        )
    if not _scope_matches(token_scope=token.scope, expected_scope=expected_scope):
        raise TradingMappedError(
            "Operator approval token scope does not match the request.",
            code="APPROVAL_TOKEN_INVALID",
            details={"approval_id": token.approval_id},
        )
    logger.debug("Operator approval {} validated successfully.", token.approval_id)


def requires_dual_approval(
    *,
    governed_action_id: str,
    matrix_entry: PolicyMatrixEntry | None = None,
) -> bool:
    """Return whether a governed action requires dual-operator approval.

    Clearing a global kill switch, promotion to ``full_live``, and raising
    any hard cap always require dual approval, independent of policy matrix
    configuration (TRD-FR-092).

    Args:
        governed_action_id: Governed action identifier.
        matrix_entry: Optional resolved policy matrix entry for this action.

    Returns:
        bool: True when two distinct operator approvals are required.
    """
    logger.info("Checking dual-approval requirement for {}.", governed_action_id)
    if governed_action_id in HARD_DUAL_APPROVAL_ACTION_IDS:
        return True
    if matrix_entry is not None:
        return matrix_entry.requires_dual_approval
    return False


def validate_dual_operator_approval(
    *,
    tokens: tuple[OperatorApprovalToken, ...],
    now: datetime,
    expected_request_hash: str,
    expected_scope: ApprovalScope,
) -> None:
    """Validate dual-operator approval evidence (TRD-FR-092).

    Args:
        tokens: Approval tokens presented for this governed action.
        now: Current UTC timestamp from an injected Clock.
        expected_request_hash: Canonical hash of the incoming order request.
        expected_scope: Scope of the incoming request.

    Raises:
        TradingMappedError: If fewer than two tokens are presented, the
            tokens do not carry two distinct operator IDs, or any individual
            token fails validation.
    """
    logger.info("Validating dual-operator approval for {} token(s).", len(tokens))
    if len(tokens) < MIN_DUAL_APPROVAL_TOKENS:
        raise TradingMappedError(
            "Dual-operator approval requires two distinct operator tokens.",
            code="APPROVAL_REQUIRED",
        )
    distinct_operators = {token.operator_id for token in tokens}
    if len(distinct_operators) < MIN_DUAL_APPROVAL_TOKENS:
        raise TradingMappedError(
            "Dual-operator approval requires two distinct operators.",
            code="APPROVAL_REQUIRED",
        )
    for token in tokens:
        validate_operator_approval(
            token=token,
            now=now,
            expected_request_hash=expected_request_hash,
            expected_scope=expected_scope,
        )
    logger.debug(
        "Dual-operator approval validated for {} operators.", len(distinct_operators)
    )


def validate_risk_decision(
    *,
    evidence: RiskDecisionEvidence,
    now: datetime,
    expected_request_hash: str,
) -> None:
    """Validate risk decision signature evidence (gate 7).

    Args:
        evidence: Risk decision evidence.
        now: Current UTC timestamp from an injected Clock.
        expected_request_hash: Canonical hash of the incoming order request.

    Raises:
        TradingMappedError: If the evidence is revoked, expired, or
            request-hash mismatched.
    """
    logger.info("Validating risk decision {}.", evidence.risk_decision_id)
    if evidence.revoked:
        raise TradingMappedError(
            "Risk decision evidence has been revoked.",
            code="APPROVAL_TOKEN_REVOKED",
            details={"risk_decision_id": evidence.risk_decision_id},
        )
    if now > _parse_utc(evidence.expires_at):
        raise TradingMappedError(
            "Risk decision evidence has expired.",
            code="APPROVAL_TOKEN_EXPIRED",
            details={"risk_decision_id": evidence.risk_decision_id},
        )
    if evidence.canonical_request_hash != expected_request_hash:
        raise TradingMappedError(
            "Risk decision evidence does not match the request.",
            code="APPROVAL_TOKEN_INVALID",
            details={"risk_decision_id": evidence.risk_decision_id},
        )
    logger.debug("Risk decision {} validated successfully.", evidence.risk_decision_id)

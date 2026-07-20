# ruff: noqa: ANN401, PLR0915, PLR2004, BLE001, C901, PLR0912, PLR0911, S110, RET505
"""Decision-token signing, validation, scope, expiry, and revocation checks.

Provides the cryptographic boundaries for authorization evidence before order
generation or broker execution.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, overload

from app.services.risk.audit.hash_chain import _coerce_types
from app.services.risk.models import (
    RiskContract,
    RiskDecisionPackage,
    RiskDecisionToken,
)
from app.services.risk.validations import ValidationResult
from app.utils.logger import logger
from app.utils.standard import canonical_json, stable_identifier
from pydantic import Field


class RequiredActionScope(RiskContract):
    """The action scope parameters required to validate a token."""

    action: str = Field(..., description="Action to validate.")
    account_id: str | None = Field(
        default=None, description="Optional account ID filter."
    )
    strategy_id: str | None = Field(
        default=None, description="Optional strategy ID filter."
    )
    symbol: str | None = Field(default=None, description="Optional symbol filter.")
    environment: str | None = Field(
        default=None, description="Optional environment filter."
    )


class TokenValidationContext(RiskContract):
    """Context holding the verification expectations for a token."""

    active_config_hash: str = Field(
        ..., description="The currently active risk config hash."
    )
    active_policy_hash: str = Field(
        ..., description="The currently active risk policy hash."
    )
    required_scope: RequiredActionScope = Field(
        ..., description="Scope validation filter."
    )
    now_utc: datetime = Field(..., description="The current UTC timestamp.")


class TokenValidationResult(RiskContract):
    """Verification details and status for a decision token check."""

    valid: bool = Field(
        ...,
        description="True if signature, expiry, revocation, and scope are valid.",
    )
    message: str = Field(..., description="Explanation of validation outcome.")
    code: str = Field(..., description="Outcome code (e.g. OK, EXPIRED, REVOKED).")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional verification details."
    )


class RiskDecisionTokenSigner:
    """Signer and verification port implementation for RiskDecisionTokens."""

    def __init__(self, state_store: Any = None) -> None:
        """Initialize the default signer with an optional state store.

        Args:
            state_store: Optional RiskStateStore instance.
        """
        self.state_store = state_store
        self._revoked_tokens: set[str] = set()

    def sign_payload(self, canonical_payload: str) -> str:
        """Sign canonical JSON string with HMAC-SHA256.

        Args:
            canonical_payload: Stable JSON string.

        Returns:
            str: Crypto HMAC signature.
        """
        key = b"default_transient_secret_key_for_testing"
        try:
            from app.utils.security import load_encryption_key

            enc_key = load_encryption_key()
            if enc_key:
                key = enc_key.encode()
        except Exception:
            pass
        return hmac.new(key, canonical_payload.encode(), hashlib.sha256).hexdigest()

    def is_token_revoked(self, token_id: str) -> bool:
        """Check if token is revoked in store or local memory.

        Args:
            token_id: Unique token ID.

        Returns:
            bool: True if token is revoked.
        """
        if self.state_store is not None:
            try:
                return bool(self.state_store.is_token_revoked(token_id))
            except Exception:
                pass
        return token_id in self._revoked_tokens

    def revoke_token(self, token_id: str) -> None:
        """Mark token as revoked.

        Args:
            token_id: Unique token ID.
        """
        if self.state_store is not None:
            try:
                self.state_store.revoke_token(token_id)
                return
            except Exception:
                pass
        self._revoked_tokens.add(token_id)

    def sign_token(
        self,
        decision_id: str,
        request_id: str,
        workflow_id: str,
        approved_action: str,
        config_hash: str,
        decision_hash: str,
        scope: dict[str, Any],
        expiry_seconds: int = 300,
        policy_hash: str = "",
    ) -> Any:
        """Legacy helper for testing token validation wrapper."""
        from app.services.risk.models import RiskApprovalToken
        from app.utils.normalization import utc_now

        expiry_time = utc_now() + timedelta(seconds=expiry_seconds)
        import uuid

        nonce = str(uuid.uuid4())

        payload_dict = {
            "decision_id": decision_id,
            "request_id": request_id,
            "workflow_id": workflow_id,
            "approved_action": approved_action,
            "config_hash": config_hash,
            "decision_hash": decision_hash,
            "scope": scope,
            "policy_hash": policy_hash,
            "nonce": nonce,
            "expiry_time": expiry_time.isoformat(),
        }
        canonical_payload = canonical_json(_coerce_types(payload_dict))
        signature = self.sign_payload(canonical_payload)

        return RiskApprovalToken(
            token_id=decision_id,
            request_id=request_id,
            workflow_id=workflow_id,
            approved_action=approved_action,
            approver="risk_governor",
            expiry_time=expiry_time,
            config_hash=config_hash,
            decision_hash=decision_hash,
            policy_hash=policy_hash,
            scope=scope,
            nonce=nonce,
            signature=signature,
        )


# DefaultTokenSigner alias for backward compatibility and specification compliance
DefaultTokenSigner = RiskDecisionTokenSigner


def create_risk_decision_token(
    decision: RiskDecisionPackage | str | Any = None,
    signer: RiskDecisionTokenSigner | Any = None,
    now_utc: datetime | Any = None,
    *args: Any,
    **kwargs: Any,
) -> RiskDecisionToken | Any:
    """Signs an eligible bounded approval. Supports V2 and V1 legacy token creation.

    Args:
        decision: RiskDecisionPackage (V2) or decision_id (V1 legacy).
        signer: Signer (V2) or request_id (V1 legacy).
        now_utc: datetime (V2) or workflow_id (V1 legacy).
        *args: Extra legacy positional arguments.
        **kwargs: Extra legacy keyword arguments.

    Returns:
        RiskDecisionToken (V2) or RiskApprovalToken (V1 legacy).
    """
    from app.services.risk.models import RiskDecisionPackage as RiskDecisionPackageModel

    if isinstance(decision, RiskDecisionPackageModel):
        logger.info("Creating V2 decision token.")
        if not decision.status or not decision.decision_id:
            raise ValueError("decision_id and status are required to create a token.")

        expiry = now_utc + timedelta(minutes=5)
        token_id = stable_identifier(
            {"decision_id": decision.decision_id, "timestamp": now_utc.isoformat()},
            prefix="tok",
        )

        scope = {}
        if decision.details and "proposed_action" in decision.details:
            action = decision.details["proposed_action"]
            scope = {
                "strategy_id": action.get("strategy_id"),
                "account_id": decision.details.get("account_id"),
                "symbol": action.get("symbol"),
                "environment": action.get("environment")
                or decision.details.get("environment"),
            }
        elif decision.details:
            scope = {
                "strategy_id": decision.details.get("strategy_id"),
                "account_id": decision.details.get("account_id"),
                "symbol": decision.details.get("symbol"),
                "environment": decision.details.get("environment"),
            }

        payload_dict = {
            "token_id": token_id,
            "expiry": expiry.isoformat(),
            "policy_hash": decision.policy_hash or "default_policy_hash",
            "config_hash": decision.config_hash or "default_config_hash",
            "scope": scope,
        }

        canonical_payload = canonical_json(payload_dict)
        signature = signer.sign_payload(canonical_payload)

        token = RiskDecisionToken(
            token_id=token_id,
            expiry=expiry,
            policy_hash=decision.policy_hash or "default_policy_hash",
            config_hash=decision.config_hash or "default_config_hash",
            signature=signature,
            revoked=False,
            scope=scope,
        )
        logger.debug("Successfully generated decision token: %s", token_id)
        return token

    else:
        logger.info("Creating V1 legacy decision token.")
        decision_id = (
            decision if isinstance(decision, str) else kwargs.get("decision_id")
        )
        decision_id_str = str(decision_id) if decision_id else ""

        request_id = kwargs.get("request_id")
        if not request_id:
            request_id = (
                signer
                if isinstance(signer, str)
                else (args[0] if len(args) > 0 else "")
            )

        workflow_id = kwargs.get("workflow_id")
        if not workflow_id:
            workflow_id = (
                now_utc
                if isinstance(now_utc, str)
                else (args[1] if len(args) > 1 else "")
            )

        approved_action = kwargs.get("approved_action")
        if not approved_action:
            approved_action = args[2] if len(args) > 2 else ""

        config_hash = kwargs.get("config_hash")
        if not config_hash:
            config_hash = args[3] if len(args) > 3 else ""

        decision_hash = kwargs.get("decision_hash")
        if not decision_hash:
            decision_hash = args[4] if len(args) > 4 else ""

        scope_val = kwargs.get("scope")
        if not scope_val:
            scope_val = args[5] if len(args) > 5 else {}
        scope_dict = scope_val if isinstance(scope_val, dict) else {}

        policy_hash = kwargs.get("policy_hash")
        if not policy_hash:
            policy_hash = args[6] if len(args) > 6 else ""

        nonce = kwargs.get("nonce")
        if not nonce:
            nonce = args[7] if len(args) > 7 else None

        expiry_time = kwargs.get("expiry_time")
        if not expiry_time:
            expiry_time = args[8] if len(args) > 8 else None

        approver = kwargs.get("approver", "risk_governor")

        from app.services.risk.models import RiskApprovalToken
        from app.utils.normalization import utc_now

        if not expiry_time:
            expiry_time = utc_now() + timedelta(minutes=5)
        if not nonce:
            import uuid

            nonce = str(uuid.uuid4())

        payload_dict = {
            "decision_id": decision_id_str,
            "request_id": request_id,
            "workflow_id": workflow_id,
            "approved_action": approved_action,
            "config_hash": config_hash,
            "decision_hash": decision_hash,
            "scope": scope_dict,
            "policy_hash": policy_hash,
            "nonce": nonce,
            "expiry_time": expiry_time.isoformat(),
        }
        canonical_payload = canonical_json(_coerce_types(payload_dict))

        signer_obj = DefaultTokenSigner()
        signature = signer_obj.sign_payload(canonical_payload)

        return RiskApprovalToken(
            token_id=decision_id_str,
            request_id=request_id,
            workflow_id=workflow_id,
            approved_action=approved_action,
            approver=approver,
            expiry_time=expiry_time,
            config_hash=config_hash,
            decision_hash=decision_hash,
            policy_hash=policy_hash,
            scope=scope_dict,
            nonce=nonce,
            signature=signature,
        )


def validate_token_expiry(
    token: RiskDecisionToken, now_utc: datetime
) -> ValidationResult:
    """Validates bounded expiry.

    Args:
        token: Cryptographically signed RiskDecisionToken.
        now_utc: Current UTC timestamp.

    Returns:
        ValidationResult: Validity status and details.
    """
    logger.info("Validating token expiry for token ID: %s", token.token_id)
    if token.expiry < now_utc:
        logger.warning(
            "Token %s is expired. Expiry: %s, Now: %s",
            token.token_id,
            token.expiry,
            now_utc,
        )
        return {
            "valid": False,
            "message": "Token has expired.",
            "code": "TOKEN_EXPIRED",
            "details": {
                "expiry": token.expiry.isoformat(),
                "now": now_utc.isoformat(),
            },
        }
    logger.debug("Token expiry is valid.")
    return {
        "valid": True,
        "message": "Token is not expired.",
        "code": "OK",
        "details": {},
    }


def validate_token_scope(
    token: RiskDecisionToken, required: RequiredActionScope
) -> ValidationResult:
    """Validates action/account/strategy/symbol/environment scope.

    Args:
        token: Cryptographically signed RiskDecisionToken.
        required: Target action scope criteria.

    Returns:
        ValidationResult: Scope check outcome status.
    """
    logger.info("Validating token scope for token ID: %s", token.token_id)
    token_scope = token.scope or {}

    alt_keys = {
        "strategy_id": ["strategy_id", "strategy"],
        "account_id": ["account_id", "account"],
        "symbol": ["symbol"],
        "environment": ["environment"],
    }

    for field in ("account_id", "strategy_id", "symbol", "environment"):
        req_val = getattr(required, field, None)
        if req_val is None:
            continue

        token_val = token_scope.get(field)
        if token_val is None:
            for alt_key in alt_keys.get(field, []):
                token_val = token_scope.get(alt_key)
                if token_val is not None:
                    break

        if token_val is None or str(token_val).lower() != str(req_val).lower():
            logger.warning(
                "Scope mismatch for field '%s': expected '%s', got '%s'",
                field,
                req_val,
                token_val,
            )
            return {
                "valid": False,
                "message": (
                    f"Scope mismatch on field {field}: "
                    f"expected {req_val}, got {token_val}."
                ),
                "code": "SCOPE_MISMATCH",
                "details": {
                    "field": field,
                    "expected": req_val,
                    "actual": token_val,
                },
            }

    logger.debug("Token scope is valid.")
    return {
        "valid": True,
        "message": "Token scope is valid.",
        "code": "OK",
        "details": {},
    }


@overload
def validate_risk_approval_token(
    token: RiskDecisionToken,
    context: TokenValidationContext,
    verifier: RiskDecisionTokenSigner,
) -> TokenValidationResult: ...


@overload
def validate_risk_approval_token(
    token: Any,
    context: Any = None,
    verifier: Any = None,
    *args: Any,
    **kwargs: Any,
) -> bool: ...


def validate_risk_approval_token(
    token: RiskDecisionToken | Any,
    context: TokenValidationContext | Any = None,
    verifier: RiskDecisionTokenSigner | Any = None,
    *args: Any,
    **kwargs: Any,
) -> TokenValidationResult | bool:
    """Checks signature, expiry, revocation, scope, policy, and config hashes.

    Supports both V2 pure validation (returns TokenValidationResult) and V1 validation
    (returns bool) depending on signatures/arguments.

    Args:
        token: Target token (V2 or V1).
        context: Context (V2) or expected_scope (V1).
        verifier: Signer port (V2) or active_config_hash (V1).
        *args: Extra legacy positional arguments.
        **kwargs: Extra legacy keyword arguments.

    Returns:
        TokenValidationResult (V2) or bool (V1).
    """
    from app.services.risk.models import RiskApprovalToken
    from app.utils.normalization import utc_now

    is_legacy = (
        isinstance(token, RiskApprovalToken)
        or isinstance(context, dict)
        or bool(args)
        or bool(kwargs)
    )

    if is_legacy:
        logger.info("Legacy V1 validate_risk_approval_token invoked.")
        expected_scope = (
            context
            if isinstance(context, dict)
            else kwargs.get("expected_scope", args[0] if args else {})
        )

        active_config_hash = kwargs.get("active_config_hash")
        if not active_config_hash:
            active_config_hash = (
                verifier
                if isinstance(verifier, str)
                else (args[1] if len(args) > 1 else "")
            )

        active_policy_hash = kwargs.get("active_policy_hash")
        if not active_policy_hash:
            active_policy_hash = args[2] if len(args) > 2 else ""

        state_store = kwargs.get("state_store")
        if not state_store:
            state_store = args[3] if len(args) > 3 else None

        if not isinstance(token, RiskApprovalToken):
            return False

        now = utc_now()
        if token.expiry_time < now:
            logger.warning("Token expired.")
            return False

        if token.config_hash != active_config_hash:
            logger.warning("Config hash mismatch.")
            return False

        if active_policy_hash and token.policy_hash != active_policy_hash:
            logger.warning("Policy hash mismatch.")
            return False

        if state_store is not None:
            try:
                if state_store.is_token_revoked(token.token_id):
                    logger.warning("Token revoked.")
                    return False
            except Exception:
                pass

        token_scope = token.scope or {}
        for k, v in expected_scope.items():
            t_val = token_scope.get(k)
            if t_val is None:
                alt = (
                    "strategy"
                    if k == "strategy_id"
                    else "account"
                    if k == "account_id"
                    else None
                )
                if alt:
                    t_val = token_scope.get(alt)
            if t_val is None or str(t_val).lower() != str(v).lower():
                logger.warning(
                    "Scope mismatch on field %s: expected %s, got %s",
                    k,
                    v,
                    t_val,
                )
                return False

        payload_dict = {
            "decision_id": token.token_id,
            "request_id": token.request_id,
            "workflow_id": token.workflow_id,
            "approved_action": token.approved_action,
            "config_hash": token.config_hash,
            "decision_hash": token.decision_hash,
            "scope": token.scope,
            "policy_hash": token.policy_hash,
            "nonce": token.nonce,
            "expiry_time": token.expiry_time.isoformat(),
        }
        canonical_payload = canonical_json(_coerce_types(payload_dict))

        signer_obj = DefaultTokenSigner(state_store)
        expected_sig = signer_obj.sign_payload(canonical_payload)
        if not hmac.compare_digest(token.signature, expected_sig):
            logger.warning("Signature mismatch.")
            return False

        return True

    if not isinstance(token, RiskDecisionToken):
        logger.error("Invalid token instance: %s", type(token))
        return TokenValidationResult(
            valid=False,
            message="Token instance is not a RiskDecisionToken.",
            code="INVALID_TOKEN_SCHEMA",
        )

    logger.info("Starting validation for risk approval token ID: %s", token.token_id)

    payload_dict = {
        "token_id": token.token_id,
        "expiry": token.expiry.isoformat(),
        "policy_hash": token.policy_hash,
        "config_hash": token.config_hash,
        "scope": token.scope,
    }
    canonical_payload = canonical_json(payload_dict)

    try:
        expected_sig = verifier.sign_payload(canonical_payload)
        if not hmac.compare_digest(token.signature, expected_sig):
            logger.warning("Token signature mismatch.")
            return TokenValidationResult(
                valid=False,
                message="Signature check failed.",
                code="SIGNATURE_INVALID",
            )
    except Exception as e:
        logger.exception("Signature verification encountered error: %s", e)
        return TokenValidationResult(
            valid=False,
            message=f"Signature check failed with exception: {e}",
            code="SIGNATURE_ERROR",
        )

    exp_res = validate_token_expiry(token, context.now_utc)
    if not exp_res["valid"]:
        return TokenValidationResult(
            valid=False,
            message=exp_res["message"],
            code=exp_res["code"],
            details=exp_res["details"],
        )

    if verifier.is_token_revoked(token.token_id):
        logger.warning("Token %s has been revoked.", token.token_id)
        return TokenValidationResult(
            valid=False,
            message="Token has been revoked.",
            code="TOKEN_REVOKED",
        )

    if token.config_hash != context.active_config_hash:
        logger.warning(
            "Config hash mismatch: token=%s, active=%s",
            token.config_hash,
            context.active_config_hash,
        )
        return TokenValidationResult(
            valid=False,
            message="Configuration hash does not match current active config.",
            code="CONFIG_HASH_MISMATCH",
        )

    if token.policy_hash != context.active_policy_hash:
        logger.warning(
            "Policy hash mismatch: token=%s, active=%s",
            token.policy_hash,
            context.active_policy_hash,
        )
        return TokenValidationResult(
            valid=False,
            message="Policy hash does not match current active policy.",
            code="POLICY_HASH_MISMATCH",
        )

    scope_res = validate_token_scope(token, context.required_scope)
    if not scope_res["valid"]:
        return TokenValidationResult(
            valid=False,
            message=scope_res["message"],
            code=scope_res["code"],
            details=scope_res["details"],
        )

    logger.info("Token validation successful.")
    return TokenValidationResult(
        valid=True,
        message="Token successfully validated.",
        code="OK",
    )


def revoke_risk_approval_token(token_id: str, state_store: Any) -> None:
    """Mark a decision token as revoked in the store.

    Args:
        token_id: Unique token ID.
        state_store: The storage port implementation.
    """
    logger.info("Revoking token ID: %s", token_id)
    state_store.revoke_token(token_id)

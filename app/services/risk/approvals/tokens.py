"""Signed, scoped, durable Risk approval-token lifecycle."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from time import monotonic
from typing import TYPE_CHECKING, NoReturn

from app.services.risk.config import RiskConfig, compute_config_hash
from app.services.risk.contracts import (
    ActionPolicyVerdict,
    ApprovalAttestation,
    ApprovalValidationResult,
    DecisionState,
    RiskApprovalToken,
    RiskAuditRecord,
    RiskDecisionPackage,
    RiskDomainError,
    RiskErrorCode,
)
from app.utils import canonical_json, logger

if TYPE_CHECKING:
    from app.services.risk.approvals.state import _TokenStateStore
    from app.services.risk.audit import RiskAuditChain

_MINIMUM_SIGNING_KEY_BYTES = 32
_EXPECTED_FIXED_KEYS = frozenset(
    {
        "action",
        "decision_id",
        "config_hash",
        "request_id",
        "workflow_id",
        "correlation_id",
    }
)


def _utc(value: datetime) -> datetime:
    """Require an aware UTC timestamp.

    Args:
        value: Timestamp to validate.

    Returns:
        Validated timestamp.

    Raises:
        ValueError: If the timestamp is not aware UTC.
    """
    logger.debug("Validating approval-token UTC timestamp")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("approval-token time must be aware UTC")
    return value


def _hash_identity(*parts: str) -> str:
    """Derive a lowercase SHA-256 identity from exact text parts.

    Args:
        *parts: Ordered identity material.

    Returns:
        Lowercase hexadecimal identity.
    """
    logger.debug("Deriving a Risk approval lifecycle identity")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _validate_dependencies(
    config: RiskConfig,
    clock: Callable[[], datetime],
    secret_resolver: Callable[[str], bytes],
    authorization_verifier: Callable[[ApprovalAttestation], bool],
) -> None:
    """Validate approval service policy and injected callables.

    Args:
        config: Active Risk policy.
        clock: Injected UTC clock.
        secret_resolver: Injected signing-key resolver.
        authorization_verifier: Injected authorization verifier.

    Raises:
        TypeError: If an injected verifier is not callable.
        ValueError: If algorithm or clock policy is invalid.
    """
    logger.debug("Validating Risk approval service dependencies")
    if config.approval_signing_algorithm != "hmac-sha256":
        raise ValueError("unsupported approval signing algorithm")
    _utc(clock())
    if not callable(secret_resolver) or not callable(authorization_verifier):
        raise TypeError("approval verification dependencies must be callable")


def _validate_clock_skew(
    now: datetime, clock_now: datetime, tolerance: timedelta
) -> None:
    """Validate operation time against an injected clock.

    Args:
        now: Checked caller time.
        clock_now: Checked injected-clock time.
        tolerance: Maximum permitted absolute skew.

    Raises:
        ValueError: If clock skew exceeds policy.
    """
    logger.debug("Validating Risk approval operation clock skew")
    if abs(now - clock_now) > tolerance:
        raise ValueError("approval operation clock skew exceeded")


def _validate_signing_key(key: object) -> bytes:
    """Validate minimum signing-key type and strength.

    Args:
        key: Resolved secret value.

    Returns:
        Valid signing-key bytes.

    Raises:
        ValueError: If key material is absent or too short.
    """
    logger.debug("Validating resolved Risk approval signing material")
    if not isinstance(key, bytes) or len(key) < _MINIMUM_SIGNING_KEY_BYTES:
        raise ValueError("approval signing key is invalid")
    return key


def _token_material(
    values: Mapping[str, object], attestation: ApprovalAttestation
) -> str:
    """Serialize the exact token and approval evidence signing material.

    Args:
        values: Token fields excluding signature.
        attestation: Authenticated approval evidence bound to the token.

    Returns:
        Canonical JSON signing material.
    """
    logger.debug("Serializing exact Risk approval-token signing material")
    material = dict(values)
    material["attestation_id"] = attestation.attestation_id
    material["policy_ref"] = attestation.policy_ref
    return canonical_json(material)


def _audit_record(
    *,
    record_id: str,
    event_type: str,
    payload: Mapping[str, object],
    evidence_refs: Mapping[str, str],
    config_hash: str,
    decision_id: str | None,
    occurred_at: datetime,
    request_id: str,
    correlation_id: str,
) -> RiskAuditRecord:
    """Build one unsealed material approval lifecycle audit record.

    Args:
        record_id: Stable audit identity.
        event_type: Material lifecycle event name.
        payload: Secret-safe event facts.
        evidence_refs: Exact evidence identities.
        config_hash: Applicable Risk configuration hash.
        decision_id: Optional bound Risk decision identity.
        occurred_at: Checked UTC event time.
        request_id: Bound request identity.
        correlation_id: Bound correlation identity.

    Returns:
        Unsealed audit record.
    """
    logger.debug("Building one Risk approval lifecycle audit record")
    return RiskAuditRecord(
        record_id=record_id,
        event_type=event_type,
        payload=dict(payload),
        evidence_refs=dict(evidence_refs),
        config_hash=config_hash,
        decision_id=decision_id,
        occurred_at=occurred_at,
        sequence=None,
        previous_hash=None,
        record_hash=None,
        sealed=False,
        request_id=request_id,
        correlation_id=correlation_id,
    )


class ApprovalTokenService:
    """Coordinate signed approval issuance and atomic durable consumption."""

    def __init__(
        self,
        config: RiskConfig,
        state: _TokenStateStore,
        audit: RiskAuditChain,
        clock: Callable[[], datetime],
        secret_resolver: Callable[[str], bytes],
        authorization_verifier: Callable[[ApprovalAttestation], bool],
    ) -> None:
        """Initialize a fail-closed approval-token coordinator.

        Args:
            config: Immutable active Risk policy.
            state: Injected atomic durable token-state port.
            audit: Injected tamper-evident Risk audit chain.
            clock: Injected aware UTC clock.
            secret_resolver: Injected signing-key resolver.
            authorization_verifier: Injected approver authorization verifier.

        Raises:
            RiskDomainError: If dependencies or signing policy are invalid.
        """
        logger.info("Initializing durable Risk approval-token service")
        try:
            _validate_dependencies(
                config, clock, secret_resolver, authorization_verifier
            )
        except (TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.INVALID_RISK_CONFIG,
                "approval-token service configuration invalid",
            ) from error
        self._config = config
        self._state = state
        self._audit = audit
        self._clock = clock
        self._secret_resolver = secret_resolver
        self._authorization_verifier = authorization_verifier

    def _checked_now(self, now: datetime) -> datetime:
        """Validate supplied time against the injected service clock.

        Args:
            now: Caller-supplied UTC operation time.

        Returns:
            Checked UTC operation time.

        Raises:
            RiskDomainError: If time is invalid or exceeds allowed skew.
        """
        logger.debug("Checking approval operation time against service clock")
        try:
            checked = _utc(now)
            clock_now = _utc(self._clock())
            tolerance = timedelta(
                seconds=float(self._config.clock_skew_tolerance_seconds or 0)
            )
            _validate_clock_skew(checked, clock_now, tolerance)
            return checked
        except (TypeError, ValueError) as error:
            raise RiskDomainError(
                RiskErrorCode.APPROVAL_TOKEN_INVALID,
                "approval operation time invalid",
            ) from error

    def _signing_key(self) -> bytes:
        """Resolve and validate signing key material without retaining it.

        Returns:
            Ephemeral signing-key bytes.

        Raises:
            RiskDomainError: If secret resolution fails or is unsafe.
        """
        logger.debug("Resolving ephemeral Risk approval signing material")
        try:
            return _validate_signing_key(
                self._secret_resolver(self._config.approval_signing_key_ref)
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR,
                "approval signing material unavailable",
            ) from error

    def _signature(
        self, values: Mapping[str, object], attestation: ApprovalAttestation
    ) -> str:
        """Compute an HMAC-SHA-256 signature over exact bound material.

        Args:
            values: Token fields excluding signature.
            attestation: Approval evidence bound into the signature.

        Returns:
            Lowercase hexadecimal HMAC signature.
        """
        logger.debug("Signing exact Risk approval-token material")
        key = self._signing_key()
        return hmac.new(
            key,
            _token_material(values, attestation).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _authorized_attestation(
        self,
        decision: RiskDecisionPackage,
        attestation: ApprovalAttestation,
        now: datetime,
    ) -> bool:
        """Check exact decision, policy, identity, scope, and time bindings.

        Args:
            decision: Eligible Risk decision.
            attestation: UI/API-produced approval evidence.
            now: Checked UTC operation time.

        Returns:
            Whether all bindings and external authorization are valid.
        """
        logger.debug("Verifying exact approval attestation bindings")
        current_hash = compute_config_hash(self._config)
        return (
            decision.state is DecisionState.APPROVE
            and decision.token is None
            and decision.config_hash == current_hash
            and decision.issued_at <= now < decision.expires_at
            and attestation.issued_at <= now < attestation.expires_at
            and attestation.policy_ref == decision.config_hash
            and attestation.policy_version == self._config.policy_version
            and attestation.request_id == decision.request_id
            and attestation.workflow_id == decision.workflow_id
            and attestation.correlation_id == decision.correlation_id
            and bool(attestation.action.strip())
            and not (_EXPECTED_FIXED_KEYS & set(attestation.scope))
            and self._authorization_verifier(attestation)
        )

    def issue(
        self,
        decision: RiskDecisionPackage,
        attestation: ApprovalAttestation,
        *,
        now: datetime,
    ) -> RiskApprovalToken:
        """Issue and durably record one eligible signed scoped token.

        Args:
            decision: Eligible approving Risk decision.
            attestation: Authenticated and authorized approval evidence.
            now: Caller-supplied UTC issue time.

        Returns:
            Durably issued tamper-evident token.

        Raises:
            RiskDomainError: If eligibility, authorization, signing, state, or
                audit persistence fails.
        """
        logger.info("Issuing one durable scoped Risk approval token")
        started_at = monotonic()
        checked_now = self._checked_now(now)
        if decision.state is not DecisionState.APPROVE or decision.token is not None:
            raise RiskDomainError(
                RiskErrorCode.APPROVAL_REQUIRED,
                "decision is not eligible for token issuance",
            )
        try:
            authorized = self._authorized_attestation(
                decision, attestation, checked_now
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.PERMISSION_DENIED,
                "approval authorization verification failed",
            ) from error
        if not authorized:
            raise RiskDomainError(
                RiskErrorCode.PERMISSION_DENIED,
                "approval attestation is not authorized for decision",
            )
        nonce = secrets.token_hex(32)
        expires_at = min(
            decision.expires_at,
            attestation.expires_at,
            checked_now
            + timedelta(seconds=float(self._config.approval_token_ttl_seconds)),
        )
        token_id = _hash_identity(
            decision.decision_id, attestation.attestation_id, nonce
        )
        values: dict[str, object] = {
            "contract_version": "v1",
            "schema_id": "risk.approval_token.v1",
            "token_id": token_id,
            "decision_id": decision.decision_id,
            "config_hash": decision.config_hash,
            "action": attestation.action,
            "scope": dict(attestation.scope),
            "approver_id": attestation.principal_id,
            "issued_at": checked_now,
            "expires_at": expires_at,
            "nonce": nonce,
            "request_id": decision.request_id,
            "workflow_id": decision.workflow_id,
            "correlation_id": decision.correlation_id,
        }
        token = RiskApprovalToken.model_validate(
            {**values, "signature": self._signature(values, attestation)}
        )
        try:
            outcome = self._state.save_issued(
                token, timeout_seconds=self._config.token_state_timeout_seconds
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "approval token state unavailable"
            ) from error
        if outcome not in {"saved", "already_saved"}:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "approval token state conflict"
            )
        self._audit.append(
            _audit_record(
                record_id=_hash_identity("approval.issued", token.token_id),
                event_type="risk.approval_token.issued",
                payload={"action": token.action, "scope": dict(token.scope)},
                evidence_refs={
                    "attestation": attestation.attestation_id,
                    "token": token.token_id,
                },
                config_hash=token.config_hash,
                decision_id=token.decision_id,
                occurred_at=checked_now,
                request_id=token.request_id,
                correlation_id=token.correlation_id,
            )
        )
        logger.bind(
            request_id=token.request_id,
            workflow_id=token.workflow_id,
            correlation_id=token.correlation_id,
            verdict="issued",
            reason_codes=(),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs={
                "attestation": attestation.attestation_id,
                "token": token.token_id,
            },
            config_hash=token.config_hash,
        ).info("Completed durable Risk approval-token issuance")
        return token

    def _token_values(self, token: RiskApprovalToken) -> dict[str, object]:
        """Return exact signed token fields excluding the signature.

        Args:
            token: Token whose signing material is required.

        Returns:
            Mutable canonical signing-value mapping.
        """
        logger.debug("Extracting exact signed Risk approval-token fields")
        values = token.model_dump(mode="python")
        values.pop("signature")
        return values

    def _validation_attestation_matches(
        self,
        token: RiskApprovalToken,
        attestation: ApprovalAttestation,
        now: datetime,
    ) -> bool:
        """Check an approval attestation against all signed token bindings.

        Args:
            token: Submitted signed token.
            attestation: Submitted authenticated approval evidence.
            now: Checked UTC validation time.

        Returns:
            Whether the attestation exactly matches and remains authorized.
        """
        logger.debug("Checking approval attestation against signed token bindings")
        return (
            attestation.principal_id == token.approver_id
            and attestation.action == token.action
            and dict(attestation.scope) == dict(token.scope)
            and attestation.policy_ref == token.config_hash
            and attestation.policy_version == self._config.policy_version
            and attestation.request_id == token.request_id
            and attestation.workflow_id == token.workflow_id
            and attestation.correlation_id == token.correlation_id
            and attestation.issued_at <= token.issued_at
            and now < attestation.expires_at
            and self._authorization_verifier(attestation)
        )

    def _expected_matches(
        self, token: RiskApprovalToken, expected: Mapping[str, str]
    ) -> bool:
        """Check the exact receiver-owned execution expectation mapping.

        Args:
            token: Submitted signed token.
            expected: Receiver-owned exact execution bindings.

        Returns:
            Whether keys and values exactly match the documented schema.
        """
        logger.debug("Checking exact expected action and token bindings")
        actual = {
            "action": token.action,
            "decision_id": token.decision_id,
            "config_hash": token.config_hash,
            "request_id": token.request_id,
            "workflow_id": token.workflow_id,
            "correlation_id": token.correlation_id,
            **dict(token.scope),
        }
        return dict(expected) == actual

    def _compatible_config(self, token_hash: str) -> bool:
        """Check explicit current-to-approved config-hash compatibility.

        Args:
            token_hash: Config hash bound to the submitted token.

        Returns:
            Whether the current policy explicitly accepts the hash.
        """
        logger.debug("Checking explicit approval-token config compatibility")
        current = compute_config_hash(self._config)
        return (
            token_hash == current
            or token_hash in self._config.compatible_config_hashes.get(current, ())
        )

    def _audit_validation_failure(
        self,
        token: RiskApprovalToken,
        code: RiskErrorCode,
        now: datetime,
    ) -> NoReturn:
        """Audit a failed validation and raise its stable failure code.

        Args:
            token: Submitted token.
            code: Stable failure reason.
            now: Checked UTC validation time.

        Raises:
            RiskDomainError: Always, after durable audit append.
        """
        logger.warning("Auditing failed Risk approval-token validation")
        self._audit.append(
            _audit_record(
                record_id=_hash_identity(
                    "approval.validation_failed",
                    token.token_id,
                    code.value,
                    now.isoformat(),
                ),
                event_type="risk.approval_token.validation_failed",
                payload={"reason_code": code.value},
                evidence_refs={"token": token.token_id},
                config_hash=token.config_hash,
                decision_id=token.decision_id,
                occurred_at=now,
                request_id=token.request_id,
                correlation_id=token.correlation_id,
            )
        )
        raise RiskDomainError(code, "approval token validation failed")

    def validate_reserve_and_consume(
        self,
        token: RiskApprovalToken,
        attestation: ApprovalAttestation,
        expected: Mapping[str, str],
        *,
        now: datetime,
    ) -> ApprovalValidationResult:
        """Validate, atomically reserve, consume, and authorize one action.

        Args:
            token: Submitted signed scoped token.
            attestation: Submitted authenticated approval evidence.
            expected: Exact receiver-owned action and scope bindings.
            now: Caller-supplied UTC validation time.

        Returns:
            Successful consumed result with an allowed action-policy verdict.

        Raises:
            RiskDomainError: If any signature, binding, time, config, state,
                authorization, persistence, or audit check fails.
        """
        logger.info("Validating and atomically consuming a Risk approval token")
        started_at = monotonic()
        checked_now = self._checked_now(now)
        if not self._compatible_config(token.config_hash):
            self._audit_validation_failure(
                token, RiskErrorCode.CONFIG_VERSION_MISMATCH, checked_now
            )
        if checked_now < token.issued_at or checked_now >= token.expires_at:
            self._audit_validation_failure(
                token, RiskErrorCode.APPROVAL_TOKEN_EXPIRED, checked_now
            )
        try:
            supplied_signature = self._signature(self._token_values(token), attestation)
            signature_valid = hmac.compare_digest(supplied_signature, token.signature)
            attestation_valid = self._validation_attestation_matches(
                token, attestation, checked_now
            )
        except RiskDomainError:
            raise
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.APPROVAL_TOKEN_INVALID,
                "approval token verification failed",
            ) from error
        if (
            not signature_valid
            or not attestation_valid
            or not self._expected_matches(token, expected)
        ):
            self._audit_validation_failure(
                token, RiskErrorCode.APPROVAL_TOKEN_INVALID, checked_now
            )
        reservation_id = _hash_identity(
            token.token_id, token.workflow_id, token.action, secrets.token_hex(32)
        )
        try:
            outcome = self._state.consume_if_active(
                token.token_id,
                expected_signature=token.signature,
                reservation_id=reservation_id,
                workflow_id=token.workflow_id,
                action=token.action,
                scope=token.scope,
                now=checked_now,
                timeout_seconds=self._config.token_state_timeout_seconds,
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "approval token state unavailable"
            ) from error
        failures = {
            "missing": RiskErrorCode.APPROVAL_TOKEN_INVALID,
            "expired": RiskErrorCode.APPROVAL_TOKEN_EXPIRED,
            "revoked": RiskErrorCode.APPROVAL_TOKEN_REVOKED,
            "already_consumed": RiskErrorCode.APPROVAL_TOKEN_CONSUMED,
            "conflict": RiskErrorCode.PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED,
        }
        if outcome != "consumed":
            self._audit_validation_failure(token, failures[outcome], checked_now)
        verdict = ActionPolicyVerdict(
            verdict_id=_hash_identity("action_policy", reservation_id),
            action=token.action,
            scope=token.scope,
            policy_version=self._config.policy_version,
            attestation_id=attestation.attestation_id,
            decision_id=token.decision_id,
            reservation_id=reservation_id,
            allowed=True,
            reasons=(),
            issued_at=checked_now,
            expires_at=token.expires_at,
            request_id=token.request_id,
            workflow_id=token.workflow_id,
            correlation_id=token.correlation_id,
        )
        sealed = self._audit.append(
            _audit_record(
                record_id=_hash_identity("approval.consumed", reservation_id),
                event_type="risk.approval_token.consumed",
                payload={
                    "action": token.action,
                    "scope": dict(token.scope),
                    "reservation_id": reservation_id,
                    "verdict_id": verdict.verdict_id,
                },
                evidence_refs={
                    "attestation": attestation.attestation_id,
                    "token": token.token_id,
                },
                config_hash=token.config_hash,
                decision_id=token.decision_id,
                occurred_at=checked_now,
                request_id=token.request_id,
                correlation_id=token.correlation_id,
            )
        )
        result = ApprovalValidationResult(
            valid=True,
            consumed=True,
            reason_code=None,
            audit_ref=sealed.record_hash,
            reservation_id=reservation_id,
            action_policy_verdict=verdict,
        )
        logger.bind(
            request_id=token.request_id,
            workflow_id=token.workflow_id,
            correlation_id=token.correlation_id,
            verdict="allowed",
            reason_codes=(),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs={
                "attestation": attestation.attestation_id,
                "token": token.token_id,
                "audit": result.audit_ref,
            },
            config_hash=token.config_hash,
        ).info("Completed atomic Risk approval-token consumption decision")
        return result

    def revoke_scope(
        self, scope: Mapping[str, str], reason: str, *, now: datetime
    ) -> int:
        """Revoke every outstanding token intersecting an authorized scope.

        Args:
            scope: Global or exact portfolio/strategy/symbol scope selector.
            reason: Material revocation reason.
            now: Caller-supplied UTC revocation time.

        Returns:
            Number of newly revoked tokens.

        Raises:
            RiskDomainError: If scope, permission evidence, state, or audit
                persistence fails.
        """
        logger.warning("Revoking outstanding Risk approval tokens by scope")
        started_at = monotonic()
        checked_now = self._checked_now(now)
        if not scope or not reason.strip():
            raise RiskDomainError(
                RiskErrorCode.PERMISSION_DENIED,
                "approval revocation scope and reason are required",
            )
        try:
            count = self._state.revoke_intersecting(
                scope,
                reason=reason.strip(),
                revoked_at=checked_now,
                timeout_seconds=self._config.token_state_timeout_seconds,
            )
        except Exception as error:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "approval token state unavailable"
            ) from error
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise RiskDomainError(
                RiskErrorCode.STORAGE_ERROR, "approval revocation result invalid"
            )
        config_hash = compute_config_hash(self._config)
        request_id = _hash_identity("approval.revoke.request", checked_now.isoformat())
        self._audit.append(
            _audit_record(
                record_id=_hash_identity(
                    "approval.revoked",
                    canonical_json(dict(scope)),
                    checked_now.isoformat(),
                ),
                event_type="risk.approval_token.revoked",
                payload={
                    "scope": dict(scope),
                    "reason": reason.strip(),
                    "revoked_count": count,
                },
                evidence_refs={"revocation_scope": canonical_json(dict(scope))},
                config_hash=config_hash,
                decision_id=None,
                occurred_at=checked_now,
                request_id=request_id,
                correlation_id=request_id,
            )
        )
        logger.bind(
            request_id=request_id,
            workflow_id="risk.approval.revoke",
            correlation_id=request_id,
            verdict="revoked",
            reason_codes=(reason.strip(),),
            latency_ms=round((monotonic() - started_at) * 1000, 3),
            evidence_refs={"revocation_scope": canonical_json(dict(scope))},
            config_hash=config_hash,
        ).info("Completed scoped Risk approval-token revocation decision")
        return count


__all__ = ["ApprovalTokenService"]

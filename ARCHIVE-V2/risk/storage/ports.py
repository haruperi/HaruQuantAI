"""Risk governance storage ports and contract definitions.

Defines repository protocols and data structures for persisting drawdown state,
kill switches, audit logs, policies, and decisions.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Protocol, TypedDict

from pydantic import Field

from app.services.risk.errors import RiskDataError as DataError
from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models.contracts import RiskContract
from app.utils.logger import logger
from app.utils.standard import canonical_json

if TYPE_CHECKING:
    from app.services.risk.models import (
        DrawdownState,
        KillSwitchReason,
        KillSwitchStateEnum,
        PolicyRule,
        RiskAuditEvent,
        RiskDecisionPackage,
        RiskMode,
    )
    from app.services.risk.validations import ValidationResult


class DecisionIdempotencyKey(RiskContract):
    """Idempotency compound key for identifying unique decisions.

    Attributes:
        request_id: The unique correlation request identifier.
        workflow_id: The workflow execution run identifier.
        signal_id: The strategy signal correlation identifier.
        decision_material_hash: Stable SHA256 of the decision inputs.
    """

    request_id: str = Field(..., description="Unique correlation request identifier.")
    workflow_id: str = Field(..., description="Workflow execution run identifier.")
    signal_id: str = Field("", description="Strategy signal correlation identifier.")
    decision_material_hash: str = Field(
        ..., description="Stable SHA256 of the decision inputs."
    )


class StoredRiskRecord(RiskContract):
    """Representation of a persisted risk record for schema validation.

    Attributes:
        schema_version: Major.minor.patch schema version.
        record_type: Identifier for the type of record.
        data: Raw dictionary payload of the record.
    """

    schema_version: str = Field(..., description="Major.minor.patch schema version.")
    record_type: str = Field(..., description="Identifier for the type of record.")
    data: dict[str, Any] = Field(
        default_factory=dict, description="Raw dictionary payload."
    )


class StorageCapability(RiskContract):
    """Capabilities supported by the storage engine.

    Attributes:
        supports_persistence: Whether writing is supported.
        is_durable: Whether storage is durable (non-ephemeral).
        supports_audit: Whether audit log writing is supported.
    """

    supports_persistence: bool = Field(
        True, description="Whether writing is supported."
    )
    is_durable: bool = Field(
        True, description="Whether storage is durable (non-ephemeral)."
    )
    supports_audit: bool = Field(
        True, description="Whether audit log writing is supported."
    )


class PersistenceResult(TypedDict):
    """Standard dictionary output of a persistence attempt.

    Attributes:
        success: Whether the persistence operation succeeded.
        message: Informational or error message.
        code: Unique error or status code.
        details: Extra diagnostic metadata.
    """

    success: bool
    message: str
    code: str
    details: dict[str, Any]


class RiskStateStore(Protocol):
    """Protocol for state storage operations.

    Includes drawdown state, kill switches, and token revocation.
    """

    def get_drawdown_state(
        self, strategy_id: str | None = None
    ) -> DrawdownState | None:
        """Retrieve the drawdown state for the portfolio or a specific strategy.

        Args:
            strategy_id: Optional strategy identifier.

        Returns:
            DrawdownState | None: The active drawdown state, or None.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def save_drawdown_state(
        self, state: DrawdownState, strategy_id: str | None = None
    ) -> None:
        """Save the drawdown state.

        Args:
            state: The DrawdownState model (required).
            strategy_id: Optional strategy identifier.

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If inputs are invalid or schema version mismatches.
        """
        ...

    def get_kill_switch_state(
        self, scope: str, target: str
    ) -> tuple[
        KillSwitchStateEnum, KillSwitchReason | None, datetime | None, str | None
    ]:
        """Retrieve kill-switch state tuple.

        Args:
            scope: Target scope string (e.g. 'global', 'symbol') (required).
            target: Target scope identifier (e.g. 'EURUSD', '*') (required).

        Returns:
            tuple: (state, reason, triggered_at, triggered_by)

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def save_kill_switch_state(
        self,
        scope: str,
        target: str,
        state: KillSwitchStateEnum,
        reason: KillSwitchReason | None = None,
        triggered_at: datetime | None = None,
        triggered_by: str | None = None,
    ) -> None:
        """Save kill-switch state updates.

        Args:
            scope: Target scope (required).
            target: Target identifier (required).
            state: Target KillSwitchStateEnum (required).
            reason: Optional trigger reason.
            triggered_at: Optional triggering timestamp.
            triggered_by: Optional triggering operator.

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If inputs are invalid or schema mismatches.
        """
        ...

    def is_token_revoked(self, token_id: str) -> bool:
        """Check if a decision token is marked as revoked.

        Args:
            token_id: Required token identifier.

        Returns:
            bool: True if token is revoked.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def revoke_token(self, token_id: str) -> None:
        """Revoke a decision token.

        Args:
            token_id: Required token identifier.

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If token_id is empty.
        """
        ...


class RiskAuditSink(Protocol):
    """Protocol defining write and verification access to the audit event chain."""

    def write_event(self, event: RiskAuditEvent) -> None:
        """Append a validated event block to the audit store.

        Args:
            event: The validated RiskAuditEvent block (required).

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If event is malformed or schema version mismatches.
        """
        ...

    def get_last_event(self) -> RiskAuditEvent | None:
        """Retrieve the latest audit event block in the chain.

        Returns:
            RiskAuditEvent | None: The latest event block or None.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def get_all_events(self) -> list[RiskAuditEvent]:
        """Retrieve all audit events chronologically.

        Returns:
            list[RiskAuditEvent]: Sorted audit event logs.

        Raises:
            DataError: If storage is unavailable.
        """
        ...


class RiskPolicyStore(Protocol):
    """Protocol defining read and write operations for active policy rules."""

    def get_rules(self) -> list[PolicyRule]:
        """Retrieve all active policy rules.

        Returns:
            list[PolicyRule]: Active policy rules.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def save_rule(self, rule: PolicyRule) -> None:
        """Store or update a policy rule.

        Args:
            rule: The PolicyRule model (required).

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If rule is invalid or schema version mismatches.
        """
        ...


class RiskDecisionStore(Protocol):
    """Protocol for indexing and retrieving risk governor decisions."""

    def get_decision(self, decision_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by ID.

        Args:
            decision_id: Required unique identifier.

        Returns:
            RiskDecisionPackage | None: The stored decision package or None.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def save_decision(self, decision: RiskDecisionPackage) -> None:
        """Persist decision package with idempotency handling.

        Args:
            decision: RiskDecisionPackage (required).

        Raises:
            DataError: If duplicate request/keys conflict or store is unavailable.
            ValidationError: If inputs are invalid or schema version mismatches.
        """
        ...

    def get_decision_by_request_id(self, request_id: str) -> RiskDecisionPackage | None:
        """Retrieve decision by original request ID.

        Args:
            request_id: Required original request ID.

        Returns:
            RiskDecisionPackage | None: Stored package or None.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def list_decisions(self) -> list[RiskDecisionPackage]:
        """List all stored decisions.

        Returns:
            list[RiskDecisionPackage]: All stored decisions.

        Raises:
            DataError: If storage is unavailable.
        """
        ...

    def get_decision_by_key(
        self,
        request_id: str,
        workflow_id: str,
        signal_id: str,
        decision_material_hash: str,
    ) -> RiskDecisionPackage | None:
        """Retrieve decision by original idempotency keys.

        Args:
            request_id: Required correlation request ID.
            workflow_id: Required workflow run identifier.
            signal_id: Signal identifier.
            decision_material_hash: Hash of decision material.

        Returns:
            RiskDecisionPackage | None: The matched decision package, or None.

        Raises:
            DataError: If storage is unavailable.
            ValidationError: If inputs are invalid.
        """
        ...


def compute_decision_material_hash(decision: RiskDecisionPackage) -> str:
    """Compute a deterministic hash of the decision's material inputs.

    Uses request_id, workflow_id, config_hash, policy_hash, and the proposed
    action details.

    Args:
        decision: The decision package to hash.

    Returns:
        str: Deterministic SHA256 hex digest.

    Raises:
        ValidationError: If calculation fails.
    """
    logger.debug(
        f"Computing decision material hash for decision_id={decision.decision_id}"
    )
    details = decision.details or {}
    proposed = details.get("proposed_action") or {}

    material = {
        "request_id": decision.request_id,
        "workflow_id": decision.workflow_id,
        "config_hash": decision.config_hash or "",
        "policy_hash": decision.policy_hash or "",
        "proposed_action": proposed,
    }

    def _coerce(v: Any) -> Any:  # noqa: ANN401
        if isinstance(v, Decimal):
            return float(v)
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, dict):
            return {k: _coerce(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_coerce(val) for val in v]
        return v

    try:
        canonical_data = canonical_json(_coerce(material))
        result = hashlib.sha256(canonical_data.encode()).hexdigest()
        logger.debug(f"Computed decision material hash: {result}")
        return result
    except Exception as e:
        msg = f"Failed to compute decision material hash: {e}"
        logger.error(msg)
        raise ValidationError(msg) from e


def _check_schema_version(obj: Any) -> None:  # noqa: ANN401
    """Enforce schema-version compatibility (expects major version 1)."""
    if hasattr(obj, "schema_version"):
        ver = obj.schema_version
        if ver and isinstance(ver, str):
            parts = ver.split(".")
            if parts and parts[0] != "1":
                msg = f"Schema version mismatch: expected major version 1, got {ver}"
                logger.error(msg)
                raise ValidationError(msg)


def persist_risk_decision(
    decision: RiskDecisionPackage,
    key: DecisionIdempotencyKey,
    store: RiskDecisionStore,
) -> PersistenceResult:
    """Idempotently persists a risk decision package.

    Args:
        decision: The decision package to persist.
        key: The idempotency compound key.
        store: The target decision store.

    Returns:
        PersistenceResult: Success or failure outcome.

    Raises:
        DataError: On idempotency conflict or database error.
        ValidationError: On invalid model structures.
    """
    logger.info(
        "Attempting to persist decision_id=%s (request_id=%s)",
        decision.decision_id,
        key.request_id,
    )

    # 1. Enforce schema check if present
    _check_schema_version(decision)

    # 2. Check request ID conflict
    existing_by_req = store.get_decision_by_request_id(key.request_id)
    if existing_by_req is not None:
        if existing_by_req.decision_id != decision.decision_id:
            msg = (
                f"Idempotency conflict: request_id '{key.request_id}' "
                f"already processed with decision '{existing_by_req.decision_id}'."
            )
            logger.error(msg)
            raise DataError(msg)
        # If identical decision_id, it's a same-material duplicate no-op
        logger.info(
            "Found matching decision_id by request_id (same-material duplicate, no-op)"
        )
        return {
            "success": True,
            "message": "Idempotent duplicate: no-op.",
            "code": "DUPLICATE_OK",
            "details": {"decision_id": decision.decision_id},
        }

    # 3. Check compound key conflict
    existing_by_key = store.get_decision_by_key(
        key.request_id,
        key.workflow_id,
        key.signal_id,
        key.decision_material_hash,
    )
    if existing_by_key is not None:
        if existing_by_key.decision_id != decision.decision_id:
            msg = (
                f"Idempotency conflict: decision for compound key already processed "
                f"with decision '{existing_by_key.decision_id}'."
            )
            logger.error(msg)
            raise DataError(msg)
        logger.info(
            "Found matching decision_id by compound key "
            "(same-material duplicate, no-op)"
        )
        return {
            "success": True,
            "message": "Idempotent duplicate: no-op.",
            "code": "DUPLICATE_OK",
            "details": {"decision_id": decision.decision_id},
        }

    # 4. Save decision
    try:
        store.save_decision(decision)
        logger.info(f"Successfully saved decision_id={decision.decision_id}")
        return {
            "success": True,
            "message": f"Successfully persisted decision {decision.decision_id}",
            "code": "SUCCESS",
            "details": {},
        }
    except Exception as e:
        if isinstance(e, (DataError, ValidationError)):
            raise
        msg = f"Unexpected failure persisting decision: {e}"
        logger.error(msg)
        raise DataError(msg) from e


def validate_storage_schema_compatibility(
    record: StoredRiskRecord,
    expected_version: str,
) -> ValidationResult:
    """Validates storage schema version compatibility with expected version.

    Major version mismatch results in a validation failure.

    Args:
        record: The stored risk record to validate.
        expected_version: The expected version string (e.g. '1.0.0').

    Returns:
        ValidationResult: The validation result outcome dictionary.
    """
    logger.debug(
        f"Validating storage schema compatibility. "
        f"Record version: {record.schema_version}, Expected version: {expected_version}"
    )
    rec_parts = record.schema_version.split(".")
    exp_parts = expected_version.split(".")

    if not rec_parts or not exp_parts:
        msg = (
            f"Invalid version strings: record='{record.schema_version}', "
            f"expected='{expected_version}'"
        )
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "INVALID_VERSION_FORMAT",
            "details": {},
        }

    if rec_parts[0] != exp_parts[0]:
        msg = (
            f"Major version mismatch: expected major version {exp_parts[0]}, "
            f"got {rec_parts[0]}"
        )
        logger.warning(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "SCHEMA_VERSION_MISMATCH",
            "details": {
                "record_version": record.schema_version,
                "expected_version": expected_version,
            },
        }

    logger.debug("Schema compatibility check passed.")
    return {
        "valid": True,
        "message": "Schema compatibility passed.",
        "code": "OK",
        "details": {},
    }


def require_live_audit_persistence(
    capability: StorageCapability,
    mode: RiskMode,
) -> ValidationResult:
    """Fails closed where audit storage is mandatory but unavailable or non-durable.

    Args:
        capability: The capability descriptors of the storage engine.
        mode: The active risk execution mode.

    Returns:
        ValidationResult: The validation result outcome.
    """
    logger.info(f"Checking live audit persistence requirement for mode={mode}")
    mode_str = mode.value if hasattr(mode, "value") else str(mode)
    if "live" in mode_str.lower() and (
        not capability.supports_audit or not capability.is_durable
    ):
        msg = (
            "Fail closed: durable audit sink persistence is mandatory "
            "for live execution."
        )
        logger.error(msg)
        return {
            "valid": False,
            "message": msg,
            "code": "AUDIT_PERSISTENCE_MANDATORY",
            "details": {
                "supports_audit": capability.supports_audit,
                "is_durable": capability.is_durable,
            },
        }

    logger.debug("Audit capability checks passed.")
    return {
        "valid": True,
        "message": "Audit persistence requirements satisfied.",
        "code": "OK",
        "details": {},
    }
